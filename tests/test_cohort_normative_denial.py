from scripts.check_cohort_normative_denial import norm_checks,scope_checks,universal_checks,binding_checks,integrated_checks,structure_checks

def test_entitlement_requires_permission_without_opposition():
    r=norm_checks();assert sum(r['permission_and_opposition'].values())==1 and r['unknown_rejected']
    assert r['exact_normative_target']['positive_requirement']

def test_scope_does_not_require_formation_or_achievement():
    r=scope_checks();assert sum(r['native_epoch_and_prospective_scope'].values())==1 and r['unknown_rejected']

def test_denial_covers_all_eligible_six_tuples():
    r=universal_checks();assert len(r['two_candidate_oracle'])==16
    assert r['counterexample_in_each_position']==[False]*6

def test_scope_and_entitlement_adapters_preserve_exact_six_positions():
    r=binding_checks();assert all(len(m)==36 and sum(m)==6 for m in r['position_matrices'].values())

def test_native_scope_and_norms_allow_unknown_formation_and_goal():
    r=integrated_checks();assert r['no_definition_boundaries'] and r['unknown_formation_and_goal_allowed']
    assert r['all_new_definitions_and_epoch_scope_native']=={'baseline':True,'allowed':False,'conflicted':True,'no_proposals':True}

def test_prior_meanings_and_manuscript_are_preserved():
    r=structure_checks();assert r['new_definitions']==6 and r['new_primitives']==3 and r['preserved_manuscript_statements']==99
