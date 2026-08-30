from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="actor_3user",
    name="3 users with conflicting formats",
    skill="eval-analyst",
    seed_traces=[
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content="Analyze delve.co",
            parent_index=None,
            actor_id="user-alice",
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content="Use bullet points for all financial metrics.",
            parent_index=0,
            actor_id="user-alice",
        ),
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content="Analyze resend.com",
            parent_index=None,
            actor_id="user-bob",
        ),
        SeedTrace(
            skill="eval-analyst",
            company="resend.com",
            message_content="Use numbered lists for financial metrics.",
            parent_index=2,
            actor_id="user-bob",
        ),
        SeedTrace(
            skill="eval-analyst",
            company="notion.so",
            message_content="Analyze notion.so",
            parent_index=None,
            actor_id="user-carol",
        ),
        SeedTrace(
            skill="eval-analyst",
            company="notion.so",
            message_content="Keep financial data in flowing prose sentences, not lists.",
            parent_index=4,
            actor_id="user-carol",
        ),
    ],
    test_company="finstack.io",
    test_query="Analyze finstack.io",
    test_actor_id="user-bob",
    rubric=[
        RubricItem(
            criterion="Financial overview uses a numbered list format (1. 2. 3.), not bullets or prose. User Bob's preference is numbered lists.",
            weight=1.0,
        ),
    ],
    description="Tests 3-user conflict resolution with actor-specific preferences",
    real_seed_file=Path(__file__).parent / "actor_3user.json",
)
