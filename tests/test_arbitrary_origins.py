import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_arbitrary_origins import (
    alignment, attribution_checks, choice_checks, clock_function_checks, coordinate_checks,
    finite_refusals, polynomial_checks, possibility_checks, protocol_checks, shift_checks,
)
from scripts.compose_arbitrary_origins import ROOT, generic_composed, source_composed


def test_spatial_translation_changes_only_spatial_arguments():
    result=polynomial_checks()
    assert len(result['claims'])==5 and all(row['status']=='valid' for row in result['claims'].values())
    assert not result['physical_origin_independence_proved']


def test_each_point_can_have_its_own_trial_and_a_possible_outcome_is_not_a_guarantee():
    result=choice_checks();rows=result['cases']
    assert len(rows)==10 and rows['baseline']==[True,True]
    assert rows['extra_failing_outcome']==rows['success_from_different_point']==[True,True]
    assert rows['only_first_point']==[True,False]
    assert rows['success_from_different_trial']==rows['no_available_plan']==[False,False]
    assert result['possibility_not_guarantee_or_actual_occurrence']


def test_translated_neighborhood_keeps_time_and_all_three_anchor_coordinates():
    result=shift_checks();rows=result['cases']
    assert len(rows)==7 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')


def test_trial_can_start_off_the_origin_but_must_keep_ray_clocks_place_and_direction():
    result=protocol_checks();rows=result['cases']
    assert len(rows)==15 and rows['baseline_nonorigin']
    assert not any(value for name,value in rows.items() if name!='baseline_nonorigin')
    assert result['no_origin_assignment_or_axis_coincidence_required']


def test_same_place_has_the_requested_auxiliary_coordinates_at_the_same_time():
    result=coordinate_checks();rows=result['cases']
    assert len(rows)==10 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert result['auxiliary_coordinate_operation_is_oracle']


def test_all_three_readings_use_the_same_tau_and_matching_rest_coordinate_records():
    result=clock_function_checks();rows=result['cases']
    assert len(rows)==12 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert result['all_three_event_readings_bound_to_one_function']


def test_possible_alternative_preserves_trial_point_coordinates_law_and_regularity():
    result=possibility_checks();rows=result['cases']
    assert len(rows)==15 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert result['possible_outcome_differs_from_start_context']


def test_all_space_quantification_cannot_be_verified_with_a_finite_sample():
    result=finite_refusals()
    assert len(result)==2 and all(row['refused'] for row in result.values())


def test_noted_possibility_and_global_equation_inference_remain_nonfactive():
    rows=attribution_checks()
    assert len(rows)==8 and rows['baseline']==[True,True]
    assert rows['missing_highlight']==[False,True]
    assert rows['wrong_global_equation']==[True,False]


def test_source_alignment_keeps_the_same_time_and_does_not_claim_full_equivalence():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={'einstein-1905:u0058'}
    assert rows[1]['math_id']=='M0105'
    assert result['same_time_parameter_retained'] and not result['facsimile_checked']
    assert result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,9)),(source_composed,(293,302))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-tau-differential.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==47
