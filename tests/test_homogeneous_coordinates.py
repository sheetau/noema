import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_homogeneous_coordinates import (
    alignment, attribution_checks, canonical_map_checks, graph_binding_checks,
    increment_checks, matrix_checks, polynomial_checks, signed_product_checks,
)
from scripts.compose_homogeneous_coordinates import ROOT, generic_composed, source_composed


def test_affine_matrix_rows_keep_separate_offsets_and_all_components():
    result=matrix_checks();rows=result['cases']
    assert len(rows)==10
    assert rows['baseline']==rows['zero_offset']==rows['constant_map']==[True,True]
    assert rows['wrong_x']==rows['wrong_y']==rows['wrong_z']==rows['wrong_t']==[True,False]
    assert rows['duplicate_axis']==rows['empty_axes']==[False,False]
    assert not result['all_real_inputs_proved']


def test_local_increment_agreement_is_not_a_global_homogeneity_proof():
    result=increment_checks();rows=result['cases']
    assert len(rows)==8
    assert rows['affine_with_offset'] and rows['affine_without_offset']
    assert not rows['quadratic']
    assert rows['quadratic_zero_shift'] and rows['quadratic_same_base']
    assert not result['global_homogeneity_proved']


def test_rational_affine_lemmas_do_not_force_zero_origins_or_prove_the_converse():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==5
    assert rows['affine_increment_is_base_independent']['status']=='valid'
    assert rows['origin_maps_to_offset']['status']=='valid'
    assert rows['affine_form_always_preserves_origin']['status']=='invalid'
    assert rows['quadratic_increment_is_base_independent']['status']=='invalid'
    assert not result['homogeneity_implies_real_affinity_proved']


def test_signed_coefficients_reuse_the_existing_positive_cut_product():
    result=signed_product_checks()
    assert len(result['cases'])==9 and all(result['cases'].values())
    assert not result['full_real_field_laws_proved']


def test_map_cannot_use_unselected_roles_as_hidden_coordinates():
    rows=canonical_map_checks()
    assert len(rows)==8
    assert {name for name,result in rows.items() if result}=={'baseline','changed_hidden_input','map_reads_hidden_input'}


def test_transform_must_match_the_complete_prior_coordinate_correspondence():
    rows=graph_binding_checks()['cases']
    assert len(rows)==6 and {name for name,value in rows.items() if value}=={'baseline'}


def test_necessary_and_obvious_are_attributed_without_executing_the_claim():
    rows=attribution_checks()
    assert rows['baseline']==[True,True]
    assert rows['wrong_premise']==[False,False]
    assert rows['wrong_conclusion']==rows['wrong_obviousness']==rows['wrong_task']==[True,False]


def test_source_alignment_discloses_affine_and_operational_readings():
    result=alignment();row=result['segments'][0]
    assert row['unit']=='einstein-1905:u0047' and row['start']==0
    assert result['affine_reading_with_unfixed_origins'] and result['homogeneity_is_operational_interpretation']
    assert not result['facsimile_checked'] and not row['full_semantic_equivalence']
    assert result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,9)),(source_composed,(260,235))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-coordinate-correspondence.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==36
