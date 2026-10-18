from scripts.check_topical_standing import capacity_checks,enabling_checks,source_checks,construction_checks,collective_checks,structure


def test_topic_capacity_uses_current_basis_and_the_same_task_content():
    assert capacity_checks()['goal_content_obtained_from_same_task_description']


def test_enabling_possibility_is_not_completed_assessment_or_guarantee():
    assert enabling_checks()['possibility_not_full_assessment_or_guarantee']


def test_source_uses_same_person_and_matters_in_one_enabling_result():
    assert source_checks()['same_person_topic_anchor_at_result']


def test_closed_task_construction_does_not_execute_unknown_references():
    assert construction_checks()['explicit_execution_requires_referent']


def test_collective_attainment_uses_the_topic_specific_capacity():
    assert collective_checks()['collective_criterion_receives_same_topical_ability']


def test_existing_text_and_reviewed_meaning_are_preserved():
    assert structure()['preserved_review_selections']==10
