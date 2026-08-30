from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="temporal_evolving_preference",
    name="Evolving preference (3-point -> 5-point -> colored)",
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
            message_content="Add a risk rating to the assessment: LOW, MEDIUM, or HIGH.",
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content="Actually, use a 5-point scale instead: VERY LOW, LOW, MEDIUM, HIGH, CRITICAL.",
            parent_index=1,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content=(
                "Also label each risk level with a color: VERY LOW=green, LOW=blue, MEDIUM=yellow, "
                "HIGH=orange, CRITICAL=red. Write it as '[color] LEVEL' format."
            ),
            parent_index=2,
        ),
    ],
    test_company="retool.com",
    test_query="Analyze retool.com",
    rubric=[
        RubricItem(
            criterion=(
                "Assessment includes a risk rating using the 5-point scale (one of: VERY LOW, LOW, "
                "MEDIUM, HIGH, CRITICAL). Must NOT use only the 3-point scale."
            ),
            weight=1.0,
        ),
        RubricItem(
            criterion="Risk rating includes a color label, formatted as '[color] LEVEL' (e.g., '[green] VERY LOW').",
            weight=1.0,
        ),
    ],
    description="Tests evolving preferences: 3-point -> 5-point -> 5-point with colors. T2 supersedes T1, T3 accumulates.",
    real_seed_file=Path(__file__).parent / "temporal_evolving_preference.json",
)
