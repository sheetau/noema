from scripts.check_civic_choice_mediation import contrast_checks,scope_content_checks,mediation_checks,intervention_binding_checks,structure_checks

def test_gradual_gain_contrast():assert contrast_checks()
def test_full_scope_content():assert scope_content_checks()
def test_native_mediation():assert mediation_checks()
def test_model_and_wrapper_bindings():assert intervention_binding_checks()
def test_structure():assert structure_checks()
