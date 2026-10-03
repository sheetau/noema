import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_transverse_rod_scale import (
    alignment, attribution_checks, endpoint_checks, inference_premise_checks,
    measurement_checks, normalization_checks, polynomial_checks, symmetry_checks,
)
from scripts.compose_transverse_rod_scale import ROOT, generic_composed, source_composed


def test_endpoint_algebra_and_positive_length_symmetry_determine_scale():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==9
    assert {name for name,row in rows.items() if row['status']=='invalid'}=={
        'reciprocity_and_evenness_without_sign_force_one','positive_evenness_without_reciprocity_forces_one','zero_rod_length_identifies_the_factors'}
    assert all(row['status'] in ('valid','invalid') for row in rows.values())
    assert not result['absolute_distance_alone_excludes_negative_phi']


def test_endpoints_preserve_signed_extent_and_require_rest_simultaneity():
    result=endpoint_checks();rows=result['cases']
    assert len(rows)==8 and rows['baseline']['accepted']==[True,True]
    assert rows['baseline']['high_rest']==['6','6','0','2']
    assert rows['baseline']['high_moving']==['0','6','0','8/5']
    assert rows['negative_pair']['high_rest'][1]=='-6'
    assert rows['nonsimultaneous']['accepted']==rows['wrong_axis_coordinate']['accepted']==[False,True]
    assert rows['zero_factor']['accepted']==[False,False]
    assert result['rest_frame_simultaneity_required']


def test_measured_length_is_bound_to_object_places_units_and_positive_extent():
    result=measurement_checks();rows=result['cases']
    assert len(rows)==12
    assert rows['baseline']==rows['reciprocal_unequal']==[True,True]
    assert rows['negative_pair']==rows['wrong_length_candidate']==[True,False]
    assert all(rows[name]==[False,False] for name in ('wrong_rod_endpoint','wrong_event_location','nonsimultaneous','not_rigid','not_transverse','wrong_motion_sign','wrong_units','zero_length'))
    assert result['same_rod_endpoints_events_units_and_distance_checked']


def test_symmetry_is_about_equal_speed_magnitude_within_the_given_scope():
    result=symmetry_checks();rows=result['cases']
    assert len(rows)==8
    assert {name for name,value in rows.items() if value}=={'opposite_equal','different_speeds_different_lengths','excluded_mismatch'}
    assert result['physical_isotropy_not_derived']


def test_reciprocity_evenness_positive_branch_and_final_formula_are_distinct():
    result=normalization_checks();rows=result['cases']
    assert len(rows)==6 and rows['baseline']==[True]*6
    assert rows['reciprocal_unequal']==[True,False,False,False,False,False]
    assert rows['equal_not_reciprocal']==[False,True,True,False,False,False]
    assert rows['negative_pair']==[True,True,True,False,False,False]
    assert rows['wrong_units']==rows['not_transverse']==[True,False,True,True,True,True]
    assert result['unknown_function_definition_unchanged']


def test_two_physical_measurements_are_needed_before_the_scale_inferences():
    result=inference_premise_checks();rows=result['cases']
    assert len(rows)==7 and rows['baseline']==[True]*5
    assert rows['reciprocal_unequal']==[True,False,False,False,True]
    assert rows['equal_not_reciprocal']==[True,True,True,False,True]
    assert rows['mixed_reverse_events']==rows['negative_pair']==[False]*4+[True]
    assert result['each_setting_has_its_own_events_and_places']


def test_physical_interpretation_added_sign_and_final_rewrite_are_separate():
    rows=attribution_checks()
    assert len(rows)==15 and rows['baseline']==[True]*10
    assert rows['wrong_length']==[True]*3+[False]+[True]*6
    assert rows['wrong_positive_premise']==[True]*7+[False,True,True]
    assert rows['wrong_final_rewrite']==[True]*9+[False]


def test_source_alignment_retains_unfinished_geometry_and_sign_interpretation():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(97,109)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={f'M{i:04}' for i in range(170,191)}
    assert not result['facsimile_checked'] and result['verified_full_units']==0
    assert result['positive_branch_is_explicit_interpretation'] and result['whole_material_segment_not_yet_defined']


def test_final_equation_does_not_redefine_the_previously_unknown_function():
    text,basis=source_composed();doc=parse(text);audit=audit_basis(doc,basis)
    dependencies=audit['definition_dependencies']['definition_primitive_dependencies']
    assert 'zeq' in dependencies['spc'] and 'zeq' in dependencies['ssl']
    assert 'zeq' not in dependencies['ssn']


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,43)),(source_composed,(386,501))])
def test_basis_roundtrips_and_frozen_parent(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-reverse-transform.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-10]==previous['statements'] and len(doc['statements'])==94
