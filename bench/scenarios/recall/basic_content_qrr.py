from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="basic_content_qrr",
    name="Express revenue as QRR not ARR",
    skill="eval-analyst",
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
                "Always express revenue in quarterly terms as QRR (quarterly recurring revenue), "
                "not annual (ARR). Convert by dividing ARR by 4."
            ),
            parent_index=0,
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion=(
                "Financial overview expresses revenue in quarterly terms as QRR (quarterly recurring "
                "revenue) rather than annual (ARR). E.g. '$7M QRR' instead of '$28M ARR'"
            ),
            weight=1.0,
        ),
    ],
    description="Tests basic content correction: QRR vs ARR",
    real_seed_file=Path(__file__).parent / "basic_content_qrr.json",
)
