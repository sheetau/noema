from scripts.check_protective_petition import native_effect_checks,selected_policy_checks,binding_checks,petition_checks,structure_checks


def test_native_causal_protection_nonhindrance_and_actual_observations():
    r=native_effect_checks();assert r['native_definitions_without_boundaries']
    assert r['native_protection_and_nonhindrance']['impossible']==[False,True]
    assert r['native_protection_and_nonhindrance']['false_activity']==[False,False]


def test_all_anchored_selected_congregations_keep_their_same_configuration():
    r=selected_policy_checks();assert sum(r['all_selected_congregations_and_configurations'].values())==6
    assert r['selection_held_at_anchor_not_outcome']


def test_exact_policy_and_community_binding():
    r=binding_checks();assert len(r['exact_policy_and_community'])==4 and r['wrong_lengths_rejected']


def test_joint_petition_does_not_execute_unknown_policy_and_protection():
    r=petition_checks();assert sum(r['shared_quoted_protective_petition'].values())==2
    assert r['policy_models_and_effects_not_executed'] and r['native_joint_proposal_and_ability']


def test_preserved_meanings_reports_and_manuscript():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(6,9,102)
