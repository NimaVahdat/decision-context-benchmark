from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import Scenario

SCENARIO = Scenario(
    id="self_assess_retry",
    name="Stop retrying async source that never resolves",
    skill="eval-analyst-async",
    seed_traces=[],
    test_company="unknown-delta.io",
    test_query="Analyze unknown-delta.io",
    rubric=[],
    description=(
        "Tests retry elimination. 3 REAL traces show premium retried 3x (always 'processing'), "
        "then basic worked. Agent should skip retries."
    ),
    behavior_checks=[
        BehaviorCheck(
            name="limited_total_calls", check_type="tool_call_max", threshold=2, weight=2.0
        ),
    ],
    real_seed_file=Path(__file__).parent / "self_assess_retry.json",
)
