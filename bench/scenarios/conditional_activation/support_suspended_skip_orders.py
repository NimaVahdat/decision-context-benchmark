from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_suspended_skip_orders",
    name="Skip order lookup when account is suspended",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="suspended-alpha.io",
            message_content="Handle support ticket for suspended-alpha.io: customer locked out after password reset",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="suspended-alpha.io",
            message_content="When account_suspended, skip both order lookup AND KB search — just escalate directly to billing.",
            parent_index=0,
        ),
    ],
    test_company="suspended-delta.io",
    test_query="Handle support ticket for suspended-delta.io: login fails after account suspension",
    rubric=[
        RubricItem(
            criterion="Agent does NOT call check_order_status or search_knowledge_base after receiving account_suspended",
            weight=1.0,
        ),
        RubricItem(
            criterion="Agent escalates to billing team directly without searching KB", weight=1.0
        ),
    ],
    description="Tests conditional skip: 'if account_suspended → skip order lookup AND KB search, escalate directly'. Agent must detect the suspension signal and skip both unnecessary lookups.",
    behavior_checks=[
        BehaviorCheck(
            name="skipped_kb_after_suspension",
            check_type="source_not_called",
            sources=["check_order_status", "search_knowledge_base"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_suspended_skip_orders.json",
)
