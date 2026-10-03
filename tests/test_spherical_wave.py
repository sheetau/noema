import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_spherical_wave import (
    alignment, attribution_checks, compatibility_checks, equation_checks,
    front_checks, polynomial_checks, proof_status_checks, source_binding_checks,
)
from scripts.compose_spherical_wave import ROOT, generic_composed, source_composed


def test_null_equation_is_preserved_without_premature_scale_normalization():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==7
    assert {name for name,row in rows.items() if row['status']=='invalid'}=={
        'nonempty_null_wave_determines_phi_to_one','zero_scale_gives_a_nonzero_future_time','negative_scale_preserves_future_time'}
    assert all(row['status'] in ('valid','invalid') for row in rows.values())
    assert not result['physical_compatibility_proved']


def test_equation_future_side_and_actual_transform_are_different():
    rows=equation_checks()['cases']
    assert len(rows)==8 and rows['baseline']['accepted']==[True]*4
    assert rows['baseline']['output']==['0','0','20','4']
    assert rows['negative_scale']['accepted']==rows['zero_scale']['accepted']==rows['emission_point']['accepted']==[True,True,True,False]
    assert rows['off_cone']['accepted']==[True,False,False,False]
    assert rows['unremoved_origin_constant']['accepted']==[False,True,False,False]


def test_front_membership_needs_all_points_and_nonempty_arrivals():
    result=front_checks();rows=result['cases']
    assert len(rows)==12 and rows['baseline']==[True]*3
    assert rows['missing_direction']==rows['extra_arrival']==[True,False,False]
    assert rows['empty_wave']==rows['nonlight_member']==[False]*3
    assert rows['empty_event_scope']==[True,False,False]
    assert rows['nonzero_emission_origin']==[False,True,True]
    assert rows['negative_scale']==rows['zero_scale']==rows['missing_moving_arrival']==[True,True,False]
    assert not result['continuous_spatial_coverage_proved']


def test_source_equations_and_extra_premises_bind_to_actual_roles():
    rows=source_binding_checks()['cases']
    assert len(rows)==9 and rows['baseline']==[True]*4
    assert rows['missing_transform_premise']==[True,True,False,False]
    assert rows['missing_record_existence']==rows['negative_scale']==rows['zero_scale']==[True,True,True,False]
    assert rows['wrong_moving_record']==[True,False,True,True]
    assert rows['wrong_emission']==[False,True,False,False]


def test_compatibility_requires_one_common_admissible_setting():
    result=compatibility_checks();rows=result['cases']
    assert len(rows)==7
    assert {name for name,value in rows.items() if value}=={'same_setting','not_every_setting'}
    assert not result['actual_physical_model_constructed']


def test_proof_not_yet_provided_is_scoped_and_not_falsity():
    result=proof_status_checks();rows=result['cases']
    assert len(rows)==7
    assert {name for name,value in rows.items() if not value}=={'supplied_here'}
    assert result['no_factiveness_inferred'] and result['later_stage_does_not_rewrite_prior_status']


def test_author_proof_claim_is_separate_from_our_sufficient_conditions():
    rows=attribution_checks()
    assert len(rows)==13 and rows['baseline']==[True]*9
    assert rows['wrong_task']==[True,False,True,True,True,True,True,True,True]
    assert rows['wrong_added_premise']==[True]*7+[False,True]
    assert rows['wrong_compatibility']==[True]*8+[False]


def test_source_alignment_keeps_the_proof_and_physical_limitations_explicit():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(86,92)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={f'M{i:04}' for i in range(140,148)}
    assert not result['facsimile_checked'] and result['verified_full_units']==0
    assert result['proof_attribution_is_not_a_verified_proof']


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,37)),(source_composed,(351,455))])
def test_basis_roundtrips_and_frozen_parent(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-origin-constants.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-9]==previous['statements'] and len(doc['statements'])==77
