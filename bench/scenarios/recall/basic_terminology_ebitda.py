from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="basic_terminology_ebitda",
    name="Use EBITDA-adjusted burn rate",
    skill="eval-analyst",
    seed_traces=[
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content="Analyze resend.com",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content=(
                "Report burn rate as 'EBITDA-adjusted burn rate' instead of raw burn rate. "
                "This excludes one-time costs like hiring bonuses and office buildouts. "
                "Always label it explicitly as 'EBITDA-adjusted'."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content=(
                "Don't just acknowledge it. Redo the full analysis with the EBITDA-adjusted burn rate. "
                "Estimate by excluding 15% from gross burn for one-time costs."
            ),
            parent_index=1,
        ),
    ],
    test_company="meridian.bio",
    test_query="Analyze meridian.bio",
    rubric=[
        RubricItem(
            criterion=(
                "Financial overview mentions 'EBITDA-adjusted burn rate' (or 'EBITDA-adjusted burn') "
                "instead of just 'burn rate'"
            ),
            weight=1.0,
        ),
        RubricItem(
            criterion="The term 'EBITDA-adjusted' appears explicitly in the financial section",
            weight=0.5,
        ),
    ],
    description="Tests domain terminology adoption: EBITDA-adjusted burn",
    real_seed_file=Path(__file__).parent / "basic_terminology_ebitda.json",
)
