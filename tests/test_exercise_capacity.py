from scripts.check_exercise_capacity import (
    combinations, contrasts, source_checks, departure_checks, presentation_checks, structure,
)


def test_normal_exercise_capacity_is_distinct_from_current_opportunity():
    assert combinations()['count'] == 16


def test_unclassified_methods_and_invalid_profiles_do_not_prove_inability():
    assert contrasts()['unknown_inputs_refused'] == 7


def test_shared_manuscript_capacity_excludes_future_acquisition():
    assert source_checks()['cases']['training_only']['current'] == [True, False, True]


def test_departure_uses_the_same_capacity_at_its_endpoint():
    assert departure_checks()['cases']['baseline']['current'] == [True]


def test_quotation_does_not_execute_the_new_capacity_context():
    assert presentation_checks()['new_profile_parameters_not_executed_by_quotation']


def test_changed_dependencies_and_unchanged_reviewed_meanings_are_separated():
    result = structure()
    assert result['changed_bodies'] == ['bc', 'up', 'be', 'fo']
    assert len(result['preserved_review_units']) == 8
