from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_auth_error_retry",
    name="Don't retry permanent auth errors",
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
            company="suspended-beta.io",
            message_content="Handle support ticket for suspended-beta.io: auth token expired after account deactivation",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="suspended-gamma.io",
            message_content="Handle support ticket for suspended-gamma.io: SSO fails after org migration",
            parent_index=None,
        ),
    ],
    test_company="suspended-delta.io",
    test_query="Handle support ticket for suspended-delta.io: login fails after account suspension",
    rubric=[
        RubricItem(
            criterion="Agent does NOT call search_knowledge_base after receiving account_suspended error",
            weight=1.0,
            mode="negative",
        ),
        RubricItem(
            criterion="Agent escalates directly after account_suspended without consulting KB",
            weight=1.0,
        ),
    ],
    description=(
        "Tests implicit learning that KB never helps for suspended accounts. "
        "Past traces show search_knowledge_base always returns empty for suspended-*.io. "
        "Agent should learn to skip KB and escalate directly."
    ),
    behavior_checks=[
        BehaviorCheck(
            name="skipped_kb_for_auth_error",
            check_type="source_not_called",
            sources=["search_knowledge_base"],
            weight=2.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_auth_error_retry.json",
)
