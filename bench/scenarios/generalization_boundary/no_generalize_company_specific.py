from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="no_generalize_company_specific",
    name="Company-specific exception does not apply to other companies",
    skill="eval-analyst",
    seed_traces=[
        SeedTrace(
            skill="eval-analyst",
            company="retool.com",
            message_content="Analyze retool.com",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="retool.com",
            message_content=(
                "For retool.com specifically: omit the Market Position section — they've asked us not to publish competitive benchmarking."
            ),
            parent_index=0,
        ),
    ],
    test_company="notion.so",
    test_query="Analyze notion.so",
    rubric=[
        RubricItem(
            criterion="Analysis includes a Market Position section — company-specific omission should NOT have generalized",
            weight=1.0,
        ),
        RubricItem(
            criterion="Analysis omits Market Position section entirely", mode="negative", weight=1.0
        ),
    ],
    description="Control=1 expected (agent naturally includes Market Position). Tests that DC does NOT generalize a company-specific omission instruction.",
    behavior_checks=[
        BehaviorCheck(
            name="market_position_present",
            check_type="keyword_present",
            keywords=["## market position"],
            weight=2.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "no_generalize_company_specific.json",
)
