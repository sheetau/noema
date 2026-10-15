from scripts import check_integral_substitution as check


def test_signed_substitution_handles_stops_reversals_and_folds():
    rows = check.substitution_checks()
    assert rows['folded_different_endpoints']['spatial_integral'] == '57/256'
    assert rows['folded_same_endpoints']['time_integral'] == '0'
    assert rows['cubic_composition']['time_integral'] == '8'
    assert not rows['absolute_derivative_is_wrong']['joint_integrals']


def test_local_condition_keeps_interior_range_and_derivative():
    assert check.local_checks() == dict(baseline=True, range_misses_interior=False, wrong_rate=False,
                                      stopped=True, alias_at_midpoint=True, alias_at_quarter=False)


def test_matching_integrals_and_three_probes_do_not_establish_derivative():
    row = check.substitution_checks()['wrong_rate_same_integral']
    assert row['joint_integrals']
    assert not row['polynomial_chain_identity']


def test_unregistered_functions_and_universal_conditions_are_not_sampled():
    assert all(check.refusal_checks().values())


def test_source_candidate_keeps_same_motion_mass_and_no_added_author_claim():
    rows = check.structure_checks()
    assert rows['no_division_by_speed']
    assert rows['new_author_attributions'] == 0
