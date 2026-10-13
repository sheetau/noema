from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_parallel_composition import (
    polynomial_checks, coordinate_checks, graph_checks, setup_checks,
    attribution_checks, alignment,
)
from scripts.compose_parallel_composition import ROOT, composed


def test_combined_speed_beta_and_all_coordinates_have_algebraic_evidence():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==9
    for key in ('two_admissible_speeds_have_positive_denominator','composed_speed_remains_admissible',
        'combined_coefficient_is_positive','combined_coefficient_satisfies_beta_of_composed_speed',
        'two_transformations_equal_one_with_composed_speed','transverse_coordinates_are_preserved',
        'opposite_speeds_compose_to_zero'):assert rows[key]['status']=='valid'
    assert rows['ordinary_addition_replaces_composed_speed']['status']=='invalid'
    assert rows['betas_multiply_without_cross_term']['status']=='invalid'
    assert not result['all_real_cut_field_and_root_laws_proved']


def test_composition_keeps_middle_record_time_and_transverse_coordinates():
    result=coordinate_checks();rows=result['cases']
    for key in ('baseline','opposite','zero_first','zero_second','both_zero','different_speeds','negative_pair'):
        assert rows[key]['accepted']==[True,True]
    assert rows['wrong_middle']['accepted']==[False,True]
    for key in ('wrong_time','wrong_transverse','naive_beta_product'):assert rows[key]['accepted']==[False,False]
    assert rows['opposite']['first']==rows['opposite']['last']
    assert result['all_four_coordinates_checked'] and result['same_middle_record_required']


def test_all_three_records_must_exist_for_same_event_and_all_aliases_must_agree():
    result=graph_checks();rows=result['cases']
    assert rows['baseline']==rows['duplicate_alias']==[True,True]
    assert rows['wrong_middle']==[False,True]
    for key in ('missing_middle','missing_final','different_event','empty_scope','conflicting_alias','wrong_time','wrong_setting','same_frame'):
        assert rows[key]==[False,False]
    assert result['all_alias_records_checked'] and result['empty_or_missing_records_rejected']


def test_third_frame_motion_retains_reference_axis_velocity_units_and_context():
    rows=setup_checks()['cases']
    assert rows['baseline']==[True]
    for key in ('wrong_reference','wrong_axis','wrong_speed','wrong_unit','wrong_setting','same_frame'):assert rows[key]==[False]


def test_setup_and_attributed_consequence_are_separate():
    result=attribution_checks();rows=result['cases']
    assert rows['baseline']==[True,True]
    assert rows['setup_replaced_by_result']==[False,True]
    assert rows['reversed_inference']==[True,False]
    assert rows['wrong_scope']==rows['wrong_context']==rows['wrong_author']==[False,False]
    assert result['quoted_physics_not_evaluated_as_global_truth']


def test_alignment_excludes_alternative_derivability_and_group_claim():
    result=alignment();rows=result['segments']
    prose=next(r for r in rows if r['unit'].endswith('u0147') and 'source' in r)
    assert prose['source'].startswith('Führen wir') and 'hätten' not in prose['source']
    tail=next(r for r in rows if r['unit'].endswith('u0149'))
    assert tail['source']=='tritt;'
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M'+str(i).zfill(4) for i in range(276,286)}
    assert result['alternative_derivation_modality_unwritten'] and result['following_group_claim_unwritten']
    assert result['verified_full_units']==0


def test_parent_preservation_meaning_basis_and_original_alphabet():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(504,758)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-light-invariance.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements'] and len(doc['statements'])==147
