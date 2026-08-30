from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_repeat_escalate",
    name="Escalate immediately for repeat issue customers",
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
            company="repeat-beta.io",
            message_content="Handle support ticket for repeat-beta.io: sync failure (reported again after prior fix)",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-gamma.io",
            message_content="Handle support ticket for repeat-gamma.io: login issue (same customer, 4th ticket)",
            parent_index=None,
        ),
    ],
    test_company="repeat-delta.io",
    test_query="Handle support ticket for repeat-delta.io: export failure (customer's 3rd report this week)",
    rubric=[
        RubricItem(
            criterion="Agent does NOT call search_knowledge_base for this repeat-issue ticket",
            weight=1.0,
            mode="negative",
        ),
        RubricItem(
            criterion="Agent escalates to tier-2 directly without attempting KB lookup", weight=1.0
        ),
    ],
    description=(
        "Tests learning that KB lookup wastes time for repeat-issue customers. "
        "Past traces show search_knowledge_base articles never resolve repeat-*.io tickets — "
        "direct escalation is always the actual resolution path."
    ),
    behavior_checks=[
        BehaviorCheck(
            name="skipped_kb_for_repeat",
            check_type="source_not_called",
            sources=["search_knowledge_base"],
            weight=2.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_repeat_escalate.json",
)
