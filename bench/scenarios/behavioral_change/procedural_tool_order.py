from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import Scenario, SeedTrace

SCENARIO = Scenario(
    id="procedural_tool_order",
    name="Learn non-default tool order (team first, financials last)",
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
                "Always look up team data FIRST before anything else. Understanding the team shapes how you interpret the financials and market."
            ),
            parent_index=0,
        ),
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
                "Look up financials LAST, after team and market. You need the team and market context before you can properly assess the financials."
            ),
            parent_index=2,
        ),
    ],
    test_company="resend.com",
    test_query="Analyze resend.com",
    rubric=[],
    description="Tests procedural memory: agent learns NON-DEFAULT tool order (team first, financials last).",
    behavior_checks=[
        BehaviorCheck(
            name="financials_called_last",
            check_type="tool_call_not_before",
            sources=["financials"],
            threshold=3,
            weight=1.0,
        ),
    ],
    real_seed_file=Path(__file__).parent / "procedural_tool_order.json",
)
