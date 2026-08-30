from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="chain_accumulating_5",
    name="5 accumulated corrections",
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
            message_content="Lead with what the product does, not the company name.",
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-writer",
            company="delve.co",
            message_content="Include the headcount.",
            parent_index=1,
        ),
        SeedTrace(
            skill="eval-writer",
            company="delve.co",
            message_content="End with 'Founded in [year].' as the last sentence.",
            parent_index=2,
        ),
        SeedTrace(
            skill="eval-writer",
            company="delve.co",
            message_content="Keep to exactly 2 sentences.",
            parent_index=3,
        ),
        SeedTrace(
            skill="eval-writer",
            company="delve.co",
            message_content="Use bullet points instead.",
            parent_index=4,
        ),
    ],
    test_company="linear.app",
    test_query="Write a brief about linear.app",
    rubric=[
        RubricItem(criterion="Output uses bullet points (not prose paragraphs)", weight=1.0),
        RubricItem(
            criterion=(
                "Output leads with the product description, not the company name "
                "(e.g. starts with 'Issue tracking platform...' not 'Linear is...')"
            ),
            weight=1.0,
        ),
        RubricItem(
            criterion=(
                "Output ends with a standalone line 'Founded in [year].' as the final sentence or "
                "bullet — not buried in a paragraph, but as a distinct closing line"
            ),
            weight=1.0,
        ),
    ],
    description="Tests accumulation of 5 successive corrections",
    real_seed_file=Path(__file__).parent / "chain_accumulating_5.json",
)
