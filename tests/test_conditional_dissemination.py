from scripts.check_conditional_dissemination import generic_checks,native_checks,attribution_and_unknown_checks,structure


def test_candidate_condition_content_and_origin_bindings():
    assert generic_checks()['candidate_condition_truth_and_origin_combinations']==256


def test_native_permission_and_dissemination_inside_same_hypotheses():
    assert native_checks()['actual_freedom_not_inferred']


def test_attribution_and_unknown_inputs_remain_separate():
    assert attribution_and_unknown_checks()['selected_condition_or_content_unknowns_refused']==4


def test_existing_manuscript_meanings_and_reviews_are_preserved():
    assert structure()['existing_statements']==33
