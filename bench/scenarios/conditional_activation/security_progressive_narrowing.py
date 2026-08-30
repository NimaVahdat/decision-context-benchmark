from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="security_progressive_narrowing",
    name="Multi-condition assessment requiring all 4 data sources",
    skill="eval-security-assessor",
    seed_traces=[
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1004",
            message_content="Assess security alert alert-1004",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1004",
            message_content=(
                "When ALL of these are true: (1) auth logs show a documented maintenance justification, "
                "AND (2) behavior analysis shows zero anomaly, AND (3) no data transfer — then add the "
                "tag 'CLEARED: AUTHORIZED-MAINTENANCE'."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1005",
            message_content="Assess security alert alert-1005",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1005",
            message_content=(
                "When auth logs show privilege escalation WITHOUT a maintenance justification AND behavior "
                "shows after-hours access, do NOT use the CLEARED tag. Instead add "
                "'FLAGGED: REQUIRES-INVESTIGATION'."
            ),
            parent_index=2,
        ),
    ],
    test_company="alert-2002",
    test_query="Assess security alert alert-2002",
    rubric=[
        RubricItem(
            criterion=(
                "Assessment contains 'FLAGGED: REQUIRES-INVESTIGATION'. alert-2002 has privilege "
                "escalation WITHOUT maintenance justification and after-hours access."
            ),
            weight=1.0,
        ),
    ],
    description="Tests multi-condition assessment: two similar incidents require different tags based on justification + timing.",
    real_seed_file=Path(__file__).parent / "security_progressive_narrowing.json",
)
