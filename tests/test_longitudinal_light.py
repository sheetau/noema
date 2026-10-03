import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_longitudinal_light import (
    alignment, attribution_checks, equation_checks, frame_checks,
    polynomial_checks, premise_checks, ray_checks, reuse_checks,
)
from scripts.compose_longitudinal_light import ROOT, generic_composed, source_composed


def test_longitudinal_substitution_does_not_prove_a_global_coordinate_map():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==8
    assert {name for name,row in rows.items() if row['status']=='invalid'}=={
        'ray_agreement_forces_global_coordinate_formula',
        'relative_speed_uses_moving_clock_time','auxiliary_xprime_is_the_moving_xi'}
    assert rows['substitution_iff_reduced_longitudinal_coordinate']['status']=='valid'
    assert rows['infinitely_many_functions_agree_on_the_selected_ray']['status']=='valid'
    assert not result['global_coordinate_transform_proved']


def test_generalized_light_law_preserves_emission_path_and_unit_conditions():
    assert all(reuse_checks().values())


def test_each_frame_uses_its_own_synchronized_local_clocks_and_all_subsegments():
    result=frame_checks();rows=result['cases']
    assert len(rows)==16
    assert {name for name,value in rows.items() if value}=={'rest_frame','moving_frame','moving_emitter'}
    assert not rows['wrong_reference_clock'] and not rows['relative_speed_substituted']
    assert not rows['bad_subsegment'] and not rows['empty_scope']
    assert result['all_selected_subsegments_checked']


def test_same_light_ray_and_both_events_bind_axis_path_measurements_and_tau():
    result=ray_checks();rows=result['cases']
    assert len(rows)==18 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert result['same_ray_and_same_events_required']


def test_static_time_and_auxiliary_position_are_not_moving_coordinates():
    result=equation_checks();rows=result['cases']
    assert len(rows)==6 and rows['baseline']==[True]*4
    assert rows['wrong_moving_time']==[False,True,True,True]
    assert rows['wrong_rest_time']==[True,False,False,False]
    assert rows['xprime_substituted_for_xi']==[False,False,True,False]
    assert rows['wrong_phi_value']==[True,False,True,False]
    assert result['rest_time_four_and_moving_time_five_not_interchanged']


def test_substitution_premise_keeps_both_laws_and_the_preceding_tau_form():
    result=premise_checks();rows=result['cases']
    assert len(rows)==8 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert result['both_global_laws_and_same_local_segments_required']


def test_prior_result_principles_rewrites_and_spatial_roles_are_attributed_separately():
    rows=attribution_checks()
    assert len(rows)==12 and rows['baseline']==[True]*6
    assert rows['wrong_coordinate_roles']==[False,True,True,True,True,True]
    assert rows['wrong_tau_rewrite']==[True,True,True,False,True,True]
    assert rows['wrong_substitution']==[True,True,True,True,True,False]


def test_alignment_keeps_both_times_and_each_substitution_step():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(65,73)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={f'M{i:04}' for i in range(118,130)}
    assert result['equations_restricted_to_selected_light_ray']
    assert not result['facsimile_checked'] and result['verified_full_units']==0


@pytest.mark.parametrize('compose', [generic_composed,source_composed])
def test_basis_roundtrip_and_frozen_predecessor(compose):
    text,basis=compose();doc=parse(text);audit_basis(doc,basis)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-affine-time-form.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-6]==previous['statements'] and len(doc['statements'])==58
