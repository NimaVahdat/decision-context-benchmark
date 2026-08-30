from .exception_ephemeral_support import SCENARIO as exception_ephemeral_support
from .exception_no_persist import SCENARIO as exception_no_persist
from .exception_vs_rule import SCENARIO as exception_vs_rule

EXCEPTION_HANDLING_SCENARIOS = [
    exception_vs_rule,
    exception_no_persist,
    exception_ephemeral_support,
]
