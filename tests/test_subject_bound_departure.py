from scripts import check_subject_bound_departure as check


def test_departure_requires_transition_subject_initial_state_and_final_ability():
    rows=check.checks()['four_condition_combinations']
    assert len(rows)==16
    for row in rows:assert row['values']==[all(row['bits'])]*2


def test_previously_accepted_unrelated_processes_are_rejected():
    rows=check.checks()['old_counterexamples']
    assert len(rows)==7
    for row in rows.values():assert row==dict(previous=[True,True],revised=[False,False])


def test_person_process_and_both_endpoints_are_bound_together():
    for rows in check.checks()['contrasts'].values():
        assert rows['baseline']==[True,True]
        for name in ('different_person','different_process','different_start','different_end','witness_only','cause_only'):
            assert rows[name]==[False,False]


def test_missing_assessment_is_not_a_successful_exit():
    for rows in check.checks()['contrasts'].values():
        for name in ('empty_final_assessment','foreign_final_assessment','unknown_initial_assessment','still_guided',
                'no_available_method','absent_cause_explanation','reversed_transition'):
            assert rows[name]==[False,False]
    assert check.checks()['unknown_subject_refused']
    assert check.checks()['unlowered_uncached_cases']==2


def test_revised_meaning_is_connected_to_title_and_opening_without_new_primitives():
    result=check.structure()
    assert result['new_declarations']==0 and result['changed_definition_bodies']==['be']
    assert result['unchanged_statement_syntax']==16
    assert {'be','bi','cp','hzic'}<=set(result['new_subject_dependencies'])


def test_title_can_present_the_revised_content_without_asserting_its_truth():
    assert check.attribution()==dict(same_bi_in_question_and_answer=True,underlying_content_not_executed=True)
