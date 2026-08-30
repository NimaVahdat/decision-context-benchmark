from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="multi_step_threat_score",
    name="Inject competitive threat score section",
    skill="eval-multi-step",
    seed_traces=[
        SeedTrace(
            skill="eval-multi-step",
            company="resend.com",
            message_content="Analyze resend.com",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-multi-step",
            company="resend.com",
            message_content=(
                "Always include a 'Competitive Threat Score' section between Team Assessment and Strategic "
                "Recommendation. Rate the threat level as LOW/MODERATE/HIGH based on number of funded competitors."
            ),
            parent_index=0,
        ),
    ],
    test_company="resend.com",
    test_query="Analyze resend.com",
    rubric=[
        RubricItem(
            criterion="Output includes a 'Competitive Threat Score' section with a threat level rating (LOW, MODERATE, or HIGH)",
            weight=1.0,
        ),
    ],
    description="Tests correction injection in multi-step reasoning. Agent doesn't naturally produce a Competitive Threat Score section.",
    real_seed_file=Path(__file__).parent / "multi_step_threat_score.json",
)
