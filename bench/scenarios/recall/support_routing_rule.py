from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_routing_rule",
    name="Recall: route tickets via escalation not KB for a customer",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="Handle support ticket for repeat-alpha.io: billing discrepancy (3rd report this month)",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="The customer told us to always escalate their tickets directly — they don't want KB self-service",
            parent_index=0,
        ),
    ],
    test_company="repeat-alpha.io",
    test_query="Handle support ticket for repeat-alpha.io: sync failure for repeat-alpha.io",
    rubric=[
        RubricItem(
            criterion="Agent escalates the ticket directly without attempting a KB search first",
            weight=1.0,
        ),
        RubricItem(
            criterion="Output does NOT include KB article suggestions or self-service steps",
            weight=0.5,
            mode="negative",
        ),
    ],
    description="Tests recall of a customer-specific routing preference. Customer correction: always escalate, skip KB.",
    behavior_checks=[
        BehaviorCheck(
            name="skipped_kb_per_customer_rule",
            check_type="source_not_called",
            sources=["search_knowledge_base"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_routing_rule.json",
)
