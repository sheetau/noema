from scripts.check_civic_feedback import generalized_profile_checks,scope_clock_checks,contrast_checks,causal_checks,wrapper_checks,structure_checks

def test_generalized_profile():assert generalized_profile_checks()
def test_scope_and_clock():assert scope_clock_checks()
def test_changing_contrast():assert contrast_checks()
def test_causal_composition():assert causal_checks()
def test_content_wrapper():assert wrapper_checks()
def test_structure():assert structure_checks()
