from scripts import check_deflection_ratio as check


def test_equal_strength_is_not_equal_signed_acceleration():
    rows = check.numeric_checks()
    assert rows['comparison']['balanced'] == [True,True]*3
    assert rows['comparison']['wrong_magnetic_sign'] == [False,True]*3
    assert rows['response']['zero_denominator'] == [False,False]*3
    assert rows['inverse_values']['unequal_calibration_misleads'] == '3/2'


def test_ratio_has_a_unique_speed_only_with_nonzero_electric_response():
    rows = check.polynomial_checks()
    assert rows['ratio_identifies_unique_speed']['status'] == 'valid'
    assert rows['equal_strength_means_same_signed_acceleration']['status'] == 'invalid'
    assert rows['zero_field_observation_determines_zero_speed']['status'] == 'invalid'


def test_source_contents_share_charge_velocity_and_response_values():
    rows = check.source_checks()['cases'][check.CORE]
    assert rows['negative_charge'] == [True]*4
    assert rows['unequal_response_gain'] == [True,True,False,False]


def test_author_claims_preserve_the_distinction_from_response_model():
    report = check.attribution_check()
    assert not report['response_model_attributed_to_author']
    assert report['quoted_targets'][-1] == ['reason','setu','setv']


def test_second_equation_keeps_one_beta_and_the_magnetic_minus_sign():
    row = check.source_equation_check()
    assert row['fractions'][2] == [['1'],['β']]
    assert row['magnetic_sign'] == 'minus'
