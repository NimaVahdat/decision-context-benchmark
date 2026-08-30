from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_enterprise_skip_kb",
    name="Skip KB search for enterprise accounts — escalate directly",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="orion-gamma.io",
            message_content="Handle support ticket for orion-gamma.io: Orion API not responding",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="orion-gamma.io",
            message_content="For enterprise-tier accounts, skip KB — they have a dedicated CSM. Always escalate directly.",
            parent_index=0,
        ),
    ],
    test_company="repeat-gamma.io",
    test_query="Handle support ticket for repeat-gamma.io: export failure for repeat-gamma.io",
    rubric=[
        RubricItem(criterion="Agent checks account tier before deciding on workflow", weight=0.5),
        RubricItem(
            criterion="Agent skips search_knowledge_base because the account is enterprise tier",
            weight=1.0,
        ),
        RubricItem(
            criterion="Agent escalates directly to dedicated support, not standard KB-first workflow",
            weight=1.0,
        ),
    ],
    description="Tests conditional activation: 'skip KB for enterprise tier' rule. Agent must look up tier, then apply the rule only when tier=enterprise.",
    behavior_checks=[
        BehaviorCheck(
            name="skipped_kb_for_enterprise",
            check_type="source_not_called",
            sources=["search_knowledge_base"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_enterprise_skip_kb.json",
)
