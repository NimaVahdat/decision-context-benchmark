from .multi_step_threat_score import SCENARIO as multi_step_threat_score
from .procedural_comparable_format import SCENARIO as procedural_comparable_format
from .procedural_conditional_skip import SCENARIO as procedural_conditional_skip
from .procedural_runway_flag import SCENARIO as procedural_runway_flag
from .procedural_tool_order import SCENARIO as procedural_tool_order
from .support_escalate_suspended_first import SCENARIO as support_escalate_suspended_first
from .support_order_before_kb import SCENARIO as support_order_before_kb

BEHAVIORAL_CHANGE_SCENARIOS = [
    support_order_before_kb,
    support_escalate_suspended_first,
    procedural_tool_order,
    procedural_conditional_skip,
    multi_step_threat_score,
    procedural_runway_flag,
    procedural_comparable_format,
]
