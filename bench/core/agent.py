"""Agent execution: run a pydantic-ai agent with eval tools."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from bench.core.config import FIXTURES_DIR, _resolve_model
from bench.core.skills import _load_skill_model, _load_skill_prompt

logger = logging.getLogger(__name__)


@dataclass
class ToolCallDetail:
    """One tool call made by the agent."""

    tool_name: str
    source: str
    query: str
    result: str = ""


@dataclass
class AgentResult:
    """Output + usage from a single agent run."""

    output: str
    input_tokens: int = 0
    output_tokens: int = 0
    requests: int = 0
    tool_calls: int = 0
    tool_call_details: list[ToolCallDetail] = field(
        default_factory=list,
    )


# -- Agent Execution -----------------------------------------


async def _run_agent(
    skill_slug: str,
    query: str,
    company: str,
    injection_text: str = "",
    tool_injection_callback: Any | None = None,
    prior_messages: list[dict] | None = None,
) -> AgentResult:
    """Run an agent with per-tool-call rules delivered through the
    system prompt channel.

    Rules retrieved between tool calls are added to the system prompt
    for the next model call (via ``SystemPromptPart`` on subsequent
    ``ModelRequest``s). Optional ``prior_messages`` is a list of dicts
    shaped like ``[{"role": "user"|"assistant", "content": str}]`` and
    is forwarded as conversation history.
    Thin shim over the unified runner (system-channel routing): kept
    so the control baseline (``bench/agent.py``) and the playground
    keep a simple ``_run_agent(...)`` entry point.
    """
    # Lazy import avoids a circular import (agent_runner imports
    # AgentResult/ToolCallDetail from this module).
    from bench.core.agent_runner import run_from_protocol
    from bench.core.channels import Channel

    async def _cb(tool: str, source: str, q: str, result: str) -> str:
        if tool_injection_callback is None:
            return ""
        out = await tool_injection_callback(tool, source, q, result)
        return out if isinstance(out, str) else ""

    return await run_from_protocol(
        skill=skill_slug,
        query=query,
        company=company,
        injection_text=injection_text,
        tool_callback=_cb,
        prior_messages=prior_messages,
        per_tool_channel=Channel.SYSTEM_PART,
    )


async def _run_agent_legacy(
    skill_slug: str,
    query: str,
    company: str,
    injection_text: str = "",
    tool_injection_callback: Any | None = None,
    prior_messages: list[dict] | None = None,
) -> AgentResult:
    """Original pydantic-ai ``Agent.run()`` loop that appends
    per-tool-call rules to the tool-result string. Kept for
    reproducibility of the channel ablation.
    """
    import os

    # Point eval_lookup at bench fixtures.
    os.environ["EVAL_FIXTURES_DIR"] = str(FIXTURES_DIR)
    from bench.tools.eval_lookup import _cache, eval_lookup

    _cache.clear()

    from pydantic_ai import Agent, FunctionToolset
    from pydantic_ai.settings import ModelSettings

    system_prompt = _load_skill_prompt(skill_slug)

    if injection_text:
        actor_note = ""
        if "your correction" in injection_text:
            actor_note = (
                " When corrections are tagged "
                "'your correction' vs 'other user', "
                "prioritize YOUR corrections. "
                "Other users' corrections are "
                "informational but yours take "
                "precedence when they conflict."
            )
        # If injection is inception-style (ends with task
        # handoff), put it BEFORE the skill prompt so the
        # skill appears as "the real task after the dream"
        if injection_text.rstrip().endswith(":"):
            system_prompt = f"{injection_text}\n\n{system_prompt}"
        else:
            system_prompt = (
                f"{system_prompt}\n\n"
                f"# Corrections from Past Runs\n\n"
                f"The following corrections were made "
                f"by users in previous runs of this "
                f"skill. You MUST apply these "
                f"corrections to all future outputs, "
                f"regardless of which company is being "
                f"analyzed.{actor_note}\n\n"
                f"{injection_text}"
            )

    _call_log: list[ToolCallDetail] = []

    def _make_tracked_lookup(callback: Any | None):
        """Create a tracked eval_lookup with optional injection."""
        _orig = eval_lookup

        async def _lookup(source: str, query: str) -> str:
            result = _orig(source, query)
            _call_log.append(
                ToolCallDetail(
                    tool_name="eval_lookup",
                    source=source,
                    query=query,
                    result=result,
                )
            )
            if callback:
                ctx = await callback(
                    "eval_lookup",
                    source,
                    query,
                    result,
                )
                if ctx:
                    result = (
                        f"{result}\n\n"
                        f"# ADDITIONAL RULES FROM PAST EXPERIENCE\n"
                        f"Apply these rules to your response:\n\n"
                        f"{ctx}"
                    )
            return result

        _lookup.__doc__ = _orig.__doc__
        return _lookup

    toolset = FunctionToolset()
    toolset.add_function(
        _make_tracked_lookup(tool_injection_callback),
        name="eval_lookup",
    )

    # Add async_lookup tool for async analyst skill
    if "async" in skill_slug:
        from bench.tools.async_lookup import (
            async_lookup,
            reset_counts,
        )

        reset_counts()

        async def _tracked_async(
            source: str,
            query: str,
        ) -> str:
            result = async_lookup(source, query)
            _call_log.append(
                ToolCallDetail(
                    tool_name="async_lookup",
                    source=source,
                    query=query,
                    result=result,
                )
            )
            if tool_injection_callback:
                ctx = await tool_injection_callback(
                    "async_lookup",
                    source,
                    query,
                    result,
                )
                if ctx:
                    result = (
                        f"{result}\n\n"
                        f"# ADDITIONAL RULES FROM PAST EXPERIENCE\n"
                        f"Apply these rules to your response:\n\n"
                        f"{ctx}"
                    )
            return result

        _tracked_async.__doc__ = (
            "Look up company data. source='premium' "
            "(preferred, may need retries) or "
            "source='basic' (fallback, always available)."
        )
        toolset.add_function(
            _tracked_async,
            name="async_lookup",
        )

    # Add security_lookup tool for security-assessor skill
    if "security" in skill_slug:
        from bench.tools.security_lookup import (
            _cache as _sec_cache,
        )
        from bench.tools.security_lookup import (
            security_lookup,
        )

        _sec_cache.clear()

        async def _tracked_security(
            source: str,
            query: str,
        ) -> str:
            result = security_lookup(source, query)
            _call_log.append(
                ToolCallDetail(
                    tool_name="security_lookup",
                    source=source,
                    query=query,
                    result=result,
                )
            )
            if tool_injection_callback:
                ctx = await tool_injection_callback(
                    "security_lookup",
                    source,
                    query,
                    result,
                )
                if ctx:
                    result = (
                        f"{result}\n\n"
                        f"# ADDITIONAL RULES FROM PAST EXPERIENCE\n"
                        f"Apply these rules to your response:\n\n"
                        f"{ctx}"
                    )
            return result

        _tracked_security.__doc__ = (
            "Look up security incident data. "
            "source: 'network', 'auth', 'vulnerabilities', "
            "or 'behavior'. query: the alert ID."
        )
        toolset.add_function(
            _tracked_security,
            name="security_lookup",
        )

    # Add support_lookup tool for support skill
    if "support" in skill_slug:
        from bench.tools.support_lookup import (
            _cache as _sup_cache,
        )
        from bench.tools.support_lookup import (
            support_lookup,
        )

        _sup_cache.clear()

        async def _tracked_support(
            source: str,
            query: str,
        ) -> str:
            result = support_lookup(source, query)
            _call_log.append(
                ToolCallDetail(
                    tool_name="support_lookup",
                    source=source,
                    query=query,
                    result=result,
                )
            )
            if tool_injection_callback:
                ctx = await tool_injection_callback(
                    "support_lookup",
                    source,
                    query,
                    result,
                )
                if ctx:
                    result = (
                        f"{result}\n\n"
                        f"# ADDITIONAL RULES FROM PAST EXPERIENCE\n"
                        f"Apply these rules to your response:\n\n"
                        f"{ctx}"
                    )
            return result

        _tracked_support.__doc__ = support_lookup.__doc__
        toolset.add_function(
            _tracked_support,
            name="support_lookup",
        )

    # Add web_search tool for researcher skill
    if "researcher" in skill_slug:
        from bench.tools.web_search import web_search

        async def _tracked_search(query: str) -> str:
            result = web_search(query)
            _call_log.append(
                ToolCallDetail(
                    tool_name="web_search",
                    source="web",
                    query=query,
                    result=result,
                )
            )
            if tool_injection_callback:
                ctx = await tool_injection_callback(
                    "web_search",
                    "web",
                    query,
                    result,
                )
                if ctx:
                    result = (
                        f"{result}\n\n"
                        f"# ADDITIONAL RULES FROM PAST EXPERIENCE\n"
                        f"Apply these rules to your response:\n\n"
                        f"{ctx}"
                    )
            return result

        _tracked_search.__doc__ = (
            "Search for information about a company. Returns JSON with search results."
        )
        toolset.add_function(
            _tracked_search,
            name="web_search",
        )

    # Per-tool-call rule injection: the tool_injection_callback's
    # return value is appended to the tool's result string directly
    # (see _make_tracked_lookup above and the other _tracked_* funcs).
    # This avoids splicing extra system messages into the message stream
    # mid-tool-call, which would break OpenAI's strict assistant/tool
    # pairing rule. The rules still reach the model — just as part of
    # the tool result text instead of a separate system message.

    skill_model = _load_skill_model(skill_slug)
    provider_config = {
        "vertexai-anthropic": {
            "project": os.environ.get(
                "GCP_PROJECT_ID",
                "",
            ),
            "location": os.environ.get(
                "GCP_LOCATION_ANTHROPIC",
                "global",
            ),
        },
    }
    model = _resolve_model(
        skill_model,
        provider_config,
    )

    # Some newer Anthropic models (e.g. Opus 4.7+) deprecated the
    # `temperature` parameter and reject it. For those, omit
    # temperature; defaults will be used.
    _no_temperature_models = ("opus-4-6", "opus-4-7")
    _supports_temperature = not any(
        tag in str(skill_model).lower() for tag in _no_temperature_models
    )
    _settings = ModelSettings(temperature=0) if _supports_temperature else ModelSettings()
    agent = Agent(
        model,
        instructions=system_prompt,
        toolsets=[toolset],
        model_settings=_settings,
    )

    # Convert simple {role, content} dicts into pydantic-ai message
    # objects so they can be passed as prior conversation history.
    message_history: list[Any] | None = None
    if prior_messages:
        from pydantic_ai.messages import (
            ModelRequest,
            ModelResponse,
            TextPart,
            UserPromptPart,
        )

        message_history = []
        for m in prior_messages:
            role = m.get("role")
            content = m.get("content", "")
            if not isinstance(content, str) or not content:
                continue
            if role == "user":
                message_history.append(
                    ModelRequest(parts=[UserPromptPart(content=content)]),
                )
            elif role == "assistant":
                message_history.append(
                    ModelResponse(parts=[TextPart(content=content)]),
                )

    try:
        if message_history:
            result = await agent.run(query, message_history=message_history)
        else:
            result = await agent.run(query)
    except Exception as e:
        # Some as-conv-turn adapters (raw_seed_as_conv_turn on huge-trace scenarios
        # like noise_100_corrections, scale_50_corrections) can push the
        # prompt past the model's context window. Don't kill the whole
        # bench — score the run as empty output and let the judge handle.
        msg = str(e).lower()
        if "prompt is too long" in msg or "context_length" in msg or "too long" in msg:
            logger.warning(
                "Agent call failed with context-length error; returning empty output: %s",
                str(e)[:200],
            )
            return AgentResult(
                output="",
                input_tokens=0,
                output_tokens=0,
                requests=0,
                tool_calls=0,
                tool_call_details=list(_call_log),
            )
        raise
    usage = result.usage()
    return AgentResult(
        output=result.output,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        requests=usage.requests,
        tool_calls=usage.tool_calls,
        tool_call_details=list(_call_log),
    )
