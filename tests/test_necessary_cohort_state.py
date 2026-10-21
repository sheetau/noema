from scripts.check_necessary_cohort_state import state_checks,method_binding_checks,necessity_checks,future_checks,content_checks,integrated_checks,structure_checks

def test_state_requires_all_nonempty_actual_contents():
    r=state_checks();assert r['unknown_rejected'] and r['native_content_evaluation']

def test_methods_keep_reference_candidate_and_start():
    assert method_binding_checks()['exact_method_and_result_arguments']

def test_necessity_is_conditional_but_has_an_actual_state_instance():
    r=necessity_checks();assert len(r['conditional_oracle'])==16
    assert sum(r['conditional_oracle'].values())==3 and r['unknown_rejected']

def test_future_state_is_of_same_later_cohort_after_same_agreement():
    r=future_checks();assert sum(r['same_agreement_later_epoch_and_condition'].values())==1

def test_six_exact_arguments_and_unexecuted_goal_quote():
    r=content_checks();assert sum(r['exact_six_bindings'].values())==1 and r['closed_quote_without_achievement']

def test_possible_gain_in_other_continuation_refutes_bound_impossibility():
    assert integrated_checks()['native_r5cw_with_same_available_methods_and_results']=={'False':True,'True':False}

def test_imported_meanings_and_main_assertions_preserved():
    r=structure_checks();assert r['new_definitions']==5 and r['new_primitives']==7 and r['preserved_manuscript_statements']==99
