from scripts.check_apparent_asymmetry import appearance_checks,application_checks,knownness_checks,structure_checks
def test_appearance():assert appearance_checks()['actual_asymmetry_compatible_with_appearance']
def test_application():assert application_checks()['existential_comparison_checked']
def test_knownness():assert knownness_checks()['knownness_does_not_erase_claim_or_qualification']
def test_structure():assert structure_checks()['general_scope_preserved']
