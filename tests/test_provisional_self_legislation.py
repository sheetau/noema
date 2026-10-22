from scripts.check_provisional_self_legislation import possibility_checks,integration_checks,binding_checks,depiction_checks,structure_checks


def test_permission_and_short_order_use_one_possible_candidate():
    r=possibility_checks();assert sum(r['same_candidate_existential_possibility'].values())==3
    assert sum(r['positive_permission_without_conflict'].values())==1


def test_native_self_adoption_preserves_period_purpose_and_first_endpoint():
    r=integration_checks();assert sum(r['native_self_adoption_short_period_purpose_and_until'].values())==1
    assert not any(r['exact_sixteen_arguments'].values())


def test_modal_reference_and_depiction_adapters_keep_same_targets():
    r=binding_checks();assert set(r['exact_ten_object_binding'])=={'r5gu','r5gv','r5gw','r5gx'}
    assert r['wrong_lengths_rejected']


def test_figurative_depiction_and_possibility_do_not_execute_quoted_world():
    r=depiction_checks();assert r['literal_expectation_truth_table']=={'False':False,'True':True}
    assert r['possibility_and_depiction_can_be_quoted_with_unknown_world']


def test_preserved_meanings_manuscript_and_separation():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(6,0,102)
    assert r['no_literal_expectation_in_world']
