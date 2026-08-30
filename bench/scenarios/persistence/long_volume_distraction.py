from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace
from bench.scenarios.persistence._helpers import _SPACER_COS, spacer

_noise = [
    ("retool.com", "For Retool specifically, mention their SQL-native approach in every section."),
    ("notion.so", "When analyzing Notion, always compare to Confluence explicitly."),
    ("shopfront.co", "For Shopfront, lead with GMV before ARR."),
    ("greenpower.energy", "GreenPower reports should focus on climate impact metrics."),
]

_traces = [
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
            "Always include 'Capital Efficiency' in the Financial Overview section. "
            "Calculate as ARR divided by total funding raised. E.g. $4.2M ARR / $12M raised = 0.35x."
        ),
        parent_index=0,
    ),
]
for company, msg in _noise:
    _traces.append(
        SeedTrace(
            skill="eval-analyst",
            company=company,
            message_content=f"Analyze {company}",
            parent_index=None,
        )
    )
    _traces.append(
        SeedTrace(
            skill="eval-analyst",
            company=company,
            message_content=msg,
            parent_index=len(_traces) - 1,
        )
    )
_traces.extend(spacer(_SPACER_COS[i % len(_SPACER_COS)]) for i in range(10))

SCENARIO = Scenario(
    id="long_volume_distraction",
    name="1 real correction + 4 noise + 10 spacers",
    skill="eval-analyst",
    seed_traces=_traces,
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion=(
                "Financial overview has a line or bullet starting with 'Capital Efficiency' or "
                "'Capital Efficiency:' as a labeled metric. General mentions in prose do NOT count."
            ),
            weight=1.0,
        ),
    ],
    description="Tests signal extraction: 1 real correction among noise",
    real_seed_file=Path(__file__).parent / "long_volume_distraction.json",
)
