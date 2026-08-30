from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="fidelity_phrasing",
    name="Exact phrasing reproduction",
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
                "In the assessment, use this exact phrase: "
                "'demonstrates strong unit economics with a clear path to profitability'"
            ),
            parent_index=0,
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion=(
                "Assessment contains the exact phrase 'demonstrates strong unit economics with a clear "
                "path to profitability' or very close variant"
            ),
            weight=1.0,
        ),
    ],
    description="Tests whether exact phrasing from a correction is reproduced verbatim",
    real_seed_file=Path(__file__).parent / "fidelity_phrasing.json",
)
