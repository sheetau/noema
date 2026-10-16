from scripts import check_causal_outcome_contrast as check


def test_occurrence_causation_and_result_truth_are_separate_conditions():
    result=check.checks()
    assert result['truth_cases']==128
    assert result['actual_rfk_executed']


def test_negative_scope_covers_a_second_activity_and_a_second_outcome():
    rows=check.checks()['contrasts'][check.CORE]
    assert rows['baseline']==[True,True,True,False,True]
    assert rows['second_activity']==rows['second_outcome']==[True,False,False,False,False]


def test_excluded_causal_result_is_not_a_globally_impossible_state():
    rows=check.checks()['contrasts'][check.CORE]
    for name in ('other_activity','right_true_only','same_truth_different_description','right_cause_no_occurrence'):
        assert rows[name]==[True,True,True,False,True]


def test_activity_target_description_and_candidate_are_not_mixed():
    rows=check.checks()['contrasts'][check.CORE]
    for name in ('wrong_causal_activity','wrong_target','wrong_description','split_cause','split_occurrence','cooccurrence_only','wrong_anchor'):
        assert rows[name]==[False,True,False,False,False]


def test_actuality_empty_kinds_and_swapped_results_have_distinct_effects():
    rows=check.checks()['contrasts'][check.CORE]
    assert rows['actual_only']==[False,True,False,True,False]
    assert rows['empty_kind']==rows['empty_candidates']==[False,True,False,False,False]
    assert rows['same_effect']==[True,False,False,False,False]
    assert rows['swapped']==[False,False,False,False,False]


def test_unknown_interpretations_are_not_false_and_eager_evaluation_agrees():
    result=check.checks()
    assert len(result['unknown_inputs_refused'])==4
    assert result['unlowered_uncached_examples']==3


def test_only_composed_definitions_are_added_without_author_assertions():
    result=check.structure()
    assert result['new_definitions']==4 and result['new_primitives']==result['new_assertions']==0
    assert result['previous_15_statements_unchanged']
