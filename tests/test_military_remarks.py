from scripts.check_military_remarks import (
    defect_checks,notes_checks,goal_checks,candidate_checks,officer_checks,execution_checks,unknown_checks,structure_checks)


def test_applicable_condition_and_its_failure():
    defect_checks()


def test_all_remarks_share_the_subject_without_asserting_their_truth():
    notes_checks()


def test_same_public_and_notes_in_the_judgment_goal():
    goal_checks()


def test_planned_creation_and_submission_without_existing_records():
    candidate_checks()


def test_same_officer_and_military_institution():
    officer_checks()


def test_creation_and_submission_require_the_same_recorded_work():
    execution_checks()


def test_unknown_inputs_remain_unknown():
    unknown_checks()


def test_preserved_meanings_evidence_and_notation():
    structure_checks()
