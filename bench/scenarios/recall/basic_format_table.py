from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="basic_format_table",
    name="Financial data as 3-column markdown table",
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
                "Present the Financial Overview section as a markdown table with three columns: "
                "Metric, Value, and Peer Benchmark. The Peer Benchmark column should show the "
                "typical range for companies at a similar stage. Do not use prose paragraphs for financials."
            ),
            parent_index=0,
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion=(
                "Financial Overview section uses a markdown table format (with | delimiters) that has "
                "THREE columns including a Peer Benchmark column (showing typical ranges for similar "
                "stage companies), not just Metric and Value"
            ),
            weight=1.0,
        ),
        RubricItem(
            criterion=(
                "The Peer Benchmark column contains meaningful comparison ranges, not just empty cells or N/A"
            ),
            weight=0.5,
        ),
    ],
    description="Tests basic format correction: 3-column table with peer benchmarks",
    real_seed_file=Path(__file__).parent / "basic_format_table.json",
)
