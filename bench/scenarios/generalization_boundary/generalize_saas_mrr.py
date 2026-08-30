from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="generalize_saas_mrr",
    name="MRR-first rule generalizes to new SaaS company",
    skill="eval-analyst",
    seed_traces=[
        SeedTrace(
            skill="eval-analyst",
            company="notion.so",
            message_content="Analyze notion.so",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="notion.so",
            message_content=(
                "For SaaS companies: always lead Financial Overview with 'Monthly Run Rate (MRR):' before ARR. MRR = ARR/12."
            ),
            parent_index=0,
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(criterion="Financial overview leads with MRR before ARR", weight=1.0),
        RubricItem(
            criterion="Contains 'Monthly Run Rate' or 'MRR:' as an explicit label", weight=1.0
        ),
    ],
    behavior_checks=[
        BehaviorCheck(
            name="mrr_present",
            check_type="keyword_present",
            keywords=["monthly run rate", "mrr:"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "generalize_saas_mrr.json",
)
