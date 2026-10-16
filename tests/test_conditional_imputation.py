from scripts import check_conditional_imputation as check


def test_causal_criterion_and_imputation_are_independent():
    assert len(check.checks()['direction_combinations'])==4


def test_one_way_condition_does_not_impose_the_reverse():
    row=next(r for r in check.checks()['direction_combinations'] if not r['criterion'] and r['imputed'])
    assert row['revised']==[False,True,True,True,True,True,False]
    assert row['previous_departure']==[False,False]


def test_causation_alone_is_not_self_imputation_or_departure():
    row=next(r for r in check.checks()['direction_combinations'] if r['criterion'] and not r['imputed'])
    assert row['revised']==[True,False,False,False,False,False,False]
    assert row['previous_departure']==[True,True]


def test_the_causal_condition_retains_all_five_conditions():
    assert check.checks()['causal_combinations_preserved']==32


def test_imputation_requires_same_person_state_and_scene_and_actual_state():
    result=check.checks()
    assert all(rows['no_initial_state']==[False]*5+[True,True] for rows in result['imputation_contrasts'].values())
    assert result['unknown_imputation_refused']


def test_the_condition_checks_another_person_too():
    rows=check.second_person()
    assert len(rows)==4
    assert next(r['values'] for r in rows if r['other_cause'] and not r['other_imputation'])==[False,False]


def test_presented_condition_is_not_silently_replaced_by_equivalence():
    result=check.presentation()
    assert result['cases']['baseline']==[True] and result['cases']['equivalence_instead']==[False]
    assert result['underlying_causality_and_imputation_not_evaluated']


def test_scope_rank_and_signature_are_preserved():
    result=check.structure()
    assert result['changed_bodies']==['bp','be','cp'] and result['statement_syntax_preserved']==17
    assert result['signature_dependencies_and_forms_unchanged'] and result['source_rank_zero_preserved']
