"""forge_dc — rule compilation via strong LLM, retrieval by edges.

Captures each correction trace into the hybrid store, then a strong
LLM compiles the correction into a strict ``RULE`` directive (one or
more imperative sentences). At query time the hybrid retriever finds
relevant past documents and walks ``FORGED_FROM`` edges to surface
only the compiled rules. The injection looks like::

    # MANDATORY RULES — FOLLOW EXACTLY

    RULE: ...

Channel routing (matches paper):
- Stage 1 corrections → fake user/assistant dialogue via
  ``get_prior_messages``. ``get_injection`` returns ``""``.
- Stage 2 per-tool-call rules → system channel (SYSTEM_PART), via
  the unified ``bench.core.agent_runner`` (see run_agent below).

Self-contained: no imports from other example files.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from forge_dc import DEFAULT_DB_URL, build

from bench.core.agent import AgentResult
from bench.core.agent_runner import run_from_protocol
from bench.core.channels import Channel
from bench.core.skills import _load_skill_prompt

logger = logging.getLogger(__name__)

name = "forge_dc"

_capture: Any = None
_query: Any = None
_captured_results: list[dict] = []
_consolidated_for_skill: str | None = None

# Stashed during get_prior_messages so on_tool_result has a meaningful
# ``task_context`` to feed ForgeQuery.retrieve. ForgeQuery's built-in
# ``evidence_corrections`` hard-codes ``task_context=""`` which causes
# ``Embedder.embed("")`` to raise (OpenAI rejects empty input), the
# error is swallowed by ``_search_nodes``'s ``except``, and zero rules
# come back. Bypassing ``evidence_corrections`` by calling
# ``retrieve`` directly with a populated ``task_context`` restores the
# paper's Stage-2 per-tool-call rule re-injection.
_current_skill: str | None = None
_current_query: str | None = None
_current_actor_id: str | None = None
_current_subjects: list | None = None


async def setup() -> None:
    return None


async def prepare() -> None:
    global _capture, _query, _captured_results, _consolidated_for_skill
    import asyncpg

    _captured_results = []
    _consolidated_for_skill = None

    db_url = DEFAULT_DB_URL.replace(
        "postgresql+asyncpg://",
        "postgresql://",
    )
    try:
        conn = await asyncpg.connect(db_url)
        await conn.execute(
            "DROP SCHEMA public CASCADE; "
            "CREATE SCHEMA public; "
            "CREATE EXTENSION IF NOT EXISTS vector;"
        )
        await conn.close()
    except Exception as exc:
        logger.warning("forge_dc db reset failed: %s", exc)

    _capture, _query = build()
    await _capture.initialize()
    await _query.initialize()


async def capture_one(trace: dict[str, Any]) -> None:
    if not _capture:
        return

    parent = trace.get("parent_doc_id", "")
    if isinstance(parent, str) and parent.startswith("$trace_ref:"):
        ref_idx = int(parent.split(":")[1])
        if ref_idx < len(_captured_results):
            trace["parent_doc_id"] = _captured_results[ref_idx].get(
                "document_id", ""
            )
        else:
            trace["parent_doc_id"] = None

    result = await _capture.capture(trace)
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    _captured_results.append(result)


async def _maybe_consolidate(skill: str) -> None:
    """Run the forge rule-compilation pipeline once per scenario.

    forge_dc's ``ForgeCapture.consolidate`` walks correction chains
    captured so far and compiles them into RULE directives with the
    strong LLM. Without this step ``precedents()`` returns
    ``rules: []`` and the injection is empty.

    Deferred to first query because the new Protocol has no
    end-of-capture signal.
    """
    global _consolidated_for_skill
    if _consolidated_for_skill == skill:
        return
    _consolidated_for_skill = skill

    if not _capture or not getattr(_capture, "supports_consolidation", False):
        return
    if not hasattr(_capture, "consolidate"):
        return

    try:
        skill_def = _load_skill_prompt(skill)
        await _capture.consolidate(skill, skill_definition=skill_def)
    except Exception as exc:
        logger.warning("forge_dc consolidate failed: %s", exc)


async def _build_injection(
    skill: str,
    company: str,
    query: str,
    actor_id: str | None,
    subjects: list[str] | None,
) -> str:
    if not _query:
        return ""

    await asyncio.sleep(0.5)
    await _maybe_consolidate(skill)

    prec_result = await _query.precedents(
        description=f"Running {skill} skill: {query}",
        subjects=subjects,
        limit=5,
        actor_id=actor_id,
    )

    raw_dict = (
        prec_result.model_dump()
        if hasattr(prec_result, "model_dump")
        else prec_result
        if isinstance(prec_result, dict)
        else {"results": prec_result}
    )

    # ForgeQuery pre-formats the RULE injection inside ``retrieve``
    # and exposes it on ``raw_dict["injection_text"]``. The shared
    # ``format_precedents`` helper does not know about ``mode="forge"``
    # and iterates ``raw_dict["results"]`` (always empty for forge),
    # so we use the pre-formatted text directly.
    return raw_dict.get("injection_text", "") or ""


async def get_injection(
    *,
    skill: str,
    company: str,
    query: str,
    actor_id: str | None,
    subjects: list[str] | None,
) -> str:
    return ""


async def get_prior_messages(
    *,
    skill: str,
    company: str,
    query: str,
    actor_id: str | None,
    subjects: list[str] | None,
) -> list[dict[str, Any]] | None:
    # Stash the query context for ``on_tool_result`` so per-tool-call
    # retrieval has a non-empty ``task_context`` to feed the embedder.
    global _current_skill, _current_query, _current_actor_id, _current_subjects
    _current_skill = skill
    _current_query = query
    _current_actor_id = actor_id
    _current_subjects = subjects

    text = await _build_injection(
        skill=skill,
        company=company,
        query=query,
        actor_id=actor_id,
        subjects=subjects,
    )
    if not text:
        return None
    return [
        {
            "role": "user",
            "content": (
                "For context, here are corrections learned from prior "
                "interactions:\n\n"
                f"{text}"
            ),
        },
        {
            "role": "assistant",
            "content": "Understood — I will apply these corrections.",
        },
    ]


async def on_tool_result(
    tool_name: str,
    source: str,
    query: str,
    tool_result: str,
) -> str:
    """Surface compiled rules per tool call as ``SystemPromptPart`` on
    the next ``ModelRequest`` (Stage 2 of B+3).

    We call ``ForgeQuery.retrieve`` directly rather than going through
    ``evidence_corrections``. The latter hard-codes ``task_context=""``,
    which makes ``Embedder.embed("")`` raise (OpenAI rejects empty
    input). The exception is silently swallowed inside
    ``_search_nodes``'s broad ``except``, retrieve returns zero rules,
    and no Stage-2 rules ever surface. Passing the actual ``skill``
    and test ``query`` (stashed during ``get_prior_messages``) gives
    the embedder real text to work with and makes paper-level rule
    retrieval reproducible.
    """
    if not _query:
        return ""
    if not hasattr(_query, "retrieve"):
        return ""
    skill = _current_skill or ""
    test_query = _current_query or ""
    task_context = (
        f"Running {skill} skill: {test_query}"
        if skill or test_query
        else "skill execution"
    )
    try:
        result = await _query.retrieve(
            task_context=task_context,
            data_context=tool_result[:1000],
            skill_name=skill,
            actor_id=_current_actor_id,
            subjects=_current_subjects,
            correction_limit=3,
            tool_limit=3,
        )
    except Exception as exc:
        logger.warning("forge_dc on_tool_result retrieve failed: %s", exc)
        return ""

    rules = result.get("rules", []) if isinstance(result, dict) else []
    if not rules:
        return ""

    lines: list[str] = []
    for r in rules:
        text = getattr(r, "text", "") or ""
        if text and text not in lines:
            lines.append(f"RULE: {text}")
            why = getattr(r, "reasoning", "") or ""
            if why:
                lines.append(f"WHY: {why}")
    return "\n".join(lines) if lines else ""


async def teardown() -> None:
    global _capture, _query, _captured_results, _consolidated_for_skill
    global _current_skill, _current_query, _current_actor_id, _current_subjects
    if _capture:
        await _capture.shutdown()
        _capture = None
    if _query:
        await _query.shutdown()
        _query = None
    _captured_results = []
    _consolidated_for_skill = None
    _current_skill = None
    _current_query = None
    _current_actor_id = None
    _current_subjects = None


async def run_agent(
    *,
    skill: str,
    query: str,
    company: str,
    injection_text: str,
    tool_callback: Any,
    prior_messages: list[dict[str, Any]] | None = None,
) -> AgentResult:
    """Stage-1 corrections flow through ``prior_messages`` as fabricated
    dialogue; stage-2 per-tool rules go into the system channel
    (``SYSTEM_PART``). Routing is declared here via the unified runner."""
    return await run_from_protocol(
        skill=skill,
        query=query,
        company=company,
        injection_text=injection_text,
        tool_callback=tool_callback,
        prior_messages=prior_messages,
        per_tool_channel=Channel.SYSTEM_PART,
    )
