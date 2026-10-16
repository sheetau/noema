from scripts import check_described_transition as check


def test_event_content_and_actual_endpoints_are_required_together():
    assert check.checks()['five_condition_combinations']==32


def test_coinciding_unrelated_property_changes_are_not_the_opening_departure():
    rows=check.checks()['old_counterexamples']
    assert len(rows)==10
    for row in rows.values():assert row==dict(previous=[True,True],revised=[False,False])


def test_before_after_roles_and_exact_subject_process_endpoints_are_retained():
    for rows in check.checks()['content_contrasts'].values():
        assert rows['baseline']==[True,True]
        for name in ('reversed_properties','weaker_before_property','other_person','other_process','other_start','other_end'):
            assert rows[name]==[False,False]


def test_same_truth_values_do_not_replace_the_description_of_a_process():
    assert check.checks()['equivalent_aliases_require_their_own_record']==[True,True,True]
    for rows in check.checks()['content_contrasts'].values():assert rows['equivalent_alias_record']==[False,False]


def test_prior_subject_and_ability_guards_and_unknown_input_are_preserved():
    result=check.checks()
    assert len(result['inherited_contrasts'])==14
    assert all(values==[False,False] for values in result['inherited_contrasts'].values())
    assert result['unknown_content_refused'] and result['unlowered_uncached_cases']==2


def test_source_and_library_share_the_revised_definition_and_existing_state_descriptions():
    result=check.structure()
    assert result['new_primitives']==['hzid'] and result['new_definitions']==0
    assert result['changed_bodies']==['be'] and result['unchanged_statement_syntax']==16
    assert {'be','bi','cp','hzic'}<=set(result['dependent_definitions'])


def test_presenting_the_definition_does_not_assert_an_actual_transition():
    assert check.attribution()==dict(same_revised_bi_in_question_and_answer=True,transition_content_not_executed=True)
