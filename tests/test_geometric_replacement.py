import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_measurements import cut
from scripts.check_geometric_replacement import (
    alignment, attribution_checks, compared_results_projection, guarded,
    snapshot_checks, source_checks, tacit_checks,
)
from scripts.compose_geometric_replacement import ROOT, generic_composed, source_composed


def test_all_occupied_points_are_compared_and_one_equal_span_is_insufficient():
    result=snapshot_checks();rows=result['cases']
    assert len(rows)==512 and sum(r['accepted'] for r in rows)==19
    assert not any(r['accepted'] for r in rows if not r['first'] or r['first']!=r['second'])
    assert len(result['equal_span_counterexamples'])==2
    assert all(not r['same_geometry'] for r in result['equal_span_counterexamples'])
    assert not result['continuous_space_evaluated']


def test_finite_result_sort_projection_requires_two_unique_positive_equal_values():
    result=compared_results_projection();rows=result['cases']
    assert len(rows)==256 and sum(r['accepted'] for r in rows)==10
    assert not any(r['accepted'] for r in rows if not r['first'] or not r['second'] or 'zero' in r['first']+r['second'])
    assert next(r for r in rows if r['first']==['five','fivealias'] and r['second']==['five'])['accepted']
    assert not result['real_cut_existence_or_uniqueness_evaluated']


def test_same_body_same_epoch_and_all_selected_bodies_need_valid_rest_counterparts():
    result=source_checks();rows=result['cases']
    assert len(rows)==21
    assert {k for k,v in rows.items() if v}=={'baseline_two_bodies_with_separate_rest_configurations','negative_epoch_allowed'}
    assert not rows['same_shape_on_a_different_body'] and not rows['second_body_cannot_be_replaced']
    assert not rows['same_context_is_not_a_rest_counterpart']
    assert not result['all_physical_bodies_or_all_spatial_points_enumerated']
    assert not result['motion_histories_identified']


def test_tacit_assumption_needs_actual_use_and_explicit_nonstatement():
    rows=tacit_checks()
    assert len(rows)==9
    assert {k for k,v in rows.items() if all(v)}=={'101'}
    assert rows['111']==rows['001']==rows['different_assumption']==[False,False]


def test_attributed_reformulation_does_not_assert_the_contents_or_prove_equivalence():
    result=attribution_checks();rows=result['cases']
    assert len(rows)==7 and rows['baseline']==[True]*3
    assert rows['wrong_first_content']==[False,True,True]
    assert rows['wrong_second_content']==[True,False,True]
    assert rows['wrong_theory']==rows['reverse_reformulation']==[True,True,False]
    assert not result['attributed_contents_executed'] and not result['logical_equivalence_proved']


def test_full_cut_time_validity_and_two_method_result_domains_are_not_sampled():
    doc=candidate(source_composed()[0],'q[t[k scl[]][k ri[]]].')
    model=guarded(doc);model['ri']=lambda:'text'
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('body',),situations=('text',),primitives=model)
    doc=candidate(source_composed()[0],'''r ja[] a.r jb[] d.r jc[] d.r jd[] h[b] c.
q[k scm[k ja[] k jb[] k jc[] k jd[] p ba]].''')
    model=guarded(doc);model.update(ja=lambda:'body',jb=lambda:'motion',jc=lambda:'rest',jd=lambda:cut(-3))
    with pytest.raises(ValueError,match='rational number domain'):
        evaluate_document(doc,individuals=('body',),situations=('motion','rest'),primitives=model)


def test_old_kinematics_alignment_keeps_the_unit_partial():
    result=alignment()
    assert result['verified_full_units']==0 and len(result['segments'])==2
    assert all(r['unit']=='einstein-1905:u0034' and not r['full_semantic_equivalence'] for r in result['segments'])
    assert result['segments'][1]['math_id']=='M0051'


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,34)),(source_composed,(161,93))])
def test_basis_notation_roundtrips_and_prior_source_are_preserved(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-rod-comparison.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-3]==old['statements'] and len(doc['statements'])==17
