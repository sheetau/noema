from scripts.check_electromotive_wording import numeric_checks,physical_checks,approximation_checks,quantifier_checks,presentation_checks,structure_checks

def test_numeric():assert numeric_checks()['ordered_three_component_scale_and_residual']
def test_physical():assert physical_checks()['physical_response_and_force_records_bound']
def test_approximation():assert approximation_checks()['all_directions_and_cross_product_order']
def test_quantifier():assert quantifier_checks()['every_witness_and_free_slot_distinguished']
def test_presentation():assert presentation_checks()['quoted_term_role_not_execution']
def test_structure():assert structure_checks()['semantic_judgment_separate']
