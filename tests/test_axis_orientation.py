from scripts import check_axis_orientation as check


def test_orientation_distinguishes_parallel_signs_zero_and_acute_angles():
    result=check.numeric_checks();rows=result['cases']
    assert rows['positive_scale'] and rows['fractional_scale'] and rows['both_negative']
    assert not any(rows[n] for n in ('antiparallel','acute_nonparallel','orthogonal','zero_first','zero_second','both_zero'))
    assert result['invalid_component_rejected']


def test_orientation_is_independent_of_positive_scale_but_preserves_sign():
    rows=check.polynomial_checks()['claims']
    assert all(r['status']=='valid' for n,r in rows.items() if n!='orientation_implies_equal_length')
    assert rows['orientation_implies_equal_length']['status']=='invalid'


def test_all_three_source_axes_need_consistent_available_direction_records():
    rows=check.source_checks()['cases'][check.CORE]
    for n in ('antiparallel_x','antiparallel_y','antiparallel_z','zero_direction','missing_record','conflicting_record'):
        assert rows[n]==[True,False]
    assert rows['positive_rescale']==rows['alias_record']==[True,True]


def test_source_orientation_keeps_chart_unit_context_and_configuration_separate():
    result=check.source_checks();rows=result['cases'][check.CORE]
    for n in ('wrong_record_chart','wrong_record_unit','wrong_record_context','wrong_context','missing_axis_assignment','duplicate_role'):
        assert rows[n]==[True,False]
    assert rows['outside_bad_record']==[True,True]
    for n in ('missing_configuration','wrong_frame','wrong_speed'):assert rows[n]==[False,False]
    assert len(result['unknown_inputs_refused'])==2


def test_source_revision_preserves_prior_bindings_and_does_not_execute_quotation():
    result=check.structure_and_attribution()
    assert result['changed_arguments']==['frames'] and result['other_205_statements_unchanged']
    assert result['quoted_orientation_not_executed'] and result['old_quote_not_substituted']
