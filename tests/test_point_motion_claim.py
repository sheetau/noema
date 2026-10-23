from scripts.check_point_motion_claim import presentation_checks,attribution_checks,structure_checks

def test_presentation():assert presentation_checks()['cases']>0
def test_attribution():assert attribution_checks()['cases']>0
def test_structure():assert structure_checks()['new_primitives']==3
