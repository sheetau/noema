from scripts.check_qualified_judgment import witness_checks,reason_checks,construction_checks,source_checks,integration_checks,structure


def test_quality_conditions_have_one_shared_judgment_witness():
    assert witness_checks()['combinations']==64


def test_a_stronger_reason_criterion_is_an_executable_noema_composition():
    assert reason_checks()['combinations']==16


def test_closed_task_retains_all_criteria_without_executing_them():
    assert construction_checks()['all_four_references_preserved']


def test_qualified_ability_keeps_criteria_and_profile_identity():
    assert source_checks()['concrete_noema_reason_criterion_executed']


def test_same_quality_survives_enabling_and_collective_evaluation():
    assert integration_checks()['same_quality_through_enabling_and_collective_attainment']


def test_existing_text_and_ten_reviewed_meanings_are_preserved():
    assert structure()['preserved_review_selections']==10
