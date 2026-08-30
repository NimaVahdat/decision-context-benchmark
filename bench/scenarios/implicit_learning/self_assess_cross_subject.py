from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import Scenario

SCENARIO = Scenario(
    id="self_assess_cross_subject",
    name="Generalize failure pattern to new company",
    skill="eval-analyst-adaptive",
    seed_traces=[],
    test_company="unknown-zeta.io",
    test_query="Analyze unknown-zeta.io",
    rubric=[],
    description=(
        "Tests cross-subject generalization. 3 REAL traces show same pattern (4 failures + profile works). "
        "Should apply to new unknown company."
    ),
    behavior_checks=[
        BehaviorCheck(
            name="skipped_failing_sources",
            check_type="source_not_called",
            sources=["financials", "market", "team", "brief"],
            weight=2.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "self_assess_cross_subject.json",
)
