from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

_corrections = [
    ("delve.co", "Use MRR instead of ARR."),
    (
        "resend.com",
        "Include 'Capital Efficiency' in Financial Overview. Calculate as ARR divided by total funding raised.",
    ),
    (
        "retool.com",
        "Include 'revenue per headcount' in Financial Overview. Calculate as ARR divided by team size.",
    ),
    (
        "notion.so",
        "Include 'Rule of 40' score in Financial Overview. Calculate as growth rate (%) + gross margin (%).",
    ),
    ("meridian.bio", "Label growth as HYPERGROWTH/FAST/STEADY."),
]

_traces = []
for co, correction in _corrections:
    _traces.append(
        SeedTrace(
            skill="eval-analyst", company=co, message_content=f"Analyze {co}", parent_index=None
        )
    )
    _traces.append(
        SeedTrace(
            skill="eval-analyst",
            company=co,
            message_content=correction,
            parent_index=len(_traces) - 1,
        )
    )

SCENARIO = Scenario(
    id="session_5conv",
    name="5 conversations, 5 corrections",
    skill="eval-analyst",
    seed_traces=_traces,
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion="Financial overview uses MRR as the PRIMARY revenue metric and does NOT lead with ARR.",
            weight=1.0,
        ),
        RubricItem(
            criterion="Financial overview has a line starting with 'Capital Efficiency' as a labeled metric.",
            weight=1.0,
        ),
        RubricItem(
            criterion="Financial overview includes a computed 'Rule of 40' score with a number.",
            weight=1.0,
        ),
    ],
    description="Tests aggregation of corrections across 5 separate conversations",
    real_seed_file=Path(__file__).parent / "session_5conv.json",
)
