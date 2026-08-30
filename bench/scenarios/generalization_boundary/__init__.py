from .generalize_runway_stage import SCENARIO as generalize_runway_stage
from .generalize_saas_mrr import SCENARIO as generalize_saas_mrr
from .no_generalize_company_specific import SCENARIO as no_generalize_company_specific

GENERALIZATION_BOUNDARY_SCENARIOS = [
    generalize_saas_mrr,
    no_generalize_company_specific,
    generalize_runway_stage,
]
