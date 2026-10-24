from scripts.check_velocity_angle_measure import integral_checks,branch_checks,geometry_checks,physical_checks,structure_checks


def test_integral():assert integral_checks()['cases']>0
def test_branch():assert branch_checks()['cases']>0
def test_geometry():assert geometry_checks()['cases']>0
def test_physical():assert physical_checks()['cases']>0
def test_structure():assert structure_checks()['new_primitives']==0
