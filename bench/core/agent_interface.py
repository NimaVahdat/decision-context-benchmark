"""Protocol describing the approach-module contract.

An "approach module" is a Python module the bench loads and calls to
drive a benchmark run for one memory-system design. The bench is
duck-typed: any module that exposes the names declared here can be
passed to ``bench/run.py`` via ``--agent path/to/agent.py``.

This module declares the contract as a :class:`AgentModule` Protocol
so adopters can type-check their implementations and see all the
hooks the bench expects in one place. No subclassing or inheritance
is required; structural typing means existing module-level files
satisfy the contract automatically as long as the names line up.

See ``examples/agent_template.py`` for a minimal pass-through agent
that implements every member.

Lifecycle (per scenario):

1. ``setup()`` runs once when the agent module is first loaded.
2. ``prepare()`` runs at the start of each scenario.
3. ``capture_one(trace)`` is called for every seed trace that
   precedes the test query, in order.
4. ``get_injection(...)`` and ``get_prior_messages(...)`` are each
   called once per scenario, after capture, to assemble whatever
   initial context the approach wants surfaced.
5. ``run_agent(...)`` runs ``num_runs`` times per scenario. Each call
   executes the agent with the provided query, the optional initial
   injection text, the optional ``prior_messages``, and a
   ``tool_callback`` that invokes ``on_tool_result(...)`` after every
   tool call.
6. ``teardown()`` runs once after the last run of the last scenario.

All async functions must accept the listed keyword arguments by name.
The bench passes them as kwargs to keep call sites stable.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

from bench.core.agent import AgentResult

#: Signature of the per-tool-call callback the bench injects into
#: ``run_agent``. Implementations should return any rule text they
#: want surfaced after the tool call, or an empty string for none.
ToolCallback = Callable[[str, str, str, str], Awaitable[str]]


@runtime_checkable
class AgentModule(Protocol):
    """Structural contract for an approach module loaded by the bench.

    All members are required except :meth:`get_prior_messages`, which
    the bench checks for via ``hasattr`` and skips if absent.
    """

    #: Short identifier for the approach. Used to name the per-approach
    #: results directory under ``bench/results/<name>/``.
    name: str

    async def setup(self) -> None:
        """One-time module-level init (loading models, opening DB
        connections, etc.). Called once before any scenarios run."""
        ...

    async def prepare(self) -> None:
        """Per-scenario reset hook. Called before each scenario's
        capture phase. Typical use: clear the approach's memory store
        so seed traces from the previous scenario don't bleed in."""
        ...

    async def capture_one(self, trace: dict[str, Any]) -> None:
        """Ingest a single seed trace into the approach's memory.

        The bench calls this once per seed trace in scenario order
        before the test query is issued. ``trace`` is the raw seed
        dictionary loaded from the scenario's seed JSON file.
        """
        ...

    async def get_injection(
        self,
        *,
        skill: str,
        company: str,
        query: str,
        actor_id: str | None,
        subjects: list[str] | None,
    ) -> str:
        """Return the up-front correction text the bench should hand
        to the agent at query time (or an empty string for none).

        Called once per scenario, after capture and before the first
        run. The returned string is forwarded to :meth:`run_agent` as
        the ``injection_text`` argument and is also recorded on the
        result record.
        """
        ...

    async def on_tool_result(
        self,
        tool_name: str,
        source: str,
        query: str,
        tool_result: str,
    ) -> str:
        """Per-tool-call hook. Return any rule text the approach
        wants surfaced for this tool call, or an empty string.

        The bench invokes this from a ``ToolCallback`` it passes into
        :meth:`run_agent`. The agent loop is expected to call the
        callback after each tool result is received.
        """
        ...

    async def run_agent(
        self,
        *,
        skill: str,
        query: str,
        company: str,
        injection_text: str,
        tool_callback: ToolCallback,
        prior_messages: list[dict[str, Any]] | None = None,
    ) -> AgentResult:
        """Execute the agent for one scenario run.

        Implementations should run the underlying LLM agent with the
        provided ``query`` and ``skill``, applying ``injection_text``
        as initial system-channel context (if non-empty) and
        ``prior_messages`` as prior conversation history (if not
        ``None``). The implementation must call ``tool_callback``
        after every tool call so per-tool-call rules can be surfaced.

        Returns an :class:`AgentResult` carrying the final output and
        usage stats.
        """
        ...

    async def teardown(self) -> None:
        """Symmetric to :meth:`setup`. Runs once after all scenarios
        finish. Typical use: close DB connections, flush caches."""
        ...


@runtime_checkable
class AgentModuleWithPriorMessages(AgentModule, Protocol):
    """Optional extension protocol. Approaches that surface their
    initial corrections as a fabricated user/assistant dialogue (the
    "fake-dialogue" stage-1 mechanism) implement this in addition to
    :class:`AgentModule`.
    """

    async def get_prior_messages(
        self,
        *,
        skill: str,
        company: str,
        query: str,
        actor_id: str | None,
        subjects: list[str] | None,
    ) -> list[dict[str, Any]] | None:
        """Return a list of ``{"role": "user"|"assistant", "content": str}``
        dicts the bench should prepend to the conversation as prior
        history. Return ``None`` to skip this stage entirely.
        """
        ...
