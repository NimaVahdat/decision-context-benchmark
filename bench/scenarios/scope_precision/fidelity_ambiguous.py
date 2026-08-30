from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="fidelity_ambiguous",
    name="Ambiguous correction must NOT generalize",
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
            message_content="Remove that last section.",
            parent_index=0,
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion=(
                "Output includes a section with the word 'Assessment' in its heading. The agent must NOT "
                "have removed this section by over-generalizing the 'remove that last section' correction."
            ),
            weight=1.0,
        ),
    ],
    description="Tests correct handling of ambiguous corrections. 'Remove that last section' is context-specific and must NOT generalize.",
    real_seed_file=Path(__file__).parent / "fidelity_ambiguous.json",
)
