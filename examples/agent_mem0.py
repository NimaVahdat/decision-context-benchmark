"""mem0 — external memory baseline via mem0ai + qdrant.

Feeds each scenario's seed traces into mem0's local ``Memory`` store
(LLM-extracted facts, stored as embeddings in an in-memory qdrant
collection). At query time mem0 retrieves the top-K facts for the
test ``(query, company)`` and we surface them as conversational
context.

This is the state-of-the-art managed-agent-memory baseline.

Channel routing (matches paper):
- Stage 1 retrieved memories → fake user/assistant dialogue via
  ``get_prior_messages``. ``get_injection`` returns ``""``.
- Stage 2 per-tool-call rules → tool channel (default
  ``bench.core.agent._run_agent``). mem0 surfaces no per-tool rules.

Self-contained: no imports from other example files.
"""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import Any

from bench.core.agent import AgentResult
from bench.core.agent_runner import run_from_protocol
from bench.core.channels import Channel

logger = logging.getLogger(__name__)

# Suppress noisy mem0 / qdrant warnings.
logging.getLogger("mem0.vector_stores.qdrant").setLevel(logging.ERROR)
logging.getLogger("mem0.utils.spacy_models").setLevel(logging.ERROR)

name = "mem0"

_memory: Any = None
_patched: bool = False


def _patch_openai_usage() -> None:
    """Route mem0's sync OpenAI calls into the forge_dc usage
    counter so the bench can report mem0's capture and query token
    spend. Idempotent — only patches once. Skipped if forge_dc's
    usage counter isn't importable."""
    global _patched
    if _patched:
        return

    try:
        from forge_dc.shared import usage as _usage_mod
    except ImportError:
        return

    from openai.resources.chat.completions import Completions
    from openai.resources.embeddings import Embeddings

    _orig_chat = Completions.create
    _orig_embed = Embeddings.create

    def _tracked_chat(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = _orig_chat(self, *args, **kwargs)
        try:
            u = resp.usage
            if u:
                _usage_mod.record_llm(u.prompt_tokens, u.completion_tokens)
        except Exception:
            pass
        return resp

    def _tracked_embed(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = _orig_embed(self, *args, **kwargs)
        try:
            u = resp.usage
            if u:
                _usage_mod.record_embed(u.prompt_tokens)
        except Exception:
            pass
        return resp

    Completions.create = _tracked_chat  # type: ignore[method-assign]
    Embeddings.create = _tracked_embed  # type: ignore[method-assign]
    _patched = True


async def setup() -> None:
    _patch_openai_usage()


async def prepare() -> None:
    global _memory
    from mem0 import Memory
    from qdrant_client import QdrantClient

    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": "mem0_bench",
                "embedding_model_dims": 1536,
                "client": QdrantClient(":memory:"),
            },
        },
        "llm": {
            "provider": "openai",
            # Paper used ``gpt-5-mini``, but mem0ai 2.0.4 still calls
            # OpenAI with ``max_tokens=...``, which the GPT-5 family
            # rejects (requires ``max_completion_tokens``). Switch to
            # ``gpt-4.1-mini`` so mem0 capture works out of the box;
            # this is one of the small unavoidable adapter drifts vs
            # the paper bit-exact runs.
            "config": {"model": "gpt-4.1-mini"},
        },
        "embedder": {
            "provider": "openai",
            "config": {"model": "text-embedding-3-small"},
        },
    }

    loop = asyncio.get_event_loop()
    _memory = await loop.run_in_executor(
        None,
        partial(Memory.from_config, config),
    )


async def capture_one(trace: dict[str, Any]) -> None:
    if not _memory:
        return

    company = (trace.get("subjects") or [{}])[0].get("id", "unknown")

    messages: list[dict] = []
    for msg in trace.get("message_history", []):
        role = msg.get("role")
        if role == "user":
            messages.append({"role": "user", "content": msg.get("content", "")})
        elif role == "assistant":
            content = msg.get("content", "")
            if content:
                messages.append({"role": "assistant", "content": content})

    outcome = trace.get("outcome_summary", "")
    if outcome:
        messages.append({"role": "assistant", "content": outcome})

    if not messages:
        return

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None,
            partial(_memory.add, messages, user_id=company),
        )
    except Exception as exc:
        logger.warning("mem0 capture failed: %s", exc)


async def _build_injection(
    skill: str,
    company: str,
    query: str,
) -> str:
    if not _memory:
        return ""

    loop = asyncio.get_event_loop()
    try:
        results = await loop.run_in_executor(
            None,
            partial(
                _memory.search,
                query,
                filters={"user_id": company},
                limit=5,
            ),
        )
    except Exception as exc:
        logger.warning("mem0 search failed: %s", exc)
        return ""

    memories = (
        results.get("results", [])
        if isinstance(results, dict)
        else (results or [])
    )
    if not memories:
        return ""

    lines = ["## Past interaction context:"]
    for mem in memories:
        text = mem.get("memory", "") if isinstance(mem, dict) else str(mem)
        if text:
            lines.append(f"- {text}")

    return "\n".join(lines)


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
    text = await _build_injection(skill=skill, company=company, query=query)
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
    global _memory
    _memory = None


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
