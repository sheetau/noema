from scripts import check_potential_speed as check


def test_potential_speed_preserves_charge_sign_and_excludes_zero_charge():
    rows = check.numeric_checks()
    assert rows['negative_charge'] == [True] * 3
    assert rows['wrong_charge_sign'] == [False] * 3
    assert rows['rest'] == [True] * 3
    assert rows['zero_charge_at_rest'] == [False] * 3


def test_derivation_gauge_shift_and_unique_speed_have_algebraic_certificates():
    rows = check.polynomial_checks()
    assert rows['balance_and_work_per_charge_imply_potential_relation']['status'] == 'valid'
    assert rows['common_potential_offset_preserves_drop']['status'] == 'valid'
    assert rows['fixed_parameters_determine_one_nonnegative_speed']['status'] == 'valid'
    assert rows['charge_sign_can_be_discarded']['status'] == 'invalid'


def test_drop_integral_keeps_path_orientation_and_work_per_charge():
    rows = check.integral_checks()['registered_polynomial_cases']
    assert rows['reverse'] and rows['negative_charge'] and rows['varying_field']
    assert rows['zero_charge_work']
    assert not rows['wrong_sign']


def test_endpoint_agreement_does_not_certify_the_whole_potential_function():
    result = check.potential_checks()
    rows = result['cases']
    assert rows['offset']['endpoint_relation']
    assert rows['same_endpoints_wrong_interior']['drop'] == '9'
    assert not rows['same_endpoints_wrong_interior']['all_polynomial_coefficients_match']
    assert not rows['same_endpoints_wrong_interior']['endpoint_relation']
    assert not rows['outside_domain']['endpoint_relation']
    assert result['all_cut_domain_evaluation_refused']


def test_source_reuses_energy_scope_without_inventing_it_from_the_formula():
    rows = check.source_checks()['cases'][check.CORE]
    assert rows['negative_charge'] == [True] * 4
    assert rows['initial_motion'] == [True, True, True, False]
    assert rows['radiation'] == [True, True, True, False]
    assert rows['wrong_potential_field'] == [False, True, False, False]
    assert rows['wrong_potential_end'] == [False, True, False, False]


def test_printed_equation_and_quoted_derivation_stay_distinct_from_evaluation():
    row = check.attribution_check()
    assert row['quoted_targets'] == [['claim', 'seuz'], ['reason', 'seva', 'seuz']]
    assert not row['physical_quantities_and_integrals_executed']
    printed = check.printed_equation_check()
    assert printed['leaf_sequence'][7:9] == [('mi', 'μ'), ('mi', 'ϵ')]
    assert not printed['printed_integral_bounds_present']
