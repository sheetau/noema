from scripts import check_arbitrary_small_charge as check


def test_addition_preserves_identity_and_excludes_cancellation():
    rows=check.capability_checks()['cases'][check.CORE]
    assert rows['already_charged'] and rows['negative']
    assert not rows['cancellation'] and not rows['replacement']
    assert not rows['wrong_point'] and not rows['wrong_unit']


def test_one_small_charge_does_not_meet_every_bound():
    report=check.bound_checks()
    assert report['finite_bound_instances']['1']['fixed_half']
    assert not report['finite_bound_instances']['1/1000']['fixed_half']
    assert report['infinite_domain_refused']


def test_universal_arithmetic_witnesses_do_not_prove_physical_capability():
    report=check.polynomial_checks()
    assert len(report['claims'])==5
    assert not report['physical_operations_or_possible_outcomes_proved']


def test_author_attribution_does_not_execute_a_physical_capability():
    assert not check.attribution_check()['physical_capability_executed_or_proved']


def test_source_scope_does_not_ignore_a_second_selected_point():
    rows=check.source_binding_checks()['one_bound_source_instances'][check.CORE]
    assert rows['baseline'] and not rows['second_selected_point']
    assert not rows['wrong_source_unit']
