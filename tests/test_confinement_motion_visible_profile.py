"""Typed confinement contracts preserve bindings, opaque quotations and unknowns."""
from copy import deepcopy
from fractions import Fraction
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,SequenceValue
from scripts import confinement_motion_visible_profile as profile
from scripts.shared_modality import call
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_contracts_survive_actual_svg():
    vocabulary=profile.ConfinementMotionVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','round','book')),vocabulary,payload=768)['pages']
    actual=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert actual==document and len(actual['declarations'])==47


def primitive(name,parameters,result):return dict(kind='primitive',name=name,parameters=parameters,result=result)


def argname(index):return 'jarg'+'abcdefg'[index]


def fixture(name):
    row=profile.CONTRACTS[name];ds=[primitive(name,row['parameters'],row['result'])];args=[]
    for i,s in enumerate(row['parameters']):
        n=argname(i)
        if isinstance(s,dict) and s['kind']=='description':
            result=s['result']
            if result=='content':
                ds.append(primitive(n,[],'content'));body=call(n)
            else:
                assert result['kind']=='function'
                ds.append(primitive(n,result['parameters'],result['result']))
                body=dict(kind='function_ref',symbol=n)
            args.append(dict(kind='quote',body=body))
        else:ds.append(primitive(n,[],s));args.append(call(n))
    question=call(name,*args)
    if row['result']!='truth':
        ds.append(primitive('jexpected',[],row['result']))
        question=dict(kind='equal',arguments=[question,call('jexpected')])
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,
        statements=[dict(kind='ask',body=question)]))


def model(doc,name,result,polarity=False):
    row=profile.CONTRACTS[name];values={};expected=[]
    def forbidden(*args):raise ValueError('Quoted confinement must not execute')
    for i,s in enumerate(row['parameters']):
        n=argname(i)
        if isinstance(s,dict) and s['kind']=='description':
            syntax=call(n) if s['result']=='content' else dict(kind='function_ref',symbol=n)
            expected.append(syntax);values[n]=forbidden
        else:
            value=polarity if s=='truth' else Fraction(i+1) if s=='number' else SequenceValue((n,'other'),json.dumps('individual')) if isinstance(s,dict) else n
            expected.append(value);values[n]=lambda value=value:value
    def relation(*args):
        actual=[json.loads(x.syntax) if hasattr(x,'syntax') else x for x in args]
        if actual!=expected:raise ValueError('Unknown confinement input')
        return result
    values[name]=relation
    if row['result']!='truth':values['jexpected']=lambda:result
    return values


def run(doc,values):
    domain=tuple(values)+('other','degree','alternative')
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=domain,
        primitives=values,memoize_definitions=False,memoize_expressions=False)]


def test_every_slot_is_bound_and_quoted_content_is_not_executed():
    for name,row in profile.CONTRACTS.items():
        doc=fixture(name)
        results=(SequenceValue((),json.dumps('individual')),SequenceValue(('degree','other'),json.dumps('individual'))) if isinstance(row['result'],dict) else (Fraction(0),Fraction(7,2)) if row['result']=='number' else ('degree','alternative') if row['result']=='individual' else (False,True)
        for result in results:assert run(doc,model(doc,name,result))==[result if row['result']=='truth' else True]
        values=model(doc,name,results[-1])
        for i,s in enumerate(row['parameters']):
            n=argname(i);changed=deepcopy(doc);alternate=dict(values)
            if isinstance(s,dict) and s['kind']=='description':
                declaration=deepcopy(next(d for d in doc['declarations'] if d['name']==n))
                declaration['name']='jother';changed['declarations'].append(declaration)
                q=changed['statements'][0]['body']
                if row['result']!='truth':q=q['arguments'][0]
                q['arguments'][i]['body']['symbol']='jother'
                alternate['jother']=values[n]
            else:
                value=True if s=='truth' else Fraction(99) if s=='number' else SequenceValue(('other',n),json.dumps('individual')) if isinstance(s,dict) else 'other'
                alternate[n]=lambda value=value:value
            with pytest.raises(ValueError,match='Unknown confinement input'):run(normalize_document(changed),alternate)
        def unknown(*args):raise ValueError('Unspecified confinement input')
        with pytest.raises(ValueError,match='Unspecified'):run(doc,values|{name:unknown})


def test_sequences_preserve_order_and_unknown_is_not_an_empty_list():
    for name in ('deviceplacesequence','structuralpartsequence'):
        doc=fixture(name);result=SequenceValue(('degree','other'),json.dumps('individual'))
        values=model(doc,name,result)
        assert run(doc,values)==[True]
        assert run(doc,values|{'jexpected':lambda:SequenceValue(('other','degree'),json.dumps('individual'))})==[False]
        assert run(doc,values|{'jexpected':lambda:SequenceValue((),json.dumps('individual'))})==[False]
        def unknown(*args):raise ValueError('Unspecified list')
        with pytest.raises(ValueError,match='Unspecified list'):run(doc,values|{name:unknown})
        with pytest.raises(ValueError):run(doc,values|{name:lambda *args:('degree','other')})
    for name in ('requiresboundcontent','permitsboundcontent'):
        doc=fixture(name)
        for polarity in (False,True):
            for result in (False,True):assert run(doc,model(doc,name,result,polarity))==[result]


def test_description_types_do_not_collapse_to_contents_or_other_arities():
    for name,row in profile.CONTRACTS.items():
        for slot,s in enumerate(row['parameters']):
            if not isinstance(s,dict) or s['kind']!='description':continue
            wrongs=['content',dict(kind='description',result=dict(kind='function',parameters=['individual']*5,result='content'))]
            for wrong in wrongs:
                params=[dict(name='arg'+'abcdefg'[i],sort=deepcopy(t)) for i,t in enumerate(row['parameters'])]
                params[slot]['sort']=wrong
                invalid=dict(kind='definition',name='wrongdescription',parameters=params,result=row['result'],
                    body=call(name,*(dict(kind='variable',name=p['name']) for p in params)))
                with pytest.raises(ValueError):normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
                    declarations=[primitive(name,row['parameters'],row['result']),invalid],statements=[]))
