from scripts.check_rational_self_imposition import scope_checks,permission_checks,possibility_checks,binding_checks,question_checks,structure_checks

def test_counterfactual_scope_does_not_presuppose_permission_or_success():
    r=scope_checks();assert sum(r['candidates_independent_of_conclusion'].values())==3
    assert r['permission_and_enactment_not_evaluated']

def test_permission_requires_exact_positive_norm_without_conflict():
    r=permission_checks();assert sum(r['positive_permission_without_opposite_requirement'].values())==1
    assert not any(r['exact_normative_tuple'].values()) and r['quoted_enactment_not_executed']

def test_native_possibility_requires_one_shared_candidate():
    r=possibility_checks();assert sum(r['native_same_candidate_possibility'].values())==4
    assert not r['native_same_candidate_possibility']['split_witness'] and r['no_definition_boundaries']

def test_all_three_argument_positions_and_lengths():
    r=binding_checks();assert len(r['exact_three_positions'])==9 and sum(r['exact_three_positions'])==3
    assert r['wrong_lengths_rejected']

def test_question_force_and_unevaluated_quotation():
    r=question_checks();assert r['question_differs_from_assertion']=={'False':[False,False],'True':[False,True]}
    assert r['quoted_question_does_not_evaluate_unknown_possibility']

def test_preserve_prior_meanings_and_main_manuscript():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(6,3,101)
