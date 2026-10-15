from scripts import check_material_acceleration as check


def test_acceleration_requires_history_and_an_actual_velocity_field():
    rows=check.acceleration_checks()['cases']
    assert rows['baseline'] and rows['initial_rest'] and rows['uniform']
    assert not rows['fake_velocity_field']
    assert not rows['sample_alias_field']


def test_same_target_event_frames_units_and_record_in_actual_source_constructor():
    rows=check.law_checks()
    assert len(rows)==3


def test_actual_field_law_rejects_a_function_only_matching_at_the_center():
    rows=check.field_probe_checks()['cases']
    assert rows['fake_velocity_field:0'] and not rows['fake_velocity_field:1']
    assert all(rows['sample_alias_field:'+str(n)] for n in (-2,-1,0,1,2))
    assert not rows['sample_alias_field:1/2']


def test_full_domains_and_unknown_functions_are_not_inferred_by_sampling():
    assert len(check.refusal_checks())==8
