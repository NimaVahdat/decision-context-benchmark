from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="support_account_format",
    name="Recall: include account tier in every support response",
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
            company="orion-acme.io",
            message_content="Always include the customer's account tier in your response — our routing team needs it",
            parent_index=0,
        ),
    ],
    test_company="orion-beta.io",
    test_query="Handle support ticket for orion-beta.io: Orion onboarding issue",
    rubric=[
        RubricItem(
            criterion="Output includes the customer's account tier (e.g. 'startup', 'growth', 'enterprise')",
            weight=1.0,
        ),
        RubricItem(criterion="Account tier is stated clearly, not buried or omitted", weight=0.5),
    ],
    description="Tests recall of a global formatting correction: always include account tier in responses.",
    real_seed_file=Path(__file__).parent / "support_account_format.json",
)
