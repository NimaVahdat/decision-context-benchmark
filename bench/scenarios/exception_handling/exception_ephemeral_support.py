from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="exception_ephemeral_support",
    name="Urgent bypass does not persist to next support ticket",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="orion-acme.io",
            message_content="Handle support ticket for orion-acme.io: critical data loss P0",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="orion-acme.io",
            message_content=(
                "For this P0 emergency — skip all standard lookups and escalate immediately without investigation."
            ),
            parent_index=0,
        ),
    ],
    test_company="orion-beta.io",
    test_query="Handle support ticket for orion-beta.io: api timeout for orion-beta.io",
    rubric=[
        RubricItem(
            criterion="Agent calls lookup_account for the new ticket — urgent bypass did not persist",
            weight=1.0,
        ),
        RubricItem(
            criterion="Agent skips lookup_account for orion-beta.io", mode="negative", weight=1.0
        ),
    ],
    description="Control=1 expected (agent naturally calls lookup_account). Tests that DC does NOT persist a one-time emergency bypass.",
    behavior_checks=[
        BehaviorCheck(
            name="lookup_account_called",
            check_type="source_called",
            sources=["lookup_account"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "exception_ephemeral_support.json",
)
