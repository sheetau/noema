import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_observer_judgments import (
    alignment, attribution_checks, criterion_checks, judgment_checks, source_checks,
)
from scripts.check_described_appraisals import candidate
from scripts.check_rod_comparison import guarded
from scripts.check_rod_measurements import ARITHMETIC, cut
from scripts.compose_observer_judgments import ROOT, generic_composed, source_composed


def test_polarity_absence_error_and_description_identity_are_independent():
    rows=judgment_checks()['cases']
    assert len(rows)==16
    mistaken=next(r for r in rows if r['positive'] and not r['negative'] and not r['first_criterion'] and r['second_criterion'])
    assert mistaken['results']==[True,False,False,False,False,False,False,False]
    assert any(r['results'][:2]==[True,True] for r in rows)
    assert all(r['results'][4:]==[False]*4 for r in rows)


def test_observer_quantification_and_opposite_judgments_do_not_evaluate_content():
    result=source_checks();rows=result['cases']
    assert len(rows)==14 and rows['baseline']==rows['outsider_dissents']==[True,True,True]
    assert rows['missing_moving_b']==rows['wrong_moving_criterion']==[False,True,False]
    assert rows['one_rest_observer_dissents']==rows['no_rest_observers']==[True,False,False]
    assert rows['wrong_context']==[False,False,False]
    assert not result['judgment_contents_executed']


def test_same_pair_can_fail_midpoint_and_pass_rest_frame_tracking():
    result=criterion_checks();rows=result['cases']
    assert len(rows)==9 and rows['moving']==[False,True]
    assert rows['stationary_limit']==[True,True]
    assert rows['clock_b_not_tracking']==rows['different_clock']==[False,False]
    assert not result['full_real_cut_midpoint_evaluated']


def test_hypothetical_author_claim_and_contrast_are_not_actual_observer_facts():
    rows=attribution_checks()
    assert len(rows)==9 and rows['baseline']==[True,True]
    assert rows['wrong_premise']==rows['wrong_conclusion']==[False,True]
    assert rows['reversed_contrast']==rows['missing_contrast']==[True,False]
    text=source_composed()[0]
    doc=parse(text)
    defs={d['name']:d for d in doc['declarations'] if d['kind']=='definition'}
    def symbols(node):
        if isinstance(node,dict):
            return ({node['symbol']} if 'symbol' in node else set()) | set().union(*(symbols(v) for v in node.values()))
        if isinstance(node,list):return set().union(*(symbols(v) for v in node))
        return set()
    premise=symbols(defs['sdu'])
    for name in ('scy','sdh','sdj','bg','yb'):
        assert name in premise


def test_full_cut_midpoint_is_not_silently_replaced_with_integer_fixture():
    doc=candidate(source_composed()[0],'q[t[k sdo[]][k yd[]]].')
    model=guarded(doc);model.update(ARITHMETIC)
    model.update(yd=lambda:'motion',zas=lambda:'first',zat=lambda:'middle',zau=lambda:'last',
        zag=lambda record:cut({'first':2,'middle':6,'last':8}[record]))
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('first','middle','last'),situations=('motion',),primitives=model)


def test_alignment_claims_only_the_observer_sentence_as_a_partial_reading():
    result=alignment();row=result['segments'][0]
    assert row['unit']=='einstein-1905:u0040' and row['start']>0
    assert row['source'].startswith('Mit dem bewegten Stabe') and row['source'].endswith('würden.')
    assert not row['full_semantic_equivalence'] and not result['facsimile_checked']
    assert result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(0,2)),(source_composed,(193,123))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-moving-light-trip.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-2]==old['statements'] and len(doc['statements'])==23
