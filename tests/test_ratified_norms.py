from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_ratified_norms import REPORT,build_report,structural_checks
from scripts.compose_ratified_norms import ROOT,PARENT


@pytest.fixture(scope='module')
def result():return build_report()


@pytest.fixture(scope='module')
def source():return parse((ROOT/'examples/v014/kant-ratified-norms.noema').read_text(encoding='utf-8'))


def test_absence_checks_both_polarities_of_requirements_and_permissions(result):
    rows=result['absence']['cases'];assert len(rows)==256
    for row in rows:
        assert row['results']==[not any(row['states'][0]),not any(row['states'][0]+row['states'][1])]
    assert result['absence']['standalone_agrees']
    assert result['absence']['target_truth_not_executed']


def test_known_empty_or_partial_lists_do_not_imply_global_absence(result):
    rows=result['absence']['selection'];assert len(rows)==4
    assert any(row['selected']==[False,False] and row['results']==[True,True] for row in rows)
    assert any(row['selected']==[True,False] and row['results']==[True,True] for row in rows)
    assert any(row['selected']==[False,True] and row['results']==[True,False] for row in rows)
    assert result['structure']['complete_list_distinguished']


def test_coverage_preserves_subject_role_description_and_ordered_arguments(result):
    assert result['absence']['coverage_contrasts']=={name:name=='baseline' for name in
        ('baseline','person','role','alias','reordered','extra','missing')}
    assert result['absence']['coverage_polarity_cases']==16
    assert result['absence']['coverage_clause_instantiated_not_full_completeness']
    assert result['absence']['unknown_norms_and_scope_refused']


def test_confirmation_and_normative_status_are_independent(result):
    rows=result['confirmation']['cases'];assert len(rows)==64
    assert any(row['results']==[True,True,True] and row['conditions']==[True,True] for row in rows)
    assert any(row['results']==[True,False,True] and row['conditions']==[False,False] for row in rows)
    assert any(row['results']==[False,True,False] and row['conditions']==[False,False] for row in rows)
    assert result['confirmation']['no_actual_confirmation_inferred']


def test_empty_approval_and_candidate_sets_are_not_silent_existential_claims(result):
    rows=result['confirmation']['contrasts']
    assert rows['empty_authorities']==rows['other_source']==[False,True,False]
    assert rows['empty_candidates']==[True,True,False]
    assert rows['one_candidate']==[True,True,True]
    assert rows['unknown_confirmation']==rows['unknown_condition']=='refused'


def test_source_keeps_current_and_hypothetical_contexts_separate(result):
    rows=result['source']['cases'];assert len(rows)==16
    for row in rows:assert row['result']==(row['current'] and (not row['confirmed'] or row['first'] and row['second']))
    assert result['source']['standalone_agrees']
    assert result['source']['full_normative_absence_is_explicit_oracle']
    assert result['source']['unknown_full_absence_refused']


def test_all_descriptions_and_argument_lists_are_not_finitely_enumerated(result):
    rows=result['unbounded'];assert set(rows)=={'rhq','rhs','rht','bindings'}
    assert all('description domain' in rows[n] for n in ('rhq','rhs','rht'))
    assert 'unbounded sequence domain' in rows['bindings']


@pytest.mark.parametrize('change',['global_scope','coverage_scope','coverage_omitted','allowed','contract','candidate_anchor','condition'])
def test_scope_and_binding_mutations_are_rejected(source,change):
    doc=deepcopy(source);ds={d['name']:d for d in doc['declarations']}
    if change=='global_scope':ds['rhq']['body']['kind']='exists'
    elif change=='coverage_scope':ds['rhs']['body']['kind']='exists'
    elif change=='coverage_omitted':ds['rht']['body']['arguments'][1]=deepcopy(ds['rht']['body']['arguments'][0])
    elif change=='allowed':ds['hzce']['body']['arguments'][3]['symbol']='h7k'
    elif change=='contract':ds['hzcf']['body']['body']['arguments'][0]['arguments'][0]=deepcopy(ds['hzcf']['body']['body']['arguments'][0]['arguments'][1])
    elif change=='candidate_anchor':
        scope=ds['hzcf']['body']['body']['arguments'][1]['arguments'][1]
        scope['body']['arguments'][0]=deepcopy(scope['body']['arguments'][1])
    else:ds['hzcf']['body']['body']['arguments'][1]['arguments'][4]['symbol']='rhu'
    with pytest.raises(ValueError):structural_checks(doc)


def test_partial_source_annotation_does_not_claim_full_invalidity_translation(result,source):
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+10
    assert source['statements']==parent['statements'] and len(source['statements'])==15
    assert result['new_primitives']==result['new_author_statements']==0
    assert all(result['structure'].values()) and result['roundtrips']
    assert len(result['alignment']['segments'])==3
    assert all(s['unit']=='kant-1784:u0013' and s['status']=='explicit_interpretive_annotation' for s in result['alignment']['segments'])
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
