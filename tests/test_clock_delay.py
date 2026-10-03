import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_clock_delay import (
    alignment, approximation_checks, asymptotic_checks, attribution_checks,
    interval_checks, polynomial_checks,
)
from scripts.compose_clock_delay import ROOT, generic_composed, source_composed


def test_exact_residual_bounds_and_duration_scaling():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==11
    assert {n for n,r in rows.items() if r['status']=='invalid'}=={
        'second_order_formula_is_exact','one_second_delay_is_always_total_delay',
        'fourth_order_bound_implies_small_error_at_any_speed'}
    assert result['small_speed_needed_for_small_absolute_approximation_error']


def test_real_values_keep_lag_approximation_and_nonzero_residual_separate():
    rows=approximation_checks()
    assert len(rows)==8
    assert {n for n,r in rows.items() if r['accepted']==[True,True]}=={
        'baseline','negative_speed','stationary','near_light'}
    assert rows['baseline']['values'][-3:]==['1/5','9/50','1/50']
    assert rows['near_light']['values'][-1]=='162/625'


def test_seconds_conversion_uses_same_clock_records_and_scale():
    result=interval_checks();rows=result['cases']
    assert len(rows)==16
    assert rows['baseline']['accepted']==rows['one_second']['accepted']==[True,True]
    assert rows['baseline']['lost_seconds']=='1'
    assert rows['one_second']['duration_seconds']=='1'
    assert rows['one_second']['lost_seconds']=='1/5'
    assert rows['one_second']['approximate_seconds']=='9/50'
    assert rows['one_second']['error_seconds']=='1/50'
    for name in ('wrong_duration','mixed_elapsed_scale','exact_equals_approximation','same_record','reversed_records'):
        assert rows[name]['accepted']==[False,True]
    for name in ('wrong_conversion','wrong_target_unit','negative_scale','nonlinear_clock','missing_observer_chart','zero_light_speed'):
        assert rows[name]['accepted']==[False,False]


def test_big_o_uses_shared_constants_accumulation_and_signed_error():
    result=asymptotic_checks();rows=result['cases']
    assert len(rows)==8
    assert {n for n,r in rows.items() if r['status']=='valid'}=={
        'bounded_error_big_o_one','exact_function_zero_scale',
        'linear_error_fixed_constant','negative_error_two_sided'}
    assert result['full_cut_condition_refuses_finite_sampling']
    assert result['real_cut_big_o_not_machine_proved']


def test_exact_statement_approximation_and_added_error_bounds_are_distinct():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']==[True]*3
    assert rows['wrong_author']==rows['wrong_scope']==rows['wrong_context']==[False]*3
    assert rows['wrong_exact']==[False,True,True]
    assert rows['wrong_approximation']==[True,False,True]
    assert rows['wrong_supplement']==[True,True,False]


def test_source_alignment_does_not_promote_error_supplement_to_source_text():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={'einstein-1905:u0125'}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M0217','M0218'}
    assert result['explicit_remainder_constants_are_supplement']
    assert result['verified_full_units']==0 and not result['facsimile_checked']


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,53)),(source_composed,(415,593))])
def test_basis_roundtrip_and_frozen_parent(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        parent=parse((ROOT/'examples/v014/einstein-origin-clock.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
        assert doc['statements'][:-3]==parent['statements'] and len(doc['statements'])==115
