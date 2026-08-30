from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_escalate_suspended_first",
    name="Escalate before KB search for suspended accounts",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="suspended-alpha.io",
            message_content="Handle support ticket for suspended-alpha.io: customer locked out",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="suspended-alpha.io",
            message_content="When account is suspended, skip KB entirely — escalate directly to billing without searching KB.",
            parent_index=0,
        ),
    ],
    test_company="suspended-delta.io",
    test_query="Handle support ticket for suspended-delta.io: login fails after account suspension",
    rubric=[
        RubricItem(
            criterion="Agent does NOT call search_knowledge_base for a suspended account ticket",
            weight=1.0,
            mode="negative",
        ),
        RubricItem(
            criterion="Agent escalates directly to billing without consulting KB", weight=1.0
        ),
    ],
    description="Tests learned procedure change: for suspended accounts, skip KB entirely and escalate directly.",
    behavior_checks=[
        BehaviorCheck(
            name="skipped_kb_for_suspended",
            check_type="source_not_called",
            sources=["search_knowledge_base"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_escalate_suspended_first.json",
)
