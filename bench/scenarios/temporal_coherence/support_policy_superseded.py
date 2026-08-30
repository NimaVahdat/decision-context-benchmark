from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_policy_superseded",
    name="Apply superseded escalation policy, not old one",
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
            message_content="For billing tickets: always search KB first, then escalate if not resolved",
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
            message_content="Updated policy: for billing tickets, skip KB — escalate directly to billing team. The KB articles are outdated.",
            parent_index=2,
        ),
    ],
    test_company="repeat-gamma.io",
    test_query="Handle support ticket for repeat-gamma.io: billing discrepancy for repeat-gamma.io",
    rubric=[
        RubricItem(
            criterion="Agent escalates directly to billing team without calling search_knowledge_base",
            weight=1.0,
        ),
        RubricItem(
            criterion="Agent follows the NEWER policy (skip KB, direct escalation) not the older one (KB first)",
            weight=1.0,
        ),
    ],
    description="Tests that the newer policy (skip KB for billing) supersedes the older one (KB first). Agent must apply the most recent instruction.",
    behavior_checks=[
        BehaviorCheck(
            name="skipped_kb_per_newer_policy",
            check_type="source_not_called",
            sources=["search_knowledge_base"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_policy_superseded.json",
)
