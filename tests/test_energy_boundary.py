from scripts import check_energy_boundary as check


def test_neighborhood_depends_on_bound_and_does_not_add_infinite_real():
    report = check.numeric_checks()
    assert len(report['exact_threshold_witnesses']) == 10
    assert not any(report['excluded_inputs'].values())
    assert report['strict_left_neighborhood']
    assert report['polynomial_certificate_premises_have_exact_witnesses']


def test_general_radius_certificate_and_fixed_radius_counterexample():
    rows = check.polynomial_checks()
    assert rows['radius_certificate_forces_energy_above_bound']['status'] == 'valid'
    assert rows['light_boundary_has_no_finite_normalized_energy']['status'] == 'valid'
    assert rows['one_fixed_radius_works_for_every_bound']['status'] == 'invalid'


def test_physical_possibility_keeps_context_particle_and_frame():
    report = check.physical_checks()
    assert report['single_speed_cases'][check.CORE]['unreachable_only']
    assert not report['single_speed_cases'][check.CORE]['allowed_alternative']
    assert all(row['supplied_divergence_and_actual_possibility'] == [True, False]
               for row in report['independence_models'])


def test_infinite_domains_are_refused_and_author_claims_are_not_executed():
    assert check.refusal_checks()['all_bounds_and_speeds_refused']
    assert check.attribution_check()['quoted_contents'] == ['setc', 'setd']
