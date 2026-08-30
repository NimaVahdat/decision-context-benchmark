from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="actor_cross_user",
    name="User A corrects, User B queries",
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
            message_content=(
                "Always label Net Dollar Retention as 'Dollar-Based Net Retention (DBNR)' in the "
                "Financial Overview. Use the term DBNR, not NDR."
            ),
            parent_index=0,
            actor_id="user-alice",
        ),
        SeedTrace(
            skill="eval-analyst",
            company="delve.co",
            message_content="Redo the full analysis with DBNR instead of NDR.",
            parent_index=1,
            actor_id="user-alice",
        ),
    ],
    test_company="linear.app",
    test_query="Analyze linear.app",
    test_actor_id="user-bob",
    rubric=[
        RubricItem(
            criterion=(
                "Financial overview includes 'Dollar-Based Net Retention' or 'DBNR'. "
                "Even though User Alice made the correction, it should still be visible to User Bob."
            ),
            weight=1.0,
        ),
    ],
    description="Tests cross-user visibility: User A's DBNR correction should be visible to User B",
    real_seed_file=Path(__file__).parent / "actor_cross_user.json",
)
