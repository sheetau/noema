from scripts.check_present_shortfall_sentence import gap_checks,source_checks,native_support_checks,settings_checks,discourse_checks,structure_checks

def test_large_gap_and_valid_assessment():gap_checks()
def test_both_distributions_not_their_union():source_checks()
def test_native_religious_support_possibility():native_support_checks()
def test_closed_source_settings():settings_checks()
def test_attribution_scope_and_focus():discourse_checks()
def test_sentence_reading_and_preserved_reviews():structure_checks()
