from scripts.check_collective_return_sentence import conditional_checks,native_scope_checks,endpoint_checks,discourse_checks,structure_checks

def test_complete_conditional():assert conditional_checks()
def test_native_same_population():assert native_scope_checks()
def test_shared_endpoints_and_relatives():assert endpoint_checks()
def test_attribution_anaphora_focus_note():assert discourse_checks()
def test_unchanged_reviews_and_roundtrips():assert structure_checks()
