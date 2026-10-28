"""Preserve typed role descriptions, ordered examples and unknown inputs."""
from copy import deepcopy
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts import delegated_activities_visible_profile as profile
from scripts.shared_modality import call
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_contracts_survive_actual_svg():
    vocabulary=profile.DelegatedActivitiesVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','round','inside')),vocabulary,payload=768)['pages']
    actual=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert actual==document and len(actual['declarations'])==33


def primitive(name,parameters,result):return dict(kind='primitive',name=name,parameters=parameters,result=result)


def fixture(name):
    row=profile.CONTRACTS[name];ds=[primitive(name,row['parameters'],row['result'])];args=[]
    def quoted(n,sort):
        result=sort['result'];assert result['kind']=='function'
        ds.append(primitive(n,result['parameters'],result['result']))
        return dict(kind='quote',body=dict(kind='function_ref',symbol=n))
    for i,s in enumerate(row['parameters']):
        n='jarg'+'abcde'[i]
        if isinstance(s,str):ds.append(primitive(n,[],s));args.append(call(n))
        elif s['kind']=='description':args.append(quoted(n,s))
        else:
            assert s['kind']=='sequence'
            args.append(dict(kind='sequence',element=s['element'],items=[quoted(n+'first',s['element']),quoted(n+'second',s['element'])]))
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,
        statements=[dict(kind='ask',body=call(name,*args))]))


def fingerprint(value):
    if hasattr(value,'syntax'):return json.loads(value.syntax)
    if hasattr(value,'items'):return [fingerprint(x) for x in value.items]
    return value


def test_every_contract_preserves_slots_and_opaque_descriptions():
    for name,row in profile.CONTRACTS.items():
        doc=fixture(name);expected=[];model={}
        def forbidden(*args):raise ValueError('Quoted activity must not execute')
        for d in doc['declarations']:
            if d['name']!=name:
                model[d['name']]=forbidden if d['parameters'] else (lambda n=d['name']:n)
        for i,s in enumerate(row['parameters']):
            n='jarg'+'abcde'[i]
            if isinstance(s,str):expected.append(n)
            elif s['kind']=='description':expected.append(dict(kind='function_ref',symbol=n))
            else:expected.append([dict(kind='function_ref',symbol=n+x) for x in ('first','second')])
        def run(values):
            return [r['value'] for r in evaluate_document(doc,individuals=tuple(model)+('other',),
                situations=tuple(model)+('other',),primitives=values,memoize_definitions=False,memoize_expressions=False)]
        for truth in (False,True):
            def relation(*args):
                if [fingerprint(x) for x in args]!=expected:raise ValueError('Unknown activity relation')
                return truth
            assert run(model|{name:relation})==[truth]
        for i,s in enumerate(row['parameters']):
            if isinstance(s,str):
                with pytest.raises(ValueError,match='Unknown activity relation'):
                    run(model|{name:relation,'jarg'+'abcde'[i]:lambda:'other'})
        with pytest.raises(ValueError,match='Unspecified'):
            run(model|{name:lambda *args:(_ for _ in ()).throw(ValueError('Unspecified relation'))})


def test_description_arity_and_content_are_not_interchangeable():
    for name,row in profile.CONTRACTS.items():
        for slot,s in enumerate(row['parameters']):
            if not isinstance(s,dict) or s['kind']!='description':continue
            for wrong_sort in ('content',dict(kind='description',result=dict(kind='function',
                parameters=['individual']*(2 if len(s['result']['parameters'])==1 else 1),result='content'))):
                d=primitive(name,row['parameters'],row['result'])
                params=[dict(name='arg'+'abcde'[i],sort=deepcopy(t)) for i,t in enumerate(row['parameters'])]
                params[slot]['sort']=wrong_sort
                invalid=dict(kind='definition',name='wrongdescription',parameters=params,result=row['result'],
                    body=call(name,*(dict(kind='variable',name=p['name']) for p in params)))
                with pytest.raises(ValueError):normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[d,invalid],statements=[]))


def test_example_sequence_keeps_order_and_description_identity():
    name='nonexhaustiveexamplepresentation';doc=fixture(name)
    def forbidden(*args):raise ValueError('Example content must not execute')
    def relation(node,presenter,examples,context):
        assert (node,presenter,context)==('first','second','scene')
        names=[json.loads(x.syntax)['symbol'] for x in examples.items]
        if names!=['jargcfirst','jargcsecond']:raise ValueError('Unknown ordered examples')
        return True
    model=dict(jarga=lambda:'first',jargb=lambda:'second',jargd=lambda:'scene',
        jargcfirst=forbidden,jargcsecond=forbidden,nonexhaustiveexamplepresentation=relation)
    def run(document):return [r['value'] for r in evaluate_document(document,individuals=('first','second'),situations=('scene',),primitives=model)]
    assert run(doc)==[True]
    changed=deepcopy(doc);changed['statements'][0]['body']['arguments'][2]['items'].reverse()
    with pytest.raises(ValueError,match='Unknown ordered examples'):run(changed)
