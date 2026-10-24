from scripts.check_seventh_section_heading import setting_checks,heading_checks,structure_checks

def test_settings():assert setting_checks()['infinite_settings_refused']
def test_heading():assert heading_checks()['same_inquiry_and_context_for_both_subjects']
def test_structure():assert structure_checks()['physical_settings_do_not_assume_printed_laws']
