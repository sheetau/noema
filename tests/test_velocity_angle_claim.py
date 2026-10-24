from scripts.check_velocity_angle_claim import reference_checks,presentation_checks,attribution_checks,structure_checks


def test_reference():assert reference_checks()['cases']>0
def test_presentation():assert presentation_checks()['cases']>0
def test_attribution():assert attribution_checks()['cases']>0
def test_structure():assert structure_checks()['other_statements_preserved']==354
