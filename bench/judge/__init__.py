"""bench.judge -- LLM + programmatic judging."""

from __future__ import annotations

# Programmatic judge has no circular deps, import eagerly.
from bench.judge.programmatic import BehaviorCheck as BehaviorCheck
from bench.judge.programmatic import evaluate_checks as evaluate_checks

# LLM judge imports bench.scenarios.models which imports
# bench.judge.programmatic, creating a circular import if
# we eagerly import here. Use lazy loading instead.


def __getattr__(name: str):
    if name in ("judge_scenario", "judge_output", "JudgeResult"):
        from bench.judge import llm

        return getattr(llm, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
