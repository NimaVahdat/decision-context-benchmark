from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace
from bench.scenarios.persistence._helpers import _SPACER_COS, spacer

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
        message_content="Express revenue as QRR (quarterly recurring revenue), not ARR. Divide ARR by 4.",
        parent_index=0,
    ),
    SeedTrace(
        skill="eval-analyst",
        company="delve.co",
        message_content="Include the 'Rule of 40' score in Financial Overview. Calculate as growth rate (%) + gross margin (%).",
        parent_index=1,
    ),
    SeedTrace(
        skill="eval-analyst",
        company="delve.co",
        message_content="In the assessment, cap any numerical scores at 7 maximum.",
        parent_index=2,
    ),
    *[spacer(_SPACER_COS[i % len(_SPACER_COS)]) for i in range(16)],
]

SCENARIO = Scenario(
    id="long_20msg_early",
    name="20-msg conversation, early corrections",
    skill="eval-analyst",
    seed_traces=_traces,
    test_company="finstack.io",
    test_query="Analyze finstack.io",
    rubric=[
        RubricItem(
            criterion="Financial overview uses QRR (quarterly recurring revenue) as the PRIMARY revenue metric with a dollar amount.",
            weight=1.0,
        ),
        RubricItem(
            criterion="Financial overview includes a computed 'Rule of 40' score (the exact phrase 'Rule of 40' with a number)",
            weight=1.0,
        ),
    ],
    description="Tests whether early corrections survive 16 subsequent follow-up messages",
    real_seed_file=Path(__file__).parent / "long_20msg_early.json",
)
