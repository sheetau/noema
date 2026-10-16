from scripts import check_density_origins as check


def cases(): return check.origin_checks()['cases'][check.CORE]


def test_same_zero_values_at_different_events_are_not_a_common_origin():
    rows = cases()
    assert rows['baseline'] == [True, True]
    assert rows['different_events_same_zero_values'] == [False, False]
    assert rows['second_event_is_common_witness'] == [False, True]


def test_all_eight_coordinates_and_zero_time_are_required():
    rows = cases()
    for frame in ('old', 'new'):
        for role in ('x', 'y', 'z', 't'): assert rows['nonzero_'+frame+'_'+role] == [False, False]
    for n in ('shifted_both_origins', 'shifted_both_times', 'moving_origin_at_later_time'):
        assert rows[n] == [False, False]


def test_origin_candidates_need_actual_assignment_and_placement():
    rows = cases()
    for frame in ('old', 'new'):
        for kind in ('assignment', 'placement'): assert rows['missing_'+frame+'_origin_'+kind] == [False, False]
    for n in ('missing_assignment', 'assignment_wrong_frame', 'assignment_wrong_context', 'wrong_supplied_context'):
        assert rows[n] == [False, False]


def test_valid_event_and_complete_valid_records_are_not_assumed():
    rows = cases()
    for n in ('not_an_event', 'invalid_oldrecord', 'invalid_newrecord', 'invalid_cut', 'duplicate_roles'):
        assert rows[n] == [False, False]
    assert len(check.origin_checks()['unknown_inputs_refused']) == 3


def test_existing_frame_condition_remains_necessary():
    rows = cases()
    for n in ('prior_frame_condition_false', 'wrong_supplied_frame', 'wrong_supplied_speed'):
        assert rows[n] == [True, False]
    assert len(check.origin_checks()['uncached']) == 8


def test_only_the_quoted_frame_argument_changes_without_new_primitives():
    result = check.structure_and_attribution()
    assert result['new_primitives'] == 0 and result['new_definitions'] == 2
    assert result['other_205_statements_unchanged'] and result['old_declarations_unchanged']
    assert result['core_equals_full_extraction'] and result['quoted_conditions_not_executed']
