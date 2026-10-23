from scripts.check_velocity_magnitude_claim import magnitude_checks,trajectory_checks,scope_checks,presentation_checks,structure_checks


def test_magnitude():assert magnitude_checks()['cases']>0
def test_trajectory():assert trajectory_checks()['cases']>0
def test_scope():assert scope_checks()['cases']>0
def test_presentation():assert presentation_checks()['cases']>0
def test_structure():assert structure_checks()['new_definitions']>0
