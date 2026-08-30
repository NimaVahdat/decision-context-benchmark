from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_order_before_kb",
    name="Check order status before KB for billing tickets",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="orion-acme.io",
            message_content="Handle support ticket for orion-acme.io: billing invoice discrepancy",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="orion-acme.io",
            message_content="For billing tickets: check order status, then escalate directly to billing team — no need to search KB, the billing team already has the articles.",
            parent_index=0,
        ),
    ],
    test_company="orion-delta.io",
    test_query="Handle support ticket for orion-delta.io: billing overcharge for orion-delta.io",
    rubric=[
        RubricItem(
            criterion="Agent calls check_order_status but does NOT call search_knowledge_base",
            weight=1.0,
        ),
        RubricItem(
            criterion="Agent escalates to billing team after checking order status, skipping KB",
            weight=1.0,
        ),
    ],
    description="Tests procedural change: for billing tickets, check orders then escalate directly — skip KB entirely.",
    behavior_checks=[
        BehaviorCheck(
            name="skipped_kb_for_billing",
            check_type="source_not_called",
            sources=["search_knowledge_base"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_order_before_kb.json",
)
