from scripts.check_evaluated_motives import motive_checks, generic_checks, attribution_checks, structure


def test_rest_and_prudence_do_not_inherit_fault_from_avoidance():
    assert motive_checks()['generic_and_static_specializations_agree']


def test_evaluated_state_keeps_fact_and_fault_independent():
    assert generic_checks()['context_dependent_evaluation']


def test_author_attribution_does_not_assert_moral_truth():
    assert attribution_checks()['all_dispositions_faults_and_causes_left_unknown']


def test_eleven_whole_unit_readings_and_raw_dispositions_are_preserved():
    assert structure()['preserved_review_meanings'] == 11
