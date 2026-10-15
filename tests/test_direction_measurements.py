from scripts import check_direction_measurements as check


def test_signed_displacement_preserves_order_and_validity():
    rows=check.numeric_checks()
    assert rows['cases']['negative'] and rows['cases']['fractional']
    assert not rows['cases']['wrong_sign'] and not rows['cases']['wrong_magnitude']
    assert rows['invalid_position_rejected']


def test_displacement_is_independent_of_common_origin_but_not_endpoint_order():
    rows=check.polynomial_checks()['claims']
    assert rows['common_origin_change_preserves_displacement']['status']=='valid'
    assert rows['swapping_endpoints_reverses_displacement']['status']=='valid'
    assert rows['change_only_head_preserves_displacement']['status']=='invalid'
    assert rows['unsigned_difference_is_sufficient']['status']=='invalid'


def test_direction_components_cannot_be_detached_from_selected_endpoint_records():
    rows=check.source_checks()['cases'][check.CORE]
    for n in ('forged_scale','extra_inconsistent_record','head_mismatch','tail_mismatch','same_endpoints','swapped_endpoints'):
        assert rows[n]==[True,False]
    for n in ('consistent_scale','common_origin_shift','different_origins','extra_consistent_record'):
        assert rows[n]==[True,True]


def test_positions_share_moment_chart_unit_context_and_keep_provenance():
    result=check.source_checks();rows=result['cases'][check.CORE]
    for n in ('missing_link','wrong_linked_order','point_outside_axis','missing_coordinates',
        'wrong_position_chart','wrong_position_unit','wrong_position_context','head_at_other_time'):
        assert rows[n]==[True,False]
    assert rows['later_observation']==[True,True]
    assert len(result['unknown_inputs_refused'])==2


def test_existing_configuration_and_unfiltered_record_scope_remain_required():
    result=check.source_checks();rows=result['cases'][check.CORE]
    assert result['original_record_set_preserved']
    for n in ('empty_axis_records','missing_configuration','wrong_frame','wrong_speed'):assert rows[n]==[False,False]


def test_endpoint_revision_keeps_old_bindings_and_quotation_boundary():
    result=check.structure_and_attribution()
    assert result['changed_arguments']==['frames'] and result['other_205_statements_unchanged']
    assert result['quoted_measurements_not_executed'] and result['old_quote_not_substituted']
