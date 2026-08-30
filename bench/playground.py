"""Playground — manually inject text and see agent behavior.

Usage:
    uv run python -m bench.playground --scenario self_assess_recurring_failure

    Then type your injection text and press Enter twice (empty line) to run.
    Type 'quit' to exit.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

from bench.core import (
    AgentResult,
    _run_agent,
)
from bench.judge import evaluate_checks, judge_scenario
from bench.scenarios import SCENARIOS


def _find_scenario(filter_str: str):
    matches = [s for s in SCENARIOS if filter_str in s.id]
    if not matches:
        print(f"No scenario matching '{filter_str}'")
        print("Available:")
        for s in SCENARIOS:
            if "self_assess" in s.id or "behavioral" in s.id or "query" in s.id:
                print(f"  {s.id}")
        sys.exit(1)
    if len(matches) > 1:
        print(f"Multiple matches for '{filter_str}':")
        for s in matches:
            print(f"  {s.id}")
        sys.exit(1)
    return matches[0]


async def _print_result(
    label: str,
    agent_out: AgentResult,
    scenario,
    elapsed_ms: float,
):
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(f"\nTool calls: {agent_out.tool_calls}")
    if agent_out.tool_call_details:
        for d in agent_out.tool_call_details:
            print(f"  - {d.tool_name}(source={d.source}, query={d.query})")
    print(f"\nTokens: in={agent_out.input_tokens} out={agent_out.output_tokens}")
    print(f"Latency: {elapsed_ms:.0f}ms")

    print("\n--- OUTPUT ---")
    print(agent_out.output)

    checks = getattr(scenario, "behavior_checks", [])
    if checks:
        results, score = evaluate_checks(
            agent_out.output,
            agent_out.tool_calls,
            checks,
            tool_call_details=agent_out.tool_call_details,
        )
        print(f"\n--- PROGRAMMATIC CHECKS (score={score:.2f}) ---")
        for name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {name}")
    else:
        # Use LLM judge for scenarios without behavior_checks
        judge_result = await judge_scenario(
            response=agent_out.output,
            scenario=scenario,
        )
        print(f"\n--- LLM JUDGE (score={judge_result.weighted_score:.2f}) ---")
        print(f"  Reasoning: {judge_result.reasoning}")
        for criterion, score in judge_result.scores.items():
            status = "✅" if score >= 0.8 else "⚠️" if score >= 0.5 else "❌"
            print(f"  {status} {score:.1f}: {criterion[:80]}")


async def run_playground(
    scenario_filter: str,
    inject_file: str | None = None,
):
    scenario = _find_scenario(scenario_filter)

    print(f"\n📋 Scenario: {scenario.id}")
    print(f"   Skill: {scenario.skill}")
    print(f"   Test: {scenario.test_query}")
    print(f"   Company: {scenario.test_company}")
    if scenario.behavior_checks:
        print(f"   Checks: {[c.name for c in scenario.behavior_checks]}")
    if scenario.rubric:
        print(f"   Rubric: {[r.criterion[:50] for r in scenario.rubric]}")

    # Run control first
    print("\n🔄 Running control (no injection)...")
    t0 = time.perf_counter()
    control_out = await _run_agent(
        skill_slug=scenario.skill,
        query=scenario.test_query,
        company=scenario.test_company,
    )
    control_ms = (time.perf_counter() - t0) * 1000
    await _print_result("CONTROL (no injection)", control_out, scenario, control_ms)

    # If inject-file provided, run once and exit
    if inject_file:
        from pathlib import Path

        injection = Path(inject_file).read_text()
        print(f"\n🔄 Running with injection from {inject_file} ({len(injection)} chars)...")
        t0 = time.perf_counter()
        agent_out = await _run_agent(
            skill_slug=scenario.skill,
            query=scenario.test_query,
            company=scenario.test_company,
            injection_text=injection,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        await _print_result(
            f"WITH INJECTION from {inject_file}",
            agent_out,
            scenario,
            elapsed_ms,
        )
        return

    # Interactive loop
    while True:
        print(f"\n{'=' * 60}")
        print("Type injection text. Type END on its own line to run.")
        print("Type 'quit' to exit.")
        print(f"{'=' * 60}")

        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip().lower() == "quit":
                print("Bye!")
                return
            if line.strip() == "END":
                break
            lines.append(line)

        if not lines:
            continue

        injection = "\n".join(lines)
        print(f"\n🔄 Running with injection ({len(injection)} chars)...")

        t0 = time.perf_counter()
        agent_out = await _run_agent(
            skill_slug=scenario.skill,
            query=scenario.test_query,
            company=scenario.test_company,
            injection_text=injection,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        await _print_result(
            f"WITH INJECTION ({len(injection)} chars)",
            agent_out,
            scenario,
            elapsed_ms,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Playground — inject text and see agent behavior",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        required=True,
        help="Scenario ID substring",
    )
    parser.add_argument(
        "--inject-file",
        type=str,
        default=None,
        help="File containing injection text (skips interactive mode)",
    )
    args = parser.parse_args()
    asyncio.run(run_playground(args.scenario, args.inject_file))


if __name__ == "__main__":
    main()
