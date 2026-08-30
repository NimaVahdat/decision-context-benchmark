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
    spacer(_SPACER_COS[0]),
    spacer(_SPACER_COS[1]),
    SeedTrace(
        skill="eval-analyst",
        company="delve.co",
        message_content="Express revenue as MRR, not ARR.",
        parent_index=0,
    ),
    spacer(_SPACER_COS[2]),
    spacer(_SPACER_COS[3]),
    SeedTrace(
        skill="eval-analyst",
        company="delve.co",
        message_content=(
            "Always include the 'Rule of 40' score in the Financial Overview section. "
            "Calculate as: growth rate (%) + gross margin (%). E.g. 180% + 72% = 252."
        ),
        parent_index=3,
    ),
    spacer(_SPACER_COS[4]),
    spacer(_SPACER_COS[5]),
    SeedTrace(
        skill="eval-analyst",
        company="delve.co",
        message_content=(
            "Express growth as monthly compound rate (CMGR) instead of YoY percentage. "
            "Calculate CMGR from annual growth: CMGR ≈ (1 + annual_rate)^(1/12) - 1."
        ),
        parent_index=6,
    ),
]

SCENARIO = Scenario(
    id="long_10msg_scattered",
    name="10-msg conversation, corrections at 3/6/9",
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
            criterion="Financial overview includes a computed 'Rule of 40' score (the exact phrase 'Rule of 40' with a number)",
            weight=1.0,
        ),
        RubricItem(
            criterion="Financial overview includes CMGR (monthly compound growth rate)", weight=1.0
        ),
    ],
    description="Tests recall of 3 corrections scattered across a 10-message conversation",
    real_seed_file=Path(__file__).parent / "long_10msg_scattered.json",
)
