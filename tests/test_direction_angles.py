import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_direction_angles import polynomial_checks, angle_checks, source_checks, attribution_checks, alignment
from scripts.compose_direction_angles import ROOT, composed


@pytest.fixture(scope='module')
def angles():
    return angle_checks()['cases']


def test_inverse_branch_and_orientation_have_algebraic_evidence():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==12
    assert rows['principal_inverse_pair_is_unique']['status']=='valid'
    assert rows['negating_both_components_keeps_principal_ratio']['status']=='valid'
    assert rows['swapping_vectors_reverses_oriented_sine']['status']=='valid'
    assert rows['principal_value_always_matches_actual_direction']['status']=='invalid'
    assert not result['analytic_arctangent_or_radian_measure_constructed']


def test_direction_and_inverse_ratio_handle_vertical_and_zero_separately(angles):
    assert angles['first_quadrant']==angles['scaled_vector']==[True]*6
    assert angles['vertical']==[True,False,False,True,True,True]
    assert angles['zero_vector']==[False,False,False,False,False,True]
    assert angles['zero_frame_velocity']==[True,True,True,False,False,True]
    assert angles['not_unit_circle']==[False]*6


def test_principal_ratio_does_not_replace_actual_direction(angles):
    assert angles['negative_x_direction']==[True,True,False,True,True,True]
    assert angles['negative_x_principal']==[False,True,True,False,False,True]
    assert angles['opposite_axis']==[True,True,False,True,True,True]
    assert angles['negative_radius']==angles['wrong_radius']==[False,True,True,False,False,True]


def test_oriented_and_unsigned_angles_preserve_different_information(angles):
    assert angles['negative_y_direction']==[True,True,True,True,False,True]
    assert angles['negative_y_unsigned']==[False,False,False,False,True,True]
    assert angles['negative_frame_oriented']==[False,True,False,True,False,True]
    assert angles['negative_frame_unsigned']==[False,False,False,False,True,True]


def test_source_readings_do_not_hide_branch_disagreements():
    result=source_checks();rows=result['cases']
    assert len(rows)==11 and rows['first_quadrant']==[True]*3
    assert rows['negative_x_direction']==[True,False,True]
    assert rows['negative_x_principal']==rows['negative_y_direction']==[True,True,False]
    assert rows['vertical']==[False,False,True]
    assert rows['wrong_motion_scope']==rows['wrong_component_context']==[False]*3
    assert result['principal_branch_not_silently_attributed']


def test_principal_alternative_is_not_attributed_to_source():
    result=attribution_checks();rows=result['cases']
    assert len(rows)==6 and rows['baseline']==[True,True]
    assert rows['principal_substituted']==[False,True]
    assert rows['readings_swapped']==[False,False]
    assert result['quoted_angle_constraints_are_not_evaluated_or_endorsed']


def test_source_range_excludes_calculation_and_retains_unresolved_convention():
    result=alignment();rows=result['segments']
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M0253','M0254','M0255','M0256'}
    sentence=next(r for r in rows if r['unit']=='einstein-1905:u0139' and 'source' in r)
    assert sentence['source'].endswith('anzusehen.') and 'Nach einfacher Rechnung' not in sentence['source']
    assert result['historical_branch_convention_unresolved']
    assert result['verified_full_units']==0 and not result['facsimile_checked']


def test_existing_language_parent_and_roundtrip_are_preserved():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(480,700)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-speed-magnitude.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements'] and len(doc['statements'])==133
