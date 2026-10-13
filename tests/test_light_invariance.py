from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_light_invariance import (
    polynomial_checks, expression_checks, fixed_point_checks, source_checks,
    attribution_checks, alignment,
)
from scripts.compose_light_invariance import ROOT, composed


def test_specialized_algebra_keeps_domain_and_conclusion_separate():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==9
    for name in ('specialized_equation_iff_nonzero_denominator_and_unchanged_value',
        'nonnegative_subluminal_input_has_positive_denominator','bounded_input_constructs_unchanged_result',
        'signed_subluminal_input_constructs_unchanged_result','exchange_of_inputs_preserves_specialized_equation',
        'singular_input_is_rejected'):
        assert rows[name]['status']=='valid'
    for name in ('equality_alone_establishes_equation_at_singularity','equation_alone_implies_subluminal_input',
        'unchanged_value_without_equation_is_sufficient'):
        assert rows[name]['status']=='invalid'
    assert not result['all_real_cut_field_laws_proved']


def test_expression_does_not_admit_zero_denominator_or_expand_source_domain():
    result=expression_checks();rows=result['cases']
    for name in ('ordinary','zero_input','near_upper_boundary'):assert rows[name]==[True]*4
    assert rows['wrong_result']==[True,False,False,True]
    for name in ('negative_subluminal','near_singular_boundary','at_light_boundary','above_light_boundary','negative_denominator'):
        assert rows[name]==[False,True,True,True]
    assert rows['singular_input']==rows['zero_limit']==rows['invalid_cut']==[False,False,True,True]
    assert result['undefined_reciprocal_fallback_cannot_admit_singularity']
    assert result['unbounded_quantification_rejected_by_finite_evaluator']


def test_fixed_point_relation_applies_to_nonphysical_operations():
    assert fixed_point_checks()=={'identity_at_three':True,'translation_by_one_at_three':False,
        'squaring_at_zero':True,'squaring_at_three':False}


def test_source_equation_uses_reviewed_value_and_same_physical_context():
    result=source_checks();rows=result['cases']
    assert rows['baseline']==rows['zero_input']==[True]
    for name in ('wrong_result','different_limit','raw_transcription_result','at_light_boundary',
        'negative_input','singularity','missing_speed_binding','wrong_physical_context'):assert rows[name]==[False]
    assert result['frame_speed_not_set_to_light_speed']


def test_attributed_inference_is_not_an_unconditional_physical_assertion():
    result=attribution_checks();rows=result['cases']
    assert rows['baseline']==[True,True]
    assert rows['wrong_author']==rows['wrong_scope']==rows['wrong_context']==[False,False]
    assert rows['reversed_inference']==[False,True]
    assert rows['formula_replaced_by_general_claim']==[True,False]
    assert result['quoted_content_not_evaluated_as_global_truth']


def test_alignment_retains_snapshot_hash_and_explicit_correction():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={'einstein-1905:u0145','einstein-1905:u0146'}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M0272','M0273'}
    corrected=next(r for r in rows if r.get('math_id')=='M0273')
    assert corrected['correction_id']=='einstein-1905:M0273:denominator-light-speed'
    assert corrected['math_sha256']!=corrected['reviewed_math_sha256']
    assert result['reviewed_layer_explicit'] and not result['snapshot_modified']
    assert result['following_transformation_composition_unwritten'] and result['verified_full_units']==0


def test_new_document_preserves_parent_and_original_alphabet():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(498,748)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-speed-deficits.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements'] and len(doc['statements'])==145
