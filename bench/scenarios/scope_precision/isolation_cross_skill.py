from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="isolation_cross_skill",
    name="Analyst correction must NOT leak to scorer",
    skill="eval-scorer",
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
                "In the Financial Overview section, always use MRR instead of ARR. Convert by dividing ARR by 12."
            ),
            parent_index=0,
        ),
    ],
    test_company="linear.app",
    test_query="Score linear.app on investment criteria",
    rubric=[
        RubricItem(
            criterion="Output uses 'MRR' terminology (this would indicate the analyst correction leaked to the scorer)",
            weight=1.0,
            mode="negative",
        ),
    ],
    description="Tests skill isolation: analyst MRR correction must NOT leak to scorer",
    real_seed_file=Path(__file__).parent / "isolation_cross_skill.json",
)
