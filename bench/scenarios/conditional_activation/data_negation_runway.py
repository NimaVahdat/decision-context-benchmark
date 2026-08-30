from pathlib import Path

from bench.scenarios.models import RubricItem, Scenario, SeedTrace

SCENARIO = Scenario(
    id="data_negation_runway",
    name="Suppress runway for hypergrowth companies",
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
                "Do NOT flag runway as a risk or warning for companies growing above 150% YoY. "
                "Hypergrowth companies will raise again before runway becomes an issue. "
                "Only flag runway for companies with growth below 150%."
            ),
            parent_index=0,
        ),
    ],
    test_company="learnnext.ai",  # 300% growth, 14mo runway
    test_query="Analyze learnnext.ai",
    rubric=[
        RubricItem(
            criterion=(
                "Assessment does NOT include a runway risk warning or concern. learnnext.ai has 320% "
                "growth which is above 150%, so runway warnings should be suppressed."
            ),
            weight=1.0,
            mode="negative",
        ),
    ],
    description="Tests data-dependent negation: suppress runway warning for hypergrowth",
    real_seed_file=Path(__file__).parent / "data_negation_runway.json",
)
