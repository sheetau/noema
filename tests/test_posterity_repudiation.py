from scripts.check_posterity_repudiation import refusal_checks,scope_checks,norm_checks,universal_checks,binding_checks,integrated_checks,structure_checks

def test_repudiation_is_an_actual_same_target_negative_response():
    r=refusal_checks();assert sum(r['native_refusal_contrasts'].values())==1
    assert r['acceptance_truth_not_evaluated'] and r['native_existential_response']

def test_posterity_includes_further_epochs_and_survivors():
    r=scope_checks();assert sum(r['native_three_epoch_scope'].values())==2
    assert r['earlier_survivor_included'] and r['unknown_rejected']

def test_entitlement_is_positive_permission_without_opposition():
    r=norm_checks();assert sum(r['permission_and_opposition'].values())==1
    assert not any(r['exact_target_contrasts'].values()) and r['quoted_refusal_not_executed']

def test_each_resolution_and_each_later_person_is_covered():
    r=universal_checks();assert sum(r['all_people_decisions_and_points'].values())==3

def test_three_and_six_argument_positions_and_lengths():
    r=binding_checks();assert [(len(m),sum(m)) for m in r['exact_position_matrices'].values()]==[(9,3),(9,3),(36,6)]

def test_native_temporal_scope_and_entitlement_are_connected():
    r=integrated_checks();assert sum(r['native_three_epochs_and_rdu'].values())==1 and r['refusal_not_executed']

def test_prior_meanings_and_all_100_assertions_are_preserved():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(7,4,100)
