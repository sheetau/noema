from scripts.check_density_unit_scope import model_checks,quantifier_checks,presentation_checks,reading_checks,structure_checks

def test_units():assert model_checks()['uncalibrated_energy_unit_rejected']
def test_quantifiers():assert quantifier_checks()['infinite_real_function_domains_refused']
def test_presentation():assert presentation_checks()['must_follow_direction_retained']
def test_reading():assert reading_checks()['first_sentence_complete_under_explicit_reading']
def test_structure():assert structure_checks()['only_unregistered_first_sentence_revised']
