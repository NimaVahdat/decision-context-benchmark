from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="exception_no_persist",
    name="One-time skip does not persist to next analysis",
    skill="eval-analyst",
    seed_traces=[
        SeedTrace(
            skill="eval-analyst",
            company="retool.com",
            message_content="Analyze retool.com",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="retool.com",
            message_content=(
                "Skip the Team section for this one — I already know the Retool team well."
            ),
            parent_index=0,
        ),
    ],
    test_company="notion.so",
    test_query="Analyze notion.so",
    rubric=[
        RubricItem(
            criterion="Analysis includes a Team section with leadership information — one-time skip should NOT have persisted",
            weight=1.0,
        ),
        RubricItem(criterion="Agent omits the Team section entirely", mode="negative", weight=1.0),
    ],
    description="Control=1 expected (agent naturally includes Team). Tests that DC does NOT over-generalize a one-time skip instruction.",
    behavior_checks=[
        BehaviorCheck(
            name="team_section_present",
            check_type="keyword_present",
            keywords=["## team"],
            weight=2.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "exception_no_persist.json",
)
