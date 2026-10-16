from scripts.check_audience_liberty import generic_checks,permission_checks,native_checks,structure


def test_permission_scope_checks_each_person_and_opposing_requirement():
    assert generic_checks()['membership_permission_and_opposition_combinations']==64


def test_public_scope_is_fixed_and_permission_does_not_execute_activity():
    assert permission_checks()['fixed_population_and_activity_reference']


def test_native_conditional_changes_do_not_assert_current_freedom_or_success():
    assert native_checks()['native_change_and_modality_evaluated_together']


def test_extension_preserves_existing_meanings_and_reviews():
    assert structure()['seven_review_bindings_preserved']
