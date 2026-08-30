"""DC Bench CLI.

The bench is provider- and approach-pluggable. You point ``--agent`` at
one or more Python files that satisfy the
:class:`bench.core.agent_interface.AgentModule` Protocol; the bench
runs control + treatment for each scenario and writes results under
``bench/results/<approach>[<suffix>]/``.

Usage examples::

    # Raw control baseline:
    uv run python -m bench.run --agent bench/agent.py --all

    # One approach on one scenario:
    uv run python -m bench.run --agent examples/agent_template.py \
        --scenario basic_format_table --runs 1

    # Multiple approaches on a suite:
    uv run python -m bench.run \
        --agent examples/agent_template.py,path/to/other_agent.py \
        --suite basic --runs 3

    # Override the agent model (sets BENCH_AGENT_MODEL):
    uv run python -m bench.run --agent examples/agent_template.py \
        --all --model vertexai-anthropic:claude-opus-4-7

    # Override the judge model (sets BENCH_JUDGE_MODEL):
    uv run python -m bench.run --agent examples/agent_template.py \
        --all --judge-model openai:gpt-4.1

    # Discover bundled example agents:
    uv run python -m bench.run --list-examples
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from types import ModuleType

from dotenv import load_dotenv

load_dotenv()

from bench.core.agent_interface import AgentModule  # noqa: E402
from bench.core.config import _resolve_model  # noqa: E402
from bench.core.orchestrator import run_scenario  # noqa: E402
from bench.core.results import (  # noqa: E402
    save_results,
)
from bench.metrics import (  # noqa: E402
    ScenarioResult,
    aggregate_results,
    compute_lift,
    format_report,
)
from bench.scenarios import SCENARIOS  # noqa: E402

logger = logging.getLogger(__name__)

from bench.core.config import RESULTS_DIR  # noqa: E402  (honors BENCH_RESULTS_DIR)

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

# -- Suites --------------------------------------------------

SUITES: dict[str, list[str]] = {
    "basic": [
        "basic_format_table",
        "basic_content_qrr",
        "basic_terminology_ebitda",
    ],
    "chains": [
        "chain_conflicting",
        "chain_accumulating_5",
        "chain_superseding",
    ],
    "data": [
        "data_threshold_stage",
        "data_conditional_growth",
        "data_negation_runway",
    ],
    "long": [
        "long_10msg_scattered",
        "long_20msg_early",
        "long_volume_distraction",
    ],
    "actors": [
        "actor_conflict",
        "actor_cross_user",
        "actor_3user",
    ],
    "fast": [
        "basic_format_table",
        "basic_content_qrr",
        "chain_conflicting",
    ],
    "key": [
        "basic_format_table",
        "basic_content_qrr",
        "chain_conflicting",
        "data_threshold_stage",
    ],
    "advanced": [
        "data_threshold_stage",
        "data_conditional_growth",
        "long_volume_distraction",
        "session_5conv",
        "evidence_informed_by",
    ],
    "self_assess": [
        "self_assess_recurring_failure",
        "self_assess_cross_subject",
        "self_assess_retry",
        "query_learn_pattern",
        "query_avoid_bad_pattern",
    ],
}


def _normalize_model_string(short: str) -> str:
    """Accept either ``provider:model`` or a bare model id.

    Bare model ids get a best-effort provider prefix so the user can
    type ``--model claude-opus-4-7`` instead of the long form.
    """
    if ":" in short:
        return short
    s = short.lower()
    if s.startswith("gpt"):
        return f"openai:{short}"
    if s.startswith("claude"):
        return f"vertexai-anthropic:{short}"
    return short


def _auto_name_suffix(model: str | None) -> str:
    """Derive a results-dir suffix from a model name.

    Keeps cross-model runs from clobbering each other under
    ``bench/results/<approach>/``.
    """
    if not model:
        return ""
    s = model.lower().split(":")[-1]
    if "haiku-4-5" in s:
        return ""  # Haiku is the canonical default, no suffix
    if "haiku" in s:
        return "_haiku"
    if "sonnet-4-5" in s:
        return "_sonnet45"
    if "sonnet" in s:
        return "_sonnet"
    if "opus-4-5" in s:
        return "_opus45"
    if "opus-4-6" in s:
        return "_opus46"
    if "opus-4-7" in s:
        return "_opus47"
    if "opus" in s:
        return "_opus"
    if "gpt-4.1" in s:
        return "_gpt41"
    if "gpt-5.5" in s:
        return "_gpt55"
    if "gpt-5" in s:
        return "_gpt5"
    if "gpt" in s:
        return "_gpt"
    return ""


def _load_agent_module(agent_path: str) -> ModuleType:
    """Load an agent file as a module from a filesystem path."""
    path = Path(agent_path).resolve()
    if not path.exists():
        print(f"ERROR: Agent file not found: {path}")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location(
        f"agent_module_{path.stem}",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _list_examples() -> list[Path]:
    """Return paths of bundled ``examples/agent_*.py`` files, sorted."""
    if not EXAMPLES_DIR.exists():
        return []
    return sorted(EXAMPLES_DIR.glob("agent_*.py"))


def _resolve_scenarios(
    scenarios_arg: str | None,
    scenario_arg: str | None,
    suite: str | None,
    run_all: bool,
):
    """Resolve the scenario list from any of the CLI selectors."""
    all_list = list(SCENARIOS)

    if run_all:
        return all_list

    if suite and suite in SUITES:
        suite_ids = SUITES[suite]
        return [s for s in all_list if s.id in suite_ids]

    if scenarios_arg:
        wanted = [s.strip() for s in scenarios_arg.split(",") if s.strip()]
        out = [s for s in all_list if any(w in s.id for w in wanted)]
        if not out:
            raise SystemExit(f"No scenarios matched any of: {wanted}")
        return out

    if scenario_arg:
        out = [s for s in all_list if scenario_arg in s.id]
        if not out:
            raise SystemExit(f"No scenario matched '{scenario_arg}'")
        return out

    raise SystemExit(
        "Specify one of: --all, --suite <name>, --scenario <id>, or --scenarios <a,b,c>."
    )


async def _run_one_approach(
    agent_path: str,
    save_suffix: str,
    scenarios: list,
    num_runs: int,
    judge_model: str | None,
) -> tuple[list[ScenarioResult], list[ScenarioResult], str]:
    """Run control + treatment for one approach across all scenarios.

    Returns (control_results, treatment_results, save_name).
    """
    agent_module: AgentModule = _load_agent_module(agent_path)  # type: ignore[assignment]
    base_name = agent_module.name if hasattr(agent_module, "name") else Path(agent_path).stem
    save_name = f"{base_name}{save_suffix}"

    await agent_module.setup()

    all_control: list[ScenarioResult] = []
    all_treatment: list[ScenarioResult] = []

    try:
        for scenario in scenarios:
            print(f"\n{scenario.id}: {scenario.name}")
            if scenario.description:
                print(f"  ({scenario.description})")

            control, treatment = await run_scenario(
                scenario=scenario,
                agent_module=agent_module,
                num_runs=num_runs,
                judge_model=judge_model,
            )

            all_control.extend(control)
            all_treatment.extend(treatment)

            save_results(scenario.id, "control", control)
            if treatment:
                save_results(scenario.id, save_name, treatment)
    finally:
        try:
            await agent_module.teardown()
        except Exception as exc:
            logger.warning("teardown failed for %s: %s", save_name, exc)

    return all_control, all_treatment, save_name


def _write_full_results(
    all_control: list[ScenarioResult],
    treatment_by_name: dict[str, list[ScenarioResult]],
) -> Path:
    """Serialize per-run records to ``results/full_results.json``."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    full_path = RESULTS_DIR / "full_results.json"
    full_data: dict[str, object] = {
        "control": [
            {
                "scenario_id": r.scenario_id,
                "run": r.run,
                "judge_score": r.judge_score,
                "injection_tokens": r.injection_tokens,
                "agent_latency_ms": round(r.agent_latency_ms, 0),
                "agent_input_tokens": r.agent_input_tokens,
                "agent_output_tokens": r.agent_output_tokens,
                "agent_requests": r.agent_requests,
                "agent_tool_calls": r.agent_tool_calls,
            }
            for r in all_control
        ],
        "treatment": [
            {
                "scenario_id": r.scenario_id,
                "approach": r.approach,
                "run": r.run,
                "judge_score": r.judge_score,
                "injection_tokens": r.injection_tokens,
                "seed_query_latency_ms": round(r.seed_query_latency_ms, 0),
                "agent_latency_ms": round(r.agent_latency_ms, 0),
                "agent_input_tokens": r.agent_input_tokens,
                "agent_output_tokens": r.agent_output_tokens,
                "agent_requests": r.agent_requests,
                "agent_tool_calls": r.agent_tool_calls,
            }
            for results in treatment_by_name.values()
            for r in results
        ],
    }
    full_path.write_text(json.dumps(full_data, indent=2) + "\n")
    return full_path


async def main(
    agent_paths: list[str],
    scenarios: list,
    num_runs: int,
    name_suffix: str,
    judge_model: str | None,
) -> None:
    """Run evaluation against one or more agent files."""
    # Smoke-check judge credentials early so we fail fast.
    from bench.judge.llm import JUDGE_MODEL

    effective_judge = judge_model or JUDGE_MODEL
    try:
        _resolve_model(effective_judge)
    except Exception as exc:
        print(
            f"ERROR: cannot resolve judge model '{effective_judge}': {exc}. "
            "Set BENCH_JUDGE_MODEL or pass --judge-model."
        )
        sys.exit(1)

    print(
        f"DC Bench Evaluation\n"
        f"Agents          : {', '.join(agent_paths)}\n"
        f"Scenarios       : {len(scenarios)}\n"
        f"Runs per cond.  : {num_runs}\n"
        f"Agent model     : {os.environ.get('BENCH_AGENT_MODEL', '(skill default)')}\n"
        f"Judge model     : {effective_judge}\n"
        f"Name suffix     : {name_suffix or '(none)'}\n"
    )

    all_control: list[ScenarioResult] = []
    treatment_by_name: dict[str, list[ScenarioResult]] = {}

    for agent_path in agent_paths:
        print(f"\n=== {agent_path} ===")
        control, treatment, save_name = await _run_one_approach(
            agent_path=agent_path,
            save_suffix=name_suffix,
            scenarios=scenarios,
            num_runs=num_runs,
            judge_model=judge_model,
        )
        # Control only needs to be aggregated once even with multiple
        # agents, but each agent runs its own control loop so we just
        # collect them all.
        all_control.extend(control)
        treatment_by_name[save_name] = treatment

    # Aggregate and report
    ctrl_agg = aggregate_results(all_control)
    treat_all = [r for results in treatment_by_name.values() for r in results]
    treat_agg = aggregate_results(treat_all)

    report = format_report(
        ctrl_agg,
        treat_agg,
        list(treatment_by_name.keys()),
    )
    print(f"\n{report}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / "report.txt"
    report_path.write_text(report + "\n")
    print(f"\nReport saved to: {report_path}")

    full_path = _write_full_results(all_control, treatment_by_name)
    print(f"Full results saved to: {full_path}")

    # Verification
    print("\n--- Verification ---")
    lifts = compute_lift(ctrl_agg, treat_agg)
    for name in treatment_by_name:
        high_lift = sum(1 for sid_lifts in lifts.values() if sid_lifts.get(name, 0) > 0.5)
        if high_lift >= 3:
            print(f"PASS: {name} has lift > 0.5 on {high_lift} scenarios")

    if treat_agg:
        print("PASS: Approaches produced results")
    else:
        print("FAIL: No treatment results")

    high_variance = [r for r in treat_agg if r.score_range > 0.3]
    if high_variance:
        print(f"WARN: {len(high_variance)} results with score range > 0.3")
    else:
        print("PASS: Judge scores consistent (range < 0.3)")


def cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DC Bench Evaluation",
    )
    parser.add_argument(
        "--agent",
        type=str,
        default=None,
        help=(
            "Path to agent file, or comma-separated list of paths. "
            "Each file must satisfy the AgentModule Protocol."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios.",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Filter to a single scenario id (substring match).",
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        default=None,
        help="Comma-separated scenario id substrings.",
    )
    parser.add_argument(
        "--suite",
        choices=list(SUITES.keys()),
        help="Run a predefined scenario suite.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Runs per condition (default: 5).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=(
            "Override the agent model. Accepts provider:model "
            "(openai:gpt-4.1) or a short alias (claude-opus-4-7). "
            "Sets BENCH_AGENT_MODEL."
        ),
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default=None,
        help=("Override the LLM judge model. provider:model format. Sets BENCH_JUDGE_MODEL."),
    )
    parser.add_argument(
        "--name-suffix",
        type=str,
        default=None,
        help=(
            "Suffix appended to each approach name when saving results. "
            "Auto-derived from --model if omitted."
        ),
    )
    parser.add_argument(
        "--list-examples",
        action="store_true",
        help="List bundled example agents under examples/ and exit.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    args = parser.parse_args()

    if args.list_examples:
        examples = _list_examples()
        if not examples:
            print("No example agents found under examples/.")
        else:
            print("Available example agents:")
            for p in examples:
                rel = p.relative_to(Path.cwd()) if p.is_relative_to(Path.cwd()) else p
                print(f"  {rel}")
        sys.exit(0)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    if not args.agent:
        print("ERROR: --agent is required (or use --list-examples).")
        parser.print_help()
        sys.exit(1)

    if not (args.all or args.scenario or args.scenarios or args.suite):
        parser.print_help()
        sys.exit(1)

    if args.model:
        os.environ["BENCH_AGENT_MODEL"] = _normalize_model_string(args.model)
    if args.judge_model:
        os.environ["BENCH_JUDGE_MODEL"] = args.judge_model

    suffix = args.name_suffix if args.name_suffix is not None else _auto_name_suffix(args.model)

    agent_paths = [p.strip() for p in args.agent.split(",") if p.strip()]
    scenarios = _resolve_scenarios(
        scenarios_arg=args.scenarios,
        scenario_arg=args.scenario,
        suite=args.suite,
        run_all=args.all,
    )

    asyncio.run(
        main(
            agent_paths=agent_paths,
            scenarios=scenarios,
            num_runs=args.runs,
            name_suffix=suffix,
            judge_model=args.judge_model,
        )
    )


if __name__ == "__main__":
    cli()
