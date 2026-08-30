from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="security_external_vs_patched",
    name="External probe: use specific severity label based on patch status",
    skill="eval-security-assessor",
    seed_traces=[
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1001",
            message_content="Assess security alert alert-1001",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1001",
            message_content=(
                "When external scanning is combined with auth failures AND unpatched critical CVEs, label "
                "the alert as 'SEVERITY-1: IMMEDIATE ESCALATION' at the top of the assessment."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1002",
            message_content="Assess security alert alert-1002",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1002",
            message_content=(
                "When external scanning has auth failures but all systems are patched with no successful "
                "logins, label as 'SEVERITY-4: ROUTINE PROBE'. Do NOT use SEVERITY-1. "
                "Patched systems with failed logins are routine."
            ),
            parent_index=2,
        ),
    ],
    test_company="alert-2001",
    test_query="Assess security alert alert-2001",
    rubric=[
        RubricItem(
            criterion=(
                "Assessment includes the label 'SEVERITY-4' or 'ROUTINE PROBE'. alert-2001 has external "
                "probing with auth failures but ALL systems are patched."
            ),
            weight=1.0,
        ),
    ],
    description="Tests conditional judgment: external scan + auth failures + patched = SEVERITY-4, not SEVERITY-1.",
    real_seed_file=Path(__file__).parent / "security_external_vs_patched.json",
)
