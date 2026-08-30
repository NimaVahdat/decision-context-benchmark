from .query_avoid_bad_pattern import SCENARIO as query_avoid_bad_pattern
from .query_learn_pattern import SCENARIO as query_learn_pattern
from .self_assess_cross_subject import SCENARIO as self_assess_cross_subject
from .self_assess_recurring_failure import SCENARIO as self_assess_recurring_failure
from .self_assess_retry import SCENARIO as self_assess_retry
from .support_auth_error_retry import SCENARIO as support_auth_error_retry
from .support_channel_lookup import SCENARIO as support_channel_lookup
from .support_new_product_gap import SCENARIO as support_new_product_gap
from .support_presales_skip import SCENARIO as support_presales_skip
from .support_repeat_escalate import SCENARIO as support_repeat_escalate

IMPLICIT_LEARNING_SCENARIOS = [
    self_assess_recurring_failure,
    self_assess_cross_subject,
    self_assess_retry,
    query_learn_pattern,
    query_avoid_bad_pattern,
    support_presales_skip,
    support_new_product_gap,
    support_auth_error_retry,
    support_repeat_escalate,
    support_channel_lookup,
]
