"""lucid_dc — hybrid capture + self-assessment consolidation.

Same hybrid graph + document store as ``hybrid_raw``. Adds a
consolidation pass (Layer 3) after capture: an LLM analyzes the
captured traces for recurring failure patterns and emits
deterministic directives like
"DO NOT call eval_lookup with source='financials'". Those directives
get prepended to the precedent injection.

Channel routing (matches paper):
- Stage 1 corrections (precedents + global readout + consolidation
  directives) → fake user/assistant dialogue via
  ``get_prior_messages``. ``get_injection`` returns ``""``.
- Stage 2 per-tool-call rules → system channel (SYSTEM_PART), via
  the unified ``bench.core.agent_runner`` (see run_agent below).

Self-contained: no imports from other example files.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from lucid_dc import DEFAULT_DB_URL, build
from lucid_dc.injection import format_global_readout, format_precedents

from bench.core.agent import AgentResult
from bench.core.agent_runner import run_from_protocol
from bench.core.channels import Channel
from bench.core.skills import _load_skill_prompt

logger = logging.getLogger(__name__)

name = "lucid_dc"

_capture: Any = None
_query: Any = None
_captured_results: list[dict] = []
_consolidation_injection: str = ""
_consolidated_for_skill: str | None = None

# See agent_hybrid_raw.py — query_evidence_corrections filters by
# skill_name; empty string returns no rows.
_current_skill: str | None = None
_current_subjects: list | None = None


async def setup() -> None:
    return None


async def prepare() -> None:
    global _capture, _query, _captured_results
    global _consolidation_injection, _consolidated_for_skill
    import asyncpg

    _captured_results = []
    _consolidation_injection = ""
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
        logger.warning("lucid_dc db reset failed: %s", exc)

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
    """Run consolidation once per scenario, lazily on first query.

    The new Protocol calls ``capture_one`` per trace with no
    end-of-capture signal, so Layer-3 consolidation is deferred until
    we need it (the first ``get_prior_messages`` call).
    """
    global _consolidation_injection, _consolidated_for_skill
    if _consolidated_for_skill == skill:
        return
    _consolidated_for_skill = skill

    if not _capture:
        return
    if not getattr(_capture, "supports_consolidation", False):
        return
    if not hasattr(_capture, "consolidate"):
        return

    try:
        skill_def = _load_skill_prompt(skill)
        consol_result = await _capture.consolidate(
            skill,
            skill_definition=skill_def,
        )
        if hasattr(consol_result, "injection_text"):
            _consolidation_injection = consol_result.injection_text
    except Exception as exc:
        logger.warning("lucid_dc consolidate failed: %s", exc)


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
        out = f"{global_text}\n\n{precedents_text}"
    else:
        out = global_text or precedents_text

    if _consolidation_injection:
        out = (
            f"{_consolidation_injection}\n\n{out}"
            if out
            else _consolidation_injection
        )
    return out


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
        logger.warning("lucid_dc evidence_corrections failed: %s", exc)
        return ""


async def teardown() -> None:
    global _capture, _query, _captured_results
    global _consolidation_injection, _consolidated_for_skill
    if _capture:
        await _capture.shutdown()
        _capture = None
    if _query:
        await _query.shutdown()
        _query = None
    _captured_results = []
    _consolidation_injection = ""
    _consolidated_for_skill = None
    global _current_skill, _current_subjects
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
