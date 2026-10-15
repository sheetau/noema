import pytest
from scripts import check_mass_coefficients as check


@pytest.mark.parametrize('real',[False,True])
def test_coefficient_and_component_contrasts(real):
    rows=check.numerical_checks(real)
    assert rows['zero_input_underdetermined'] and not rows['zero_input_does_not_fix_coefficients']


def test_polynomial_implications_and_counterexample():
    rows=check.polynomial_checks()
    assert rows['zero_input_alone_identifies_coefficients']['status']=='invalid'


def test_universal_domains_cannot_be_sampled():
    assert len(check.universal_refusals())==2


def test_same_matter_event_frames_and_units():
    rows=check.convention_checks()
    assert rows['baseline'] and rows['unknown_convention']=='refused'


def test_inference_attribution_does_not_execute_quoted_claims():
    assert not check.attribution_check()['numeric_or_physical_claim_executed']


def test_conclusion_preserves_numeric_and_physical_bindings():
    assert check.source_conclusion_checks()['baseline']
