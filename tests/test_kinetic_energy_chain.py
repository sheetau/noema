from scripts import check_kinetic_energy_chain as check


def test_energy_is_zero_at_rest_and_preserves_mass_factor():
    rows=check.numeric_checks()
    assert rows['at_rest']==[True]*3
    assert rows['mass_factor_omitted']==rows['rest_energy_included']==[False]*3


def test_normalized_and_weighted_integrands_are_distinct():
    report=check.integrand_checks()
    assert report['normalized_integrand']!=report['mass_weighted_integrand']
    assert report['full_integral_evaluation_refused']


def test_differentiated_normalization_has_only_conditional_algebraic_proofs():
    report=check.polynomial_checks()
    assert len(report['claims'])==4
    assert not report['fundamental_theorem_of_calculus_proved']


def test_printed_formula_is_not_silently_replaced_by_the_candidate():
    assert not check.printed_structure()['source_silently_corrected']
    assert not check.attribution_check()['corrected_content_attributed_to_author']
