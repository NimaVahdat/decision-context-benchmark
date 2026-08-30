from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_routing_noise",
    name="Routing rule survives contradictory noise ticket",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="Handle support ticket for repeat-alpha.io: billing discrepancy",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="Always escalate billing tickets directly — skip KB",
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-beta.io",
            message_content="Handle support ticket for repeat-beta.io: billing dispute",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-beta.io",
            message_content="For this one ticket it was fine to include KB links",
            parent_index=2,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-gamma.io",
            message_content="Handle support ticket for repeat-gamma.io: billing discrepancy for repeat-gamma.io",
            parent_index=None,
        ),
    ],
    test_company="repeat-delta.io",
    test_query="Handle support ticket for repeat-delta.io: billing dispute for repeat-delta.io",
    rubric=[
        RubricItem(
            criterion="Agent escalates directly without calling search_knowledge_base", weight=1.0
        ),
        RubricItem(
            criterion="Agent applies the standing billing rule (direct escalation) despite the one-off noise correction",
            weight=1.0,
        ),
    ],
    description="Tests noise resistance: a one-off contradictory correction should not override the standing rule for billing tickets.",
    behavior_checks=[
        BehaviorCheck(
            name="skipped_kb_for_billing",
            check_type="source_not_called",
            sources=["search_knowledge_base"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_routing_noise.json",
)
