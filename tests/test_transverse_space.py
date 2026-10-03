import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_transverse_space import (
    alignment, attribution_checks, equation_checks, polynomial_checks,
    premise_checks, ray_checks,
)
from scripts.compose_transverse_space import ROOT, generic_composed, source_composed


def test_positive_diagonal_path_and_zero_xprime_give_transverse_formula():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==10
    rejected={'total_speed_can_replace_component_in_denominator',
        'moving_clock_can_replace_rest_time','transverse_ray_agreement_forces_global_formula'}
    assert {name for name,row in rows.items() if row['status']=='invalid'}==rejected
    assert all(row['status']=='valid' for name,row in rows.items() if name not in rejected)
    assert not result['global_coordinate_transform_proved']


def test_both_axis_rays_bind_different_distances_and_the_correct_diagonal_path():
    result=ray_checks();rows=result['cases']
    assert len(rows)==27 and rows['baseline']==rows['stationary_limit']==[True,True]
    assert rows['nonzero_xprime']==rows['diagonal_path_replaced_by_transverse_distance']==[False,True]
    assert rows['negative_path_root']==[False,True]
    assert rows['reuse_y_coordinates_for_z']==rows['z_uses_y_segment']==[True,False]
    assert rows['duplicate_axes']==rows['total_speed_as_component']==[False,False]
    assert result['distinct_axis_events_and_distances'] and result['rest_path_is_diagonal']


def test_both_transverse_equations_use_the_same_scale_and_their_own_events():
    result=equation_checks();rows=result['cases']
    assert len(rows)==9 and rows['baseline']==rows['stationary_limit']==[True]*6
    assert rows['nonzero_xprime']==[False,False,True,True,True,True]
    assert rows['wrong_scale']==[False,True,False,False,True,False]
    assert rows['reuse_y_coordinates_for_z']==[True,True,True,False,True,False]
    assert result['y_distance_eight_gives_eta_twenty']
    assert result['z_distance_twelve_gives_zeta_thirty']


def test_both_axis_premises_include_both_frame_laws_and_time_formula():
    result=premise_checks();rows=result['cases']
    assert len(rows)==10 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert result['both_axes_required']


def test_analogy_and_substitution_keep_their_axis_specific_contents():
    rows=attribution_checks()
    assert len(rows)==12 and rows['baseline']==[True]*5
    assert rows['wrong_both_axes_content']==[False,True,True,True,True]
    assert rows['wrong_eta_chain']==[True,False,True,True,True]
    assert rows['wrong_substitution_premise']==[True,True,True,False,True]
    assert rows['wrong_zeta_formula']==rows['missing_second_analogy']==[True,True,True,True,False]


def test_alignment_includes_both_transverse_axes_and_the_zero_xprime_condition():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(73,81)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={f'M{i:04}' for i in range(130,134)}
    assert result['both_axis_equations_restricted_to_their_rays']
    assert not result['facsimile_checked'] and result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,25)),(source_composed,(324,395))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-longitudinal-light.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-5]==previous['statements'] and len(doc['statements'])==63
