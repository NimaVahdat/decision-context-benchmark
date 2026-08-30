from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="chain_conflicting",
    name="Conflicting corrections (MRR -> QRR)",
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
            message_content="Express revenue in monthly terms (MRR), not annual (ARR).",
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="notion.so",
            message_content="Analyze notion.so",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content="Actually, use quarterly recurring revenue (QRR) instead. Divide ARR by 4 to get QRR.",
            parent_index=1,
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion=(
                "Financial overview expresses revenue in quarterly terms (QRR), not annual (ARR) or "
                "monthly (MRR). E.g. '$7M QRR' instead of '$28M ARR'."
            ),
            weight=1.0,
        ),
    ],
    description="Tests conflicting correction resolution: MRR -> QRR supersession",
    real_seed_file=Path(__file__).parent / "chain_conflicting.json",
)
