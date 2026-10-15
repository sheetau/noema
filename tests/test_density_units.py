from scripts import check_density_units as check


def test_only_two_unit_references_change_in_the_actual_manuscript():
    result=check.structural_checks()
    assert result['changed_arguments']==['lengthunit','timeunit']
    assert result['declarations_identical'] and result['other_205_statements_identical']
    assert result['old_unit_references_unreachable_from_revised_statement']


def test_actual_density_and_total_adapters_receive_the_same_earlier_units():
    result=check.routing_checks()
    assert result['revised']==result['previous_with_explicit_aliases']
    assert result['previous']!=result['revised']
    assert not result['physical_density_law_evaluated']


def test_mixed_velocity_units_change_the_actual_normalization_guard():
    result=check.arithmetic_checks()
    assert result['rational_proofs']['common_positive_speed_scale']['status']=='valid'
    assert result['rational_proofs']['only_relative_speed_scaled']['status']=='invalid'
    rows=result['real_cut_guard_probes']
    assert rows['original']['guard'] and rows['consistent_new_units']['guard']
    assert not rows['mixed_units']['guard'] and not rows['mixed_units_negative_velocity']['guard']
    assert rows['zero_velocity']['guard']


def test_revised_unit_quote_is_attributed_without_executing_physics():
    result=check.attribution_checks()
    assert len(result['cases'])==8
    assert result['old_quote_not_automatically_substituted']
    assert not result['physical_content_evaluated']
