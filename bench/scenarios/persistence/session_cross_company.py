from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

_companies = ["delve.co", "resend.com", "meridian.bio"]

_traces = []
for co in _companies:
    _traces.append(
        SeedTrace(
            skill="eval-analyst", company=co, message_content=f"Analyze {co}", parent_index=None
        )
    )
    _traces.append(
        SeedTrace(
            skill="eval-analyst",
            company=co,
            message_content=(
                "Include 'implied ARR multiple' in the Financial Overview section. "
                "Calculate as last known valuation divided by current ARR."
            ),
            parent_index=len(_traces) - 1,
        )
    )

SCENARIO = Scenario(
    id="session_cross_company",
    name="Same correction across 3 companies",
    skill="eval-analyst",
    seed_traces=_traces,
    test_company="finstack.io",
    test_query="Analyze finstack.io",
    rubric=[
        RubricItem(
            criterion=(
                "Financial overview includes a metric explicitly labeled 'implied ARR multiple' "
                "(those exact words) with the computed value"
            ),
            weight=1.0,
        ),
    ],
    description="Tests whether a correction seeded across 3 companies transfers to an unseen 4th",
    real_seed_file=Path(__file__).parent / "session_cross_company.json",
)
