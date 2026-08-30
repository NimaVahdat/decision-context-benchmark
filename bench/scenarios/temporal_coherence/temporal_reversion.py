from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="temporal_reversion",
    name="Preference reversion (table -> bullets -> back to table)",
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
                "Present the financial overview as a markdown table with columns: Metric, Value, Peer Benchmark."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content=(
                "Actually, use bullet points instead of a table for the financial overview."
            ),
            parent_index=1,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content=(
                "Go back to the table format. The bullet points are hard to scan. "
                "Use the 3-column markdown table (Metric, Value, Peer Benchmark)."
            ),
            parent_index=2,
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion=(
                "Financial overview is presented as a markdown table with columns (Metric, Value, "
                "Peer Benchmark or similar), NOT as bullet points or prose paragraphs."
            ),
            weight=1.0,
        ),
    ],
    description="Tests preference reversion: table -> bullets -> table. System must track final state.",
    real_seed_file=Path(__file__).parent / "temporal_reversion.json",
)
