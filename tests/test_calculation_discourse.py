import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_calculation_discourse import (
    chain_checks, appraisal_checks, source_chain_checks, source_appraisal_checks,
    symmetry_checks, attribution_checks, alignment,
)
from scripts.compose_calculation_discourse import ROOT, generic_composed, composed


@pytest.fixture(scope='module')
def chains():
    return chain_checks()['cases']


def test_finite_derivation_keeps_order_endpoints_and_permitted_transitions(chains):
    assert chains['baseline']['linked']
    for key in ('empty','reversed_order','broken_chain','wrong_start','wrong_end','unapproved_transition'):
        assert not chains[key]['linked'] and not chains[key]['low_burden']


def test_workload_belongs_to_same_chain_and_counts_each_occurrence(chains):
    assert chains['baseline']['low_burden'] and chains['baseline']['cost']=='3'
    assert chains['expensive_valid_chain']['linked'] and not chains['expensive_valid_chain']['low_burden']
    assert not chains['negative_cost']['low_burden']
    assert not chains['cheap_other_chain_cannot_replace_cost']['low_burden']
    assert chains['repeated_loop_is_counted']['cost']=='5'
    assert not chains['repeated_loop_is_counted']['low_burden']
    assert chains['same_loop_with_larger_budget']['low_burden']
    assert chains['twenty_repeated_steps']['cost']=='23' and chains['twenty_repeated_steps']['low_burden']
    assert all(row['cost_equals_independent_sum'] for row in chains.values())


def test_appraisal_retains_description_and_context_without_evaluating_content():
    result=appraisal_checks();rows=result['cases']
    assert rows['baseline']==[True,False] and rows['changed_description']==[False,True]
    for key in ('wrong_context','low_value','different_standard'):
        assert rows[key]==[False,False]
    assert result['truth_and_actual_attention_not_inferred']


def test_source_calculation_retains_its_premise_conclusion_and_cost_context():
    result=source_chain_checks();rows=result['cases']
    assert rows['baseline']==[True] and len(rows)==7
    assert all(row==[False] for key,row in rows.items() if key!='baseline')
    assert result['one_step_fixture_not_attributed_as_historical_procedure']
    assert result['physical_premise_and_result_contents_not_evaluated']


def test_source_appraises_symmetry_without_substituting_formula_truth():
    result=source_appraisal_checks();rows=result['cases']
    assert rows['baseline']==[True] and rows['formula_instead_of_symmetry']==[False]
    assert rows['wrong_context']==rows['low_value']==rows['high_standard']==[False]
    assert result['actual_symmetry_and_attention_not_evaluated']


def test_symmetry_has_algebraic_evidence_but_real_domain_is_not_enumerated():
    result=symmetry_checks();rows=result['finite_binding_cases']
    assert result['rational_algebra']['status']=='valid'
    assert rows['baseline']==rows['opposite_direction']==[True]
    assert rows['zero_light']==rows['negative_light']==[False]
    assert result['sampled_relation_callback_is_not_a_universal_proof']
    assert result['unbounded_real_domain_enumeration_rejected']


def test_attribution_keeps_derivation_direction_and_separate_assessments():
    result=attribution_checks();rows=result['cases']
    assert rows['baseline']==[True]*4
    assert rows['reversed_derivation']==[False,True,True,True]
    assert rows['swapped_appraisals']==[True,False,True,False]
    for key in ('wrong_author','wrong_scope','wrong_context'):
        assert rows[key]==[False]*4
    assert result['quoted_derivation_and_appraisal_contents_not_evaluated']


def test_alignment_excludes_parallel_motion_and_preserves_reading_limits():
    result=alignment();rows=result['segments']
    prose=[row for row in rows if 'source' in row]
    assert len(prose)==2 and prose[0]['source']=='Nach einfacher Rechnung ergibt sich:'
    assert prose[1]['source'].startswith('Es ist bemerkenswert,') and 'Hat auch' not in prose[1]['source']
    assert {row['math_id'] for row in rows if 'math_id' in row}=={'M0258','M0259'}
    assert result['verified_full_units']==0
    assert result['specific_calculation_steps_and_numeric_appraisals_not_supplied_by_source']


def test_generic_library_source_parent_and_alphabet_roundtrips():
    for builder,counts in ((generic_composed,(2,4)),(composed,(489,718))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'])==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-angle-composition.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-4]==parent['statements'] and len(doc['statements'])==138
