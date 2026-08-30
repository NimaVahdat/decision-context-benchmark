from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

_corrections = [
    "Always bold the company name in headers.",
    "Include the currency (USD) next to all monetary amounts.",
    "Add a 'Data Sources' footer section.",
    "Use metric tons for weight measurements.",
    "Always mention ESG scores.",
    "Include patent count in team section.",
    "Add a risk matrix table.",
    "Use British spelling throughout.",
    "Include LinkedIn profile links.",
    "Add a SWOT analysis section.",
    "Use relative dates, not absolute.",
    "Include NPS score if available.",
    "Add a competitive moat assessment.",
    "Use title case for all headers.",
    "Include board member names.",
    "Add a 'Key Risks' section.",
    "Use percentages, not decimals.",
    "Include social media metrics.",
    "Add a timeline of key events.",
    "Use active voice throughout.",
    "Include customer concentration data.",
    "Add a glossary of terms.",
    "Use Harvard referencing style.",
    "Include geographic breakdown.",
    "Add a valuation estimate.",
    "Use sans-serif formatting.",
    "Include churn rate data.",
    "Add a product roadmap section.",
    "Use ISO date format.",
    "Include regulatory compliance.",
    "Add a market trend analysis.",
    "Use numbered lists for findings.",
    "Include debt-to-equity ratio.",
    "Add an executive summary.",
    "Use color coding for risk levels.",
    "Include cap table information.",
    "Add a peer comparison table.",
    "Use footnotes for data sources.",
    "Include customer testimonials.",
    "Add a technology stack section.",
    "Use quarterly breakdowns.",
    "Include advisor names.",
    "Add a culture assessment.",
    "Use median instead of mean.",
    "Include IP portfolio details.",
    "Add a succession plan section.",
    "Use confidence intervals.",
    "Include diversity metrics.",
    "Add a sustainability report.",
    "Include net promoter score trends.",
]

_traces = [
    SeedTrace(
        skill="eval-analyst",
        company="delve.co",
        message_content="Analyze delve.co",
        parent_index=None,
    )
]
_traces += [
    SeedTrace(skill="eval-analyst", company="delve.co", message_content=c, parent_index=0)
    for c in _corrections
]

SCENARIO = Scenario(
    id="scale_50_corrections",
    name="Precision at scale (50 corrections)",
    skill="eval-analyst",
    seed_traces=_traces,
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion="Output includes currency labels (USD) next to monetary amounts", weight=1.0
        ),
        RubricItem(
            criterion="Output has a 'Data Sources' footer or section at the end", weight=1.0
        ),
    ],
    description="Tests retrieval precision at scale: 50 corrections seeded, only 3 relevant",
    real_seed_file=Path(__file__).parent / "scale_50_corrections.json",
)
