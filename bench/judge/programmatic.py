"""Programmatic judge for agent behavioral checks.

Evaluates agent behavior by checking WHAT THE AGENT DID
(tool calls made, sources used) rather than what it wrote.

Two types of checks:
1. Tool-call checks — verify which tools were called,
   how many times, with what parameters. Based on the
   actual ToolCallDetail log from the agent run.
2. Output checks — simple keyword/regex presence in the
   agent's output text. No context-awareness (if the
   keyword appears anywhere, it matches).

Used for scenarios with behavior_checks. Scenarios without
behavior_checks use the LLM judge (judge.py) instead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class BehaviorCheck:
    """A single check on agent behavior.

    check_type determines what is checked:

    Tool-call checks (use tool_call_details):
      source_not_called  — PASS if agent did NOT call any
                           of the listed sources
      source_called      — PASS if agent called at least
                           one of the listed sources
      no_duplicate_calls — PASS if no (source, query) pair
                           was called more than once
      tool_call_max      — PASS if total tool calls <= threshold
      early_quality_result — PASS if one of the first N calls
                           (N=threshold) returned a result with
                           results_count >= 5 (JSON parsed).
                           Tests that the agent found the right
                           query strategy early.

    Output text checks:
      keyword_present    — PASS if any keyword found in output
      keyword_absent     — PASS if no keyword found in output
      regex_absent       — PASS if regex does NOT match output
    """

    name: str
    check_type: str
    threshold: int = 0
    keywords: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    pattern: str = ""
    weight: float = 1.0


def evaluate_checks(
    output: str,
    tool_calls: int,
    checks: list[BehaviorCheck],
    tool_call_details: list | None = None,
) -> tuple[dict[str, bool], float]:
    """Run all checks and return results + weighted score.

    Args:
        output: Agent's output text.
        tool_calls: Total number of tool calls made.
        checks: List of BehaviorCheck to evaluate.
        tool_call_details: List of ToolCallDetail objects
            (each has tool_name, source, query attributes).

    Returns:
        (results dict, weighted score 0.0-1.0)
    """
    if not checks:
        return {}, 1.0

    details = tool_call_details or []
    results: dict[str, bool] = {}
    total_weight = 0.0
    weighted_sum = 0.0

    for check in checks:
        passed = _run_check(output, tool_calls, details, check)
        results[check.name] = passed
        total_weight += check.weight
        if passed:
            weighted_sum += check.weight

    score = weighted_sum / total_weight if total_weight > 0 else 1.0
    return results, score


def _run_check(
    output: str,
    tool_calls: int,
    details: list,
    check: BehaviorCheck,
) -> bool:
    """Run a single check."""
    output_lower = output.lower()
    called_sources = [getattr(d, "source", "") for d in details]

    match check.check_type:
        # -- Tool-call checks --
        case "tool_call_max":
            return tool_calls <= check.threshold

        case "source_not_called":
            return not any(s in called_sources for s in check.sources)

        case "source_called":
            return any(s in called_sources for s in check.sources)

        case "no_duplicate_calls":
            seen: set[str] = set()
            for d in details:
                key = f"{getattr(d, 'source', '')}:{getattr(d, 'query', '')}"
                if key in seen:
                    return False
                seen.add(key)
            return True

        case "early_quality_result":
            import json as _json

            n = check.threshold or 2
            for d in details[:n]:
                result_str = getattr(d, "result", "")
                if not result_str:
                    continue
                try:
                    parsed = _json.loads(result_str)
                    if parsed.get("results_count", 0) >= 5:
                        return True
                except (ValueError, TypeError, AttributeError):
                    continue
            return False

        case "tool_call_order":
            # Verify a source appears at or before position N.
            # threshold = max allowed position (1-indexed).
            # sources = [source that should be at that position].
            pos = check.threshold or 1
            for i, d in enumerate(details):
                src = getattr(d, "source", "")
                if src in check.sources:
                    return (i + 1) <= pos
            return False  # source not called at all

        case "tool_call_not_before":
            # Verify a source does NOT appear before position N.
            # PASS if source is at position >= threshold.
            # Used to check "financials must not be first."
            pos = check.threshold or 2
            for i, d in enumerate(details):
                src = getattr(d, "source", "")
                if src in check.sources:
                    return (i + 1) >= pos
            return True  # source not called = OK

        # -- Output text checks --
        case "keyword_present":
            return any(kw.lower() in output_lower for kw in check.keywords)

        case "keyword_absent":
            return not any(kw.lower() in output_lower for kw in check.keywords)

        case "regex_absent":
            return not bool(re.search(check.pattern, output))

        case _:
            return True
