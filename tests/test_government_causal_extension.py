from scripts.check_government_causal_extension import clock_checks,content_checks,contrast_checks,causal_checks,binding_checks,structure_checks

def test_shared_extended_clock():assert clock_checks()
def test_actual_adoption_content():assert content_checks()
def test_signed_change_contrast():assert contrast_checks()
def test_same_structural_cause():assert causal_checks()
def test_same_endpoint_bindings():assert binding_checks()
def test_structure():assert structure_checks()
