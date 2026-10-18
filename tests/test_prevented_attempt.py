from scripts.check_prevented_attempt import causal_checks,temporal_checks,attribution_checks,structure


def test_nonattempt_requires_a_shared_actual_cause_not_just_absence():
    result=causal_checks()
    assert result['combinations']==32 and result['unknown_inputs_refused']==4


def test_both_stages_precede_the_warning_without_an_added_internal_order():
    result=temporal_checks()
    assert result['cases']['simultaneous']==[True,True,False]
    assert result['cases']['reverse_prefix']==[True,True,False]


def test_attribution_does_not_execute_the_warning_or_assert_its_truth():
    assert attribution_checks()['all_world_and_model_inputs_unknown']


def test_the_active_clause_has_no_causal_equation_model_dependency():
    result=structure()
    assert result['causal_equation_model_not_required'] and result['nine_review_bindings_preserved']
