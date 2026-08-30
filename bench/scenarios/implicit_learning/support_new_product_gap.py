from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_new_product_gap",
    name="Skip KB search for new product with no docs",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="orion-acme.io",
            message_content="Handle support ticket for orion-acme.io: question about Orion product feature",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="orion-beta.io",
            message_content="Handle support ticket for orion-beta.io: Orion onboarding issue",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="orion-gamma.io",
            message_content="Handle support ticket for orion-gamma.io: Orion billing confusion",
            parent_index=None,
        ),
    ],
    test_company="orion-delta.io",
    test_query="Handle support ticket for orion-delta.io: Orion integration not working",
    rubric=[
        RubricItem(
            criterion="Agent does NOT call search_knowledge_base for this Orion ticket",
            weight=1.0,
            mode="negative",
        ),
        RubricItem(
            criterion="Agent escalates directly without wasting a KB search call", weight=1.0
        ),
    ],
    description=(
        "Tests learning that KB has no docs for newly launched Orion product. "
        "Past traces show search_knowledge_base always returns empty for orion-*.io queries."
    ),
    behavior_checks=[
        BehaviorCheck(
            name="skipped_empty_kb",
            check_type="source_not_called",
            sources=["search_knowledge_base"],
            weight=2.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_new_product_gap.json",
)
