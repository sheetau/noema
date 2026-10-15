from scripts import check_positive_axis_calibration as check


def test_positive_order_is_not_positive_values_or_a_parallel_offset_line():
    rows=check.numeric_checks()
    assert rows['cases']['negative_coordinate_values_increase'] and rows['cases']['both_endpoints_on_negative_half']
    assert not rows['cases']['positive_coordinate_values_decrease']
    assert not rows['cases']['parallel_offset_line'] and not rows['cases']['head_off_axis']
    assert rows['duplicate_roles_rejected'] and rows['invalid_component_rejected']


def test_positive_affine_change_preserves_the_axial_coordinate_order():
    rows=check.polynomial_checks()['claims']
    assert rows['positive_affine_coordinate_change_preserves_order']['status']=='valid'
    assert rows['reverse_order_cannot_also_increase']['status']=='valid'
    assert rows['positive_values_imply_positive_order']['status']=='invalid'


def test_common_orientation_cannot_substitute_for_own_axis_calibration():
    rows=check.source_checks()['cases'][check.CORE]
    for n in ('own_reversed_x','own_reversed_y','own_reversed_z','common_reversed_y','own_zero_y','own_swapped_roles'):
        assert rows[n]==[True,False]
    assert rows['own_positive_scale']==rows['different_origins']==[True,True]


def test_own_frame_coordinates_must_be_available_in_the_same_record_context():
    result=check.source_checks();rows=result['cases'][check.CORE]
    for n in ('missing_own_coordinates','own_wrong_unit','own_wrong_context','own_wrong_time','invalid_own_frame'):
        assert rows[n]==[True,False]
    assert len(result['unknown_inputs_refused'])==2


def test_calibration_retains_all_records_and_previous_displacement_constraints():
    rows=check.source_checks()['cases'][check.CORE]
    assert rows['extra_consistent_record']==[True,True]
    for n in ('missing_configuration','wrong_frame','wrong_speed','head_mismatch','empty_axis_records'):assert rows[n]==[False,False]
    assert rows['own_offset_axes']==rows['own_head_off_axis']==[True,False]


def test_calibration_adds_no_primitives_and_preserves_the_quotation_boundary():
    result=check.structure_and_attribution()
    assert result['new_primitives']==0 and result['other_205_statements_unchanged']
    assert result['extracted_core_equals_actual_full_statement_dependencies']
    assert result['quoted_calibration_not_executed'] and result['old_quote_not_substituted']
