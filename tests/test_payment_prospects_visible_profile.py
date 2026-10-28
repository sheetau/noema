"""Preserve payment values, opaque work descriptions and unknown inputs."""
from copy import deepcopy
from fractions import Fraction
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts import payment_prospects_visible_profile as profile
from scripts.shared_modality import call
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_contracts_survive_actual_svg():
    vocabulary=profile.PaymentProspectsVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','round','aki')),vocabulary,payload=768)['pages']
    actual=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert actual==document and len(actual['declarations'])==11


def primitive(name,parameters,result):return dict(kind='primitive',name=name,parameters=parameters,result=result)


def fixture(name):
    row=profile.CONTRACTS[name];ds=[primitive(name,row['parameters'],row['result'])];args=[]
    for i,s in enumerate(row['parameters']):
        n='jarg'+'abcde'[i]
        if isinstance(s,str):ds.append(primitive(n,[],s));args.append(call(n))
        else:
            assert s['kind']=='description' and s['result']['kind']=='function'
            ds.append(primitive(n,s['result']['parameters'],s['result']['result']))
            args.append(dict(kind='quote',body=dict(kind='function_ref',symbol=n)))
    question=call(name,*args)
    if row['result']=='number':
        ds.append(primitive('jexpected',[],'number'))
        question=dict(kind='equal',arguments=[question,call('jexpected')])
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,
        statements=[dict(kind='ask',body=question)]))


def model(doc,name,result):
    row=profile.CONTRACTS[name];values={};expected=[]
    def forbidden(*args):raise ValueError('Quoted work must not execute')
    for d in doc['declarations']:
        if d['name']!=name:values[d['name']]=forbidden if d['parameters'] else (lambda n=d['name']:n)
    for i,s in enumerate(row['parameters']):
        n='jarg'+'abcde'[i]
        expected.append(n if isinstance(s,str) else dict(kind='function_ref',symbol=n))
    def relation(*args):
        actual=[json.loads(x.syntax) if hasattr(x,'syntax') else x for x in args]
        if actual!=expected:raise ValueError('Unknown payment or prospect input')
        return result
    values[name]=relation
    if row['result']=='number':values['jexpected']=lambda:result
    return values


def run(doc,values):
    domain=tuple(values)+('other',)
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=domain,
        primitives=values,memoize_definitions=False,memoize_expressions=False)]


def test_each_contract_keeps_slots_and_does_not_evaluate_quotation():
    for name,row in profile.CONTRACTS.items():
        doc=fixture(name)
        results=(Fraction(-1),Fraction(0),Fraction(9,2)) if row['result']=='number' else (False,True)
        for result in results:assert run(doc,model(doc,name,result))==[True if row['result']=='number' else result]
        values=model(doc,name,results[-1])
        for i,s in enumerate(row['parameters']):
            if isinstance(s,str):
                with pytest.raises(ValueError,match='Unknown payment or prospect input'):
                    run(doc,values|{'jarg'+'abcde'[i]:lambda:'other'})
        def unknown(*args):raise ValueError('Unspecified payment or prospect input')
        with pytest.raises(ValueError,match='Unspecified'):run(doc,values|{name:unknown})


def test_unknown_amount_is_not_free_and_amounts_are_not_truth_values():
    for name in ('creditedpaymentvalue','requiredpaymentvalue'):
        doc=fixture(name);values=model(doc,name,Fraction(0))
        assert run(doc,values)==[True]
        assert run(doc,values|{'jexpected':lambda:Fraction(1)})==[False]
        def unknown(*args):raise ValueError('Unspecified amount')
        with pytest.raises(ValueError,match='Unspecified amount'):run(doc,values|{name:unknown})
        with pytest.raises(ValueError):run(doc,values|{name:lambda *args:False})


def test_descriptions_are_not_executed_contents_or_binary_relations():
    for name,row in profile.CONTRACTS.items():
        for slot,s in enumerate(row['parameters']):
            if not isinstance(s,dict):continue
            for wrong in ('content',dict(kind='description',result=dict(kind='function',parameters=['individual','individual'],result='content'))):
                params=[dict(name='arg'+'abcde'[i],sort=deepcopy(t)) for i,t in enumerate(row['parameters'])]
                params[slot]['sort']=wrong
                invalid=dict(kind='definition',name='wrongdescription',parameters=params,result=row['result'],
                    body=call(name,*(dict(kind='variable',name=p['name']) for p in params)))
                with pytest.raises(ValueError):normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
                    declarations=[primitive(name,row['parameters'],row['result']),invalid],statements=[]))
