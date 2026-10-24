from scripts.check_unipolar_machine import polarity_checks,machine_checks,witness_checks,annotation_checks,structure_checks

def test_polarity():assert polarity_checks()['both_polarities_nonconstant_and_zero_crossings_distinguished']
def test_machine():assert machine_checks()['complete_turn_fixed_circuit_two_contacts_and_induction_bound']
def test_witnesses():assert witness_checks()['one_configuration_with_shared_device_and_operation']
def test_annotation():assert annotation_checks()['source_expression_bound_to_composed_machine_rule']
def test_structure():assert structure_checks()['old_361_statements_preserved']
