from scripts.check_institutional_outlook import improvement_checks,law_content_checks,target_checks,attitude_checks,connection_checks,structure_checks

def test_better_is_strict_and_concerns_the_same_public_law_and_community():
    r=improvement_checks();assert len(r['strict_comparison'])==16
    assert sum(x['value'] for x in r['strict_comparison'])==1
    assert not any(r['same_public_law_and_frame'].values())

def test_better_law_contains_all_operative_clauses_for_the_complete_people():
    r=law_content_checks();assert r['no_definition_boundaries']
    assert len(r['complete_people_and_all_three_operative_clauses'])==8
    assert sum(x['value'] for x in r['complete_people_and_all_three_operative_clauses'])==1

def test_typed_targets_preserve_bindings_and_distinguish_future_from_introduction():
    r=target_checks();assert r['r5fk']['points']==[False,False,True,True,False]
    assert r['r5fl']['points']==[False,True,True,True,False]
    assert len(r['r5fl']['permutations'])==6

def test_attitudes_do_not_assert_their_targets_or_switch_contexts():
    r=attitude_checks();assert len(r['independent_aim_and_expectation'])==4
    assert len(r['seven_argument_positions'])==14 and r['targets_not_executed']
    assert r['wrong_quoted_target_rejected']

def test_same_introduction_requires_its_purpose_without_literal_expectation():
    r=connection_checks();assert len(r['same_actual_introduction_aim_and_until'])==8
    assert sum(x['values'][1] for x in r['same_actual_introduction_aim_and_until'])==1
    assert r['expectation_and_improvement_not_asserted']

def test_preserved_imports_and_no_unreviewed_main_statement():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'])==(7,3)
    assert r['no_manuscript_mutation']
