from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="isolation_negative_transfer",
    name="Analyst correction must NOT leak to writer",
    skill="eval-writer",
    seed_traces=[
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content="Analyze delve.co",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content=(
                "Always express funding as a multiple of ARR (e.g. 'raised 2.9x ARR'). "
                "Calculate by dividing total raised by current ARR. Include the absolute amount in parentheses."
            ),
            parent_index=0,
        ),
    ],
    test_company="finstack.io",
    test_query="Write a brief about finstack.io",
    rubric=[
        RubricItem(
            criterion=(
                "The brief uses standard funding amounts (absolute numbers like '$15M raised') without "
                "expressing them as ARR multiples. The analyst correction must NOT have leaked to the writer skill."
            ),
            weight=1.0,
        ),
    ],
    description="Tests skill isolation: analyst's 'funding as ARR multiple' correction must NOT transfer to writer skill",
    real_seed_file=Path(__file__).parent / "isolation_negative_transfer.json",
)
