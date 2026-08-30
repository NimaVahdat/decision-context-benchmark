from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="basic_cap_scores",
    name="Cap all scores at 7 maximum",
    skill="eval-scorer",
    seed_traces=[
        SeedTrace(
            skill="eval-scorer",
            company="delve.co",
            message_content="Score delve.co on investment criteria",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-scorer",
            company="delve.co",
            message_content=(
                "Never give a score above 7. We use a conservative scoring policy — no company should "
                "get 8, 9, or 10 on any criterion."
            ),
            parent_index=0,
        ),
    ],
    test_company="linear.app",
    test_query="Score linear.app on investment criteria",
    rubric=[
        RubricItem(
            criterion="ALL numerical scores are 7 or below. No score of 8, 9, or 10 appears anywhere in the output",
            weight=1.0,
        ),
    ],
    description="Tests hard constraint enforcement: cap all scores at 7 maximum",
    real_seed_file=Path(__file__).parent / "basic_cap_scores.json",
)
