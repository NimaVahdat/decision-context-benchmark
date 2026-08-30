from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="procedural_comparable_format",
    name="Learn to include Key Comparables paragraph in Market Position",
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
                "Always include a 'Key Comparables:' paragraph in Market Position listing 3 named competitors with one-sentence comparisons."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="linear.app",
            message_content="Analyze linear.app",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="linear.app",
            message_content=(
                "Don't forget the Key Comparables format in Market Position — 3 named peers, one line each."
            ),
            parent_index=2,
        ),
    ],
    test_company="retool.com",
    test_query="Analyze retool.com",
    rubric=[
        RubricItem(
            criterion="Market Position section includes a 'Key Comparables' paragraph with named competitors",
            weight=1.0,
        ),
    ],
    behavior_checks=[
        BehaviorCheck(
            name="key_comparables_present",
            check_type="keyword_present",
            keywords=["key comparables"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "procedural_comparable_format.json",
)
