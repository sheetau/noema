from scripts import check_force_mass_units as check


def test_independent_scales_and_signed_values():
    rows=check.numerical_checks()
    assert rows['scaled']==[True]*3 and rows['mass_reading_only']==[False]*3


def test_coherent_units_and_preserved_physical_mass():
    rows=check.polynomial_checks()
    assert rows['mass_number_alone_always_determines_coefficients']['status']=='invalid'


def test_same_target_mass_and_unit_records_in_the_source_constructor():
    assert len(check.physical_checks()['cases'])==3


def test_missing_assignment_and_calibration_are_not_invented():
    assert len(check.refusal_checks())==4
