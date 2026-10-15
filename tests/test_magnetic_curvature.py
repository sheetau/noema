from scripts import check_magnetic_curvature as check


def test_radius_is_positive_and_does_not_encode_bending_direction():
    rows = check.numeric_checks()
    assert rows['geometry']['tangential_added'] == [True] * 3
    assert rows['geometry']['space_curve'] == [True] * 3
    assert rows['geometry']['straight_accelerating'] == [False] * 3
    assert rows['geometry']['negative_radius'] == [False] * 3
    assert rows['magnetic']['negative_charge'] == [False, False, True] * 3
    assert rows['magnetic']['zero_field'] == [False] * 9


def test_general_curvature_and_source_rearrangement_have_algebraic_certificates():
    rows = check.polynomial_checks()
    assert rows['tangential_acceleration_preserves_radius']['status'] == 'valid'
    assert rows['quarter_turn_preserves_radius']['status'] == 'valid'
    assert rows['geometry_and_oriented_magnetic_law_imply_printed_chain']['status'] == 'valid'
    assert rows['printed_forms_are_equivalent_under_motion_law']['status'] == 'valid'
    assert rows['same_radius_requires_same_bending_direction']['status'] == 'invalid'


def test_radius_uses_derivatives_of_the_same_local_trajectory():
    report = check.trajectory_checks()
    rows = report['cases'][check.CORE]
    assert rows['tangential_acceleration']
    assert not rows['fake_velocity_field']
    assert not rows['sample_alias_field']
    assert not rows['wrong_event']
    assert not rows['isolated']
    assert report['all_cut_history_and_derivative_fields_refused']


def test_source_preserves_field_ownership_exclusivity_and_orientation():
    report = check.source_checks()
    rows = report['cases'][check.CORE]
    assert rows['both_negative'] == [True] * 5
    assert rows['reversed_charge'] == [True, False, False, False, True]
    assert rows['wrong_bending_direction'] == [True, False, True, False, False]
    assert rows['other_deflection'] == [False, False, False, False, True]
    assert rows['wrong_source_event'] == [False, False, False, False, True]
    assert report['unknown_exclusivity_refused']


def test_author_claims_keep_derivation_and_reformulation_without_execution():
    row = check.attribution_check()
    assert row['quoted_targets'][-2:] == [
        ['reason', 'sevo', 'sevm'], ['reason', 'sevm', 'sevn']]
    assert not row['trajectories_and_fields_executed']


def test_printed_equations_keep_minus_sign_and_nonzero_denominators():
    rows = check.printed_equations()
    assert rows['M0441']['leaf_sequence'][0] == '−'
    assert rows['M0441']['fractions'][1] == [['v', '2'], ['R']]
    assert rows['M0442']['fractions'][0] == [['μ'], ['ϵ']]
    assert rows['M0442']['fractions'][-1] == [['1'], ['N']]
