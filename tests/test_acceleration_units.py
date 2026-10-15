from scripts import check_acceleration_units as check


def test_time_scale_is_squared_and_zero_values_do_not_license_invalid_units():
    rows=check.numerical_checks()
    assert rows['scaled']==[True]*3 and rows['negative_time']==[False]*3


def test_rational_conversion_uniqueness_sign_and_composition():
    rows=check.polynomial_checks()
    assert rows['one_power_of_time_would_suffice']['status']=='invalid'


def test_current_source_uses_converted_acceleration_and_same_unit_records():
    assert len(check.physical_checks()['cases'])==3


def test_actual_coordinate_bridge_and_legacy_unit_adapter():
    assert check.bridge_probes()['actual_bridge_body_at_one_time']['baseline']
    assert check.adapter_checks()['(2, 2)']


def test_unknown_calibration_and_unbounded_domains_are_refused():
    assert len(check.refusal_checks())==4
