from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="query_avoid_bad_pattern",
    name="Learn to avoid query patterns that return nothing",
    skill="eval-researcher",
    seed_traces=[
        SeedTrace(
            skill="eval-researcher",
            company="delve.co",
            message_content="Research delve.co",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-researcher",
            company="linear.app",
            message_content="Research linear.app",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-researcher",
            company="meridian.bio",
            message_content="Research meridian.bio",
            parent_index=None,
        ),
    ],
    test_company="delve.co",
    test_query="Research delve.co",
    rubric=[
        RubricItem(
            criterion="Agent does NOT use revenue or financial-specific queries that previously returned no results",
            weight=1.0,
            mode="negative",
        ),
        RubricItem(
            criterion="Agent finds more results than the previous attempts by using a different query strategy",
            weight=1.0,
        ),
    ],
    description="Tests learning to avoid bad query patterns. Revenue/financial queries return nothing.",
    behavior_checks=[
        BehaviorCheck(
            name="early_quality_result", check_type="early_quality_result", threshold=1, weight=2.0
        ),
    ],
    real_seed_file=Path(__file__).parent / "query_avoid_bad_pattern.json",
)
