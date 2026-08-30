"""Result I/O: save, load, and check cached results."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from bench.core.config import RESULTS_DIR
from bench.metrics import ScenarioResult

logger = logging.getLogger(__name__)


def save_results(
    scenario_id: str,
    approach: str,
    results: list[ScenarioResult],
) -> Path:
    """Save results JSON for a scenario x approach."""
    approach_dir = RESULTS_DIR / approach
    approach_dir.mkdir(parents=True, exist_ok=True)

    # Per-scenario cost fields persisted so token/latency aggregate across a
    # self-healing multi-invocation run (capture = build cost, query = retrieval
    # cost, stage2 = per-tool, agent_* = injected-context inference overhead).
    _COST_FIELDS = (
        "seed_query_latency_ms",
        "capture_latency_ms",
        "query_latency_ms",
        "agent_latency_ms",
        "judge_latency_ms",
        "agent_input_tokens",
        "agent_output_tokens",
        "agent_requests",
        "agent_tool_calls",
        "capture_llm_in",
        "capture_llm_out",
        "capture_llm_reqs",
        "capture_embed_in",
        "capture_embed_calls",
        "query_llm_in",
        "query_llm_out",
        "query_llm_reqs",
        "query_embed_in",
        "query_embed_calls",
        "stage2_llm_in",
        "stage2_llm_out",
        "stage2_llm_reqs",
        "stage2_embed_in",
        "stage2_embed_calls",
    )
    data = [
        {
            "scenario_id": r.scenario_id,
            "approach": r.approach,
            "run": r.run,
            "judge_score": r.judge_score,
            "judge_reasoning": r.judge_reasoning,
            "output": r.output,
            "injection_text": r.injection_text,
            "tool_injections": r.tool_injections or [],
            "injection_tokens": r.injection_tokens,
            **{f: getattr(r, f) for f in _COST_FIELDS},
        }
        for r in results
    ]

    path = approach_dir / f"{scenario_id}.json"
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def load_results(
    scenario_id: str,
    approach: str,
    expected_runs: int | None = None,
) -> list[ScenarioResult] | None:
    """Load cached results for a scenario x approach."""
    path = RESULTS_DIR / approach / f"{scenario_id}.json"
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    if expected_runs and len(data) != expected_runs:
        return None

    return [
        ScenarioResult(
            scenario_id=r["scenario_id"],
            approach=r["approach"],
            run=r["run"],
            judge_score=r["judge_score"],
            judge_reasoning=r.get(
                "judge_reasoning",
                "",
            ),
            output=r.get("output", ""),
            injection_text=r.get(
                "injection_text",
                "",
            ),
            tool_injections=r.get(
                "tool_injections",
                [],
            ),
            injection_tokens=r.get(
                "injection_tokens",
                0,
            ),
            **{
                f: r[f]
                for f in (
                    "seed_query_latency_ms",
                    "capture_latency_ms",
                    "query_latency_ms",
                    "agent_latency_ms",
                    "judge_latency_ms",
                    "agent_input_tokens",
                    "agent_output_tokens",
                    "agent_requests",
                    "agent_tool_calls",
                    "capture_llm_in",
                    "capture_llm_out",
                    "capture_llm_reqs",
                    "capture_embed_in",
                    "capture_embed_calls",
                    "query_llm_in",
                    "query_llm_out",
                    "query_llm_reqs",
                    "query_embed_in",
                    "query_embed_calls",
                    "stage2_llm_in",
                    "stage2_llm_out",
                    "stage2_llm_reqs",
                    "stage2_embed_in",
                    "stage2_embed_calls",
                )
                if f in r
            },
        )
        for r in data
    ]


def has_cached_results(
    scenario_id: str,
    approaches: list[str],
    num_runs: int,
) -> bool:
    """Check if all results exist for a scenario."""
    ctrl = load_results(
        scenario_id,
        "control",
        num_runs,
    )
    if ctrl is None:
        return False
    return all(load_results(scenario_id, a, num_runs) is not None for a in approaches)
