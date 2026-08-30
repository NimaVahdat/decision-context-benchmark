from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_rule_isolation",
    name="Routing rule for customer A does not apply to customer B",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="Handle support ticket for repeat-alpha.io: billing dispute",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="For repeat-alpha.io specifically: always escalate billing tickets — they have a dedicated billing contact",
            parent_index=0,
        ),
    ],
    test_company="repeat-beta.io",
    test_query="Handle support ticket for repeat-beta.io: billing dispute for repeat-beta.io",
    rubric=[
        RubricItem(
            criterion="Agent does NOT automatically escalate for repeat-beta.io — uses standard workflow (KB search first)",
            weight=1.0,
        ),
        RubricItem(
            criterion="Agent correctly scopes the escalation rule to repeat-alpha.io only, not all customers",
            weight=1.0,
        ),
    ],
    description="Tests scope isolation: a company-specific routing rule for repeat-alpha.io must not bleed over to repeat-beta.io.",
    real_seed_file=Path(__file__).parent / "support_rule_isolation.json",
)
