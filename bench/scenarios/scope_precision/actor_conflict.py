from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="actor_conflict",
    name="User A (WRR) vs User B (DRR) conflict",
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
            message_content="Express revenue as WRR (weekly run rate). Divide ARR by 52 to get WRR.",
            parent_index=0,
            actor_id="user-alice",
        ),
        SeedTrace(
            skill="eval-analyst",
            company="retool.com",
            message_content="Analyze retool.com",
            parent_index=None,
            actor_id="user-bob",
        ),
        SeedTrace(
            skill="eval-analyst",
            company="retool.com",
            message_content="Express revenue as DRR (daily run rate). Divide ARR by 365 to get DRR.",
            parent_index=2,
            actor_id="user-bob",
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    test_actor_id="user-alice",
    rubric=[
        RubricItem(
            criterion="Financial overview includes WRR (weekly run rate). DRR must NOT appear. User Alice's preference is WRR.",
            weight=1.0,
        ),
    ],
    description="Tests actor-specific routing: User A's WRR preference should win when querying as User A",
    real_seed_file=Path(__file__).parent / "actor_conflict.json",
)
