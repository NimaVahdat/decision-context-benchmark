from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_tier_change",
    name="Apply updated routing after account tier upgrade",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="Handle support ticket for repeat-alpha.io: sync failure",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="repeat-alpha.io just upgraded to Enterprise. From now on route their tickets directly to dedicated CSM, skip tier-1 queue.",
            parent_index=0,
        ),
    ],
    test_company="repeat-alpha.io",
    test_query="Handle support ticket for repeat-alpha.io: login issue for repeat-alpha.io",
    rubric=[
        RubricItem(
            criterion="Agent routes to dedicated CSM or enterprise support, not standard tier-1",
            weight=1.0,
        ),
        RubricItem(
            criterion="Output reflects the enterprise routing path, not the old growth-tier path",
            weight=0.5,
        ),
    ],
    description="Tests applying updated routing after a tier upgrade. Agent must use the new enterprise routing, not the old growth-tier default.",
    real_seed_file=Path(__file__).parent / "support_tier_change.json",
)
