import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_sphere_slice import (
    alignment, attribution_checks, equation_checks, membership_checks,
    polynomial_checks, semiaxis_checks, simultaneity_checks,
)
from scripts.compose_sphere_slice import ROOT, generic_composed, source_composed


def test_transformation_rotation_and_positive_semiaxes_are_algebraic():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==9
    assert {name for name,row in rows.items() if row['status']=='invalid'}=={
        'contracted_endpoint_is_on_original_uncontracted_sphere',
        'diameter_can_replace_the_semiaxis',
        'laboratory_simultaneity_is_moving_frame_simultaneity'}
    assert not result['rigidity_or_material_boundary_proved']


def test_surface_equations_distinguish_time_slice_and_interior():
    result=equation_checks();rows=result['cases']
    assert len(rows)==11 and rows['baseline']['accepted']==[True]*6
    assert rows['baseline']['rest']==['4','0','0','0']
    assert rows['baseline']['moving']==['5','0','0','-3/5']
    assert rows['later_surface']['accepted']==[True]*3+[False]*3
    assert rows['interior']['accepted']==[True]+[False]*5
    assert rows['wrong_rest_point']['accepted']==[False,True]+[False]*4
    assert rows['wrong_moving_point']['accepted']==[False,False]+[True]*4
    assert rows['light_speed_boundary']['accepted']==[False,True]+[False]*4
    assert result['sqrt_structure_and_three_equivalent_zero_slices_checked']


def test_half_axes_preserve_transverse_radius_and_signed_velocity():
    result=semiaxis_checks();rows=result['cases']
    assert len(rows)==9
    assert {name for name,value in rows.items() if value}=={
        'baseline','stationary','opposite_velocity'}
    assert result['semiaxis_not_diameter']


def test_surface_membership_requires_same_body_and_measured_events():
    result=membership_checks();rows=result['cases']
    assert len(rows)==14 and rows['baseline']==[True]*4
    for label in ('missing_surface_point','interior_as_surface',
                  'unmeasured_surface_event','wrong_body','empty_event_scope'):
        assert rows[label]==[False]*4
    assert rows['wrong_rest_point']==[True,False,False,False]
    for label in ('wrong_moving_point','wrong_center','not_rigid',
                  'not_stationary','wrong_origin_assignment','wrong_motion'):
        assert rows[label]==[False,True,True,True]
    assert rows['no_zero_slice']==[True,True,False,False]
    assert not result['continuous_spatial_coverage_proved']


def test_lab_simultaneity_is_not_assumed_in_the_moving_frame():
    rows=simultaneity_checks()['cases']
    assert rows['baseline']=={'equal_times':[True,False],'moving_times':['3/5','-3/5']}
    assert rows['stationary']=={'equal_times':[True,True],'moving_times':['0','0']}


def test_heading_setup_transform_slice_and_shape_have_separate_attributions():
    rows=attribution_checks()
    assert len(rows)==11 and rows['baseline']==[True]*6
    assert rows['wrong_author']==rows['wrong_scope']==rows['wrong_context']==[False]*6
    assert rows['missing_clock_topic']==[False]+[True]*5
    assert rows['wrong_transform']==[True,True,False,True,True,True]
    assert rows['wrong_slice']==[True]*3+[False,True,True]
    assert rows['wrong_shape']==[True]*4+[False,True]


def test_alignment_keeps_sqrt_and_semiaxes_without_claiming_completion():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={f'einstein-1905:u{i:04}' for i in range(109,116)}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={f'M{i:04}' for i in range(191,201)}
    assert result['mathml_sqrt_structure_preserved'] and result['source_axes_read_as_semiaxes']
    assert result['verified_full_units']==0 and not result['facsimile_checked']
    assert all(not r['full_semantic_equivalence'] for r in rows)


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,47)),(source_composed,(397,526))])
def test_basis_roundtrips_and_frozen_parent(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-transverse-rod-scale.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-6]==previous['statements'] and len(doc['statements'])==100
