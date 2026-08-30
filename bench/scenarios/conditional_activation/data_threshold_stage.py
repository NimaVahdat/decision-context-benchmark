from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="data_threshold_stage",
    name="Multi-dimensional stage classification",
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
                "In the verdict, classify companies using these exact labels:\n"
                "- 'SCALED GROWTH' if ARR > $20M AND gross margins > 75%\n"
                "- 'GROWTH (MARGIN WATCH)' if ARR > $20M AND gross margins <= 75%\n"
                "- 'EARLY BREAKOUT' if ARR <= $20M AND growth > 100%\n"
                "- 'EARLY STAGE' otherwise\n"
                "Always use these exact labels in uppercase."
            ),
            parent_index=0,
        ),
    ],
    test_company="linear.app",  # $28M ARR, 85% margins -> SCALED GROWTH
    test_query="Score linear.app on investment criteria",
    rubric=[
        RubricItem(
            criterion=(
                "The verdict labels linear.app as 'SCALED GROWTH' (not 'EARLY STAGE' or 'GROWTH STAGE' "
                "or 'EARLY BREAKOUT'). Linear has $28M ARR and 85% gross margins."
            ),
            weight=1.0,
        ),
    ],
    description="Tests multi-dimensional classification: ARR + margins = 'SCALED GROWTH'",
    real_seed_file=Path(__file__).parent / "data_threshold_stage.json",
)
