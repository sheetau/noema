import json

import pytest

from noema.grammar import parse
from scripts.check_contained_conflict import REPORT,build_report
from scripts.compose_contained_conflict import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_parts_may_each_be_compatible_without_a_joint_model(result):
    # A and B separately coexist with not(A and B), but A and B together do not.
    row=next(row for row in result['finite']['logical_collections']
        if row['parts']==['c1','c2'] and row['standard']==['c3'])
    assert row['results']==[False,True,True,False,True,False]


def test_empty_and_inconsistent_ranges_do_not_prove_relational_opposition(result):
    assert len(result['finite']['scope_cases'])==16
    row=next(row for row in result['finite']['scope_cases'] if not any(row['selected']))
    assert row['results']==[False]*6
    edge=result['finite']['edge_cases']
    assert edge['false_part']==[False,False,True,False,False,False]
    assert edge['false_standard']==[False,True,False,False,False,False]
    assert edge['opposite_claims']==[False,True,True,False,True,True]
    assert edge['inconsistent_document'][1:5]==[False,True,False,False]
    assert edge['empty_both']==[True,True,True,True,False,False]


def test_joint_satisfiability_requires_one_shared_witness(result):
    rows=result['finite']['logical_collections']
    assert len(rows)==64
    for row in rows:
        _,first,second,joint,opposed,contained=row['results']
        assert not joint or (first and second and not opposed and not contained)
        assert opposed==(first and second and not joint)


def test_believed_witness_can_vary_but_de_re_witness_cannot(result):
    row=next(row for row in result['finite']['belief_cases'] if row['selected']==[True,True] and
        row['judged']==[True,False,False,True] and row['actual']==[False,False])
    assert row['results']==[False,True,True,False,False,True]
    for row in result['finite']['belief_cases']:
        assert not row['results'][3] or row['results'][2]


def test_absent_belief_is_not_belief_of_absence(result):
    rows=result['finite']['belief_cases']
    assert len(rows)==256
    for row in rows:
        if not any(row['selected']):assert row['results'][2:5]==[False]*3
    row=next(row for row in rows if row['selected']==[True,True] and
        row['judged']==[True,False,False,False] and row['actual']==[False,False])
    assert row['results'][2:5]==[False,False,False]


def test_false_beliefs_and_actual_conflict_are_independent(result):
    rows=result['finite']['belief_cases']
    for judged in ([True]*4,[False]*4):
        samples=[row for row in rows if row['selected']==[True,True] and row['judged']==judged]
        assert len(samples)==4
        assert len({tuple(row['results'][2:5]) for row in samples})==1
        for row in samples:
            assert row['results'][:2]==[any(row['actual']),not any(row['actual'])]
            assert row['results'][5]==(not any(row['actual']))


def test_belief_scope_and_membership_anchor_are_preserved(result):
    rows=result['finite']['binding_contrasts']
    assert len(rows)==10
    for name in ('person','document','standard','anchor'):
        assert rows['candidates_'+name][2:5]==[False]*3
    assert rows['membership_only_at_candidates']==[False,True,False,False,True,False]
    assert rows['clashes_point']==[False,True,True,True,False,True]


def test_unknown_inputs_are_not_empty_or_false_and_norms_are_not_inferred(result):
    assert result['finite']['unknown_inputs_refused']
    assert result['finite']['relation_based_belief_independent_of_content_truth']
    assert result['finite']['inner_message_truth_and_norms_not_executed']
    assert not result['finite']['general_logical_or_religious_contradiction_proved']


def test_source_and_independent_notation_preserve_the_parent(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+12
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['finite']['standalone_agrees'] and result['roundtrips']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
