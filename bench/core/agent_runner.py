"""Unified, channel-routing agent runner.

ONE agent loop that any approach can use. The benchmark owns the
scaffolding adopters should never have to rewrite — the skill prompt,
the mocked tools, model resolution, the tool-call loop, usage
tracking — and exposes the only decision that belongs to the
approach: *which channel each piece of retrieved memory goes into*.

The adopter supplies two things:

* ``initial`` — a list of :class:`~bench.core.channels.Injection`
  applied once before the first model call (system-prompt additions
  and/or fabricated dialogue turns).
* ``on_tool`` — an async callback ``(tool_name, source, query,
  result) -> list[Injection]`` run after every tool call; its
  injections reach the model on the *next* request.

Every ``Injection.content`` is delivered verbatim — the runner adds
no wrapper text. The adopter has byte-level control over the prompt.

This is the canonical run loop for every approach adapter. The old
channel choices are now just presets expressed in ``Injection``s:
the default loop was ``SYSTEM_APPEND`` + ``TOOL_RESULT_SUFFIX``; the
B+3 channel-correct loop (the one that reproduces the paper) is
``USER_TURN``/``ASSISTANT_TURN`` + ``SYSTEM_PART``. The standalone
``_run_agent`` in ``bench.core.agent`` is kept only for the raw
control baseline and the playground.

:func:`run_from_protocol` is the thin bridge an adapter's ``run_agent``
calls to map the orchestrator's ``injection_text`` / ``prior_messages``
/ ``tool_callback`` onto channels.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

from bench.core.agent import AgentResult, ToolCallDetail
from bench.core.channels import Channel, Injection
from bench.core.config import FIXTURES_DIR, _resolve_model
from bench.core.skills import _load_skill_model, _load_skill_prompt
from bench.core.tool_harness import (
    _build_tool_defs,
    _clear_tool_caches,
    _execute_tool,
    _parse_tool_args,
)

logger = logging.getLogger(__name__)

#: Adopter per-tool hook signature.
OnTool = Callable[[str, str, str, str], Awaitable[list[Injection]]]


def _assemble_system_prompt(skill_slug: str, initial: list[Injection]) -> str:
    """Skill prompt with SYSTEM_PREPEND/SYSTEM_APPEND injections applied."""
    base = _load_skill_prompt(skill_slug)
    prepends = [i.content for i in initial if i.channel == Channel.SYSTEM_PREPEND]
    appends = [i.content for i in initial if i.channel == Channel.SYSTEM_APPEND]
    parts = [*prepends, base, *appends]
    return "\n\n".join(p for p in parts if p)


async def run_agent(
    *,
    skill: str,
    query: str,
    company: str,
    initial: list[Injection] | None = None,
    on_tool: OnTool | None = None,
    dedupe_per_tool: bool = True,
    max_iters: int = 16,
) -> AgentResult:
    """Run the benchmark agent with adopter-controlled channel routing.

    Args:
        skill: skill slug (loads the system prompt + tool set).
        query: the test query.
        company: subject company (passed through for parity).
        initial: injections applied before the first model call.
        on_tool: async ``(tool, source, query, result) -> [Injection]``
            run after each tool call; injections reach the next request.
        dedupe_per_tool: drop a per-tool injection whose exact content
            already fired earlier in the run (prevents the system slot
            from accumulating duplicates across tool calls).
        max_iters: safety bound on tool-call rounds.
    """
    from pydantic_ai.messages import (
        ModelRequest,
        ModelResponse,
        SystemPromptPart,
        TextPart,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )
    from pydantic_ai.models import ModelRequestParameters
    from pydantic_ai.settings import ModelSettings

    initial = initial or []
    os.environ["EVAL_FIXTURES_DIR"] = str(FIXTURES_DIR)
    _clear_tool_caches(skill)

    # --- System prompt (skill + SYSTEM_PREPEND/APPEND) ---
    system_prompt = _assemble_system_prompt(skill, initial)

    # --- Resolve model ---
    skill_model = _load_skill_model(skill)
    provider_config = {
        "vertexai-anthropic": {
            "project": os.environ.get("GCP_PROJECT_ID", ""),
            "location": os.environ.get("GCP_LOCATION_ANTHROPIC", "global"),
        },
    }
    model: Any = _resolve_model(skill_model, provider_config)
    no_temp_tags = ("opus-4-6", "opus-4-7")
    supports_temp = not any(t in str(skill_model).lower() for t in no_temp_tags)
    settings = ModelSettings(temperature=0) if supports_temp else ModelSettings()
    params = ModelRequestParameters(
        function_tools=_build_tool_defs(skill),
        builtin_tools=[],
        output_mode="text",
        output_object=None,
        output_tools=[],
        prompted_output_template=None,
        allow_text_output=True,
        allow_image_output=False,
        thinking=None,
    )

    # --- Initial message history: fabricated dialogue then the query ---
    # USER_TURN / ASSISTANT_TURN injections become prior conversation
    # turns, in the order the adopter listed them. The system prompt
    # rides on the first ModelRequest's `instructions`.
    messages: list[Any] = []
    dialogue = [
        i for i in initial if i.channel in (Channel.USER_TURN, Channel.ASSISTANT_TURN) and i.content
    ]
    first_request_made = False
    for inj in dialogue:
        if inj.channel == Channel.USER_TURN:
            if first_request_made:
                messages.append(ModelRequest(parts=[UserPromptPart(content=inj.content)]))
            else:
                messages.append(
                    ModelRequest(
                        parts=[UserPromptPart(content=inj.content)],
                        instructions=system_prompt,
                    )
                )
            first_request_made = True
        else:  # ASSISTANT_TURN
            messages.append(ModelResponse(parts=[TextPart(content=inj.content)]))

    if first_request_made:
        messages.append(ModelRequest(parts=[UserPromptPart(content=query)]))
    else:
        messages.append(
            ModelRequest(parts=[UserPromptPart(content=query)], instructions=system_prompt)
        )

    # --- Agent loop ---
    call_log: list[ToolCallDetail] = []
    in_tokens = out_tokens = requests = 0
    seen: set[str] = set()

    def _result(output: str) -> AgentResult:
        return AgentResult(
            output=output,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            requests=requests,
            tool_calls=len(call_log),
            tool_call_details=list(call_log),
        )

    for _ in range(max_iters):
        try:
            response = await model.request(messages, settings, params)
        except Exception as e:
            msg = str(e).lower()
            if "too long" in msg or "context_length" in msg:
                logger.warning("agent context-length error: %s", str(e)[:200])
                return _result("")
            raise

        requests += 1
        usage = response.usage
        if usage:
            in_tokens += getattr(usage, "input_tokens", 0) or 0
            out_tokens += getattr(usage, "output_tokens", 0) or 0
        messages.append(response)

        tool_calls = [p for p in response.parts if isinstance(p, ToolCallPart)]
        text_parts = [p.content for p in response.parts if isinstance(p, TextPart)]
        if not tool_calls:
            return _result("\n".join(text_parts))

        return_parts: list[Any] = []
        sys_parts: list[str] = []
        user_notes: list[str] = []
        for tc in tool_calls:
            args = _parse_tool_args(tc.args)
            source = args.get("source", "")
            qarg = args.get("query", "")
            result_text = _execute_tool(tc.tool_name, args, skill)
            call_log.append(
                ToolCallDetail(
                    tool_name=tc.tool_name, source=source, query=qarg, result=result_text
                )
            )

            injs: list[Injection] = []
            if on_tool is not None:
                injs = await on_tool(tc.tool_name, source, qarg, result_text) or []

            suffixes: list[str] = []
            for inj in injs:
                if not inj.content:
                    continue
                if inj.is_initial():
                    logger.warning(
                        "Channel %s returned from per-tool hook; ignored "
                        "(use SYSTEM_PART / TOOL_RESULT_SUFFIX / USER_NOTE).",
                        inj.channel,
                    )
                    continue
                if dedupe_per_tool and inj.content in seen:
                    continue
                seen.add(inj.content)
                if inj.channel == Channel.TOOL_RESULT_SUFFIX:
                    suffixes.append(inj.content)
                elif inj.channel == Channel.SYSTEM_PART:
                    sys_parts.append(inj.content)
                elif inj.channel == Channel.USER_NOTE:
                    user_notes.append(inj.content)

            content = result_text
            if suffixes:
                content = result_text + "\n\n" + "\n\n".join(suffixes)
            return_parts.append(
                ToolReturnPart(
                    tool_name=tc.tool_name, content=content, tool_call_id=tc.tool_call_id
                )
            )

        # Next request: SYSTEM_PART(s) + USER_NOTE(s) + the tool returns.
        request_parts: list[Any] = []
        for sp in sys_parts:
            request_parts.append(SystemPromptPart(content=sp))
        for un in user_notes:
            request_parts.append(UserPromptPart(content=un))
        request_parts.extend(return_parts)
        messages.append(ModelRequest(parts=request_parts))

    return _result("(max iterations reached)")


async def run_from_protocol(
    *,
    skill: str,
    query: str,
    company: str,
    injection_text: str,
    tool_callback: Any,
    prior_messages: list[dict[str, Any]] | None = None,
    initial_channel: Channel = Channel.SYSTEM_APPEND,
    per_tool_channel: Channel = Channel.SYSTEM_PART,
) -> AgentResult:
    """Bridge the orchestrator's Protocol arguments onto channels.

    An adapter's ``run_agent`` is then a one-liner:

        return await run_from_protocol(
            skill=skill, query=query, company=company,
            injection_text=injection_text, tool_callback=tool_callback,
            prior_messages=prior_messages,
            initial_channel=Channel.USER_TURN,
            per_tool_channel=Channel.SYSTEM_PART,
        )

    Mapping:
    * ``injection_text`` (from ``get_injection``) -> ``initial_channel``.
      If that channel is ``USER_TURN``, an acknowledgement
      ``ASSISTANT_TURN`` is added so the fabricated dialogue reads
      naturally.
    * ``prior_messages`` (from ``get_prior_messages``) -> ``USER_TURN`` /
      ``ASSISTANT_TURN`` injections in order (roles preserved).
    * each ``tool_callback`` result -> ``per_tool_channel``.

    Content is passed through verbatim — the adopter owns the wording.
    """
    initial: list[Injection] = []
    if injection_text:
        initial.append(Injection(injection_text, initial_channel))
        if initial_channel == Channel.USER_TURN:
            initial.append(
                Injection("Understood — I will apply these corrections.", Channel.ASSISTANT_TURN)
            )
    for m in prior_messages or []:
        content = m.get("content", "")
        if not content:
            continue
        chan = Channel.USER_TURN if m.get("role") == "user" else Channel.ASSISTANT_TURN
        initial.append(Injection(content, chan))

    async def _on_tool(tool: str, source: str, q: str, result: str) -> list[Injection]:
        text = await tool_callback(tool, source, q, result)
        return [Injection(text, per_tool_channel)] if text else []

    return await run_agent(
        skill=skill,
        query=query,
        company=company,
        initial=initial,
        on_tool=_on_tool,
    )
