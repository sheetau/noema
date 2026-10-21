from scripts.check_cognitive_correction import error_checks,judgment_checks,correction_checks,collective_checks,impossibility_checks,integrated_checks,structure_checks

def test_error_is_accepted_false_content_at_fixed_assessment():
    r=error_checks();assert {n for n,v in r['native_accepted_false_content'].items() if v}=={'baseline','alias_before'}

def test_rejection_uses_same_person_content_judgment_and_support():
    r=judgment_checks();assert r['judgment_does_not_execute_its_content']
    assert {n for n,v in r['native_ya_and_same_negative_content'].items() if v}=={'baseline'}

def test_correction_is_not_forgetting_alias_deletion_or_population_change():
    r=correction_checks();assert r['unknown_rejected']
    assert {n for n,v in r['native_correction_contrasts'].items() if v}=={'baseline','alias_before','at_end','other_error_gained'}

def test_partial_member_correction_requires_same_group_and_valid_time():
    r=collective_checks();assert r['unanimous_revision_not_required']
    assert r['native_single_member_correction_with_valid_history']=={'baseline':True,'outsider':False,'cycle':False,'alias_retained':False}

def test_possible_success_refutes_inability_even_if_not_guaranteed():
    r=impossibility_checks();assert len(r['possible_success_table'])==8
    assert not r['possible_success_table']['(True, False, True)']
    assert not r['binding_contrasts']['empty_results']

def test_native_inability_executes_the_same_correction_goal():
    r=integrated_checks();assert r['no_definition_boundaries']
    assert r['native_cohort_correction_through_rjb']=={'baseline':False,'unsupported':True}

def test_manuscript_and_prior_evidence_are_unchanged():
    r=structure_checks();assert r['preserved_manuscript_statements']==99
    assert r['new_definitions']==8 and r['new_primitives']==4
