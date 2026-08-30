"""DC Bench scenario registry.

Exports:
    SCENARIOS: flat list of all scenarios across 9 behavioral dimensions
"""

from __future__ import annotations

from bench.scenarios.behavioral_change import BEHAVIORAL_CHANGE_SCENARIOS
from bench.scenarios.conditional_activation import CONDITIONAL_ACTIVATION_SCENARIOS
from bench.scenarios.exception_handling import EXCEPTION_HANDLING_SCENARIOS
from bench.scenarios.generalization_boundary import GENERALIZATION_BOUNDARY_SCENARIOS
from bench.scenarios.implicit_learning import IMPLICIT_LEARNING_SCENARIOS
from bench.scenarios.models import RubricItem, Scenario, SeedTrace
from bench.scenarios.persistence import PERSISTENCE_SCENARIOS
from bench.scenarios.recall import RECALL_SCENARIOS
from bench.scenarios.scope_precision import SCOPE_PRECISION_SCENARIOS
from bench.scenarios.temporal_coherence import TEMPORAL_COHERENCE_SCENARIOS

__all__ = [
    "SCENARIOS",
    "RubricItem",
    "Scenario",
    "SeedTrace",
]

SCENARIOS: list[Scenario] = [
    *RECALL_SCENARIOS,  # 9
    *TEMPORAL_COHERENCE_SCENARIOS,  # 9
    *CONDITIONAL_ACTIVATION_SCENARIOS,  # 12
    *PERSISTENCE_SCENARIOS,  # 10
    *SCOPE_PRECISION_SCENARIOS,  # 8
    *BEHAVIORAL_CHANGE_SCENARIOS,  # 7
    *IMPLICIT_LEARNING_SCENARIOS,  # 10
    *EXCEPTION_HANDLING_SCENARIOS,  # 3
    *GENERALIZATION_BOUNDARY_SCENARIOS,  # 3
]
