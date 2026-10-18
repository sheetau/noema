from scripts.audit_opening_claims import conditional_checks,imputation_checks,presentation_checks,structure


def test_classification_is_universal_and_does_not_assert_converse_or_existence():
    assert conditional_checks()['count']==16


def test_imputation_needs_the_same_person_state_and_scene_and_is_not_filled_from_cause():
    assert imputation_checks()['unknown_imputation_refused']


def test_authored_conditional_is_quoted_without_certifying_world_facts():
    result=presentation_checks()
    assert result['cases']['baseline']==[True]
    assert result['cases']['equivalence_instead']==[False]


def test_reading_decisions_bind_current_source_without_completing_paragraph():
    assert structure()['new_whole_units']==0
