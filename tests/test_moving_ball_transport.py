from scripts.check_moving_ball_transport import surface_checks,plane_checks,advection_checks,quantifier_checks,physical_checks,adapter_checks,polynomial_checks,structure_checks


def test_surface():assert surface_checks()['opposite_surface_cancellation_not_accepted']
def test_plane():assert plane_checks()['instantaneous_fields_used_together']
def test_advection():assert advection_checks()['phase_and_instantaneous_density_follow_same_path']
def test_quantifiers():assert quantifier_checks()['all_four_spacetime_or_initial_position_time_slots_checked']
def test_physical():assert physical_checks()['all_26_physical_roles_bound']
def test_adapters():assert adapter_checks()['same_70_role_background_preserved']
def test_polynomial():assert polynomial_checks()['phase_constant_on_unit_normal_characteristics']['status']=='valid'
def test_structure():assert structure_checks()['all_388_statements_and_judgments_preserved']
