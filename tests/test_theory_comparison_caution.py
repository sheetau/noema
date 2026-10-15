from scripts import check_theory_comparison_caution as check


def test_uncertain_alignment_cannot_support_a_numerical_difference_judgment():
    rows=check.procedure_checks()['cases']
    assert rows['different_meaning']==[False]*3
    assert rows['unselected_equal']==[True]*3


def test_requirement_and_actual_adherence_are_independent():
    rows=check.norm_checks()['cases'][check.CORE]
    assert rows['different_units']==[True,False]
    assert rows['no_requirement']==[False,True]


def test_author_inference_does_not_prove_a_norm_or_execute_the_procedure():
    assert not check.attribution_check()['norm_or_actual_procedure_executed']
