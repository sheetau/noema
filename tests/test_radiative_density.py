from scripts.check_radiative_density import density_checks,average_checks,physical_checks,transport_checks,setting_checks,polynomial_checks,structure_checks

def test_density():assert density_checks()['electric_and_magnetic_contributions_kept']
def test_average():assert average_checks()['same_profile_interval_integral_and_mean']
def test_physical():assert physical_checks()['work_calibration_reused']
def test_transport():assert transport_checks()['wrong_boundary_velocity_and_nontransverse_field_distinguished']
def test_setting():assert setting_checks()['all_66_roles_shared_between_frames']
def test_polynomial():assert len(polynomial_checks()['lemmas'])==4
def test_structure():assert structure_checks()['all_385_statements_and_judgments_preserved']
