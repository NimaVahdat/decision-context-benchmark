from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="procedural_runway_flag",
    name="Learn to open Assessment with runway flag for short-runway companies",
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
                "When runway < 20 months: open the Assessment section with 'RUNWAY FLAG: X months remaining' as the very first line."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content="Analyze resend.com",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content=(
                "resend.com has 21 months — borderline. Always flag short runway at the start of Assessment."
            ),
            parent_index=2,
        ),
    ],
    test_company="greenpower.energy",
    test_query="Analyze greenpower.energy",
    rubric=[
        RubricItem(criterion="Assessment section opens with 'RUNWAY FLAG:' label", weight=1.0),
        RubricItem(
            criterion="Agent applies learned short-runway procedure to greenpower.energy",
            weight=1.0,
        ),
    ],
    behavior_checks=[
        BehaviorCheck(
            name="runway_flag_present",
            check_type="keyword_present",
            keywords=["runway flag"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "procedural_runway_flag.json",
)
