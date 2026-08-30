"""zep / Graphiti — temporal knowledge graph baseline.

Each scenario's seed traces are fed into Graphiti as episodes (one
episode per user turn). Graphiti's LLM-driven pipeline extracts
entities and relations into a temporal knowledge graph in Neo4j. At
query time we search the graph for facts relevant to the test query
and surface them as conversational context.

"Zep Community Edition" was deprecated in April 2025; this adapter
uses Graphiti, the open-source temporal-graph engine that powers
Zep Cloud.

Channel routing (matches paper):
- Stage 1 retrieved graph facts → fake user/assistant dialogue via
  ``get_prior_messages``. ``get_injection`` returns ``""``.
- Stage 2 per-tool-call rules → tool channel (default
  ``bench.core.agent._run_agent``). zep surfaces no per-tool rules.

Requires:
- Neo4j reachable at ``NEO4J_URI`` (default ``bolt://localhost:7687``)
- ``graphiti-core`` package installed
- ``OPENAI_API_KEY`` in the environment

Self-contained: no imports from other example files.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from bench.core.agent import AgentResult
from bench.core.agent_runner import run_from_protocol
from bench.core.channels import Channel

logger = logging.getLogger(__name__)

logging.getLogger("graphiti_core").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)

name = "zep"

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "testpassword")
ZEP_MODEL = os.environ.get("ZEP_MODEL", "gpt-4o-mini")
ZEP_EMBEDDING = os.environ.get("ZEP_EMBEDDING", "text-embedding-3-small")

_client: Any = None
_group_id: str | None = None
_indices_built: bool = False
_patched: bool = False


def _patch_openai_usage() -> None:
    """Patch OpenAI sync/async/Responses clients for usage tracking.
    Graphiti uses the OpenAI SDK under the hood, so the same
    monkey-patch trick the mem0 adapter uses applies here. Idempotent
    via the shared ``_patched`` flag."""
    global _patched
    if _patched:
        return

    try:
        from forge_dc.shared import usage as _usage_mod
    except ImportError:
        return

    from openai.resources.chat.completions import (
        AsyncCompletions,
        Completions,
    )
    from openai.resources.embeddings import (
        AsyncEmbeddings,
        Embeddings,
    )
    from openai.resources.responses import (
        AsyncResponses,
        Responses,
    )

    _orig_chat = Completions.create
    _orig_embed = Embeddings.create
    _orig_async_chat = AsyncCompletions.create
    _orig_async_embed = AsyncEmbeddings.create
    _orig_resp_parse = Responses.parse
    _orig_resp_create = Responses.create
    _orig_async_resp_parse = AsyncResponses.parse
    _orig_async_resp_create = AsyncResponses.create

    def _record_chat(resp: Any) -> None:
        try:
            u = getattr(resp, "usage", None)
            if u is None:
                return
            pin = getattr(u, "prompt_tokens", None)
            pout = getattr(u, "completion_tokens", None)
            if pin is None and pout is None:
                pin = getattr(u, "input_tokens", 0) or 0
                pout = getattr(u, "output_tokens", 0) or 0
            _usage_mod.record_llm(int(pin or 0), int(pout or 0))
        except Exception:
            pass

    def _record_embed(resp: Any) -> None:
        try:
            u = resp.usage
            if u:
                _usage_mod.record_embed(u.prompt_tokens)
        except Exception:
            pass

    def _tracked_chat(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = _orig_chat(self, *args, **kwargs)
        _record_chat(resp)
        return resp

    def _tracked_embed(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = _orig_embed(self, *args, **kwargs)
        _record_embed(resp)
        return resp

    def _tracked_resp_parse(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = _orig_resp_parse(self, *args, **kwargs)
        _record_chat(resp)
        return resp

    def _tracked_resp_create(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = _orig_resp_create(self, *args, **kwargs)
        _record_chat(resp)
        return resp

    async def _tracked_async_chat(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = await _orig_async_chat(self, *args, **kwargs)
        _record_chat(resp)
        return resp

    async def _tracked_async_embed(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = await _orig_async_embed(self, *args, **kwargs)
        _record_embed(resp)
        return resp

    async def _tracked_async_resp_parse(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = await _orig_async_resp_parse(self, *args, **kwargs)
        _record_chat(resp)
        return resp

    async def _tracked_async_resp_create(self: Any, *args: Any, **kwargs: Any) -> Any:
        resp = await _orig_async_resp_create(self, *args, **kwargs)
        _record_chat(resp)
        return resp

    Completions.create = _tracked_chat  # type: ignore[method-assign]
    Embeddings.create = _tracked_embed  # type: ignore[method-assign]
    Responses.parse = _tracked_resp_parse  # type: ignore[method-assign]
    Responses.create = _tracked_resp_create  # type: ignore[method-assign]
    AsyncCompletions.create = _tracked_async_chat  # type: ignore[method-assign]
    AsyncEmbeddings.create = _tracked_async_embed  # type: ignore[method-assign]
    AsyncResponses.parse = _tracked_async_resp_parse  # type: ignore[method-assign]
    AsyncResponses.create = _tracked_async_resp_create  # type: ignore[method-assign]
    _patched = True


async def setup() -> None:
    global _client, _indices_built
    _patch_openai_usage()

    if _client is not None:
        return

    from graphiti_core import Graphiti
    from graphiti_core.embedder.openai import (
        OpenAIEmbedder,
        OpenAIEmbedderConfig,
    )
    from graphiti_core.llm_client.config import LLMConfig
    from graphiti_core.llm_client.openai_client import OpenAIClient

    llm_cfg = LLMConfig(model=ZEP_MODEL, small_model=ZEP_MODEL)
    _client = Graphiti(
        NEO4J_URI,
        NEO4J_USER,
        NEO4J_PASSWORD,
        llm_client=OpenAIClient(config=llm_cfg),
        embedder=OpenAIEmbedder(
            config=OpenAIEmbedderConfig(embedding_model=ZEP_EMBEDDING),
        ),
    )

    if not _indices_built:
        try:
            await _client.build_indices_and_constraints()
            _indices_built = True
        except Exception as exc:
            logger.warning("graphiti index build failed: %s", exc)


async def prepare() -> None:
    """Per-scenario reset. Each scenario gets a fresh ``group_id`` so
    its facts are isolated from other scenarios."""
    global _group_id
    _group_id = f"dc-bench-{uuid.uuid4().hex[:12]}"


async def capture_one(trace: dict[str, Any]) -> None:
    """Add the seed trace's user turns into Graphiti as episodes.

    Graphiti's LLM pipeline extracts entities and edges from each
    episode. This is where zep incurs its capture-phase token cost.
    """
    if _client is None or _group_id is None:
        return

    from graphiti_core.nodes import EpisodeType

    for msg in trace.get("message_history", []):
        role = msg.get("role")
        if role != "user":
            continue
        content = msg.get("content", "")
        if not isinstance(content, str) or not content.strip():
            continue
        try:
            await _client.add_episode(
                name=f"user_msg_{trace.get('conversation_id', '')[:8]}",
                episode_body=content,
                source=EpisodeType.message,
                source_description="seed user turn",
                reference_time=datetime.now(UTC),
                group_id=_group_id,
            )
        except Exception as exc:
            logger.warning("graphiti add_episode failed: %s", exc)


async def _build_injection(query: str) -> str:
    if _client is None or _group_id is None:
        return ""

    try:
        results = await _client.search(
            query=query,
            group_ids=[_group_id],
            num_results=10,
        )
    except Exception as exc:
        logger.warning("graphiti search failed: %s", exc)
        return ""

    facts: list[str] = []
    for edge in results or []:
        fact = getattr(edge, "fact", "") or ""
        if fact:
            facts.append(fact)

    if not facts:
        return ""

    lines = ["## Past interaction context:"]
    for fact in facts:
        lines.append(f"- {fact}")
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
    text = await _build_injection(query=query)
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
    """Drop the scenario's group from Neo4j to keep the graph clean."""
    global _group_id

    if _client is None or _group_id is None:
        _group_id = None
        return

    try:
        async with _client.driver.session() as s:
            await s.run(
                "MATCH (n {group_id: $g}) DETACH DELETE n",
                g=_group_id,
            )
    except Exception as exc:
        logger.warning("graphiti group delete failed: %s", exc)
    _group_id = None


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
