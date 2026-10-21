from scripts.check_cognitive_acquisition import holding_checks,acquisition_checks,collective_checks,proof_checks,impossibility_checks,integrated_checks,structure_checks

def test_truth_acceptance_grasp_and_actual_ground_are_separate():
    r=holding_checks();assert len(r['independent_conditions'])==64 and r['unknown_rejected']
    assert sum(r['independent_conditions'].values())==1

def test_acquiring_understanding_and_grounds_is_more_than_truth_table_growth():
    r=acquisition_checks();assert r['new_tautological_content_can_be_learned']
    assert {n for n,v in r['native_individual_gain'].items() if v}=={'baseline','grasp_acquired','ground_acquired','loss_elsewhere'}

def test_birth_can_extend_cohort_cognition_without_counting_mere_replacement():
    r=collective_checks();assert r['same_level_replacement_is_not_expansion']
    assert {n for n,v in r['native_population_and_gain_with_holding_boundary'].items() if v}=={'individual','newborn_new_content'}

def test_actual_noema_proof_can_be_content_of_new_cognition():
    r=proof_checks();assert r['native_rre_content_as_new_cognition']=={'new_proof':[True,True,True],'invalid_proof':[False,False,True],
        'proof_without_grasp':[True,False,True],'proof_without_acceptance':[True,False,True]}

def test_possible_success_is_not_confused_with_guaranteed_success():
    r=impossibility_checks();assert not r['native_rjb_and_fixed_gain_arguments']['mixed_results']
    assert not r['native_rjb_and_fixed_gain_arguments']['empty_results']

def test_native_gain_connects_to_impossibility():
    r=integrated_checks();assert r['no_definition_boundaries']
    assert r['all_definitions_native']=={'baseline':False,'already_known':True}

def test_manuscript_and_pinned_definitions_are_preserved():
    r=structure_checks();assert r['preserved_manuscript_statements']==99
    assert r['new_definitions']==6 and r['new_primitives']==3
