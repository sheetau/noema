from scripts import check_targeted_adequacy as check


def test_two_goals_can_have_independent_assessments_without_goal_execution():
    result=check.goal_assessment_checks()
    assert result['two_goal_three_assessment_combinations']==64 and result['goals_not_evaluated']


def test_same_goal_deficits_and_actual_causation_are_both_required():
    assert check.checks()['condition_combinations']==32


def test_deficits_for_another_goal_cannot_establish_the_source_condition():
    rows=check.checks()['previous_and_revised']
    for name in ('old_resolve_refers_to_another_goal','old_courage_refers_to_another_goal','old_understanding_refers_to_another_goal'):
        assert rows[name]==dict(previous=[True,True],revised=[False]*4)
    assert rows['actual_deficits_despite_other_goal_adequacy']==dict(previous=[False,False],revised=[True]*4)


def test_legacy_assessments_do_not_control_explicit_target_assessments():
    assert len(check.checks()['independent_legacy_assessments'])==8


def test_missing_assessments_are_not_treated_as_negative_assessments():
    assert len(check.checks()['unknown_evidence_refused'])==4


def test_causal_descriptions_and_departure_subject_remain_bound():
    result=check.checks()
    for rows in result['cause_contrasts'].values():
        assert rows['baseline']==[True]*4
        assert all(v==[False]*4 for n,v in rows.items() if n!='baseline')
    assert len(result['inherited_departure_contrasts'])==6 and result['unlowered_uncached_cases']==2


def test_only_opening_condition_changes_and_signature_is_preserved():
    result=check.structure()
    assert result['changed_bodies']==['bd'] and result['statement_syntax_preserved']==17
    assert result['signature_dependency_declarations_and_conventions_unchanged'] and result['identifier_forms_unchanged']


def test_source_presentation_does_not_require_actual_resolve_courage_or_success():
    assert check.attribution()==dict(source_condition_rank_zero=True,definition_presentation_does_not_evaluate_assessments=True,
        opening_three_definition_descriptions=['bi','bf','bp'])
