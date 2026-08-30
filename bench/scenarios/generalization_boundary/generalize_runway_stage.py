from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="generalize_runway_stage",
    name="Short-runway rule generalizes to other short-runway companies",
    skill="eval-analyst",
    seed_traces=[
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content="Analyze delve.co",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content=(
                "For companies with short runway (under 20 months): open Financial Overview with 'RUNWAY RISK: X months' as the very first line before revenue."
            ),
            parent_index=0,
        ),
    ],
    test_company="learnnext.ai",
    test_query="Analyze learnnext.ai",
    rubric=[
        RubricItem(criterion="Financial overview opens with 'RUNWAY RISK:' label", weight=1.0),
        RubricItem(
            criterion="Agent generalizes the short-runway rule to learnnext.ai which also has < 20 months",
            weight=1.0,
        ),
    ],
    behavior_checks=[
        BehaviorCheck(
            name="runway_risk_present",
            check_type="keyword_present",
            keywords=["runway risk"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "generalize_runway_stage.json",
)
