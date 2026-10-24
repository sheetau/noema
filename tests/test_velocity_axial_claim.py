from scripts.check_velocity_axial_claim import numeric_checks,symmetry_checks,appraisal_checks,physical_checks,presentation_checks,structure_checks

def test_numeric():assert numeric_checks()['cases']>0
def test_symmetry():assert symmetry_checks()['native_unbounded_real_enumeration_rejected']
def test_appraisal():assert appraisal_checks()['quoted_symmetry_not_executed_as_truth']
def test_physical():assert physical_checks()['cases']>0
def test_presentation():assert presentation_checks()['cases']>0
def test_structure():assert structure_checks()['other_statements_preserved']==353
