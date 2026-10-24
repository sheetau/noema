from scripts.check_vacuum_equation_assumption import physical_checks,witness_checks,equation_binding_checks,vector_checks,curl_checks,presentation_checks,structure_checks


def test_physical():assert physical_checks()['native_current_field_units_and_positive_factors']
def test_witnesses():assert witness_checks()['native_real_witnesses_refused']
def test_equation_binding():assert equation_binding_checks()['same_region_fields_light_vacuum_and_physical_convention']
def test_vectors():assert vector_checks()['native_full_domain_refused']
def test_curl():assert curl_checks()['all_eighteen_derivative_slots_and_six_signs']
def test_presentation():assert presentation_checks()['assumed_physical_truth_not_executed']
def test_structure():assert structure_checks()['other_357_statements_and_prior_judgments_preserved']
