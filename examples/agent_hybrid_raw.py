"""hybrid_raw — hybrid graph + document store with evidence retrieval.

Captures each trace as a document with extracted nodes/edges in a
hybrid Postgres+pgvector store. At query time pulls precedents +
skill-level global readout. Per tool call, queries
``evidence_corrections`` for past corrections tied to similar tool
results and surfaces them as per-tool rules.

Channel routing (matches paper):
- Stage 1 corrections → fake user/assistant dialogue via
  ``get_prior_messages``. ``get_injection`` returns ``""``.
- Stage 2 per-tool-call rules → system channel (SYSTEM_PART), via
  the unified ``bench.core.agent_runner`` (see run_agent below).
  ``on_tool_result`` returns evidence corrections, which are
  delivered as ``SystemPromptPart`` on the next ``ModelRequest``.

Self-contained: no imports from other example files.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from hybrid_raw import DEFAULT_DB_URL, build
from hybrid_raw.injection import format_global_readout, format_precedents

from bench.core.agent import AgentResult
from bench.core.agent_runner import run_from_protocol
from bench.core.channels import Channel

logger = logging.getLogger(__name__)

name = "hybrid_raw"

_capture: Any = None
_query: Any = None
_captured_results: list[dict] = []

# Stashed during ``get_prior_messages`` so ``on_tool_result`` can pass
# the real skill name to ``evidence_corrections``. HybridQuery's
# ``query_evidence_corrections`` filters with
# ``Document.skill_name == skill_name``, so an empty string matches no
# rows and Stage-2 rule re-injection silently produces nothing.
_current_skill: str | None = None
_current_subjects: list | None = None


async def setup() -> None:
    return None


async def prepare() -> None:
    global _capture, _query, _captured_results
    import asyncpg

    _captured_results = []

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
        logger.warning("hybrid_raw db reset failed: %s", exc)

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

    global_text = ""
    if _query.supports_global_readout:
        readout = await _query.global_readout(
            skill_name=skill,
            min_runs=1,
            actor_id=actor_id,
        )
        global_text = format_global_readout(readout)

    precedents_text = format_precedents(
        raw_dict,
        mode=_query.format_mode,
        actor_id=actor_id,
    )

    if global_text and precedents_text:
        return f"{global_text}\n\n{precedents_text}"
    return global_text or precedents_text


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
    global _current_skill, _current_subjects
    _current_skill = skill
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
    """Surface evidence corrections (per-tool-call rules learned from
    past tool calls with similar results). Passes the real skill name
    because ``query_evidence_corrections`` filters with
    ``Document.skill_name == skill_name`` — empty string matches no
    rows."""
    if not _query or not _query.supports_evidence_corrections:
        return ""
    try:
        ev_results = await _query.evidence_corrections(
            tool_result=tool_result[:1000],
            skill_name=_current_skill or "",
            limit=3,
            subjects=_current_subjects,
        )
        if not ev_results:
            return ""
        lines = []
        for ev in ev_results:
            correction = ev.get("correction", "")
            if correction:
                lines.append(f"[CORRECTION] {correction}")
        return "\n".join(lines) if lines else ""
    except Exception as exc:
        logger.warning("hybrid_raw evidence_corrections failed: %s", exc)
        return ""


async def teardown() -> None:
    global _capture, _query, _captured_results
    global _current_skill, _current_subjects
    if _capture:
        await _capture.shutdown()
        _capture = None
    if _query:
        await _query.shutdown()
        _query = None
    _captured_results = []
    _current_skill = None
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
