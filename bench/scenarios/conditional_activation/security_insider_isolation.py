from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="security_insider_isolation",
    name="Insider threat: use EXFIL-SCORE and specific response codes",
    skill="eval-security-assessor",
    seed_traces=[
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1003",
            message_content="Assess security alert alert-1003",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-security-assessor",
            company="alert-1003",
            message_content=(
                "For insider threats with data transfers, add an 'EXFIL-SCORE' rating. "
                "Large daytime transfers get EXFIL-SCORE: HIGH. Also add response code 'RC-3: ISOLATE'."
            ),
            parent_index=0,
        ),
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
                "When privilege escalation has a documented justification and zero data transfer, set "
                "EXFIL-SCORE: NONE and response code 'RC-1: MONITOR'. Do NOT use RC-3."
            ),
            parent_index=2,
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
                "This is the most dangerous pattern. Small after-hours transfers are MORE concerning "
                "than large daytime ones — targeted exfil of high-value docs. Set EXFIL-SCORE: CRITICAL "
                "(not HIGH). Use response code 'RC-4: ISOLATE AND ESCALATE'."
            ),
            parent_index=4,
        ),
    ],
    test_company="alert-2002",
    test_query="Assess security alert alert-2002",
    rubric=[
        RubricItem(
            criterion="Assessment contains the exact text 'EXFIL-SCORE: CRITICAL'.", weight=1.0
        ),
        RubricItem(criterion="Assessment contains the exact response code 'RC-4'.", weight=1.0),
    ],
    description="Tests counter-intuitive judgment: small after-hours = EXFIL-SCORE CRITICAL + RC-4.",
    real_seed_file=Path(__file__).parent / "security_insider_isolation.json",
)
