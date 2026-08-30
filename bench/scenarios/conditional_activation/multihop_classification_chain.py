from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="multihop_classification_chain",
    name="3-hop classification chain (ARR -> stage -> moat -> score)",
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
                "In the assessment, classify companies using these labels: 'Scaling' if ARR > $20M, "
                "'Growth' if ARR $5-20M, 'Early' if ARR < $5M."
            ),
            parent_index=0,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content="Analyze resend.com",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content=(
                "For companies classified as 'Scaling', always include a detailed competitive moat analysis section."
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
            message_content=(
                "The competitive moat analysis must include a 'Moat Durability Score' rated from 1 to 10 "
                "with a one-sentence justification."
            ),
            parent_index=4,
        ),
    ],
    test_company="linear.app",  # $28M ARR -> Scaling
    test_query="Analyze linear.app",
    rubric=[
        RubricItem(
            criterion="The assessment contains the exact label 'Scaling' as a stage classification.",
            weight=1.0,
        ),
        RubricItem(
            criterion="Output includes a section explicitly titled 'Competitive Moat Analysis' or 'Moat Analysis'.",
            weight=1.0,
        ),
        RubricItem(
            criterion="The output contains a numerical 'Moat Durability Score' written as a number out of 10.",
            weight=1.0,
        ),
    ],
    description="Tests 3-hop multi-hop consolidation: ARR -> stage -> moat section -> durability score.",
    real_seed_file=Path(__file__).parent / "multihop_classification_chain.json",
)
