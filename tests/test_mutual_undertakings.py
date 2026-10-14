from copy import deepcopy
from itertools import product
import json

import pytest

from noema.grammar import parse
from scripts.check_mutual_undertakings import REPORT,build_report,structural_checks,setup,model_for,values,PEOPLE,SCENES
from scripts.compose_mutual_undertakings import ROOT,PARENT


@pytest.fixture(scope='module')
def result():return build_report()


@pytest.fixture(scope='module')
def source():return parse((ROOT/'examples/v014/kant-mutual-undertakings.noema').read_text(encoding='utf-8'))


def test_every_party_and_assigned_terms_are_required(result):
    assert len(result['generic']['cases'])==8
    for row in result['generic']['cases']:
        assert row['results']==[row['first'],row['first'],row['first'] and row['second'] and row['assigned']]
    assert result['generic']['standalone_agrees']


def test_occurrence_actor_and_declaration_are_independent(result):
    assert len(result['generic']['action_components'])==8
    for row in result['generic']['action_components']:assert row['result']==all(row['bits'])
    for name in ('split_act','split_time','wrong_owner'):
        assert result['generic']['contrasts'][name]==[False,False,False]


def test_empty_single_or_uncommitted_party_sets_do_not_form_mutual_undertaking(result):
    for name in ('empty_parties','one_party','uncommitted_party','ineligible'):
        assert result['generic']['contrasts'][name]==[True,True,False]


def test_each_party_can_have_a_different_past_or_current_witness(result):
    rows=result['generic']['contrasts']
    assert rows['alternative_witness']==[False,False,True]
    assert rows['current_second']==[True,True,True]
    for name in ('future_second','foreign_second','missing_second'):assert rows[name]==[True,True,False]
    for name in ('missing_anchor','cyclic'):assert rows[name]==[True,False,False]


def test_revision_alias_agreement_and_personal_arguments_are_not_interchangeable(result):
    rows=result['generic']['contrasts']
    for name in ('revised_assignment','alias_terms','other_agreement','different_arguments'):
        assert rows[name]==[True,True,False]
    assert rows['extra_arguments']==[True,True,True]
    assert result['generic']['terms_not_executed']
    assert result['generic']['unknown_records_refused']


def test_formation_and_normative_effects_are_independent_in_source_and_general_form(result):
    for row in result['source']['cases']:
        formed,absence=row['formed'],row['no_normative_effect']
        assert row['results']==[formed,formed and absence,not formed or absence]
    assert result['source']['global_normative_absence_is_explicit_oracle']
    text=(ROOT/'examples/v014/mutual-undertakings-core.noema').read_text(encoding='utf-8')
    doc=setup(text,True)
    # rh2 is the general conjunction; source hzch invokes the corresponding source bindings.
    ds={d['name']:d for d in doc['declarations']}
    source_call=deepcopy(doc['statements'][1]['body'])
    formation=ds['hzcg'];mapping={p['name']:a for p,a in zip(formation['parameters'],source_call['arguments'],strict=True)}
    def substitute(node):
        if isinstance(node,list):return [substitute(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='variable' and node['name'] in mapping:return deepcopy(mapping[node['name']])
        return {key:substitute(value) for key,value in node.items()}
    general=substitute(formation['body']);general['symbol']='rh2'
    general['arguments'] += [dict(kind='function_ref',symbol='h7k'),dict(kind='function_ref',symbol='h7l')]
    doc['statements']=[dict(kind='ask',body=general)]
    for formed,absence in product((False,True),repeat=2):
        assert values(doc,model_for(doc,second=formed,absence=absence),PEOPLE,SCENES)==[formed and absence]


@pytest.mark.parametrize('change',['party_scope','terms','bindings','actor','generic_effect','source_effect','actual','conditional_contract','conditional_context'])
def test_binding_and_scope_mutations_are_rejected(source,change):
    doc=deepcopy(source);ds={d['name']:d for d in doc['declarations']}
    if change in ('party_scope','terms','bindings'):
        every=ds['rhz']['body']['arguments'][1]['arguments'][1]
        if change=='party_scope':every['body']['arguments'][0]['arguments'][1]=dict(kind='variable',name=every['variable'])
        else:
            witness=every['body']['arguments'][1]['arguments'][1]['body']['body']
            if change=='terms':witness['arguments'][3]=deepcopy(witness['arguments'][2])
            else:witness['arguments'][4]['arguments'][0]=deepcopy(witness['arguments'][2])
    elif change=='actor':ds['hzcg']['body']['arguments'][10]['symbol']='dg'
    elif change in ('generic_effect','source_effect'):
        body=ds['rh2' if change=='generic_effect' else 'hzch']['body']
        body['arguments'][1]['arguments'][0]=deepcopy(body['arguments'][1]['arguments'][1])
    elif change=='actual':ds['hzci']['body']['body']['kind']='and'
    elif change=='conditional_contract':
        body=ds['hzci']['body']['body']['arguments'][1]['content']
        body['arguments'][0]=deepcopy(body['arguments'][1])
    else:ds['hzci']['body']['body']['arguments'][1]['situation']=dict(kind='variable',name='wrong')
    with pytest.raises(ValueError):structural_checks(doc)


def test_partial_annotation_preserves_parent_and_does_not_claim_completion(result,source):
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+7
    assert source['statements']==parent['statements'] and len(source['statements'])==15
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['roundtrips'] and all(result['structure'].values())
    assert len(result['alignment']['segments'])==2
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
