from scripts import check_enlightenment_incapacity as checks


def test_no_attainment_method_in_any_valid_opportunity():
    assert checks.capacity_checks()['all_opportunities_not_one_failure']


def test_learning_routes_can_defeat_incapacity():
    assert checks.source_checks()['current_exercise_incapacity_not_used_as_acquisition_incapacity']


def test_guardianship_is_about_other_members_of_the_same_public():
    assert checks.role_checks()['no_appointment_or_actual_enlightenment_inferred']


def test_native_role_and_capacity_are_used_in_reversal_condition():
    assert checks.integration_checks()['role_and_incapacity_functions_filled']


def test_existing_reviews_survive():
    assert checks.structure_checks()['preserved_sentence_characters'] == 382
