from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_derivation_modalities import (
    derivation_checks, necessity_checks, source_necessity_checks, attribution_checks, alignment,
)
from scripts.compose_derivation_modalities import ROOT, composed, generic_composed


def test_alternative_derivation_uses_one_available_method_and_its_own_steps():
    result=derivation_checks();rows=result['cases']
    assert len(rows)==14 and rows['baseline']==[True]
    assert all(value==[False] for name,value in rows.items() if name!='baseline')
    assert result['quoted_premises_and_conclusions_never_evaluated']
    assert result['same_method_stage_sequence_and_conclusion_required']
    assert result['actual_execution_not_required']


def test_necessity_is_nonempty_and_universal_and_does_not_supply_current_truth():
    result=necessity_checks();rows=result['cases'];assert len(rows)==32
    assert any(r['accepted']==[True,False,False] for r in rows)
    for row in rows:
        first,second=row['selected'];a,b=row['candidate_truths'];current=row['current_truth']
        necessary=(first or second) and (not first or a) and (not second or b)
        assert row['accepted']==[necessary,necessary and current,current]
    assert result['empty_candidates_do_not_establish_necessity']
    assert result['universal_candidates_not_single_success']


def test_source_alternative_keeps_composition_step_and_same_target_formula():
    result=derivation_checks(True);rows=result['cases']
    assert rows['baseline']==[True]
    for name in ('wrong_stage','wrong_rule_stage','different_baseline_conclusion','broken_chain',
        'missing_required_step','reversed_required_step','only_previous_method_available','required_step_in_other_method',
        'stage_not_earlier','same_stage'):
        assert rows[name]==[False]
    assert result['fixture_steps_not_claimed_as_historical_or_machine_checked_proof']


def test_source_necessity_preserves_group_content_and_selected_scope():
    result=source_necessity_checks();rows=result['cases']
    assert rows['baseline']==rows['false_current']==[True]
    for name in ('one_failing_candidate','empty_candidates','wrong_context','wrong_content'):assert rows[name]==[False]
    assert result['candidate_truth_is_not_a_proof_of_real_transform_group']


def test_attribution_does_not_replace_modality_by_bare_result():
    result=attribution_checks();rows=result['cases']
    assert rows['baseline']==[True,True]
    assert rows['possibility_replaced_by_result']==[False,True]
    assert rows['necessity_replaced_by_group']==[True,False]
    assert rows['wrong_author']==rows['wrong_scope']==rows['wrong_context']==[False,False]
    assert result['attributed_contents_not_executed_as_truth']


def test_alignment_adds_previously_excluded_modal_clauses_only():
    result=alignment();rows=result['segments']
    prose=next(r for r in rows if r['unit'].endswith('u0147') and 'source' in r)
    assert prose['source'].startswith('Wir hätten') and 'können.' in prose['source']
    assert 'Führen wir' not in prose['source']
    aside=next(r for r in rows if r['unit'].endswith('u0149'))
    assert aside['source']=='— wie dies sein muß —'
    assert {r['math_id'] for r in rows if 'math_id' in r}=={'M0274','M0275'}
    assert result['verified_full_units']==0 and not result['unique_historical_reading_claimed']


def test_parent_basis_and_quoted_modal_contents_roundtrip_in_both_notations():
    for compose,counts in ((generic_composed,(0,6,0)),(composed,(513,785,150))):
        text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-transform-group.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements']
