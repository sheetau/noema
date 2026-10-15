from scripts import check_density_frame_binding as check


def test_named_frame_pair_and_signed_velocity_reject_unrelated_configurations():
    rows=check.source_checks()['cases'][check.CORE]
    assert rows['baseline']==[True,True]
    for name in ('other_first','other_second','reversed','reversed_and_negated','wrong_magnitude','negated_speed','same_frame_references'):
        assert rows[name]==[True,False]


def test_reference_binding_does_not_invent_configuration_or_replace_context():
    result=check.source_checks();rows=result['cases'][check.CORE]
    assert rows['missing_configuration']==[False,False]
    assert rows['other_context']==[False,False]
    assert rows['zero_velocity']==[True,True]
    assert len(result['unknown_inputs_refused'])==2
    assert result['caller_context_preserved']


def test_generic_binding_permits_explicit_inverse_and_non_frame_relations():
    rows=check.generic_checks()['cases']
    assert not rows['reversed'] and rows['explicit_inverse']
    assert rows['same_reference_allowed_generically']
    assert not rows['invalid_values'] and not rows['missing_relation']


def test_only_frame_argument_changes_and_coordinate_units_stay_connected():
    result=check.structural_checks()
    assert result['changed_arguments']==['frames']
    assert result['new_primitives']==0
    assert result['coordinate_unit_fix_preserved']
    assert result['physical_configuration_predicate_retained']


def test_attribution_preserves_description_identity_without_running_configuration():
    result=check.attribution_checks()
    assert len(result['cases'])==8 and result['old_quote_not_substituted']
    assert result['configuration_and_velocity_not_executed']
