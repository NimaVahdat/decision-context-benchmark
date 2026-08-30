from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="exception_vs_rule",
    name="Persistent rule survives one-off exception",
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
                "Always include Rule of 40 score in Financial Overview. Calculate as: growth_rate% + gross_margin%. Label it 'Rule of 40:' explicitly."
            ),
            parent_index=0,
        ),
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
                "Skip Rule of 40 for this one — the gross margin figures are still being restated."
            ),
            parent_index=2,
        ),
    ],
    test_company="notion.so",
    test_query="Analyze notion.so",
    rubric=[
        RubricItem(
            criterion="Financial overview includes 'Rule of 40:' score (the persistent rule should apply)",
            weight=1.0,
        ),
        RubricItem(
            criterion="Agent applies standing Rule of 40 rule despite one-off retool.com exception",
            weight=1.0,
        ),
    ],
    behavior_checks=[
        BehaviorCheck(
            name="rule_of_40_present",
            check_type="keyword_present",
            keywords=["rule of 40"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "exception_vs_rule.json",
)
