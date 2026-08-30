from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="forget_partial_rollback",
    name="Partial rollback (keep 2 of 3 changes, remove 1)",
    skill="eval-writer",
    seed_traces=[
        SeedTrace(
            skill="eval-writer",
            company="delve.co",
            message_content="Write a brief about delve.co",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-writer",
            company="delve.co",
            message_content=(
                "Three changes: (1) use bullet points instead of prose, "
                "(2) start with what the product does instead of the company name, "
                "(3) end with 'Founded in [year].' as the last line."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-writer",
            company="delve.co",
            message_content=(
                "Actually, go back to prose instead of bullet points. But keep starting with what "
                "the product does and keep the 'Founded in [year].' ending."
            ),
            parent_index=1,
        ),
    ],
    test_company="linear.app",
    test_query="Write a brief about linear.app",
    rubric=[
        RubricItem(
            criterion=(
                "Output starts with what the product does, NOT the company name. "
                "E.g., starts with 'Issue tracking platform...' not 'Linear is...'"
            ),
            weight=1.0,
        ),
        RubricItem(
            criterion="Output ends with 'Founded in [year].' as the last sentence or line.",
            weight=1.0,
        ),
    ],
    description="Tests partial rollback: adds bullets+product-first+founded, then removes only bullets.",
    real_seed_file=Path(__file__).parent / "forget_partial_rollback.json",
)
