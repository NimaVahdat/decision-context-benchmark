from .actor_3user import SCENARIO as actor_3user
from .actor_conflict import SCENARIO as actor_conflict
from .actor_cross_user import SCENARIO as actor_cross_user
from .fidelity_ambiguous import SCENARIO as fidelity_ambiguous
from .isolation_cross_skill import SCENARIO as isolation_cross_skill
from .isolation_negative_transfer import SCENARIO as isolation_negative_transfer
from .support_cross_skill_isolation import SCENARIO as support_cross_skill_isolation
from .support_rule_isolation import SCENARIO as support_rule_isolation

SCOPE_PRECISION_SCENARIOS = [
    support_rule_isolation,
    support_cross_skill_isolation,
    isolation_cross_skill,
    isolation_negative_transfer,
    actor_conflict,
    actor_cross_user,
    actor_3user,
    fidelity_ambiguous,
]
