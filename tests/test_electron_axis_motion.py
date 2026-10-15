from scripts import check_electron_axis_motion as check


def test_matching_endpoints_and_midpoint_do_not_certify_axial_motion():
    rows=check.geometry_checks()['cases'][check.CORE]
    assert rows['baseline']==[True]*4
    assert rows['sample_alias_excursion']==[False,True,True,True]
    assert rows['domain_gap'][0] is False


def test_conditional_does_not_assert_its_motion_antecedent():
    report=check.conditional_checks()
    assert report['truth_table']['(False, False)']
    assert not report['truth_table']['(True, False)']


def test_author_attribution_does_not_execute_a_trajectory_or_integral():
    assert not check.attribution_check()['trajectory_or_work_integral_executed']
