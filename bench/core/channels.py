"""Injection channels — the declarative surface adopters use to control
*what* gets injected, *when*, *with which exact wording*, and into
*which channel*.

The benchmark's job is to run an agent over a skill with mocked tools
and score it. *How* an approach surfaces its retrieved memory is the
approach's decision, not the benchmark's. This module lets an adopter
express that decision as data: a list of :class:`Injection` objects,
each pairing the exact text to inject with the :class:`Channel` it
should go into. :func:`bench.core.agent_runner.run_agent` reads those
objects and routes each one to the right place in the agent loop.

There is no hidden wrapping: ``Injection.content`` is delivered
verbatim. If you want a prefix like ``"RULE: "`` or
``"# Corrections from past runs"``, put it in ``content`` yourself.
That is the point — you get byte-level control over the prompt.

Two timing points exist:

* **Initial** — assembled once before the agent's first model call.
  Use channels ``SYSTEM_APPEND``, ``SYSTEM_PREPEND``, ``USER_TURN``,
  ``ASSISTANT_TURN``.
* **Per-tool-call** — produced after each tool call, available to the
  model on its *next* request. Use channels ``SYSTEM_PART``,
  ``TOOL_RESULT_SUFFIX``, ``USER_NOTE``.

A channel used at the wrong timing point is ignored with a warning
(e.g. ``SYSTEM_APPEND`` returned from the per-tool hook), so mistakes
are loud rather than silent.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Channel(StrEnum):
    """Where an injection is placed in the agent's message stream."""

    # ---- initial (before the first model call) -------------------
    SYSTEM_APPEND = "system_append"
    """Appended to the end of the skill's system prompt."""

    SYSTEM_PREPEND = "system_prepend"
    """Prepended before the skill's system prompt (e.g. an
    'inception'-style framing that makes the skill read as the task
    that follows)."""

    USER_TURN = "user_turn"
    """A fabricated user message inserted into the prior conversation
    history, before the real query. The model sees it as something
    'the user said earlier'. This is the stage-1 channel that worked
    across frontier models in the channel study."""

    ASSISTANT_TURN = "assistant_turn"
    """A fabricated assistant message inserted into the prior history,
    typically paired after a ``USER_TURN`` to simulate the agent
    having acknowledged a correction."""

    # ---- per-tool-call (after a tool result, before next request) -
    SYSTEM_PART = "system_part"
    """A ``SystemPromptPart`` placed on the next ``ModelRequest``.
    pydantic-ai concatenates these into the system slot of the next
    API call on both Anthropic and OpenAI backends, so the model
    treats it as trusted operating instructions. This is the stage-2
    channel that survived safety-trained models (Opus 4.5+, GPT-5)."""

    TOOL_RESULT_SUFFIX = "tool_result_suffix"
    """Appended to the tool's returned content string. Cheapest path;
    safety-trained models may discount it as untrusted tool data."""

    USER_NOTE = "user_note"
    """A ``UserPromptPart`` placed alongside the tool returns on the
    next request — a user-channel note. Included for completeness; the
    channel study found models treat this as a fresh conversational
    turn and lose focus on the tool data."""


_INITIAL = {
    Channel.SYSTEM_APPEND,
    Channel.SYSTEM_PREPEND,
    Channel.USER_TURN,
    Channel.ASSISTANT_TURN,
}
_PER_TOOL = {
    Channel.SYSTEM_PART,
    Channel.TOOL_RESULT_SUFFIX,
    Channel.USER_NOTE,
}


@dataclass
class Injection:
    """One piece of retrieved memory plus the channel it goes into.

    ``content`` is injected verbatim — no wrapper is added by the
    runner. Include any prefix/framing you want in ``content``.
    """

    content: str
    channel: Channel

    def is_initial(self) -> bool:
        return self.channel in _INITIAL

    def is_per_tool(self) -> bool:
        return self.channel in _PER_TOOL


# Convenience constructors — purely sugar over Injection(...).
def system_append(text: str) -> Injection:
    return Injection(text, Channel.SYSTEM_APPEND)


def system_prepend(text: str) -> Injection:
    return Injection(text, Channel.SYSTEM_PREPEND)


def user_turn(text: str) -> Injection:
    return Injection(text, Channel.USER_TURN)


def assistant_turn(text: str) -> Injection:
    return Injection(text, Channel.ASSISTANT_TURN)


def system_part(text: str) -> Injection:
    return Injection(text, Channel.SYSTEM_PART)


def tool_result_suffix(text: str) -> Injection:
    return Injection(text, Channel.TOOL_RESULT_SUFFIX)


def user_note(text: str) -> Injection:
    return Injection(text, Channel.USER_NOTE)
