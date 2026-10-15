from scripts import check_electron_power_law as check


def test_zero_power_does_not_establish_the_force_law_at_rest():
    assert check.numeric_checks()['zero_speed_wrong_force']==[False,True]*3
    assert check.polynomial_checks()['power_equality_alone_implies_force_law']['status']=='invalid'


def test_each_time_uses_its_own_velocity_beta_and_position():
    rows=check.local_checks()['cases'][check.CORE]
    assert rows['baseline']==[True]*3
    assert rows['fixed_terminal_beta']==[False,False,True]
    assert rows['zero_speed_wrong_force']==[False,True,True]


def test_source_binding_preserves_the_same_local_conditions():
    rows=check.source_instance_checks()['single_time_source_instances'][check.CORE]
    assert rows['baseline']==[True]*3
    assert rows['fixed_terminal_beta']==[False,False,True]


def test_author_attribution_does_not_execute_dynamics_or_integrals():
    assert not check.attribution_check()['dynamics_or_work_integrals_executed']
