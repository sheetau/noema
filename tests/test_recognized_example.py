from scripts import check_recognized_example as checks


def test_recognition_preserves_example_time_and_distinct_experiencer():
    assert checks.generic_checks()['unknown_inputs_refused'] == 5


def test_native_failure_and_fall_preserve_recognition_and_are_independent():
    assert checks.native_checks()['observer_may_differ_from_experiencer']


def test_depiction_is_bound_to_deterrence_clause_and_does_not_assert_falls():
    assert checks.attribution_checks()['all_world_contents_unknown']


def test_previous_judgments_and_three_notations_are_preserved():
    assert checks.structure()['preserved_reviewed_sentence_characters'] == 1021
