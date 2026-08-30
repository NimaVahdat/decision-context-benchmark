"""Scenario runner: orchestrates control + treatment runs."""

from __future__ import annotations

import json
import logging
import time

from bench.core import usage as _usage
from bench.core.agent_interface import AgentModule
from bench.core.scoring import _combined_score
from bench.judge import judge_scenario
from bench.metrics import ScenarioResult, count_tokens
from bench.scenarios.models import Scenario

logger = logging.getLogger(__name__)


def _print_trace_sent(idx: int, total: int, trace: dict) -> None:
    """Dump the raw trace handed to the approach."""
    print(
        f"\n── capture_one [{idx + 1}/{total}] ──",
        flush=True,
    )
    print(json.dumps(trace, indent=2, default=str), flush=True)


def _load_seeds(scenario: Scenario) -> list[dict]:
    """Load seed traces for a scenario."""
    if not scenario.real_seed_file:
        raise ValueError(f"Scenario {scenario.id} has no real_seed_file.")
    data: list[dict] = json.loads(scenario.real_seed_file.read_text())
    return data


async def run_scenario(
    scenario: Scenario,
    agent_module: AgentModule,
    num_runs: int = 5,
    judge_model: str | None = None,
) -> tuple[list[ScenarioResult], list[ScenarioResult]]:
    """Run one scenario: control + treatment.

    The agent_module must satisfy the
    :class:`bench.core.agent_interface.AgentModule` Protocol.

    `prepare()` is lifecycle-only (init DB / capture / query).
    `capture_one(trace)` is called once per seed trace, in
    order. The approach must be query-ready after each
    `capture_one` returns — in the real world there is no
    signal that the next trace will ever arrive.

    Returns:
        (control_results, treatment_results)
    """
    seeds = _load_seeds(scenario)

    control_results: list[ScenarioResult] = []
    treatment_results: list[ScenarioResult] = []

    # Control runs (no injection, raw agent)
    async def _noop_tool_callback(
        tool_name: str,
        source: str,
        query_arg: str,
        tool_result: str,
    ) -> str:
        return ""

    print("  Control runs...", end="", flush=True)
    for run_idx in range(num_runs):
        t0 = time.perf_counter()
        agent_out = await agent_module.run_agent(
            skill=scenario.skill,
            query=scenario.test_query,
            company=scenario.test_company,
            injection_text="",
            tool_callback=_noop_tool_callback,
        )
        agent_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        judge_result = await judge_scenario(
            response=agent_out.output,
            scenario=scenario,
            model=judge_model,
        )
        judge_ms = (time.perf_counter() - t0) * 1000

        combined = _combined_score(
            judge_result.weighted_score,
            agent_out.output,
            agent_out.tool_calls,
            scenario,
            tool_call_details=agent_out.tool_call_details,
        )
        control_results.append(
            ScenarioResult(
                scenario_id=scenario.id,
                approach="control",
                run=run_idx,
                judge_score=combined,
                judge_reasoning=(judge_result.reasoning),
                output=agent_out.output,
                injection_tokens=0,
                agent_latency_ms=agent_ms,
                judge_latency_ms=judge_ms,
                agent_input_tokens=(agent_out.input_tokens),
                agent_output_tokens=(agent_out.output_tokens),
                agent_requests=agent_out.requests,
                agent_tool_calls=agent_out.tool_calls,
            )
        )

    ctrl_avg = sum(r.judge_score for r in control_results) / len(control_results)
    print(f" avg={ctrl_avg:.2f}")

    # Treatment run (with approach injection)
    print(
        f"  {agent_module.name if hasattr(agent_module, 'name') else 'approach'}...",
        end="",
        flush=True,
    )

    # Reset usage accumulators. Incremental capture: each
    # trace is fed one at a time and the approach must be
    # query-ready after every capture_one call.
    _usage.reset_all()
    _usage.set_phase("capture")
    t0 = time.perf_counter()
    await agent_module.prepare()
    for i, trace in enumerate(seeds):
        _print_trace_sent(i, len(seeds), trace)
        await agent_module.capture_one(trace)
    capture_ms = (time.perf_counter() - t0) * 1000
    capture_usage = _usage.get_capture()

    # Get injection. This and get_prior_messages (below) both run in the
    # query phase. Many adapters (forge, ace, awm, memp, jef) DEFER their
    # build/retrieval LLM+embedding work to get_prior_messages, so query
    # usage/latency must be captured AFTER it (see below) or the cost reads
    # as zero.
    _usage.set_phase("query")
    t0 = time.perf_counter()
    injection_text = await agent_module.get_injection(
        skill=scenario.skill,
        company=scenario.test_company,
        query=scenario.test_query,
        actor_id=scenario.test_actor_id,
        subjects=scenario.test_subjects,
    )
    injection_tokens = count_tokens(injection_text)

    # Build tool callback from approach's on_tool_result
    _tool_injection_tokens: list[int] = []
    _tool_injections: list[dict] = []

    async def _tool_callback(
        tool_name: str,
        source: str,
        query_arg: str,
        tool_result: str,
    ) -> str:
        text: str = await agent_module.on_tool_result(
            tool_name,
            source,
            query_arg,
            tool_result,
        )
        if text:
            _tool_injection_tokens.append(
                count_tokens(text),
            )
            _tool_injections.append(
                {
                    "tool": tool_name,
                    "source": source,
                    "query": query_arg,
                    "injection": text,
                }
            )
        return text

    # Optional in-conversation mode: adapters that implement
    # `get_prior_messages` return a list of `{"role", "content"}` dicts
    # to be prepended to the agent's context as actual conversation
    # history rather than as a prefix in the system prompt. Adapters
    # that don't implement it get the current behavior (None).
    prior_messages: list[dict] | None = None
    if hasattr(agent_module, "get_prior_messages"):
        try:
            prior_messages = await agent_module.get_prior_messages(
                skill=scenario.skill,
                company=scenario.test_company,
                query=scenario.test_query,
                actor_id=scenario.test_actor_id,
                subjects=scenario.test_subjects,
            )
        except Exception as e:
            import logging as _l

            _l.getLogger(__name__).warning(
                "get_prior_messages failed: %s",
                e,
            )
            prior_messages = None

    # Capture query-phase usage/latency now that BOTH get_injection and
    # get_prior_messages (deferred distillation/retrieval) have run, so the
    # build + retrieval LLM/embedding cost is included.
    query_ms = (time.perf_counter() - t0) * 1000
    query_usage = _usage.get_query()
    if injection_text or prior_messages:
        print(
            f"\n    injection={injection_tokens}tok "
            f"capture={capture_ms:.0f}ms query={query_ms:.0f}ms",
            end="",
            flush=True,
        )

    try:
        for run_idx in range(num_runs):
            _tool_injection_tokens.clear()
            _tool_injections.clear()

            pre_run_query = _usage.get_query()

            t0 = time.perf_counter()
            agent_out = await agent_module.run_agent(
                skill=scenario.skill,
                query=scenario.test_query,
                company=scenario.test_company,
                injection_text=injection_text,
                tool_callback=_tool_callback,
                prior_messages=prior_messages,
            )
            agent_ms = (time.perf_counter() - t0) * 1000

            post_run_query = _usage.get_query()
            stage2_usage = {k: post_run_query[k] - pre_run_query[k] for k in query_usage}

            tool_tok = sum(_tool_injection_tokens)
            total_injection = injection_tokens + tool_tok

            t0 = time.perf_counter()
            judge_result = await judge_scenario(
                response=agent_out.output,
                scenario=scenario,
                model=judge_model,
            )
            judge_ms = (time.perf_counter() - t0) * 1000

            combined = _combined_score(
                judge_result.weighted_score,
                agent_out.output,
                agent_out.tool_calls,
                scenario,
                tool_call_details=agent_out.tool_call_details,
            )
            treatment_results.append(
                ScenarioResult(
                    scenario_id=scenario.id,
                    approach=(agent_module.name if hasattr(agent_module, "name") else "approach"),
                    run=run_idx,
                    judge_score=combined,
                    judge_reasoning=(judge_result.reasoning),
                    output=agent_out.output,
                    injection_text=injection_text,
                    tool_injections=list(_tool_injections),
                    injection_tokens=total_injection,
                    seed_query_latency_ms=capture_ms + query_ms,
                    capture_latency_ms=capture_ms,
                    query_latency_ms=query_ms,
                    agent_latency_ms=agent_ms,
                    judge_latency_ms=judge_ms,
                    agent_input_tokens=(agent_out.input_tokens),
                    agent_output_tokens=(agent_out.output_tokens),
                    agent_requests=agent_out.requests,
                    agent_tool_calls=agent_out.tool_calls,
                    capture_llm_in=capture_usage["llm_in"],
                    capture_llm_out=capture_usage["llm_out"],
                    capture_llm_reqs=capture_usage["llm_reqs"],
                    capture_embed_in=capture_usage["embed_in"],
                    capture_embed_calls=capture_usage["embed_calls"],
                    query_llm_in=query_usage["llm_in"],
                    query_llm_out=query_usage["llm_out"],
                    query_llm_reqs=query_usage["llm_reqs"],
                    query_embed_in=query_usage["embed_in"],
                    query_embed_calls=query_usage["embed_calls"],
                    stage2_llm_in=stage2_usage["llm_in"],
                    stage2_llm_out=stage2_usage["llm_out"],
                    stage2_llm_reqs=stage2_usage["llm_reqs"],
                    stage2_embed_in=stage2_usage["embed_in"],
                    stage2_embed_calls=stage2_usage["embed_calls"],
                )
            )

        scores = [r.judge_score for r in treatment_results if r.scenario_id == scenario.id]
        avg = sum(scores) / len(scores) if scores else 0.0
        print(f" avg={avg:.2f}")
    finally:
        await agent_module.teardown()

    return control_results, treatment_results
