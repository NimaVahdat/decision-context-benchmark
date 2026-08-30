"""Build real seed trace payloads by running the actual agent.

Runs the real agent with real tools, captures the actual
pydantic-ai messages, converts them to the capture pipeline's
dict format, and saves as payloads.

Usage:
    uv run python bench/build_real_seeds.py \
        --skill eval-analyst-adaptive \
        --companies unknown-alpha.io,unknown-beta.io \
        --output bench/seeds/scenario.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _convert_messages(pydantic_messages: list) -> list[dict]:
    """Convert pydantic-ai messages to capture pipeline format.

    The capture splitter expects INTERLEAVED tool_call + tool_result
    pairs. Pydantic-ai batches them (3 calls then 3 results).
    We need to pair them up and interleave.

    Output format:
    {"role": "user", "content": "..."}
    {"role": "assistant", "content": "..."}
    {"role": "tool_call", "name": "...", "call_id": "...", "arguments": {...}}
    {"role": "tool_result", "call_id": "...", "content": "..."}
    """
    result = []

    # Collect calls and results per message pair
    pending_calls: list[dict] = []
    pending_results: list[dict] = []

    for msg in pydantic_messages:
        if not hasattr(msg, "parts"):
            continue

        for part in msg.parts:
            part_type = type(part).__name__

            if part_type == "UserPromptPart":
                result.append(
                    {
                        "role": "user",
                        "content": str(part.content),
                    }
                )

            elif part_type == "TextPart":
                content = str(part.content)
                if content:
                    result.append(
                        {
                            "role": "assistant",
                            "content": content,
                        }
                    )

            elif part_type == "ToolCallPart":
                call_id = getattr(part, "tool_call_id", None) or str(uuid.uuid4())[:8]
                args = part.args if isinstance(part.args, dict) else {}
                pending_calls.append(
                    {
                        "role": "tool_call",
                        "name": part.tool_name,
                        "call_id": call_id,
                        "arguments": args,
                        "content": f"[{part.tool_name}({json.dumps(args)})]",
                    }
                )

            elif part_type == "ToolReturnPart":
                call_id = getattr(part, "tool_call_id", None) or str(uuid.uuid4())[:8]
                pending_results.append(
                    {
                        "role": "tool_result",
                        "call_id": call_id,
                        "content": str(part.content),
                    }
                )

        # After each message, interleave pending calls+results
        if pending_calls and pending_results:
            for call, res in zip(
                pending_calls,
                pending_results,
            ):
                result.append(call)
                result.append(res)
            pending_calls = []
            pending_results = []

    # Flush any remaining
    for call in pending_calls:
        result.append(call)
    for res in pending_results:
        result.append(res)

    return result


async def run_and_capture(
    skill_slug: str,
    company: str,
    prompt: str | None = None,
    actor_id: str = "eval-runner",
    conversation_id: str | None = None,
    parent_doc_id: str | None = None,
    prior_messages: list | None = None,
) -> dict:
    """Run the agent for real and return a capture payload.

    Args:
        prompt: Custom prompt. Defaults to "Analyze {company}".
        actor_id: Actor ID for the payload.
        conversation_id: Conversation ID for linking traces.
        parent_doc_id: Parent document ID for correction chains.
        prior_messages: pydantic-ai message history from a
            previous run. When set, the agent continues the
            conversation (multi-turn correction).
    """

    os.environ.setdefault(
        "EVAL_FIXTURES_DIR",
        str(Path(__file__).resolve().parent.parent / "fixtures"),
    )

    from bench.tools.eval_lookup import _cache, eval_lookup

    _cache.clear()

    from pydantic_ai import Agent, FunctionToolset
    from pydantic_ai.settings import ModelSettings

    from bench.core import (
        _load_skill_model,
        _load_skill_prompt,
        _resolve_model,
    )

    system_prompt = _load_skill_prompt(skill_slug)
    skill_model = _load_skill_model(skill_slug)

    provider_config = {
        "vertexai-anthropic": {
            "project": os.environ.get("GCP_PROJECT_ID", ""),
            "location": os.environ.get(
                "CP_LOCATION_ANTHROPIC",
                os.environ.get("GCP_LOCATION", "us-east5"),
            ),
        },
    }
    model = _resolve_model(skill_model, provider_config)

    toolset = FunctionToolset()
    toolset.add_function(eval_lookup, name="eval_lookup")

    if "async" in skill_slug:
        from bench.tools.async_lookup import async_lookup, reset_counts

        reset_counts()
        toolset.add_function(async_lookup, name="async_lookup")

    if "support" in skill_slug:
        from bench.tools.support_lookup import _cache as _sup_cache
        from bench.tools.support_lookup import support_lookup

        _sup_cache.clear()
        toolset.add_function(support_lookup, name="support_lookup")

    if "researcher" in skill_slug:
        from bench.tools.web_search import web_search

        toolset.add_function(web_search, name="web_search")

    agent = Agent(
        model,
        instructions=system_prompt,
        toolsets=[toolset],
        model_settings=ModelSettings(temperature=0),
    )

    user_prompt = prompt or f"Analyze {company}"
    result = await agent.run(
        user_prompt,
        message_history=prior_messages,
    )

    # Convert real pydantic-ai messages to capture format.
    # For multi-turn, only convert the NEW messages (skip
    # prior history so the payload only has this turn).
    all_msgs = result.all_messages()
    if prior_messages:
        new_msgs = all_msgs[len(prior_messages) :]
    else:
        new_msgs = all_msgs
    message_history = _convert_messages(new_msgs)

    ts = datetime.now(UTC).isoformat()

    payload = {
        "skill_name": skill_slug,
        "skill_version": "eval-v2",
        "actor_id": actor_id,
        "actor_type": "agent",
        "subjects": [{"id": company, "name": company}],
        "conversation_id": (conversation_id or f"real-seed-{company}"),
        "parent_doc_id": parent_doc_id,
        "timestamp": ts,
        "outcome_summary": result.output[:200],
        "message_history": message_history,
    }

    # Return raw pydantic-ai messages so caller can
    # continue the conversation for multi-turn corrections
    payload["_raw_messages"] = result.all_messages()  # type: ignore[assignment]

    return payload


async def main():
    parser = argparse.ArgumentParser(
        description="Build real seed traces",
    )
    parser.add_argument("--skill", type=str, required=True)
    parser.add_argument(
        "--companies",
        type=str,
        required=True,
        help="Comma-separated company list",
    )
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    companies = [c.strip() for c in args.companies.split(",")]

    payloads = []
    for company in companies:
        print(f"Running {args.skill} on {company}...")
        payload = await run_and_capture(args.skill, company)

        # Summarize
        tool_calls = [m for m in payload["message_history"] if m["role"] == "tool_call"]
        tool_results = [m for m in payload["message_history"] if m["role"] == "tool_result"]
        print(f"  Tool calls: {len(tool_calls)}")
        for tc, tr in zip(tool_calls, tool_results):
            content = tr["content"]
            is_error = (
                len(content) < 100 or '"error"' in content or '"status": "processing"' in content
            )
            status = "❌" if is_error else "✅"
            print(
                f"  {status} {tc.get('name', '?')}"
                f"({tc.get('arguments', {})}) "
                f"→ {len(content)} chars"
            )
        print(f"  Output: {payload['outcome_summary'][:100]}...")
        print()

        payloads.append(payload)

    formatted = json.dumps(payloads, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        Path(args.output).write_text(formatted)
        print(f"Saved {len(payloads)} payloads to {args.output}")
    else:
        print(formatted)


if __name__ == "__main__":
    asyncio.run(main())
