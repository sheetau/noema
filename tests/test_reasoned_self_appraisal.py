from scripts.check_reasoned_self_appraisal import generic_checks,source_checks,goal_checks,change_checks,unknown_checks,structure


def test_reason_and_support_belong_to_the_same_judgment():
    assert generic_checks()['four_relation_combinations']==16


def test_self_appraisal_and_assent_do_not_assert_the_norm_or_execute_thinking():
    assert source_checks()['each_person_bound_to_own_task']


def test_the_task_requires_the_same_persons_independent_reasoned_judgment():
    assert goal_checks()['source_thinking_definition_executed']


def test_acquisition_and_cause_use_the_same_constructed_state():
    assert change_checks()['self_approval_wrapper_not_used']


def test_unknown_judgment_valuation_assent_and_norms_are_not_false():
    assert unknown_checks()['unknown_inputs_refused']==9


def test_prior_meanings_statements_and_reviews_are_preserved():
    assert structure()['independent_thinking_body_reused_exactly']
