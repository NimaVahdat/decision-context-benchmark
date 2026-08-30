from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="query_learn_pattern",
    name="Learn which query pattern returns best results",
    skill="eval-researcher",
    seed_traces=[
        SeedTrace(
            skill="eval-researcher",
            company="delve.co",
            message_content="Research delve.co",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-researcher",
            company="linear.app",
            message_content="Research linear.app",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-researcher",
            company="delve.co",
            message_content="Research delve.co",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-researcher",
            company="meridian.bio",
            message_content="Research meridian.bio",
            parent_index=None,
        ),
    ],
    test_company="meridian.bio",
    test_query="Research meridian.bio",
    rubric=[
        RubricItem(
            criterion="Output contains 5 high-quality results about the company, indicating the agent used the optimal query strategy",
            weight=1.0,
        ),
        RubricItem(
            criterion="Output mentions or implies using a funding-focused query strategy based on learning from past searches",
            weight=0.5,
        ),
    ],
    description="Tests query strategy learning. Past traces show only 'name + funding' queries return 5 good results.",
    behavior_checks=[
        BehaviorCheck(
            name="early_quality_result", check_type="early_quality_result", threshold=1, weight=2.0
        ),
    ],
    real_seed_file=Path(__file__).parent / "query_learn_pattern.json",
)
