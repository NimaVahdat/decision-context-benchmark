from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_cross_skill_isolation",
    name="Support routing rule does not transfer to analyst skill",
    skill="eval-analyst",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="Handle support ticket for repeat-alpha.io: billing dispute",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="For billing tickets: escalate directly, skip KB",
            parent_index=0,
        ),
    ],
    test_company="repeat-alpha.io",
    test_query="Analyze repeat-alpha.io",
    rubric=[
        RubricItem(
            criterion="Agent produces a standard analyst report — does NOT skip data sources or escalate",
            weight=1.0,
        ),
        RubricItem(
            criterion="Agent does not apply support routing rules (skip KB, escalate) to the analyst task",
            weight=1.0,
        ),
    ],
    description="Tests skill scope isolation: a support routing rule must not affect the analyst skill's data gathering workflow.",
    real_seed_file=Path(__file__).parent / "support_cross_skill_isolation.json",
)
