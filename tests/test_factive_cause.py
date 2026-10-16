from scripts import check_factive_cause as check


def test_causal_facts_and_factor_occurrence_are_checked_independently():
    assert check.checks()['five_condition_combinations']==32


def test_explanatory_adoption_cannot_substitute_for_actual_causality():
    rows=check.checks()['previous_and_revised']
    for name in ('adopted_but_no_cause','adopted_but_no_resolve_deficit','adopted_but_no_courage_deficit','excluded_factor_actually_causes'):
        assert rows[name]['previous_departure']==[True,True]
        assert rows[name]['revised'][:4]==[False]*4
    assert rows['actual_cause_not_adopted']['previous_departure']==[False,False]
    assert rows['actual_cause_not_adopted']['revised']==[True]*4+[False]


def test_excluding_a_cause_does_not_require_its_factor_to_be_absent():
    assert check.checks()['previous_and_revised']['excluded_factor_exists_without_causing']['revised']==[True]*5


def test_adoption_is_still_available_as_a_separate_relation():
    rows=check.checks()['independent_adoption_cases'];assert len(rows)==4
    assert all(row['values'][:4]==[True]*4 for row in rows)


def test_causal_direction_person_and_scene_cannot_be_swapped():
    for rows in check.checks()['role_contrasts'].values():
        assert rows['baseline']==[True]*5
        assert all(values==[False]*4+[True] for name,values in rows.items() if name!='baseline')


def test_existing_departure_checks_and_unknown_causality_are_preserved():
    result=check.checks();assert len(result['inherited_departure_contrasts'])==13
    assert result['unknown_causality_refused'] and result['unlowered_uncached_cases']==2


def test_source_specialization_preserves_the_quote_rank_boundary():
    assert check.rank_and_attribution()==dict(generic_requires_rank_one=True,specialized_source_remains_rank_zero=True,
        presentation_does_not_evaluate_causality=True)


def test_only_the_opening_causal_definition_is_revised():
    result=check.structure()
    assert result['changed_bodies']==['bd'] and result['statement_syntax_preserved']==16
    assert result['old_adoption_definitions_preserved'] and result['causal_condition_replaces_adoption_in_bd']
