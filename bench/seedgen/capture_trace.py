"""Capture a real agent trace for a scenario.

Runs the actual skill with real tools on a given company,
captures the full trace (tool calls, results, output), and
prints it as JSON that can be used for seed trace construction.

Usage:
    uv run python bench/capture_real_trace.py --skill eval-analyst-adaptive --company unknown-alpha.io
    uv run python bench/capture_real_trace.py --skill eval-analyst-async --company unknown-alpha.io
    uv run python bench/capture_real_trace.py --skill eval-researcher --company delve.co
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time


async def capture_trace(
    skill_slug: str,
    company: str,
) -> dict:
    """Run the skill with real tools and capture everything."""

    os.environ.setdefault(
        "EVAL_FIXTURES_DIR",
        str(__import__("pathlib").Path(__file__).resolve().parent.parent / "fixtures"),
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
                "GCP_LOCATION_ANTHROPIC",
                "global",
            ),
        },
    }
    model = _resolve_model(skill_model, provider_config)

    # Track all tool calls with full details
    call_log: list[dict] = []

    toolset = FunctionToolset()

    # Wire eval_lookup
    def _tracked_eval_lookup(source: str, query: str) -> str:
        result = eval_lookup(source, query)
        call_log.append(
            {
                "tool": "eval_lookup",
                "args": {"source": source, "query": query},
                "result": result,
                "result_len": len(result),
            }
        )
        return result

    _tracked_eval_lookup.__doc__ = eval_lookup.__doc__
    toolset.add_function(_tracked_eval_lookup, name="eval_lookup")

    # Wire async_lookup if needed
    if "async" in skill_slug:
        from bench.tools.async_lookup import async_lookup, reset_counts

        reset_counts()

        def _tracked_async(source: str, query: str) -> str:
            result = async_lookup(source, query)
            call_log.append(
                {
                    "tool": "async_lookup",
                    "args": {"source": source, "query": query},
                    "result": result,
                    "result_len": len(result),
                }
            )
            return result

        _tracked_async.__doc__ = "Look up company data. source='premium' or 'basic'."
        toolset.add_function(_tracked_async, name="async_lookup")

    # Wire web_search if needed
    if "researcher" in skill_slug:
        from bench.tools.web_search import web_search

        def _tracked_search(query: str) -> str:
            result = web_search(query)
            call_log.append(
                {
                    "tool": "web_search",
                    "args": {"query": query},
                    "result": result,
                    "result_len": len(result),
                }
            )
            return result

        _tracked_search.__doc__ = "Search for company info."
        toolset.add_function(_tracked_search, name="web_search")

    agent = Agent(
        model,
        instructions=system_prompt,
        toolsets=[toolset],
        model_settings=ModelSettings(temperature=0),
    )

    t0 = time.perf_counter()
    result = await agent.run(f"Analyze {company}")
    elapsed = (time.perf_counter() - t0) * 1000

    usage = result.usage()

    return {
        "skill": skill_slug,
        "company": company,
        "tool_calls": [
            {
                "tool": c["tool"],
                "args": c["args"],
                "result_len": c["result_len"],
                "result_preview": c["result"][:200],
            }
            for c in call_log
        ],
        "full_tool_results": [
            {
                "tool": c["tool"],
                "args": c["args"],
                "result": c["result"],
            }
            for c in call_log
        ],
        "output": result.output,
        "tool_call_count": usage.tool_calls,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "latency_ms": round(elapsed),
    }


async def main():
    parser = argparse.ArgumentParser(
        description="Capture real agent trace",
    )
    parser.add_argument(
        "--skill",
        type=str,
        required=True,
        help="Skill slug (e.g. eval-analyst-adaptive)",
    )
    parser.add_argument(
        "--company",
        type=str,
        required=True,
        help="Company to analyze (e.g. unknown-alpha.io)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Save trace to file (default: print to stdout)",
    )
    args = parser.parse_args()

    trace = await capture_trace(args.skill, args.company)

    formatted = json.dumps(trace, indent=2)

    if args.output:
        from pathlib import Path

        Path(args.output).write_text(formatted)
        print(f"Saved to {args.output}")
    else:
        print(formatted)


if __name__ == "__main__":
    asyncio.run(main())
