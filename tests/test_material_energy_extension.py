from scripts import check_material_energy_extension as check


def test_energy_readings_change_coherently_with_each_unit():
    rows = check.numerical_checks()
    assert rows['speed_unit_rescaled'] == [True]*3
    assert rows['energy_unit_rescaled'] == [True]*3
    assert rows['ignores_unit_scales'] == [False]*3
    proofs = check.polynomial_checks()
    assert proofs['same_light_and_speed_under_new_unit']['status'] == 'valid'
    assert proofs['raw_numbers_always_obey_unscaled_expression']['status'] == 'invalid'


def test_all_materials_cases_and_quantity_owners_are_preserved():
    report = check.scope_checks()
    rows = report['cases'][check.CORE]
    assert rows['bad_second'] == [True, False]
    assert rows['valid_second_event'] == [True, True]
    assert rows['bad_second_event'] == [True, False]
    assert rows['wrong_light_value'] == [True, False]
    assert rows['wrong_kinetic_frame'] == [False, False]
    assert report['unknown_assignment_refused']
    assert not report['existence_of_materials_or_cases_inferred']


def test_previous_charging_argument_is_quoted_not_executed_as_proof():
    result = check.attribution_check()
    assert result['quoted_targets'] == [['claim', 'seti'], ['reason', 'seqw', 'seti']]
    assert not result['energy_law_derived_from_charge_capability']
