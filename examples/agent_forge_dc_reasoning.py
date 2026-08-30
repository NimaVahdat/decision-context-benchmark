"""forge_dc_reasoning — forge_dc with WHY reasoning emission.

Same hybrid + rule-compilation pipeline as ``agent_forge_dc``, but
the strong-LLM rule compiler is asked to emit a brief WHY string
alongside each RULE. The WHY is persisted on the rule node and
appears directly after the RULE in the precedent injection. This
tests whether handing the model the *reason* behind a rule changes
compliance.

Toggle: ``FORGE_EMIT_WHY=1`` env var. The rest of the wiring is
identical to ``forge_dc``.

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
import os
from typing import Any

from forge_dc import DEFAULT_DB_URL, build

from bench.core.agent import AgentResult
from bench.core.agent_runner import run_from_protocol
from bench.core.channels import Channel
from bench.core.skills import _load_skill_prompt

logger = logging.getLogger(__name__)

name = "forge_dc_reasoning"

_capture: Any = None
_query: Any = None
_captured_results: list[dict] = []
_consolidated_for_skill: str | None = None

# See agent_forge_dc.py for why we stash these — ForgeQuery's built-in
# ``evidence_corrections`` silently fails when ``task_context=""``.
_current_skill: str | None = None
_current_query: str | None = None
_current_actor_id: str | None = None
_current_subjects: list | None = None


async def setup() -> None:
    # Enable WHY emission in the forge rule compiler.
    os.environ["FORGE_EMIT_WHY"] = "1"


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
        logger.warning("forge_dc_reasoning db reset failed: %s", exc)

    _capture, _query = build(emit_reasoning=True)
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
    """forge_dc compilation step, deferred to first query."""
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
        logger.warning(
            "forge_dc_reasoning consolidate failed: %s",
            exc,
        )


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

    # ForgeQuery pre-formats the RULE+WHY injection inside ``retrieve``
    # and exposes it on ``raw_dict["injection_text"]``. See agent_forge_dc.py.
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
    """Stage-2 per-tool-call rule re-injection. See agent_forge_dc.py
    for the explanation of why we call ``retrieve`` directly instead
    of going through ``evidence_corrections``."""
    if not _query or not hasattr(_query, "retrieve"):
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
        logger.warning(
            "forge_dc_reasoning on_tool_result retrieve failed: %s", exc,
        )
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
