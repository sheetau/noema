from scripts.check_cohort_covenant_purpose import cause_checks,binding_checks,declaration_checks,formation_checks,integrated_checks,structure_checks

def test_causal_success_needs_same_cause_and_actual_result():
    r=cause_checks();assert sum(r['causation_and_actual_result'].values())==1 and r['unknown_rejected']

def test_goal_terms_and_policy_preserve_each_position_and_length():
    r=binding_checks();assert [len(r['position_matrices'][n]) for n in ('r5c5','r5c6','r5db')]==[36,49,36]
    assert [sum(r['position_matrices'][n]) for n in ('r5c5','r5c6','r5db')]==[6,7,6]

def test_same_mutual_oath_act_adopts_same_goal():
    r=declaration_checks();assert r['quote_contents_not_required']
    assert not r['native_mutual_oath_and_same_act_purpose']['different_act']

def test_all_actual_parties_adopt_the_goal_without_its_achievement():
    r=formation_checks();assert r['unknown_rejected'] and r['unrealized_goal_terms_and_deity_allowed']
    assert sum(r['all_parties_same_terms_and_purpose'].values())==1

def test_complete_native_formation_and_closed_policy_quote():
    r=integrated_checks();assert r['no_definition_boundaries'] and r['closed_policy_quote_not_executed']
    assert r['native_frame_formation_oath_and_purpose']=={'baseline':True,'missing_purpose':False,'missing_mutual':False}

def test_imported_meanings_and_manuscript_unchanged():
    r=structure_checks();assert r['new_definitions']==6 and r['new_primitives']==4 and r['preserved_manuscript_statements']==99
