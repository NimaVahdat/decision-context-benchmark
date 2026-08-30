from .chain_accumulating_5 import SCENARIO as chain_accumulating_5
from .chain_conflicting import SCENARIO as chain_conflicting
from .chain_superseding import SCENARIO as chain_superseding
from .forget_explicit_deletion import SCENARIO as forget_explicit_deletion
from .forget_partial_rollback import SCENARIO as forget_partial_rollback
from .support_policy_superseded import SCENARIO as support_policy_superseded
from .support_tier_change import SCENARIO as support_tier_change
from .temporal_evolving_preference import SCENARIO as temporal_evolving_preference
from .temporal_reversion import SCENARIO as temporal_reversion

TEMPORAL_COHERENCE_SCENARIOS = [
    support_policy_superseded,
    support_tier_change,
    chain_conflicting,
    chain_accumulating_5,
    chain_superseding,
    temporal_reversion,
    temporal_evolving_preference,
    forget_explicit_deletion,
    forget_partial_rollback,
]
