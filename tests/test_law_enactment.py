from scripts.check_law_enactment import scope_checks,provision_checks,enactment_checks,self_checks,binding_checks,structure_checks

def test_complete_people_and_nonempty_law_without_enactment():
    r=scope_checks();assert sum(r['complete_nonempty_people_and_law'].values())==1 and r['clause_states_not_evaluated']

def test_all_normative_clauses_at_one_point_without_performance():
    r=provision_checks();assert sum(r['all_three_distinct_normative_clauses'].values())==1
    assert r['target_actions_not_executed'] and r['inner_three_positions_checked']

def test_same_enactment_can_establish_or_confirm_existing_rules():
    r=enactment_checks();assert sum(r['native_same_act_actor_people_and_legal_effect'].values())==2 and r['no_required_prior_absence']

def test_self_imposition_uses_same_people_as_actor_and_addressee():
    r=self_checks();assert r['native_self_imposition_and_complete_history']['people']==[False,True]
    assert r['native_self_imposition_and_complete_history']['actor']==[True,False] and r['no_definition_boundaries']

def test_outer_three_positions_and_fixed_reference():
    r=binding_checks();assert all(len(m)==9 and sum(m)==3 for m in r['exact_outer_three_positions'].values())

def test_prior_meanings_and_101_assertions_preserved():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(7,6,101)
