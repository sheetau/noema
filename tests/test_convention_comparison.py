from scripts import check_convention_comparison as check


def test_selected_alternatives_empty_domains_and_shared_cases():
    rows=check.comparison_checks()['cases'][check.LIBRARY]
    assert rows['baseline']==[True,True,False]
    assert rows['proportional_change']==[False,False,False]
    assert rows['actual_only']==[False,False,True]


def test_nonzero_input_and_proportional_change_counterexample():
    rows=check.polynomial_checks()
    assert rows['changing_both_evaluations_always_changes_coefficient']['status']=='invalid'


def test_author_attribution_does_not_assert_counterfactual_truth():
    assert not check.attribution_check()['evaluations_or_counterfactuals_executed']
