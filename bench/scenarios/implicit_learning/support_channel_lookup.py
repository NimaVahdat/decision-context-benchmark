from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_channel_lookup",
    name="Skip direct account lookup for chat-channel tickets",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="chat-alpha.io",
            message_content="Handle support ticket for chat-alpha.io: customer can't find invoice",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="chat-beta.io",
            message_content="Handle support ticket for chat-beta.io: customer asking about subscription tier",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="chat-gamma.io",
            message_content="Handle support ticket for chat-gamma.io: customer needs usage report",
            parent_index=None,
        ),
    ],
    test_company="chat-delta.io",
    test_query="Handle support ticket for chat-delta.io: customer asking about overdue payment",
    rubric=[
        RubricItem(
            criterion="Agent does NOT call lookup_account for the chat ticket (lookup_account fails without account_id)",
            weight=1.0,
            mode="negative",
        ),
        RubricItem(
            criterion="Agent calls search_by_email instead, which succeeds for chat-channel tickets",
            weight=1.0,
        ),
    ],
    description=(
        "Tests learning optimal lookup strategy for chat-channel tickets. "
        "Past traces show lookup_account always fails for chat-*.io (no account_id in chat metadata), "
        "while search_by_email succeeds. Agent should skip lookup_account and go straight to search_by_email."
    ),
    behavior_checks=[
        BehaviorCheck(
            name="skipped_failing_lookup",
            check_type="source_not_called",
            sources=["lookup_account"],
            weight=2.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_channel_lookup.json",
)
