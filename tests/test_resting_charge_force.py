from scripts.check_resting_charge_force import force_checks,rest_checks,witness_checks,conditional_checks,presentation_checks,structure_checks

def test_force():assert force_checks()['physical_response_and_all_units_shared']
def test_rest():assert rest_checks()['nonzero_acceleration_allowed']
def test_witness():assert witness_checks()['two_witness_slots_distinguished']
def test_conditional():assert conditional_checks()['two_separate_conditions_not_simultaneously_asserted']
def test_presentation():assert presentation_checks()['definition_reference_not_new_definition_or_proof']
def test_structure():assert structure_checks()['whole_unit_review_not_claimed']
