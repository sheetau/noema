from scripts import check_topical_guardian_interest as check


def test_topical_guardianship_binds_the_same_action_and_target():check.activity_checks()
def test_closed_guardianship_content_without_execution():check.quotation_checks()
def test_interest_and_actual_guardianship_are_independent():check.interest_checks()
def test_arts_and_sciences_both_require_absence_of_interest():check.dual_domain_checks()
def test_complete_subjects_of_the_same_ruler():check.subject_checks()
def test_source_collation_and_inherited_meanings():check.structure_checks()
