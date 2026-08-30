"""Basic smoke tests for scenario loading."""

from bench.scenarios import SCENARIOS
from bench.scenarios.models import Scenario


def test_scenarios_load():
    """All scenarios should load without errors."""
    assert len(SCENARIOS) == 71


def test_scenario_ids_unique():
    """Scenario IDs must be unique."""
    ids = [s.id for s in SCENARIOS]
    assert len(ids) == len(set(ids))


def test_scenario_types():
    """All scenarios should be Scenario instances."""
    for s in SCENARIOS:
        assert isinstance(s, Scenario)
        assert s.skill
        assert s.test_company
        assert s.test_query
        assert s.rubric or s.behavior_checks
