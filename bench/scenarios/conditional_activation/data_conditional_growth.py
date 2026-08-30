from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="data_conditional_growth",
    name="Growth + burn multi-variable tagging",
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
                "Tag every company in the Assessment section using BOTH growth rate AND burn multiple:\n"
                "- [EFFICIENT HYPERGROWTH] if growth > 150% AND burn multiple < 2x\n"
                "- [BURNING HYPERGROWTH] if growth > 150% AND burn multiple >= 2x\n"
                "- [FAST] if growth 50-150%\n"
                "- [STEADY] if growth < 50%\n"
                "Put the tag at the start of the assessment."
            ),
            parent_index=0,
        ),
    ],
    test_company="resend.com",  # 210% growth, ~1.0x burn -> EFFICIENT HYPERGROWTH
    test_query="Analyze resend.com",
    rubric=[
        RubricItem(
            criterion=(
                "Assessment section begins with [EFFICIENT HYPERGROWTH] tag (not [BURNING HYPERGROWTH] "
                "or just [HYPERGROWTH]). Resend has 210% YoY growth (>150%) AND ~1.0x burn multiple (<2x)."
            ),
            weight=1.0,
        ),
    ],
    description="Tests multi-variable conditional tagging based on growth + burn multiple",
    real_seed_file=Path(__file__).parent / "data_conditional_growth.json",
)
