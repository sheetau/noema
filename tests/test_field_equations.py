from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_field_equations import (
    polynomial_checks, slice_checks, jet_checks, source_checks, finite_refusals, attribution_checks, alignment,
)
from scripts.compose_field_equations import ROOT, PARENT, composed, generic_composed


def test_positive_denominator_and_scaling_with_sign_counterexample():
    result=polynomial_checks();rows=result['claims'];assert len(rows)==4
    assert rows['reversing_spatial_difference_preserves_equation']['status']=='invalid'
    assert all(r['status']=='valid' for name,r in rows.items() if name!='reversing_spatial_difference_preserves_equation')
    assert result['rational_algebra_not_a_derivative_proof']


def test_each_partial_changes_only_one_coordinate_in_the_same_domain():
    result=slice_checks();rows=result['cases'];assert len(rows)==36
    for name,value in rows.items():assert value==[name.endswith(':baseline')]
    assert result['other_coordinates_held_fixed'] and result['relative_domain_passed_to_derivative']
    assert result['derivative_relation_is_explicit_affine_fixture_oracle']


def test_all_eighteen_derivatives_are_bound_to_the_same_fields_and_point():
    result=jet_checks();rows=result['cases'];assert len(rows)==23
    for name,value in rows.items():assert value==[name=='baseline']
    assert result['partial_derivatives_are_oracles']


def test_six_equations_detect_each_used_derivative_and_keep_v_positive():
    result=jet_checks(True);rows=result['cases'];assert len(rows)==25
    for name,value in rows.items():assert value==[name in ('baseline','zero_fields','static_nonzero_divergence')]
    assert not result['partial_derivatives_are_oracles']
    assert result['all_six_nonzero_time_rates_exercised']


def test_source_keeps_rest_frame_field_order_and_same_light():
    result=source_checks();rows=result['cases'];assert len(rows)==7
    for name,value in rows.items():assert value==[name=='baseline']
    assert result['full_region_equation_is_explicit_oracle']


def test_finite_evaluator_does_not_claim_a_real_derivative_or_global_solution():
    rows=finite_refusals();assert len(rows)==3
    assert all(r['refused'] and 'Cannot finitely quantify' in r['reason'] for r in rows.values())


def test_assumption_does_not_evaluate_its_quoted_content_as_physical_truth():
    result=attribution_checks();rows=result['cases'];assert len(rows)==5
    for name,value in rows.items():assert value==[name=='baseline']
    assert result['assumed_content_not_executed_as_physical_truth']


def test_source_table_keeps_six_equations_without_invented_force_definitions():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={'einstein-1905:u0153','einstein-1905:u0154'}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M0286','M0287'}
    assert len(result['source_derivative_order'])==18
    assert result['source_derivative_order'][:6]==[['∂X','∂t'],['∂N','∂y'],['∂M','∂z'],['∂L','∂t'],['∂Y','∂z'],['∂Z','∂y']]
    assert result['electric_magnetic_force_and_vacuum_concepts_unwritten']
    assert result['divergence_conditions_not_added'] and result['verified_full_units']==0


def test_previous_document_preserved_and_field_functions_roundtrip():
    for builder,counts in ((generic_composed,(4,1,0)),(composed,(532,798,153))):
        text,basis=builder();doc=parse(text);a=audit_basis(doc,basis)
        assert (a['primitive_count'],a['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            formatted=format_graph(doc,notation)
            assert parse(formatted)==parse(decode(encode(formatted,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements']
