"""Benchmark agent template.

This is the file you copy and modify to test your approach.
The APPROACH HOOKS section is where you add your context
injection logic. The AGENT section below runs the skill —
you usually don't need to modify it.

Usage:
    # Run raw (no approach, control baseline):
    uv run python -m bench.run --agent bench/agent.py --all

    # Run with your approach:
    uv run python -m bench.run --agent path/to/your_agent.py --all

How it works:
    1. setup() is called once at start
    2. For each scenario:
       a. prepare() — initialize your approach (DB / state)
       b. capture_one(trace) — called once per seed trace, in order.
          Your approach MUST be query-ready after each call;
          there is no signal that another trace will arrive.
       c. get_injection(...) — return text to prepend to the prompt
       d. The benchmark runs the agent with your injection
       e. on_tool_result(...) — optionally inject after each tool call
       f. teardown() — clean up for next scenario
    3. The benchmark judges the agent's output against the rubric
"""

from __future__ import annotations

from bench.core.agent import AgentResult, _run_agent

# ═══════════════════════════════════════════════════════
# APPROACH HOOKS — modify these to test your approach
# ═════════════════════════════════════════���═════════════


async def setup() -> None:
    """Called once at start. Set up your approach."""
    pass


async def prepare() -> None:
    """Called per scenario. Initialize DB / approach state.

    No arguments — seed traces arrive one at a time via
    capture_one.
    """
    pass


async def capture_one(trace: dict) -> None:
    """Called once per seed trace, in order.

    The approach must be query-ready (i.e. get_injection
    must work) after this returns — in the real world
    there is no signal that another trace will arrive.

    Each trace is a dict with:
        skill_name, actor_id, subjects, conversation_id,
        parent_doc_id, outcome_summary, message_history
    """
    pass


async def get_injection(
    skill: str,
    company: str,
    query: str,
    actor_id: str | None = None,
    subjects: list[str] | None = None,
) -> str:
    """Called per scenario. Return injection text.

    This text gets prepended to the agent's prompt.
    Return empty string for no injection (control run).
    """
    return ""


async def on_tool_result(
    tool_name: str,
    source: str,
    query_arg: str,
    tool_result: str,
) -> str:
    """Called after each tool call. Return text to append.

    Return empty string to not inject anything.
    """
    return ""


async def teardown() -> None:
    """Called per scenario. Clean up between scenarios."""
    pass


# ═══════════════════════════════════════════════════════
# AGENT — usually no need to modify below
# ═══════════════════════════════════════════════════════


async def run_agent(
    skill: str,
    query: str,
    company: str,
    injection_text: str = "",
    tool_callback=None,
) -> AgentResult:
    """Run the benchmark agent with optional injection."""
    return await _run_agent(
        skill_slug=skill,
        query=query,
        company=company,
        injection_text=injection_text,
        tool_injection_callback=tool_callback,
    )
