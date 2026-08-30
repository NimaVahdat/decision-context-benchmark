"""Data models for evaluation scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from bench.judge.programmatic import BehaviorCheck


@dataclass
class RubricItem:
    """Single criterion for judging output quality."""

    criterion: str
    weight: float = 1.0
    mode: str = "positive"  # "positive" or "negative"


@dataclass
class SeedTrace:
    """One trace in a multi-trace seed sequence.

    Defines the recipe for building real seeds via
    bench/seedgen/build_scenario.py. Each trace is
    either an initial agent run or a correction
    (linked via parent_index).
    """

    skill: str
    company: str
    message_content: str  # user message / correction text
    parent_index: int | None = None
    actor_id: str = "eval-runner"


@dataclass
class Scenario:
    """A benchmark evaluation scenario."""

    id: str
    name: str
    skill: str

    # Seed trace recipe (used by seedgen to build real seeds)
    seed_traces: list[SeedTrace]

    # Test query
    test_company: str
    test_query: str

    # Real seed file (required — all seeds must be real)
    real_seed_file: Path

    # Multi-criterion rubric (supports negative mode)
    rubric: list[RubricItem] = field(
        default_factory=list,
    )

    # Human-readable description
    description: str = ""

    # Expected approach ordering (documentation only)
    expected_ordering: str = ""

    # Actor ID for query-time actor boost
    test_actor_id: str | None = None

    # Subjects for query-time subject filtering
    test_subjects: list[str] | None = None

    # Programmatic behavioral checks (optional)
    behavior_checks: list[BehaviorCheck] = field(
        default_factory=list,
    )
