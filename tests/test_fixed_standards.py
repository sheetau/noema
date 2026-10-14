from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_fixed_standards import REPORT,build_report,structural_checks
from scripts.compose_fixed_standards import ROOT,PARENT


@pytest.fixture(scope='module')
def result():return build_report()


@pytest.fixture(scope='module')
def source():return parse((ROOT/'examples/v014/kant-fixed-standards.noema').read_text(encoding='utf-8'))


def test_version_identity_and_adoption_are_separate_at_every_point(result):
    rows=result['generic']['cases'];assert len(rows)==16
    for row in rows:
        vfirst,vmiddle,afirst,amiddle=row['bits']
        assert row['results']==[vfirst and afirst,all(row['bits']),all(row['bits'])]
    assert any(row['bits']==[True,False,True,True] and row['results']==[True,False,False] for row in rows)
    assert any(row['bits']==[True,True,True,False] and row['results']==[True,False,False] for row in rows)


def test_interval_cannot_drop_intermediate_points_or_the_anchor(result):
    rows=result['generic']['contrasts']
    for name in ('empty','gap','no_anchor','outside','past','cycle','missing_history'):
        assert rows[name]==[True,False,False]
    assert rows['singleton']==[True,True,True]


def test_standard_identity_and_unknown_records_are_not_guessed(result):
    assert result['generic']['contrasts']['organization']==[False,False,False]
    assert result['generic']['contrasts']['standard']==[False,False,False]
    assert result['generic']['unknown_records_refused']
    assert result['generic']['criterion_truth_not_executed']
    assert result['generic']['alias_with_identical_body_distinguished']


def test_undertaking_and_performance_and_normative_effect_are_independent(result):
    rows=result['source']['cases'];assert len(rows)==8
    for row in rows:
        formed,retained,absence=row['formed'],row['retained'],row['no_normative_effect']
        assert row['results']==[formed,formed and absence,not formed or absence,retained]
    assert result['source']['full_normative_absence_is_explicit_oracle']
    assert result['source']['unknown_performance_does_not_block_undertaking']
    assert result['source']['unknown_performance_evaluation_refused']


def test_closed_terms_keep_the_same_organization_standard_and_description(result):
    assert result['source']['contrasts']=={n:[False,False,True] for n in ('organization','standard','description')}
    assert result['source']['closed_terms_roundtrip']
    assert result['source']['standalone_agrees'] and result['generic']['standalone_agrees']


@pytest.mark.parametrize('change',['organization','standard','description','history','scope','order_anchor','convexity'])
def test_policy_and_context_mutations_are_rejected(source,change):
    doc=deepcopy(source);ds={d['name']:d for d in doc['declarations']}
    if change=='convexity':ds['rh4']['body']['arguments'][0]['symbol']='ta'
    elif change=='order_anchor':
        inner=ds['hzcj']['body']['arguments'][-1]['body']
        inner['body']['arguments'][-1]=deepcopy(inner['body']['arguments'][0])
    else:
        call=ds['rh5']['body']['body']['body']
        index={'organization':0,'standard':1,'description':2,'history':6,'scope':7}[change]
        if index<3:call['arguments'][index]=deepcopy(call['arguments'][(index+1)%3])
        else:call['arguments'][index]['arguments'][0]=dict(kind='variable',name='wrong')
    with pytest.raises(ValueError):structural_checks(doc)


def test_parent_and_partial_status_are_preserved(result,source):
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+4
    assert source['statements']==parent['statements'] and len(source['statements'])==15
    assert result['new_primitives']==result['new_author_statements']==0
    assert all(result['structure'].values()) and result['roundtrips']
    assert result['alignment']['segments'][0]['unit']=='kant-1784:u0013'
    assert result['alignment']['segments'][0]['status']=='explicit_interpretive_annotation'
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
