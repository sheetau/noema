from scripts.check_mirror_energy_work import transport_checks,integral_checks,coverage_checks,binding_checks,printed_checks,structure_checks

def test_relative_transport():assert transport_checks()['same_four_coordinates_and_mirror_trace']
def test_work_and_mean_integrals():assert integral_checks()['mechanical_work_signed_and_zero_speed_safe']
def test_all_patch_points():assert coverage_checks()['all_real_tangential_positions_retained']
def test_shared_physical_roles():assert binding_checks()['all_98_physical_and_102_shared_roles_checked']
def test_printed_candidates():assert printed_checks()['work_balance_separate_from_mechanical_definition']
def test_preservation():assert structure_checks()['all_402_statements_and_meanings_preserved']
