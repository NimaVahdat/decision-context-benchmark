from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="evidence_multi_tool",
    name="Corrections with computed metrics per source",
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
                "After looking at the financial data, always include the 'efficiency score' in the "
                "Financial Overview section. Calculate it as: growth rate (%) divided by burn multiple. "
                "E.g. 220% growth / 2.1x burn = 104.8."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content=(
                "After looking at the market data, always include a 'competitive moat' rating in the "
                "Market Position section. Rate as DEEP (dominant position, >30% share), "
                "MODERATE (growing, 10-30% share or strong differentiation), or SHALLOW (<10% share)."
            ),
            parent_index=1,
        ),
    ],
    test_company="datavault.io",
    test_query="Analyze datavault.io",
    rubric=[
        RubricItem(
            criterion="Financial Overview includes an 'efficiency score' (growth rate divided by burn multiple)",
            weight=1.0,
        ),
        RubricItem(
            criterion=(
                "Market Position includes a labeled line like 'Competitive Moat: MODERATE' or "
                "'Moat Rating: DEEP' — an explicit rating label with the value in caps."
            ),
            weight=1.0,
        ),
    ],
    description="Tests tool-scoped corrections with computed metrics: efficiency score and moat rating",
    real_seed_file=Path(__file__).parent / "evidence_multi_tool.json",
)
