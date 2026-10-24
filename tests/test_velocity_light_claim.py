from scripts.check_velocity_light_claim import numeric_checks,universal_checks,physical_checks,presentation_checks,structure_checks

def test_numeric():assert numeric_checks()['cases']>0
def test_universal():assert universal_checks()['native_all_real_enumeration_refused']
def test_physical():assert physical_checks()['frame_speed_not_set_to_light']
def test_presentation():assert presentation_checks()['cases']>0
def test_structure():assert structure_checks()['other_statements_preserved']==354
