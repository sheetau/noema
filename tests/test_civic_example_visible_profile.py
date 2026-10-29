"""Typed civic example contracts preserve bindings, opaque quotations and unknowns."""
from copy import deepcopy
from fractions import Fraction
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,SequenceValue,DescriptionValue,FunctionValue,Content
from scripts import civic_example_visible_profile as profile
from scripts.shared_modality import call,renamed
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_contracts_survive_actual_svg():
    vocabulary=profile.CivicExampleVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','above','book')),vocabulary,payload=768)['pages']
    actual=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert actual==document and len(actual['declarations'])==28


def primitive(name,parameters,result):return dict(kind='primitive',name=name,parameters=parameters,result=result)


def argname(index):return 'jarg'+'abcdefghi'[index]


def fixture(name):
    row=profile.ALL_CONTRACTS[name];ds=[primitive(name,row['parameters'],row['result'])];args=[]
    for i,s in enumerate(row['parameters']):
        n=argname(i)
        if isinstance(s,dict) and s['kind']=='description':
            result=s['result']
            if result in ('content','truth') or isinstance(result,dict) and result['kind']=='question':
                ds.append(primitive(n,[],result));body=call(n)
            else:
                assert result['kind']=='function'
                ds.append(primitive(n,result['parameters'],result['result']))
                body=dict(kind='function_ref',symbol=n)
            args.append(dict(kind='quote',body=body,**({'rank':s['rank']} if s.get('rank') else {})))
        else:ds.append(primitive(n,[],s));args.append(call(n))
    if isinstance(row['result'],dict) and row['result']['kind']=='description':
        assert row['result']['kind']=='description'
        ds.extend(primitive(n,[],row['result']['result']) for n in ('jreturned','jotherreturned'))
    question=call(name,*args)
    if row['result']!='truth':
        ds.append(primitive('jexpected',[],row['result']))
        if isinstance(row['result'],dict) and row['result']['kind']=='function':
            assert row['result']['parameters']==['individual']
            ds.extend(primitive(n,[],'individual') for n in ('jprobea','jprobeb'))
            def applied(fn,value):return dict(kind='apply',function=fn,arguments=[call(value)])
            question=dict(kind='and',arguments=[dict(kind='equal',arguments=[applied(question,value),applied(call('jexpected'),value)]) for value in ('jprobea','jprobeb')])
        else:question=dict(kind='equal',arguments=[question,call('jexpected')])
    if isinstance(row['result'],dict) and row['result']['kind']=='description':
        ds.append(primitive('jregister',[row['result'],row['result']],'truth'))
        question=dict(kind='and',arguments=[call('jregister',*(dict(kind='quote',body=call(n),**({'rank':row['result']['rank']} if row['result'].get('rank') else {}))
            for n in ('jreturned','jotherreturned'))),question])
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,
        statements=[dict(kind='ask',body=question)]))


def model(doc,name,result,polarity=False):
    row=profile.ALL_CONTRACTS[name];values={};expected=[];issued={}
    def forbidden(*args):raise ValueError('Quoted civic example must not execute')
    for i,s in enumerate(row['parameters']):
        n=argname(i)
        if isinstance(s,dict) and s['kind']=='description':
            syntax=call(n) if s['result'] in ('content','truth') or isinstance(s['result'],dict) and s['result']['kind']=='question' else dict(kind='function_ref',symbol=n)
            expected.append(dict(syntax=syntax,rank=s.get('rank',0)));values[n]=forbidden
        else:
            value=FunctionValue(tuple(s['parameters']),s['result'],lambda item,n=n:item==n) if isinstance(s,dict) and s['kind']=='function' else polarity if s=='truth' else Fraction(i+1) if s=='number' else SequenceValue((n,'other'),json.dumps('individual')) if isinstance(s,dict) else n
            expected.append(value);values[n]=lambda value=value:value
    def relation(*args):
        actual=[dict(syntax=json.loads(x.syntax),rank=x.rank) if hasattr(x,'syntax') else x for x in args]
        # The evaluator wraps function values; compare two distinguishing inputs,
        # not Python callable identity. This is a binding diagnostic only.
        for i,(found,wanted) in enumerate(zip(actual,expected,strict=True)):
            if isinstance(wanted,FunctionValue):
                if not isinstance(found,FunctionValue) or (found.parameters,found.result)!=(wanted.parameters,wanted.result):
                    raise ValueError('Unknown civic example input')
                if any(found.implementation(x)!=wanted.implementation(x) for x in (argname(i),'other')):
                    raise ValueError('Unknown civic example input')
            elif found!=wanted:raise ValueError('Unknown civic example input')
        return issued[result] if isinstance(row['result'],dict) and row['result']['kind']=='description' else result
    values[name]=relation
    if isinstance(row['result'],dict) and row['result']['kind']=='function':
        values.update(jprobea=lambda:'jprobea',jprobeb=lambda:'jprobeb')
    if isinstance(row['result'],dict) and row['result']['kind']=='description':
        def register(first,second):
            issued.update(jreturned=first,jotherreturned=second)
            return True
        values.update(jreturned=forbidden,jotherreturned=forbidden,jregister=register)
    if row['result']!='truth':values['jexpected']=lambda:issued[result] if isinstance(row['result'],dict) and row['result']['kind']=='description' else result
    return values


def run(doc,values):
    domain=tuple(values)+('other','degree','alternative')
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=domain,
        primitives=values,memoize_definitions=False,memoize_expressions=False)]


def test_every_slot_is_bound_and_quoted_content_is_not_executed():
    for name,row in profile.ALL_CONTRACTS.items():
        if name=='standingassessmentconditions':continue  # Sequence-of-function return is checked below.
        doc=fixture(name)
        results=('jreturned','jotherreturned') if isinstance(row['result'],dict) and row['result']['kind']=='description' else (FunctionValue(('individual',),'truth',lambda n:n=='jprobea'),FunctionValue(('individual',),'truth',lambda n:n=='jprobeb')) if isinstance(row['result'],dict) and row['result']['kind']=='function' else (SequenceValue(('degree','alternative'),json.dumps(row['result']['element'])),SequenceValue(('alternative','degree'),json.dumps(row['result']['element']))) if isinstance(row['result'],dict) else (Fraction(0),Fraction(7,2)) if row['result']=='number' else ('degree','alternative') if row['result'] in ('individual','situation') else (False,True)
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
                value=FunctionValue(tuple(s['parameters']),s['result'],lambda item,n=n:item!=n) if isinstance(s,dict) and s['kind']=='function' else True if s=='truth' else Fraction(99) if s=='number' else SequenceValue(('other',n),json.dumps('individual')) if isinstance(s,dict) else 'other'
                alternate[n]=lambda value=value:value
            with pytest.raises(ValueError,match='Unknown civic example input'):run(normalize_document(changed),alternate)
        def unknown(*args):raise ValueError('Unspecified civic example input')
        with pytest.raises(ValueError,match='Unspecified'):run(doc,values|{name:unknown})




def test_description_types_do_not_collapse_to_contents_or_other_arities():
    for name,row in profile.ALL_CONTRACTS.items():
        for slot,s in enumerate(row['parameters']):
            if not isinstance(s,dict) or s['kind']!='description':continue
            wrongs=['content',dict(kind='description',result=dict(kind='function',parameters=['individual']*5,result='content'))]
            for wrong in wrongs:
                params=[dict(name='arg'+'abcdefghi'[i],sort=deepcopy(t)) for i,t in enumerate(row['parameters'])]
                params[slot]['sort']=wrong
                invalid=dict(kind='definition',name='wrongdescription',parameters=params,result=row['result'],
                    body=call(name,*(dict(kind='variable',name=p['name']) for p in params)))
                with pytest.raises(ValueError):normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
                    declarations=[primitive(name,row['parameters'],row['result']),invalid],statements=[]))


def test_every_description_refuses_a_different_rank():
    seen=set()
    for name,row in profile.ALL_CONTRACTS.items():
        for slot,sort in enumerate(row['parameters']):
            if not isinstance(sort,dict) or sort.get('kind')!='description':continue
            seen.add(name)
            params=[dict(name=argname(i),sort=deepcopy(s)) for i,s in enumerate(row['parameters'])]
            params[slot]['sort']['rank']=sort.get('rank',0)+1
            invalid=dict(kind='definition',name='rankprobe',parameters=params,result=row['result'],
                body=call(name,*(dict(kind='variable',name=p['name']) for p in params)))
            with pytest.raises(ValueError):normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
                declarations=[primitive(name,row['parameters'],row['result']),invalid],statements=[]))
    assert seen=={'rankedreferenceboundinduction', 'ranktwoexpectationatleast', 'boundrequirementresponse', 'boundpracticalcommitment', 'rankthreeassessmentasideexplanation', 'rankthreeparallelexamplepresentation', 'rankthreeadditivefocuspresentation', 'twotargetreferencemessagepresentation', 'assessmentboundsanctionresponse', 'rankedreferenceboundpermission'}


def test_assessment_condition_sequence_preserves_order_both_arguments_and_unknowns():
    name='standingassessmentconditions';row=profile.ALL_CONTRACTS[name]
    canonical=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    element=row['result']['element'];assert element==dict(kind='function',parameters=['individual','individual'],result='content')
    ds=[primitive(name,row['parameters'],row['result']),primitive('jinspect',[row['result']],'truth')]
    ds += [primitive(n,[],s) for n,s in zip(('jstanding','jsubject','jreference'),row['parameters'],strict=True)]
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,
        statements=[dict(kind='ask',body=call('jinspect',call(name,call('jstanding'),call('jsubject'),call('jreference'))))]))
    def sequence(flags):
        return SequenceValue(tuple(FunctionValue(('individual','individual'),'content',
            lambda person,standing,flag=flag:Content(('reference','other'),(flag if (person,standing)==('person','standing') else not flag,False))) for flag in flags),canonical(element))
    def run_local(values):
        return [r['value'] for r in evaluate_document(doc,individuals=('standing','subject','person','other'),situations=('reference','other'),primitives=values)]
    values=dict(jstanding=lambda:'standing',jsubject=lambda:'subject',jreference=lambda:'reference')
    for flags in ((),(False,True),(True,False),(True,True)):
        def relation(standing,subject,reference):
            if (standing,subject,reference)!=('standing','subject','reference'):raise ValueError('Unknown assessment bindings')
            return sequence(flags)
        def inspect(actual):
            assert isinstance(actual,SequenceValue) and actual.element_type==canonical(element)
            assert len(actual.items)==len(flags)
            for fn,flag in zip(actual.items,flags,strict=True):
                assert fn.parameters==('individual','individual') and fn.result=='content'
                for pair,expected in [(('person','standing'),flag),(('other','standing'),not flag),(('person','other'),not flag)]:
                    assert fn(*pair)==Content(('reference','other'),(expected,False))
            return True
        current=values|{name:relation,'jinspect':inspect}
        assert run_local(current)==[True]
        for slot in ('jstanding','jsubject','jreference'):
            with pytest.raises(ValueError,match='Unknown assessment bindings'):run_local(current|{slot:lambda:'other'})
    def unknown(*args):raise ValueError('Unspecified assessment condition')
    with pytest.raises(ValueError,match='Unspecified'):run_local(current|{name:unknown})
    opaque=SequenceValue((FunctionValue(('individual','individual'),'content',unknown),),canonical(element))
    with pytest.raises(ValueError,match='Unspecified'):run_local(current|{name:lambda *args:opaque,'jinspect':lambda seq:seq.items[0]('person','standing')})
    for wrong in (SequenceValue((),canonical('individual')),SequenceValue(('person',),canonical(element)),
                  SequenceValue((FunctionValue(('individual',),'content',unknown),),canonical(element))):
        with pytest.raises(ValueError):run_local(current|{name:lambda *args,wrong=wrong:wrong})
