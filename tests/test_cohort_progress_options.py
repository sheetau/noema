from scripts.check_cohort_progress_options import enlightenment_checks,union_checks,frame_checks,impossibility_checks,integrated_checks,structure_checks

def test_progress_is_within_same_cohort_including_new_generation():
    r=enlightenment_checks();assert r['unknown_rejected']
    assert {n for n,v in r['native_cohort_and_individual_or_collective_progress'].items() if v}=={'partial_gain','new_generation'}

def test_any_of_three_gains_is_progress():
    r=union_checks();assert len(r['three_way_disjunction'])==8
    assert sum(r['three_way_disjunction'].values())==7

def test_missing_invalid_or_changed_initial_continuation_cannot_prove_inability():
    r=frame_checks();assert r['unknown_rejected']
    assert {n for n,v in r['all_results_all_continuations_validated'].items() if v}=={'baseline','no_methods','mixed_results','two_methods'}

def test_different_method_or_unguaranteed_success_refutes_inability():
    r=impossibility_checks();assert sum(r['no_kind_of_possible_progress'].values())==1
    assert not r['method_result_branch_binding']['mixed_results'] and not r['method_result_branch_binding']['two_methods']
    assert r['method_result_branch_binding']['unselected_continuation']

def test_native_cognition_in_other_continuation_is_not_lost():
    r=integrated_checks();assert r['native_acquisition_correction_and_modal_binding']
    assert r['native_different_continuation_and_old_fixed_history_contrast']=={'baseline':[False,True],'already_known':[True,True]}

def test_no_author_assertions_or_pinned_meanings_changed():
    r=structure_checks();assert r['preserved_manuscript_statements']==99
    assert r['new_definitions']==7 and r['new_primitives']==1
