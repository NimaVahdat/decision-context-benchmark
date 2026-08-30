from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_presales_skip",
    name="Skip account/order lookups for pre-sales tickets",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="presales-alpha.io",
            message_content="Handle support ticket for presales-alpha.io: pre-sales pricing question",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="presales-beta.io",
            message_content="Handle support ticket for presales-beta.io: pre-sales integration question",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="presales-gamma.io",
            message_content="Handle support ticket for presales-gamma.io: pre-sales trial request",
            parent_index=None,
        ),
    ],
    test_company="presales-delta.io",
    test_query="Handle support ticket for presales-delta.io: pre-sales demo request",
    rubric=[
        RubricItem(
            criterion="Agent does NOT call lookup_account or check_order_status for the pre-sales ticket",
            weight=1.0,
            mode="negative",
        ),
        RubricItem(
            criterion="Agent routes directly to knowledge base or sales team without wasting calls on account lookups",
            weight=0.5,
        ),
    ],
    description=(
        "Tests learning that pre-sales contacts have no account/order data. "
        "Past traces show lookup_account and check_order_status always return errors for presales-*.io contacts."
    ),
    behavior_checks=[
        BehaviorCheck(
            name="skipped_useless_lookups",
            check_type="source_not_called",
            sources=["lookup_account", "check_order_status"],
            weight=2.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_presales_skip.json",
)
