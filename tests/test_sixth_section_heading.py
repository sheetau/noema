from scripts.check_sixth_section_heading import equation_checks,driving_checks,heading_checks,structure_checks


def test_equations():assert equation_checks()['native_full_region_refused']
def test_driving():assert driving_checks()['native_full_history_refused']
def test_heading():assert heading_checks()['two_subjects_share_inquiry_and_context']
def test_structure():assert structure_checks()['conductor_case_and_later_conclusions_not_imported']
