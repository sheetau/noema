from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_speed_deficits import (
    polynomial_checks, shortfall_checks, quotient_checks, bounded_claim_checks,
    source_checks, attribution_checks, alignment,
)
from scripts.compose_speed_deficits import ROOT, composed


def test_deficit_substitution_and_strict_bound_have_separate_algebraic_evidence():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==12
    for key in ('strict_shortfall_implies_positive_amount_below_limit','positive_amount_has_the_strict_shortfall',
        'shortfall_is_unique','substitution_preserves_original_quotient',
        'strict_deficits_make_numerator_and_denominator_positive','result_strictly_between_zero_and_limit','remaining_gap_identity'):
        assert rows[key]['status']=='valid'
    for key in ('zero_deficit_is_admitted','deficit_equal_to_limit_is_admitted','strict_inequality_alone_establishes_equation'):
        assert rows[key]['status']=='invalid'
    assert not result['all_real_cut_order_and_field_laws_proved']


def test_strict_shortfall_and_nonnegative_speed_domain_have_different_boundaries():
    rows=shortfall_checks()['cases']
    assert rows['ordinary']==rows['near_limit']==[True,True]
    assert rows['zero_amount']==rows['wrong_gap']==[False,True]
    assert rows['at_limit']==rows['negative_gap']==rows['negative_amount']==[False,False]


def test_exact_quotient_is_not_replaced_by_a_value_merely_below_limit():
    result=quotient_checks();rows=result['cases']
    assert rows['baseline']==rows['exchanged']==rows['very_near_limit']==[True,True]
    assert rows['wrong_value_below_limit']==rows['limit_deficit']==[False,True]
    assert rows['zero_deficit']==rows['wrong_value_at_limit']==[False,False]
    assert result['out_of_domain_reciprocal_values_do_not_bypass_guard']


def test_universal_claim_retains_zero_cases_and_cannot_be_finitely_enumerated():
    result=bounded_claim_checks();rows=result['instances']
    for key in ('ordinary','zero_first','zero_second','both_zero','near_boundary'):
        assert rows[key]==[True,True]
    for key in ('at_boundary','above_boundary','negative_input','zero_limit','invalid_cut'):
        assert rows[key]==[False,True]
    assert result['computed_result_is_required_to_be_a_valid_composition']
    assert result['full_real_quantification_not_replaced_by_samples']
    assert result['unbounded_quantification_rejected_by_finite_evaluator']


def test_source_substitution_uses_same_values_and_preserves_physical_binding():
    rows=source_checks()['cases']
    assert rows['baseline']==[True]*3
    assert rows['swapped_deficit_references']==rows['mismatched_moving_value']==[False,False,True]
    assert rows['wrong_result']==[True,False,False]
    assert rows['missing_rest_derivative']==rows['wrong_physical_context']==[True,False,True]
    assert rows['zero_velocity_boundary']==rows['light_velocity_boundary']==[False]*3


def test_proof_presentation_and_local_assumptions_do_not_evaluate_the_claim():
    result=attribution_checks();rows=result['cases']
    assert rows['baseline']==[True]*4
    assert rows['wrong_global_scope']==[False,True,True,False]
    assert rows['wrong_local_scope']==[True,False,False,True]
    assert rows['reversed_general_inference']==[False,True,True,True]
    assert rows['proof_target_replaced']==[True,True,True,False]
    assert result['quoted_claim_substitution_and_argument_not_evaluated']
    assert result['presentation_as_proof_does_not_certify_validity']


def test_source_ranges_preserve_strict_deficits_and_stop_before_light_invariance():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={'einstein-1905:u0143','einstein-1905:u0144'}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={'M'+str(i).zfill(4) for i in range(264,272)}
    prose=next(row['source'] for row in rows if row.get('source','').startswith('Aus dieser'))
    assert 'stets' in prose and 'positiv und kleiner' in prose
    assert result['zero_velocity_boundary_not_silently_added_to_strict_deficit_argument']
    assert result['following_light_speed_invariance_unwritten'] and result['verified_full_units']==0


def test_parent_preservation_basis_and_original_alphabet_roundtrip():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(496,740)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-axial-composition.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-4]==parent['statements'] and len(doc['statements'])==143
