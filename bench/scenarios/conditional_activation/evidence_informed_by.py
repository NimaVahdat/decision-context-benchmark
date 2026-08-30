from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="evidence_informed_by",
    name="Evidence-based retrieval via INFORMED_BY",
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
                "Whenever the burn multiple is mentioned in the Assessment section, always add a CAUTION "
                "flag right after it noting 'burn multiple indicates inefficient growth'. Always include "
                "this CAUTION flag alongside any burn multiple reference in Assessment."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content="Show me the full analysis again with the CAUTION flag in the Assessment section.",
            parent_index=1,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="notion.so",
            message_content="Analyze notion.so",
            parent_index=None,
        ),
    ],
    test_company="meridian.bio",
    test_query="Analyze meridian.bio",
    rubric=[
        RubricItem(
            criterion=(
                "Assessment includes the literal text 'CAUTION:' followed by a warning about burn "
                "efficiency or burn multiple. The word CAUTION must appear explicitly as a flag/label."
            ),
            weight=1.0,
        ),
    ],
    description="Tests evidence-based retrieval: correction about burn multiple CAUTION found via INFORMED_BY evidence matching",
    real_seed_file=Path(__file__).parent / "evidence_informed_by.json",
)
