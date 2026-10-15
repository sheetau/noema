from scripts import check_electron_energy_balance as check


def test_zero_initial_energy_and_radiation_are_separate_assumptions():
    report=check.numeric_checks()
    assert report['baseline'][1:4]==[True,True,True]
    assert report['equal_despite_both_nonzero'][1:4]==[True,False,True]


def test_balance_proofs_include_counterexamples_to_missing_assumptions():
    report=check.polynomial_checks()
    assert report['zero_initial_and_zero_radiation_imply_equality']['status']=='valid'
    assert report['zero_radiation_alone_implies_equality']['status']=='invalid'


def test_quantity_bindings_preserve_the_same_episode_field_and_particle():
    rows=check.binding_checks()['cases'][check.CORE]
    assert rows['baseline']==[True,True]
    assert rows['wrong_withdrawal_field']==rows['wrong_withdrawal_particle']==[False,False]


def test_author_claims_do_not_execute_integrals_or_invent_physical_assignments():
    assert not check.attribution_check()['physical_assignments_or_integrals_executed']
    assert check.work_integral_refusal()['full_integral_evaluation_refused']


def test_oriented_work_preserves_charge_and_direction_signs():
    report=check.oriented_work_checks()
    rows=report['registered_constant_field_cases']
    assert rows['forward'] and rows['reverse'] and not rows['wrong_reverse_sign']
    assert rows['negative_charge'] and rows['negative_field']
    assert not report['arbitrary_functions_sampled']
