from scripts.check_civic_oversight import realization_checks,universal_checks,oversight_checks,adapter_checks,structure_checks

def test_implementation_requires_same_activity_and_changed_content():
    assert not realization_checks()['same_change_activity_community_content_and_point']['other_activity']

def test_preventing_incompatible_implementation_can_preserve_order():
    assert universal_checks()['unimplemented_incompatible_proposal_new_then_old']==[True,False]

def test_oversight_requires_attention_effect_and_result():
    assert oversight_checks()['same_monarch_action_goal_attention_causal_contribution_and_result']['no_effect']==[True,False]

def test_goal_and_ruler_adapters_keep_exact_bindings():
    assert adapter_checks()['exact_goal_and_actor_bindings']['r5nh']==[0,1,2]

def test_prior_main_and_evidence_preserved_without_overstrong_condition():
    assert structure_checks()['previous_all_proposals_possible_claim_not_used']
