from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import Scenario, SeedTrace

SCENARIO = Scenario(
    id="procedural_conditional_skip",
    name="Conditional tool skip (skip market if ARR < $5M)",
    skill="eval-analyst",
    seed_traces=[
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
                "If a company has less than $5M ARR, skip the market analysis entirely. "
                "It is too early stage for meaningful market positioning. Focus only on financials and team instead."
            ),
            parent_index=0,
        ),
    ],
    test_company="learnnext.ai",  # $1.8M ARR -> skip market
    test_query="Analyze learnnext.ai",
    rubric=[],
    description="Tests conditional procedural memory: skip market tool call when financials show ARR < $5M.",
    behavior_checks=[
        BehaviorCheck(
            name="skipped_market", check_type="source_not_called", sources=["market"], weight=1.0
        ),
    ],
    real_seed_file=Path(__file__).parent / "procedural_conditional_skip.json",
)
