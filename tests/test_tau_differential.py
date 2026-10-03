from fractions import Fraction
import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_rod_measurements import cut
from scripts.check_tau_differential import (
    ConstructedCuts, alignment, attribution_checks, equation_checks, finite_refusals,
    polynomial_checks, reuse_checks, slice_checks, source_checks,
)
from scripts.compose_tau_differential import ROOT, generic_composed, source_composed


def test_differential_equations_are_algebraically_equivalent_with_fixed_partial_roles():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==6
    assert rows['inverse_sum_form_iff_rearranged_coefficient_equation']['status']=='valid'
    assert rows['affine_candidate_has_zero_two_variable_linear_remainder']['status']=='valid'
    assert rows['swapping_partial_roles_preserves_the_equation']['status']=='invalid'
    assert rows['wrong_sign_on_speed_term_is_equivalent']['status']=='invalid'
    assert rows['diagonal_counterexample_defeats_zero_linear_map']['status']=='valid'
    assert not result['general_chain_rule_proved']


def test_limits_derivatives_and_signed_inverse_preserve_the_existing_definitions():
    assert all(reuse_checks().values())


def test_rational_cut_oracle_refuses_unregistered_predicates_instead_of_sampling_them():
    fixture=ConstructedCuts();value=fixture.make(Fraction(3,8))
    assert fixture.read(value)==Fraction(3,8)
    with pytest.raises(ValueError,match='not constructed'):
        fixture.read(cut(Fraction(3,8)))


def test_both_real_cut_equations_accept_the_same_derivatives_and_reject_bad_domains():
    result=equation_checks();rows=result['cases']
    assert len(rows)==10
    assert {name for name,value in rows.items() if value==[True,True]}=={'baseline','scaled_partials','zero_speed'}
    assert all(value==[False,False] for name,value in rows.items() if name not in {'baseline','scaled_partials','zero_speed'})
    assert result['no_real_cut_sampling']


def test_each_partial_varies_one_argument_and_keeps_the_same_base_point():
    result=slice_checks();rows=result['cases']
    assert len(rows)==9 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert result['other_coordinates_fixed']


def test_source_requires_neighborhood_total_derivative_and_the_same_partial_values():
    result=source_checks();rows=result['cases']
    assert len(rows)==12 and rows['baseline']
    assert not rows['single_trial_only'] and not rows['no_total_derivative']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert result['origin_and_same_time_preserved']


def test_finite_evaluator_refuses_the_full_real_neighborhood_and_limit_conditions():
    rows=finite_refusals()
    assert len(rows)==3 and all(row['refused'] for row in rows.values())
    assert all('rational number domain' in row['reason'] for row in rows.values())


def test_limit_step_and_algebraic_reformulation_remain_separate_attributions():
    rows=attribution_checks()
    assert len(rows)==9 and rows['baseline']==[True,True]
    assert rows['wrong_limit_premise']==[False,True]
    assert rows['wrong_rewrite_before']==rows['wrong_rewrite_after']==[True,False]


def test_alignment_records_added_sufficient_regularity_without_claiming_completion():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(54,58)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={'M0102','M0103','M0104'}
    assert result['explicit_sufficient_regularity_added'] and result['arbitrary_starting_point_not_yet_generalized']
    assert not result['facsimile_checked'] and result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,7)),(source_composed,(286,287))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-light-time-arguments.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==45
