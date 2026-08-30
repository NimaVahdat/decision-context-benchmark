from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import Scenario

SCENARIO = Scenario(
    id="self_assess_recurring_failure",
    name="Learn to skip failing sources and use profile",
    skill="eval-analyst-adaptive",
    seed_traces=[],
    test_company="unknown-epsilon.io",
    test_query="Analyze unknown-epsilon.io",
    rubric=[],
    description=(
        "Tests learning from 4 REAL traces where 4/5 tool calls fail and only profile returns data. "
        "Agent should skip failing sources."
    ),
    behavior_checks=[
        BehaviorCheck(
            name="skipped_failing_sources",
            check_type="source_not_called",
            sources=["financials", "market", "team", "brief"],
            weight=2.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "self_assess_recurring_failure.json",
)
