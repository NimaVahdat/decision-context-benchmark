"""Build real seed payloads for any scenario.

Follows the process:
1. Run real agent for initial traces (no parent)
2. Build correction traces with real eval_lookup results
3. Save as bench/seeds/{scenario_id}.json

Usage:
    uv run python bench/seedgen/build_scenario.py --scenario basic_content_qrr
    uv run python bench/seedgen/build_scenario.py --all
    uv run python bench/seedgen/build_scenario.py --list
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime


async def _run_real_agent(
    skill_slug: str,
    company: str,
    prompt: str,
    actor_id: str = "eval-runner",
    conversation_id: str | None = None,
    parent_doc_id: str | None = None,
    prior_messages: list | None = None,
) -> dict:
    """Run real agent and capture trace as payload."""
    from bench.seedgen.build_real import run_and_capture

    return await run_and_capture(
        skill_slug,
        company,
        prompt=prompt,
        actor_id=actor_id,
        conversation_id=conversation_id,
        parent_doc_id=parent_doc_id,
        prior_messages=prior_messages,
    )


async def build_scenario_seeds(scenario_id: str) -> list[dict]:
    """Build real seed payloads for a scenario."""
    from bench.scenarios import SCENARIOS

    scenario = next(
        (s for s in SCENARIOS if s.id == scenario_id),
        None,
    )
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    datetime.now(UTC).isoformat()

    # Assign conversation IDs
    conv_ids: list[str] = []
    for i, seed in enumerate(scenario.seed_traces):
        if seed.parent_index is not None:
            conv_ids.append(conv_ids[seed.parent_index])
        else:
            conv_ids.append(f"real-seed-{scenario.id}-c{i}")

    payloads: list[dict] = []

    for i, seed in enumerate(scenario.seed_traces):
        prior_msgs = None
        if seed.parent_index is not None:
            # Get the parent's raw pydantic-ai messages
            # so the correction continues the conversation
            prior_msgs = payloads[seed.parent_index].get(
                "_raw_messages",
            )

        if seed.parent_index is None:
            # Initial trace: run real agent
            print(f"  [{i}] Running agent: {seed.skill} on {seed.company}...")
            payload = await _run_real_agent(
                seed.skill,
                seed.company,
                prompt=seed.message_content,
                actor_id=seed.actor_id,
                conversation_id=conv_ids[i],
            )
        else:
            # Correction: conversation_id groups it with parent.
            # Aftermath classifier discovers the chain — no
            # explicit parent_doc_id needed.
            print(f"  [{i}] Correcting: {seed.message_content[:60]}...")
            payload = await _run_real_agent(
                seed.skill,
                seed.company,
                prompt=seed.message_content,
                actor_id=seed.actor_id,
                conversation_id=conv_ids[i],
                prior_messages=prior_msgs,
            )

        payloads.append(payload)

    # Strip _raw_messages before returning (not serializable)
    for p in payloads:
        p.pop("_raw_messages", None)

    return payloads


def _summarize_payload(payload: dict, idx: int) -> None:
    """Print a summary of a payload."""
    mh = payload["message_history"]
    tool_calls = [m for m in mh if m["role"] == "tool_call"]
    tool_results = [m for m in mh if m["role"] == "tool_result"]
    actor = payload.get("actor_id", "?")
    parent = payload.get("parent_doc_id")
    company = payload["subjects"][0]["id"]

    print(f"  [{idx}] actor={actor} company={company} parent={parent}")
    print(f"       {len(tool_calls)} tool calls, {len(tool_results)} results")

    for tc, tr in zip(tool_calls, tool_results):
        content = tr["content"]
        is_error = len(content) < 100 or '"error"' in content or '"status": "processing"' in content
        status = "ERR" if is_error else "OK"
        name = tc.get("name", "?")
        source = tc.get("arguments", {}).get("source", "?")
        print(f"       {status} {name}(source={source}) → {len(content)}ch")

    output = payload.get("outcome_summary", "")[:80]
    print(f"       output: {output}...")


async def process_scenario(scenario_id: str) -> None:
    """Process one scenario: build seeds and save."""
    from bench.scenarios import SCENARIOS

    scenario = next((s for s in SCENARIOS if s.id == scenario_id), None)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    print(f"\n{'=' * 60}")
    print(f"Processing: {scenario_id}")
    print(f"{'=' * 60}")

    payloads = await build_scenario_seeds(scenario_id)

    print(f"\nPayloads built: {len(payloads)}")
    for i, p in enumerate(payloads):
        _summarize_payload(p, i)

    output_path = scenario.real_seed_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payloads, indent=2))
    print(f"\nSaved to {output_path}")


async def main():
    parser = argparse.ArgumentParser(
        description="Build real seed traces for scenarios",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Scenario ID to process",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Rebuild seeds for all scenarios",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all scenarios and their seed status",
    )
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Only generate seeds for scenarios with stub (empty) seed files",
    )
    args = parser.parse_args()

    from bench.scenarios import SCENARIOS

    def _is_stub(s) -> bool:
        return bool(s.real_seed_file.exists() and s.real_seed_file.stat().st_size <= 3)

    if args.list:
        for s in SCENARIOS:
            status = (
                "stub" if _is_stub(s) else ("populated" if s.real_seed_file.exists() else "missing")
            )
            print(f"  [{status}] {s.id}: {s.skill}, {len(s.seed_traces)} traces")
        return

    if args.scenario:
        await process_scenario(args.scenario)
    elif args.all:
        to_process = [s for s in SCENARIOS if s.seed_traces]
        print(f"Processing {len(to_process)} scenarios...")
        for s in to_process:
            try:
                await process_scenario(s.id)
            except Exception as e:
                print(f"\n  ERROR: {s.id}: {e}")
                continue
    elif args.missing_only:
        to_process = [s for s in SCENARIOS if s.seed_traces and _is_stub(s)]
        print(f"Processing {len(to_process)} scenarios with stub seeds...")
        for s in to_process:
            try:
                await process_scenario(s.id)
            except Exception as e:
                print(f"\n  ERROR: {s.id}: {e}")
                continue
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
