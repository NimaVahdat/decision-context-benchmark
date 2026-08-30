"""The one general template — copy this to integrate ANY approach.

This is the single file an adopter edits to plug their own memory
system into the benchmark, regardless of approach. You decide:

* **what** to inject  — your retrieval, in ``_retrieve_initial`` /
  ``_retrieve_per_tool`` (swap in your store: vector DB, graph,
  compiled rules, an external product like mem0/zep, anything).
* **when**            — initial (before the agent runs) vs per-tool-call.
* **with which exact wording** — you return the verbatim strings;
  the runner adds no wrapper.
* **into which channel** — you tag each piece with a
  :class:`~bench.core.channels.Channel`.

The agent loop, mocked tools, skill prompt, model resolution, scoring,
and usage tracking are all handled by the benchmark via
``bench.core.agent_runner.run_agent`` — you never reimplement those.

Channel cheat-sheet (see bench/core/channels.py for the full list):

* initial:   SYSTEM_APPEND, SYSTEM_PREPEND, USER_TURN, ASSISTANT_TURN
* per-tool:  SYSTEM_PART (trusted, survives Opus/GPT-5),
             TOOL_RESULT_SUFFIX (cheap, may be discounted), USER_NOTE

The two constants below pick the channels for the common case. For
per-item mixing (different channels for different memories), return a
list of ``Injection`` from the retrieval helpers directly.

Run it:
    uv run python -m bench.run --agent examples/agent_template.py \
        --suite basic --runs 1 --model openai:gpt-4.1 --judge-model openai:gpt-4.1
"""

from __future__ import annotations

from typing import Any

from bench.core.agent import AgentResult
from bench.core.agent_runner import run_agent as _run
from bench.core.channels import (
    Channel,
    Injection,
    assistant_turn,
)

# ── Channel choices (edit these to change routing) ──────────────────
# Stage-1 corrections (known before the agent runs):
INITIAL_CHANNEL = Channel.USER_TURN          # B+3 stage-1; try SYSTEM_APPEND too
# Stage-2 per-tool-call rules (surfaced after a tool returns):
PER_TOOL_CHANNEL = Channel.SYSTEM_PART        # B+3 stage-2; survives safety-trained models

name = "template"


# ── Approach state (swap in your own store) ─────────────────────────
async def setup() -> None:
    """One-time init: open DB connections, load models. TODO."""
    return None


async def prepare() -> None:
    """Per-scenario reset: clear your memory store. TODO."""
    return None


async def capture_one(trace: dict[str, Any]) -> None:
    """Ingest one seed trace into your store, in order. TODO."""
    return None


# ── Retrieval (YOUR approach decides what comes back) ───────────────
async def _retrieve_initial(skill: str, company: str, query: str) -> str:
    """Return the up-front correction text for this query, or "".
    TODO: query your store. This is your stage-1 content."""
    return ""


async def _retrieve_per_tool(tool_name: str, source: str, query: str, result: str) -> str:
    """Return any rule text relevant to this tool call, or "".
    TODO: query your store keyed on the tool result. Stage-2 content."""
    return ""


# ── Protocol bridge (orchestrator records metrics through these) ────
async def get_injection(
    *, skill: str, company: str, query: str, actor_id: str | None, subjects: list[str] | None
) -> str:
    # Returned text is recorded by the bench for injection-token metrics.
    # run_agent below routes it into INITIAL_CHANNEL.
    return await _retrieve_initial(skill, company, query)


async def on_tool_result(tool_name: str, source: str, query: str, tool_result: str) -> str:
    # Recorded as a tool-injection; routed into PER_TOOL_CHANNEL by run_agent.
    return await _retrieve_per_tool(tool_name, source, query, tool_result)


async def teardown() -> None:
    """One-time cleanup. TODO."""
    return None


# ── Run: map the recorded content onto channels via the unified runner
async def run_agent(
    *,
    skill: str,
    query: str,
    company: str,
    injection_text: str,
    tool_callback: Any,
    prior_messages: list[dict[str, Any]] | None = None,
) -> AgentResult:
    """Build the channel-tagged injection plan and hand it to the
    unified runner. ``injection_text`` is what ``get_injection``
    returned; ``tool_callback`` invokes ``on_tool_result`` (and lets
    the bench record per-tool injections)."""
    initial: list[Injection] = []
    if injection_text:
        initial.append(Injection(injection_text, INITIAL_CHANNEL))
        # A fabricated dialogue turn reads better with an acknowledgement.
        if INITIAL_CHANNEL == Channel.USER_TURN:
            initial.append(assistant_turn("Understood — I will apply these corrections."))

    async def _on_tool(tool: str, source: str, q: str, result: str) -> list[Injection]:
        text = await tool_callback(tool, source, q, result)
        return [Injection(text, PER_TOOL_CHANNEL)] if text else []

    return await _run(
        skill=skill,
        query=query,
        company=company,
        initial=initial,
        on_tool=_on_tool,
    )
