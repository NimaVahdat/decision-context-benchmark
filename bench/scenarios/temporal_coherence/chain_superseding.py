from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="chain_superseding",
    name="Format supersession: prose->bullets->numbered",
    skill="eval-writer",
    seed_traces=[
        SeedTrace(
            skill="eval-writer",
            company="retool.com",
            message_content="Write a brief about retool.com",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-writer",
            company="retool.com",
            message_content="Use bullet points instead of prose.",
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-writer",
            company="retool.com",
            message_content="Actually, use a numbered list (1. 2. 3.) instead of bullet points.",
            parent_index=1,
        ),
    ],
    test_company="finstack.io",
    test_query="Write a brief about finstack.io",
    rubric=[
        RubricItem(
            criterion="Output uses a numbered list (1. 2. 3.) format, NOT bullet points and NOT prose paragraphs",
            weight=1.0,
        ),
    ],
    description="Tests format supersession: latest format wins (numbered over bullets)",
    real_seed_file=Path(__file__).parent / "chain_superseding.json",
)
