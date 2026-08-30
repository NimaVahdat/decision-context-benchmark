from pathlib import Path

from bench.judge.programmatic import BehaviorCheck
from bench.scenarios.models import RubricItem, Scenario, SeedTrace
from bench.scenarios.persistence._helpers import support_spacer

_SPACER_DATA = [
    ("repeat-beta.io", 0),
    ("repeat-gamma.io", 1),
    ("orion-acme.io", 2),
    ("orion-beta.io", 3),
    ("orion-gamma.io", 4),
    ("repeat-alpha.io", 5),
    ("orion-acme.io", 6),
    ("repeat-beta.io", 7),
    ("orion-beta.io", 8),
]

SCENARIO = Scenario(
    id="support_routing_10tickets",
    name="Routing correction persists across 10 support tickets",
    skill="eval-support",
    seed_traces=[
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="Handle support ticket for repeat-alpha.io: billing discrepancy",
            parent_index=None,
        ),
        SeedTrace(
            skill="eval-support",
            company="repeat-alpha.io",
            message_content="Stop including KB article links in responses — our customers find them confusing. Just state the action.",
            parent_index=0,
        ),
        *[support_spacer(c, i) for c, i in _SPACER_DATA],
    ],
    test_company="repeat-delta.io",
    test_query="Handle support ticket for repeat-delta.io: export failure for repeat-delta.io",
    rubric=[
        RubricItem(
            criterion="Output does NOT include KB article links or URLs",
            weight=1.0,
            mode="negative",
        ),
        RubricItem(
            criterion="Response states the recommended action directly without referencing KB articles",
            weight=1.0,
        ),
    ],
    description="Tests that a formatting correction (no KB article links) persists across 10 intervening support tickets.",
    behavior_checks=[
        BehaviorCheck(
            name="no_kb_refs_in_output",
            check_type="keyword_absent",
            keywords=["kb articles found", "knowledge base articles found", "relevant kb"],
            weight=1.5,
        ),
    ],
    real_seed_file=Path(__file__).parent / "support_routing_10tickets.json",
)
