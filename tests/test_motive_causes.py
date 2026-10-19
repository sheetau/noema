from scripts.check_motive_causes import motive_checks, causal_checks, attribution_checks, structure


def test_motive_dispositions_allow_ranked_exceptions_and_keep_reason_bindings():
    assert motive_checks()['actual_mf_mg_mj_mk_mq_mr_executed']


def test_adopted_explanations_do_not_substitute_for_actual_causes():
    assert causal_checks()['combinations'] == 256


def test_causal_source_content_stays_quotable_without_asserting_its_truth():
    assert attribution_checks()['all_causal_and_motive_facts_left_unknown']


def test_existing_eleven_whole_unit_readings_are_preserved():
    assert structure()['preserved_review_meanings'] == 11
