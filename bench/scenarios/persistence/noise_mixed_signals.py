from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="noise_mixed_signals",
    name="Mixed signals: corrections from multiple conversations",
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
                "End every analysis with a standalone line: 'CONFIDENCE: [HIGH/MEDIUM/LOW]' rating your overall confidence."
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
                "Always include a 'Capital Efficiency' metric calculated as ARR divided by total funding raised. Express as '0.45x'."
            ),
            parent_index=2,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="notion.so",
            message_content="Analyze notion.so",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="notion.so",
            message_content="Present the financial overview section as a markdown table instead of prose.",
            parent_index=4,
        ),
    ],
    test_company="resend.com",
    test_query="Analyze resend.com",
    rubric=[
        RubricItem(
            criterion="Output ends with a standalone 'CONFIDENCE:' line rating HIGH, MEDIUM, or LOW.",
            weight=1.0,
        ),
        RubricItem(
            criterion="Output includes a 'Capital Efficiency' metric expressed as a ratio.",
            weight=1.0,
        ),
        RubricItem(
            criterion="Financial overview is presented as a markdown table, not prose paragraphs.",
            weight=1.0,
        ),
    ],
    description="Tests that corrections from 3 separate conversations all transfer to a 4th unseen company.",
    real_seed_file=Path(__file__).parent / "noise_mixed_signals.json",
)
