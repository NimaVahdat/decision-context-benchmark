from .basic_cap_scores import SCENARIO as basic_cap_scores
from .basic_content_qrr import SCENARIO as basic_content_qrr
from .basic_format_table import SCENARIO as basic_format_table
from .basic_runway_risk import SCENARIO as basic_runway_risk
from .basic_terminology_ebitda import SCENARIO as basic_terminology_ebitda
from .basic_two_sentences import SCENARIO as basic_two_sentences
from .fidelity_phrasing import SCENARIO as fidelity_phrasing
from .support_account_format import SCENARIO as support_account_format
from .support_routing_rule import SCENARIO as support_routing_rule

RECALL_SCENARIOS = [
    support_routing_rule,
    support_account_format,
    basic_format_table,
    basic_content_qrr,
    basic_terminology_ebitda,
    basic_runway_risk,
    basic_cap_scores,
    basic_two_sentences,
    fidelity_phrasing,
]
