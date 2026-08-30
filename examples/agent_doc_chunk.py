"""doc_chunk — chunked document capture with structured retrieval.

Same family as doc_naive, but each captured document is split into
overlapping chunks at capture time. At query time the top-K most
similar chunks (across all past documents) are returned and
formatted with structured headers (``## Relevant Precedents``).

Channel routing (matches paper):
- Stage 1 corrections → fake user/assistant dialogue via
  ``get_prior_messages``. ``get_injection`` returns ``""``.
- Stage 2 per-tool-call rules → tool channel (default
  ``bench.core.agent._run_agent``). doc_chunk does not surface
  per-tool rules.

Self-contained: no imports from other example files.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from doc_chunk import DEFAULT_DB_URL, build
from doc_chunk.injection import format_precedents

from bench.core.agent import AgentResult
from bench.core.agent_runner import run_from_protocol
from bench.core.channels import Channel

logger = logging.getLogger(__name__)

name = "doc_chunk"

_capture: Any = None
_query: Any = None
_captured_results: list[dict] = []


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
        logger.warning("doc_chunk db reset failed: %s", exc)

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

    return format_precedents(
        raw_dict,
        mode=_query.format_mode,
        actor_id=actor_id,
    )


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
    return ""


async def teardown() -> None:
    global _capture, _query, _captured_results
    if _capture:
        await _capture.shutdown()
        _capture = None
    if _query:
        await _query.shutdown()
        _query = None
    _captured_results = []


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
