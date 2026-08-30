from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="forget_explicit_deletion",
    name="Selective deletion (keep QRR + table, remove disclaimer)",
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
                "Three changes: (1) Express revenue as QRR (quarterly recurring revenue) instead of ARR. "
                "Divide ARR by 4. (2) Present the financial overview as a markdown table. "
                "(3) Start every analysis with the line 'PRELIMINARY ASSESSMENT — SUBJECT TO REVISION' in bold."
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
            company="delve.co",
            message_content=(
                "Remove the preliminary assessment disclaimer. Our reports are final, not preliminary. "
                "But keep using QRR for revenue and the table format."
            ),
            parent_index=1,
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion="Revenue is expressed as QRR (quarterly recurring revenue), e.g. '$7M QRR' not '$28M ARR'.",
            weight=1.0,
        ),
        RubricItem(
            criterion="Financial overview is presented as a markdown table, not prose paragraphs.",
            weight=1.0,
        ),
    ],
    description="Tests selective deletion: adds QRR + table + disclaimer, then removes only disclaimer.",
    real_seed_file=Path(__file__).parent / "forget_explicit_deletion.json",
)
