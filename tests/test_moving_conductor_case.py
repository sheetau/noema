from scripts.check_moving_conductor_case import case_checks,comparison_checks,numeric_checks,quantifier_checks,structure_checks

def test_single_case_connections():assert case_checks()['comparison_not_required_for_single_case']
def test_current_comparison():assert comparison_checks()['same_relative_different_current_rejected']
def test_driving_and_denials():assert numeric_checks()['zero_or_absent_energy_allowed']
def test_quantifier_scope():assert quantifier_checks()['relative_equality_scoped_only_to_comparison']
def test_presentation_and_inheritance():assert structure_checks()['quoted_physics_not_executed']
