from scripts import check_intellectual_credit as check


def test_credit_is_separate_from_actual_contribution():
    rows=check.source_checks()['cases']
    assert rows['baseline']==[True,True,True,True,True]
    assert rows['misattributed']==[True,True,False,True,False]
    for name in ('no_event','wrong_giver','different_input','unused','wrong_work','wrong_recipient'):
        assert rows[name]==[False,False,False,True,False]


def test_plural_inputs_are_not_duplicate_judgment_records():
    rows=check.source_checks()['cases']
    assert rows['three_inputs'][0] is True
    for name in ('duplicate_input','one_input','bad_second'):
        assert rows[name][:2]==[False,False]


def test_judgment_keeps_description_subject_bindings_and_nonempty_candidates():
    rows=check.source_checks()['cases']
    for name in ('empty_candidates','different_description','reordered_bindings','wrong_subject','bad_candidate','no_standard'):
        assert rows[name][:2]==[False,False]
    assert check.source_checks()['unknown_occurrence_refused']


def test_four_place_adapter_preserves_order_length_and_repeated_individuals():
    result=check.adapter_checks()
    assert result['ordered']==[True,False,False,False,False]
    assert result['repeated']==[False,False,False,False,True]


def test_attribution_does_not_run_the_quoted_credit_claim():
    result=check.attribution_check()
    assert result['quoted_targets']==['sewl']
    assert result['credit_claim_evaluated'] is False
