import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_measurements import cut
from scripts.check_rod_comparison import (
    alignment, attribution_checks, candidate_checks, guarded, label_checks,
    projected_uniqueness, question_checks,
)
from scripts.compose_rod_comparison import ROOT, generic_composed, source_composed


def test_finite_value_carrier_projection_rejects_empty_ambiguous_and_invalid_results():
    result=projected_uniqueness()
    rows=result['cases']
    assert len(rows)==64 and sum(r['accepted'] for r in rows)==5
    assert not any(r['accepted'] for r in rows if not r['selected'] or not r['baseline_valid'])
    assert next(r for r in rows if r['selected']==['alias','baseline'] and r['equals_baseline'] and r['baseline_valid'])['accepted']
    assert not any(r['accepted'] for r in rows if r['selected']==['another','different'])
    assert not result['real_cut_domain_evaluated'] and not result['full_real_cut_uniqueness_proved']


def test_actual_candidate_kernel_keeps_value_baseline_validity_and_measurement_roles():
    rows=candidate_checks()
    assert len(rows)==16 and sum(r['accepted'] for r in rows)==1
    assert next(r for r in rows if r['accepted'])['conditions']==[True]*4


def test_length_names_preserve_frame_object_unit_and_moving_rod_qualification():
    rows=label_checks()
    assert len(rows)==11 and rows['baseline']==[True,True]
    assert rows['wrong_moving_frame']==[False,True]
    assert rows['wrong_rest_frame']==rows['motion_missing']==[True,False]
    assert rows['wrong_rod']==rows['wrong_value']==rows['wrong_context']==[False,False]


def test_announced_question_uses_its_method_and_setting():
    rows=question_checks()
    assert len(rows)==4 and [k for k,v in rows.items() if v]==['correct_method_b_setting']


def test_author_attribution_preserves_principles_conclusions_and_future_argument():
    result=attribution_checks();rows=result['cases']
    assert len(rows)==13
    assert rows['baseline']==rows['premise_order_irrelevant']==[True]*4
    assert rows['missing_second_principle']==rows['duplicated_first_principle']==[True,True,True,False]
    assert rows['names_swapped']==[False,False,True,True]
    assert rows['equality_based_on_second_principle']==[True,True,False,True]
    assert rows['wrong_future_argument']==[True,True,True,False]
    assert not result['quoted_physical_contents_executed'] and not result['derivation_completed']


def test_full_real_existence_uniqueness_and_answers_are_not_finitely_sampled():
    for query in ('q[t[k scc[]][k ri[]]].','q[t[k scd[]][k ri[]]].','q[k scf[]].'):
        doc=candidate(source_composed()[0],query)
        model=guarded(doc)
        model.update(ya=lambda:cut(5),ri=lambda:'text',yf=lambda:'slice')
        with pytest.raises(ValueError,match='rational number domain'):
            evaluate_document(doc,individuals=('object',),situations=('text','slice'),primitives=model)


def test_naming_and_announcement_alignment_is_partial_and_not_a_completed_proof():
    result=alignment()
    assert result['verified_full_units']==0 and len(result['segments'])==4
    assert {r['unit'] for r in result['segments']}=={'einstein-1905:u0032','einstein-1905:u0033'}
    assert {r['math_id'] for r in result['segments'] if 'math_id' in r}=={'M0049','M0050'}
    assert all(not r['full_semantic_equivalence'] for r in result['segments'])


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,31)),(source_composed,(146,83))])
def test_basis_notations_and_prior_source_are_preserved(compose,counts):
    text,basis=compose();doc=parse(text)
    audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-rod-setup.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-4]==old['statements'] and len(doc['statements'])==14
