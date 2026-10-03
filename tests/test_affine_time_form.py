import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_affine_time_form import (
    alignment, attribution_checks, coefficient_checks, finite_refusals,
    formula_checks, origin_checks, polynomial_checks, uncertainty_checks,
)
from scripts.compose_affine_time_form import ROOT, generic_composed, source_composed


def test_affine_coefficients_reduce_to_formula_only_with_origin_convention():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==8
    rejected={'derivatives_alone_force_zero_origin','coefficient_is_forced_to_one'}
    assert {name for name,row in rows.items() if row['status']=='invalid'}==rejected
    assert all(row['status']=='valid' for name,row in rows.items() if name not in rejected)
    assert not result['full_real_derivative_theorem_proved']


def test_formula_preserves_free_scale_offset_and_transverse_independence():
    rows=formula_checks()['cases']
    assert len(rows)==6
    assert rows['baseline']['tau']==rows['other_transverse_position']['tau']=='7'
    assert rows['other_scale']['tau']=='21/2'
    assert rows['nonzero_origin']=={'checks':[True,True,False],'tau':'7','affine_value':'14'}
    assert rows['stationary']['tau']=='10' and rows['negative_xprime']['tau']=='13'


def test_same_phi_value_is_bound_to_time_coefficient_before_the_inference():
    result=coefficient_checks();rows=result['cases']
    assert len(rows)==11
    assert {name for name,value in rows.items() if value}=={'baseline','other_scale','offset_not_yet_removed'}
    assert not rows['wrong_phi_value'] and not rows['space_time_swapped']
    assert not rows['nonzero_y'] and not rows['nonzero_z']
    assert result['same_phi_speed_and_time_coefficient_bound']


def test_common_origin_requires_same_event_both_charts_and_zero_clock_readings():
    result=origin_checks();rows=result['cases']
    assert len(rows)==12 and rows['baseline']==[True,True]
    assert rows['tau_offset_not_zero']==rows['missing_tau_correspondence']==[True,False]
    assert all(row==[False,False] for name,row in rows.items() if name not in ('baseline','tau_offset_not_zero','missing_tau_correspondence'))
    assert result['same_event_in_both_frames_required']


def test_unknown_coefficient_is_stage_scoped_without_conflating_function_values():
    result=uncertainty_checks();rows=result['cases']
    assert len(rows)==11 and rows['two_values']==[True,True]
    assert rows['wrong_current_function']==[True,False]
    assert rows['same_value_at_selected_speed']==[False,True]
    assert rows['different_value_at_another_speed']==[True,True]
    assert rows['later_stage']==rows['wrong_agent']==rows['empty_candidates']==[False,True]
    assert result['knowledge_in_general_not_defined']


def test_infinite_affine_and_unknown_function_conditions_are_not_sampled():
    rows=finite_refusals()
    assert len(rows)==4 and all(row['refused'] for row in rows.values())


def test_brevity_assumption_inference_and_unknown_claim_remain_distinct():
    rows=attribution_checks()
    assert len(rows)==9 and rows['baseline']==[True]*3
    assert rows['missing_brevity']==[False,True,True]
    assert rows['wrong_formula']==[True,False,True]
    assert rows['wrong_unknown_content']==[True,True,False]


def test_alignment_covers_affine_form_unknown_phi_and_zero_origin():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(62,65)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={f'M{i:04}' for i in range(111,118)}
    assert result['origin_choice_and_unfixed_scale_separated']
    assert not result['facsimile_checked'] and result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,18)),(source_composed,(308,348))])
def test_basis_roundtrip_and_predecessor_are_preserved(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-transverse-time.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-3]==previous['statements'] and len(doc['statements'])==52
