from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="basic_two_sentences",
    name="Brief must be exactly two sentences",
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
                "Keep the brief to exactly two sentences. First sentence: what they do. "
                "Second sentence: traction and funding combined."
            ),
            parent_index=0,
        ),
    ],
    test_company="linear.app",
    test_query="Write a brief about linear.app",
    rubric=[
        RubricItem(
            criterion="The brief contains exactly two sentences (not one, not three or more)",
            weight=1.0,
        ),
    ],
    description="Tests precise structural constraint: exactly 2 sentences",
    real_seed_file=Path(__file__).parent / "basic_two_sentences.json",
)
