from .long_10msg_scattered import SCENARIO as long_10msg_scattered
from .long_20msg_early import SCENARIO as long_20msg_early
from .long_volume_distraction import SCENARIO as long_volume_distraction
from .noise_100_corrections import SCENARIO as noise_100_corrections
from .noise_mixed_signals import SCENARIO as noise_mixed_signals
from .scale_50_corrections import SCENARIO as scale_50_corrections
from .session_5conv import SCENARIO as session_5conv
from .session_cross_company import SCENARIO as session_cross_company
from .support_routing_10tickets import SCENARIO as support_routing_10tickets
from .support_routing_noise import SCENARIO as support_routing_noise

PERSISTENCE_SCENARIOS = [
    support_routing_10tickets,
    support_routing_noise,
    long_10msg_scattered,
    long_20msg_early,
    long_volume_distraction,
    session_5conv,
    session_cross_company,
    scale_50_corrections,
    noise_100_corrections,
    noise_mixed_signals,
]
