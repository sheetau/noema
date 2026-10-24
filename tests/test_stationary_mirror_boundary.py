from scripts.check_stationary_mirror_boundary import vector_checks,boundary_checks,binding_checks,polynomial_checks,structure_checks

def test_vectors():assert vector_checks()['full_direction_and_six_field_components_checked']
def test_boundary():assert boundary_checks()['all_field_components_phase_and_boundary_coordinates_checked']
def test_bindings():assert binding_checks()['all_four_universal_coordinate_slots_checked']
def test_polynomial():assert polynomial_checks()['rational_polynomial_only']
def test_structure():assert structure_checks()['all_394_statements_and_judgments_preserved']
