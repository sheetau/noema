from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_transform_group import (
    finite_group_checks, polynomial_checks, coordinate_checks, domain_checks,
    quantification_checks, attribution_checks, alignment,
)
from scripts.compose_transform_group import ROOT, composed, generic_composed


def test_group_requires_more_than_closure_and_does_not_require_commutativity():
    result=finite_group_checks();rows=result['cases']
    assert rows['cyclic_three']==rows['noncommutative_permutations']==[True]*5
    assert rows['nonassociative_loop']==[True,False,True,True,False]
    assert rows['empty_carrier']==[True,True,False,True,False]
    assert rows['not_closed']==[False,True,True,False,False]
    assert rows['left_projection']==rows['wrong_identity']==[True,True,False,False,False]
    assert rows['wrong_inverse']==rows['inverse_outside_carrier']==[True,True,True,False,False]
    assert result['no_physical_primitives_used'] and result['commutativity_not_required']


def test_signed_composition_laws_and_map_faithfulness_have_algebraic_evidence():
    result=polynomial_checks();rows=result['claims']
    for key in ('composition_closed_on_signed_subluminal_speeds','composition_is_associative',
        'zero_is_a_two_sided_identity','negative_speed_is_a_two_sided_inverse_in_same_domain',
        'same_unit_time_probe_determines_speed'):assert rows[key]['status']=='valid'
    assert rows['positive_only_domain_contains_every_inverse']['status']=='invalid'
    assert rows['zero_event_alone_determines_speed']['status']=='invalid'
    assert not result['all_real_cut_field_and_root_laws_proved']


def test_four_coordinate_action_preserves_composition_identity_and_inverse():
    result=coordinate_checks();rows=result['cases']
    for key in ('ordinary','negative','zero_speed','inverse_pair','zero_event','time_probe','extra_role_values'):
        assert rows[key]==[True]*5
    assert rows['wrong_time']==rows['wrong_transverse']==[True,True,True,True,False]
    assert result['coordinate_equality_not_function_implementation_identity']
    assert result['only_four_roles_are_coordinate_components']


def test_velocity_group_contains_both_signs_and_zero_but_excludes_light_boundaries():
    result=domain_checks();rows=result['cases']
    for key in ('positive','negative','zero','near_positive_boundary','near_negative_boundary'):assert rows[key]==[True]
    for key in ('positive_boundary','negative_boundary','outside','zero_light','negative_light','invalid_cut'):assert rows[key]==[False]
    assert result['both_signs_and_zero_retained'] and result['light_speed_boundaries_excluded']


def test_real_group_and_extensional_map_equality_are_not_finite_samples():
    result=quantification_checks()
    assert set(result['rejections'])=={'s47','s5d','s5e'}
    assert set(result['rejections'].values())=={'Cannot finitely quantify the rational number domain'}
    assert result['real_group_and_function_equality_not_sampled']


def test_authors_inference_keeps_group_distinct_from_composition():
    result=attribution_checks();rows=result['cases']
    assert rows['baseline']==[True]
    for key in ('wrong_author','wrong_scope','wrong_context','reversed_inference','closure_replaces_group'):assert rows[key]==[False]
    assert result['closure_alone_not_certified_as_sufficient']


def test_source_alignment_excludes_unresolved_necessity_parenthesis():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={'einstein-1905:u0149'}
    assert len(rows)==2 and 'Gruppe bilden.' in rows[1]['source']
    assert not any('sein muß' in r['source'] for r in rows)
    assert result['necessity_parenthesis_unwritten'] and result['alternative_derivation_modality_unwritten']
    assert result['verified_full_units']==0


def test_bases_parent_preservation_and_original_alphabet():
    for compose,counts in ((generic_composed,(0,5,0)),(composed,(505,778,148))):
        text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-parallel-composition.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements']
