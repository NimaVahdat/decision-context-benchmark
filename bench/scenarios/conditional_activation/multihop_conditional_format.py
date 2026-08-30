from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="multihop_conditional_format",
    name="2-hop conditional format (growth -> table -> peer column)",
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
                "For companies with more than 100% YoY revenue growth, present the financial overview "
                "as a markdown table instead of prose paragraphs."
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
                "When presenting financials as a table, always include a 'Peer Benchmark' column that "
                "compares each metric to the category median."
            ),
            parent_index=2,
        ),
    ],
    test_company="resend.com",  # 210% growth -> table -> peer column
    test_query="Analyze resend.com",
    rubric=[
        RubricItem(
            criterion="Financial overview is presented as a markdown table (resend.com has 210% YoY growth).",
            weight=1.0,
        ),
        RubricItem(
            criterion="The financial table includes a 'Peer Benchmark' column comparing metrics to category medians.",
            weight=1.0,
        ),
    ],
    description="Tests 2-hop conditional format: high growth -> table format -> peer benchmark column.",
    real_seed_file=Path(__file__).parent / "multihop_conditional_format.json",
)
