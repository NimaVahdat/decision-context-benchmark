from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="basic_runway_risk",
    name="Include runway risk rating (GREEN/YELLOW/RED)",
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
                "In the assessment, always include a runway risk rating: GREEN if runway > 24 months, "
                "YELLOW if 12-24 months, RED if < 12 months."
            ),
            parent_index=0,
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion="Assessment includes a runway risk rating using GREEN/YELLOW/RED classification",
            weight=1.0,
        ),
    ],
    description="Tests simple threshold-based categorical labeling: GREEN/YELLOW/RED runway risk",
    real_seed_file=Path(__file__).parent / "basic_runway_risk.json",
)
