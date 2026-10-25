from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.shared_evidence import *
from scripts.check_shared_evidence import (doc,values,model,query,claim,ref,records,unknown,describe,
    belief_checks,proof_checks,origin_checks,entailment_checks,binding_diagnostics,example,example_model,example_expected,EXAMPLES)

def test_shared_inventory_preserves_six_existing_definitions_and_contracts():
    d=composed();b=basis();byname={x['name']:x for x in d['declarations']}
    assert len(byname)==31 and len(MEANINGS)==25 and not b['primitives']
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['definitions'])==set(b['public_contracts'])==set(byname)
    for source in SOURCES:
        old={x['name']:x for x in parse((ROOT/source['document']).read_text(encoding='utf-8'))['declarations']}
        oldbasis=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        for name in source['names']:
            assert byname[name]==old[name]
            assert b['definitions'][name]==oldbasis['definitions'][name]
            assert b['public_contracts'][name]==oldbasis['public_contracts'][name]
    for d in raw()['declarations']:
        contract=b['public_contracts'][d['name']]
        assert [p['sort'] for p in d['parameters']]==[p['sort'] for p in contract['arguments']]
        assert len(set(p['role'] for p in contract['arguments']))==len(d['parameters'])
        assert d['result']==contract['result']

def test_belief_candidate_truth_and_awareness_models():
    assert belief_checks()==dict(models=128,people=2,situations=2,checks_per_model=6)

def test_all_two_record_dependency_graphs_and_orders():
    assert proof_checks()==dict(models=512,records=2,orders=8,checks_per_model=9)

def test_shared_empty_and_separate_provenance():
    assert origin_checks()==dict(models=288,records=2,origins=2,checks_per_model=7)

def test_entailment_scopes_empty_premises_and_actual_truth():
    assert entailment_checks()==dict(models=192,situations=2,premise_lengths=[0,1,2],checks_per_model=2)

def test_every_social_tuple_slot_with_fixed_witnesses():
    rows=binding_diagnostics();assert len(rows)==26 and not any(x['result'] for x in rows)

@pytest.mark.parametrize('mode',EXAMPLES)
def test_native_connected_provenance_and_mistaken_belief(mode):
    assert parse((ROOT/EXAMPLES[mode]).read_text(encoding='utf-8'))==example(mode)
    assert values(example(mode),example_model(),('a','b','c'))==example_expected(mode)

def test_equivalent_but_unrecognized_description_does_not_inherit_awareness():
    assert values(doc([query('beliefaccepted'),query('beliefaccepted',description=claim('otherclaimform'))]),model())==[True,False]

def test_report_requires_the_same_description_even_when_both_records_and_relay_exist():
    m=model(descriptionat=lambda n,p,q:q if n=='b' else p,recorded=lambda *a:True,relayed=lambda *a:True)
    assert values(doc([query('evidencereported')]),m)==[False]

def test_separate_sources_with_different_descriptions_are_not_corroboration():
    m=model(descriptionat=lambda n,p,q:q if n=='b' else p,parents=lambda *a:False)
    assert values(doc([query('proofseparateorigins'),query('proofcorroborates')]),m)==[True,False]

@pytest.mark.parametrize('name',['evidenceobserved','evidencereported','evidenceinferred','beliefnonempty'])
def test_recording_evidence_does_not_execute_its_claim(name):
    assert values(doc([query(name)]),model(payload=unknown))==[True]

@pytest.mark.parametrize('name',['beliefaccepted','beliefdenied','beliefunsettled','beliefaccurate','beliefmistaken','evidenceentails','evidencepremisestrue','beliefgrounded'])
def test_content_evaluation_rejects_unknown_truth_instead_of_assuming_false(name):
    with pytest.raises(ValueError,match='Unknown'):values(doc([query(name)]),model(payload=unknown))

@pytest.mark.parametrize('field',['recorded','holders','descriptionat','observed','events'])
def test_observation_rejects_unknown_required_interpretations(field):
    with pytest.raises(ValueError,match='Unknown'):values(doc([query('evidenceobserved')]),model(**{field:unknown}))

def test_provenance_rejects_unknown_inputs_even_if_a_guard_would_fail():
    with pytest.raises(ValueError,match='Unknown'):
        values(doc([query('prooforigin')]),model(local=lambda n:False,roots=unknown))

def test_premise_descriptions_keep_record_order_and_reject_duplicate_records():
    p=('description','claimform');other=('description','otherclaimform')
    m=model(record=lambda:'c',descriptionat=lambda n,a,b:b if n=='b' else a,recorded=lambda *a:True,available=lambda *a:True,
        inferred=lambda *xs:tuple(describe(x) for x in xs)==('c','c',(p,other),p,'a','now'))
    bodies=[query('evidenceinferred',premises=records(order)) for order in ('ab','ba','aa')]
    assert values(doc(bodies),m,('a','b','c'))==[True,False,False]

@pytest.mark.parametrize('parents,premises,expected',[
    ({('b','a')},'a',True),({('b','a')},'',False),({('b','a')},'aa',False),
    ({('b','a'),('b','b')},'a',False),({('b','b')},'b',False),(set(),'',True)])
def test_explicit_premise_list_matches_exactly_the_graph(parents,premises,expected):
    assert values(doc([query('evidenceparents',premises=records(premises))]),model(parents=lambda n,p:(n,p) in parents))==[expected]

def test_removing_an_inference_dependency_does_not_silently_weaken_the_certificate():
    d=deepcopy(example('inference'));parents=next(x for x in d['declarations'] if x['name']=='parents')
    a,b=[v(p['name']) for p in parents['parameters']]
    parents['body']=op('and',parents['body'],op('not',op('and',eq(a,call('third')),eq(b,call('second')))))
    d['statements']=d['statements'][:2]
    assert values(d,example_model(),('a','b','c'))==[False,False]

def test_removing_the_initial_observation_invalidates_the_relay_chain():
    d=deepcopy(example('relay'));next(x for x in d['declarations'] if x['name']=='observed')['body']=truth(False)
    d['statements']=d['statements'][:2]
    assert values(d,example_model(),('a','b','c'))==[False,False]

def test_empty_premise_inference_can_be_recorded_without_inventing_a_source():
    m=model(inferred=lambda *a:True,available=unknown,parents=lambda *a:False,roots=lambda *a:False)
    assert values(doc([query('evidenceinferred',premises=records('')),query('proofsupports'),query('proofseparateorigins')]),m)==[True,True,False]

def test_a_supported_mistaken_belief_is_not_a_true_supported_belief():
    assert values(doc([query('beliefgrounded'),query('beliefgroundedtrue')]),model())==[True,False]

@pytest.mark.parametrize('field',['agent','target'])
def test_the_believer_and_supported_record_holder_are_the_same_person(field):
    body=query('beliefgrounded',**{field:call('first')})
    assert values(doc([body]),model(aware=lambda *a:True))==[False]
