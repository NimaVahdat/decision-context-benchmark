"""Scoring: combined programmatic + LLM judge score."""

from __future__ import annotations

from bench.judge.programmatic import evaluate_checks


def _combined_score(
    judge_score: float,
    output: str,
    tool_calls: int,
    scenario: object,
    tool_call_details: list | None = None,
) -> float:
    """Score using programmatic checks when available,
    LLM judge otherwise."""
    checks = getattr(scenario, "behavior_checks", [])
    if not checks:
        return judge_score
    _, prog_score = evaluate_checks(
        output,
        tool_calls,
        checks,
        tool_call_details=tool_call_details,
    )
    return prog_score
