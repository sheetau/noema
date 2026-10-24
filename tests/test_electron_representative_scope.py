from scripts.check_electron_representative_scope import field_checks,setting_checks,transport_checks,candidate_preservation_checks,binder_checks,structure_checks

def test_rotated_fields_and_profiles():assert field_checks()
def test_general_setting_and_candidate():assert setting_checks()
def test_complete_physical_transport():assert transport_checks()
def test_preserved_law_answers():assert candidate_preservation_checks()
def test_all_representative_binders():assert binder_checks()
def test_structure():assert structure_checks()
