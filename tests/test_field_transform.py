from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_field_transform import (
    polynomial_checks, component_checks, region_checks, equation_checks, inverse_checks,
    premise_checks, attribution_checks, finite_refusal, alignment,
)
from scripts.compose_field_transform import ROOT, PARENT, composed, generic_composed


def test_mixing_inverse_uses_opposite_speed_and_normalized_beta():
    rows=polynomial_checks()['claims'];assert len(rows)==4
    assert rows['same_direction_mixing_is_its_own_inverse']['status']=='invalid'
    assert all(r['status']=='valid' for name,r in rows.items() if name!='same_direction_mixing_is_its_own_inverse')


def test_all_six_components_keep_signs_and_inverse_coordinate_arguments():
    result=component_checks();rows=result['cases'];assert len(rows)==17
    for name,value in rows.items():assert all(value)==name.startswith('baseline')
    assert result['inverse_coordinate_map_and_component_mixing_tested_separately']


def test_region_is_inverse_image_not_same_numeric_coordinates():
    result=region_checks();rows=result['cases'];assert len(rows)==6
    assert any(r['accepted'] and not r['unchanged_numeric_point_would_be_inside'] for r in rows.values())
    assert any(not r['accepted'] and r['unchanged_numeric_point_would_be_inside'] for r in rows.values())
    assert result['region_and_fields_use_same_inverse_map']


def test_old_six_equations_do_not_alone_imply_new_six_equations():
    result=equation_checks();rows=result['cases'];assert len(rows)==7
    assert rows['nonzero_divergence_counterexample']==[True,False]
    assert rows['counterexample_zero_speed_masks_failure']==[True,True]
    assert rows['plane_profile_forward_boost']==rows['plane_profile_reverse_boost']==[True,True]
    assert rows['arbitrary_affine_fields_not_solutions']==[False,False]
    assert result['counterexample']['time_derivative']=='15/4'
    assert result['six_old_curl_equations_alone_are_insufficient']
    assert not result['all_real_chain_rule_or_vacuum_covariance_proved']


def test_opposite_transform_recovers_both_fields_and_domain():
    result=inverse_checks();rows=result['cases'];assert len(rows)==6
    assert all(r==[True]*7 for r in rows.values())
    assert result['both_mixing_and_coordinate_pullback_reversed']


def test_source_premise_preserves_old_equations_transform_and_admissibility():
    result=premise_checks();rows=result['cases'];assert len(rows)==8
    for r in rows:assert r['accepted']==(r['old_equations'] and r['coordinate_transform'] and r['admissible'])
    assert result['premise_is_not_claimed_sufficient_for_conclusion']


def test_reported_inference_is_not_a_certificate_of_validity():
    result=attribution_checks();rows=result['cases'];assert len(rows)==7
    for name,r in rows.items():assert r==[name=='baseline']
    assert result['claimed_inference_does_not_certify_its_validity']
    assert result['quoted_contents_not_executed_as_truth']


def test_full_region_quantification_is_not_replaced_by_finite_examples():
    result=finite_refusal();assert result['refused'] and 'Cannot finitely quantify' in result['reason']


def test_source_formulas_keep_all_eighteen_derivative_positions():
    result=alignment()
    assert {r['math_id'] for r in result['segments']}=={'M0290','M0291','M0292','M0293'}
    assert len(result['source_derivative_order'])==18
    assert all('source' not in r for r in result['segments'])
    assert result['insufficient_displayed_premise_recorded'] and result['verified_full_units']==0


def test_parent_and_both_field_function_notations_roundtrip():
    for builder,counts in ((generic_composed,(3,2,0)),(composed,(533,813,154))):
        text,basis=builder();doc=parse(text);a=audit_basis(doc,basis)
        assert (a['primitive_count'],a['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            rendered=format_graph(doc,notation)
            assert parse(rendered)==parse(decode(encode(rendered,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements']
