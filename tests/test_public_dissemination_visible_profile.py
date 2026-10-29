"""Typed public dissemination contracts preserve bindings, opaque quotations and unknowns."""
from copy import deepcopy
from fractions import Fraction
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,SequenceValue,DescriptionValue
from scripts import public_dissemination_visible_profile as profile
from scripts.shared_modality import call,renamed
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_contracts_survive_actual_svg():
    vocabulary=profile.PublicDisseminationVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','above','book')),vocabulary,payload=768)['pages']
    actual=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert actual==document and len(actual['declarations'])==28


def primitive(name,parameters,result):return dict(kind='primitive',name=name,parameters=parameters,result=result)


def argname(index):return 'jarg'+'abcdefgh'[index]


def fixture(name):
    row=profile.ALL_CONTRACTS[name];ds=[primitive(name,row['parameters'],row['result'])];args=[]
    for i,s in enumerate(row['parameters']):
        n=argname(i)
        if isinstance(s,dict) and s['kind']=='description':
            result=s['result']
            if result in ('content','truth'):
                ds.append(primitive(n,[],result));body=call(n)
            else:
                assert result['kind']=='function'
                ds.append(primitive(n,result['parameters'],result['result']))
                body=dict(kind='function_ref',symbol=n)
            args.append(dict(kind='quote',body=body,**({'rank':s['rank']} if s.get('rank') else {})))
        else:ds.append(primitive(n,[],s));args.append(call(n))
    if isinstance(row['result'],dict):
        assert row['result']['kind']=='description'
        ds.extend(primitive(n,[],row['result']['result']) for n in ('jreturned','jotherreturned'))
    question=call(name,*args)
    if row['result']!='truth':
        ds.append(primitive('jexpected',[],row['result']))
        question=dict(kind='equal',arguments=[question,call('jexpected')])
    if isinstance(row['result'],dict):
        ds.append(primitive('jregister',[row['result'],row['result']],'truth'))
        question=dict(kind='and',arguments=[call('jregister',*(dict(kind='quote',body=call(n))
            for n in ('jreturned','jotherreturned'))),question])
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,
        statements=[dict(kind='ask',body=question)]))


def model(doc,name,result,polarity=False):
    row=profile.ALL_CONTRACTS[name];values={};expected=[];issued={}
    def forbidden(*args):raise ValueError('Quoted public dissemination must not execute')
    for i,s in enumerate(row['parameters']):
        n=argname(i)
        if isinstance(s,dict) and s['kind']=='description':
            syntax=call(n) if s['result'] in ('content','truth') else dict(kind='function_ref',symbol=n)
            expected.append(dict(syntax=syntax,rank=s.get('rank',0)));values[n]=forbidden
        else:
            value=polarity if s=='truth' else Fraction(i+1) if s=='number' else SequenceValue((n,'other'),json.dumps('individual')) if isinstance(s,dict) else n
            expected.append(value);values[n]=lambda value=value:value
    def relation(*args):
        actual=[dict(syntax=json.loads(x.syntax),rank=x.rank) if hasattr(x,'syntax') else x for x in args]
        if actual!=expected:raise ValueError('Unknown public dissemination input')
        return issued[result] if isinstance(row['result'],dict) else result
    values[name]=relation
    if isinstance(row['result'],dict):
        def register(first,second):
            issued.update(jreturned=first,jotherreturned=second)
            return True
        values.update(jreturned=forbidden,jotherreturned=forbidden,jregister=register)
    if row['result']!='truth':values['jexpected']=lambda:issued[result] if isinstance(row['result'],dict) else result
    return values


def run(doc,values):
    domain=tuple(values)+('other','degree','alternative')
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=domain,
        primitives=values,memoize_definitions=False,memoize_expressions=False)]


def test_every_slot_is_bound_and_quoted_content_is_not_executed():
    for name,row in profile.ALL_CONTRACTS.items():
        doc=fixture(name)
        results=('jreturned','jotherreturned') if isinstance(row['result'],dict) else (Fraction(0),Fraction(7,2)) if row['result']=='number' else ('degree','alternative') if row['result'] in ('individual','situation') else (False,True)
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
            with pytest.raises(ValueError,match='Unknown public dissemination input'):run(normalize_document(changed),alternate)
        def unknown(*args):raise ValueError('Unspecified public dissemination input')
        with pytest.raises(ValueError,match='Unspecified'):run(doc,values|{name:unknown})




def test_description_types_do_not_collapse_to_contents_or_other_arities():
    for name,row in profile.ALL_CONTRACTS.items():
        for slot,s in enumerate(row['parameters']):
            if not isinstance(s,dict) or s['kind']!='description':continue
            wrongs=['content',dict(kind='description',result=dict(kind='function',parameters=['individual']*5,result='content'))]
            for wrong in wrongs:
                params=[dict(name='arg'+'abcdefgh'[i],sort=deepcopy(t)) for i,t in enumerate(row['parameters'])]
                params[slot]['sort']=wrong
                invalid=dict(kind='definition',name='wrongdescription',parameters=params,result=row['result'],
                    body=call(name,*(dict(kind='variable',name=p['name']) for p in params)))
                with pytest.raises(ValueError):normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
                    declarations=[primitive(name,row['parameters'],row['result']),invalid],statements=[]))


def test_candidate_designations_are_opaque_until_checked_against_the_target():
    for name,sort in [('individualdesignationcandidate','individual'),('situationdesignationcandidate','situation')]:
        doc=fixture(name)
        candidate=DescriptionValue(json.dumps(call('jreturned'),sort_keys=True,separators=(',',':')),json.dumps(sort))
        values=model(doc,name,'jreturned')
        # Equality of descriptions does not run the candidate's reference.
        assert run(doc,values)==[True]
        registration=deepcopy(doc['statements'][0]['body']['arguments'][0])
        doc['statements']=[dict(kind='ask',body=dict(kind='and',arguments=[registration,
            dict(kind='equal',arguments=[dict(kind='disquote',description=call(name,call('jarga'))),call('jarga')])]))]
        doc=normalize_document(doc)
        assert run(doc,values|{'jreturned':lambda:'jarga'})==[True]
        assert run(doc,values|{'jreturned':lambda:'other'})==[False]
        with pytest.raises(ValueError,match='must not execute'):run(doc,values)
        for wrong in (candidate,DescriptionValue(candidate.syntax,json.dumps('situation' if sort=='individual' else 'individual')),
                      DescriptionValue(candidate.syntax,candidate.result_type,1)):
            with pytest.raises(ValueError):run(doc,values|{name:lambda *args,wrong=wrong:wrong})
        free=DescriptionValue(json.dumps(dict(kind='variable',name='unbound')),json.dumps(sort))
        with pytest.raises(ValueError):run(doc,values|{name:lambda *args:free})


def test_endorsement_polarity_and_ranked_derogatory_presentation():
    name='judgmentcontentendorsement';doc=fixture(name)
    for polarity in (False,True):
        for result in (False,True):
            assert run(doc,model(doc,name,result,polarity=polarity))==[result]
    name='disparagingreferencepresentation';row=profile.ALL_CONTRACTS[name]
    for index in (2,3):
        assert row['parameters'][index]['rank']==1
        parameters=[dict(name=argname(i),sort=deepcopy(s)) for i,s in enumerate(row['parameters'])]
        parameters[index]['sort']['rank']=0
        wrong=dict(kind='definition',name='rankprobe',parameters=parameters,result='truth',
            body=call(name,*(dict(kind='variable',name=p['name']) for p in parameters)))
        with pytest.raises(ValueError):normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=[primitive(name,row['parameters'],'truth'),wrong],statements=[]))


def test_text_spans_preserve_scalars_combining_marks_spaces_and_punctuation():
    from scripts.sentence_text_span_references import SentenceTextSpanReferences
    text='A😀e\u0301, X'
    assert len(text)==7
    refs=SentenceTextSpanReferences({('doc','sentence','context'):text},{
        ('doc','sentence',1,2,'context'):'emoji',('doc','sentence',2,4,'context'):'accented',
        ('doc','sentence',2,5,'context'):'with-comma',('doc','sentence',4,5,'context'):'comma',
        ('doc','sentence',5,6,'context'):'space',('doc','sentence',0,7,'context'):'whole'})
    assert refs.span('doc','sentence',Fraction(1),Fraction(2),'context')=='emoji'
    assert refs.span('doc','sentence',2,4,'context')=='accented'
    assert refs.span('doc','sentence',2,5,'context')=='with-comma'
    assert refs.span('doc','sentence',4,5,'context')=='comma'
    assert refs.span('doc','sentence',5,6,'context')=='space'
    assert refs.span('doc','sentence',0,7,'context')=='whole'
    # UTF-16 would count the astral character twice; byte offsets differ too.
    with pytest.raises(ValueError,match='outside'):refs.span('doc','sentence',0,8,'context')
    with pytest.raises(ValueError,match='Unicode scalars'):
        SentenceTextSpanReferences({('doc','sentence','context'):'\ud800'}, {})


def test_exact_source_boundaries_and_unknown_spans_are_not_silently_widened():
    from scripts.sentence_text_span_references import SentenceTextSpanReferences
    anchor=json.loads((profile.ROOT/'data/kant-public-dissemination-text-anchors-v1.json').read_text(encoding='utf-8'))
    rows=anchor['source_character_spans']
    bindings={('doc','sentence',r['first_character'],r['past_last_character'],'context'):name for name,r in rows.items()}
    refs=SentenceTextSpanReferences({('doc','sentence','context'):anchor['text']},bindings)
    for name,row in rows.items():
        first,last=row['first_character'],row['past_last_character']
        assert anchor['text'][first:last]==row['text'] and anchor['text'][last]==','
        assert refs.span('doc','sentence',first,last,'context')==name
        with pytest.raises(ValueError,match='Unknown sentence text span'):refs.span('doc','sentence',first,last+1,'context')
    for first,last in ((-1,2),(1,1),(3,2),(0,len(anchor['text'])+1),(True,2),(0,Fraction(3,2)),(0,2.0)):
        with pytest.raises(ValueError):refs.span('doc','sentence',first,last,'context')
    for args in [('other','sentence',89,107,'context'),('doc','other',89,107,'context'),('doc','sentence',89,107,'other')]:
        with pytest.raises(ValueError,match='Unknown fixed sentence'):refs.span(*args)


def test_character_reference_runs_through_the_typed_native_interface():
    from scripts.sentence_text_span_references import SentenceTextSpanReferences
    name='sentencetextspanreference';doc=fixture(name);values=model(doc,name,'degree')
    values['jargc']=lambda:Fraction(1);values['jargd']=lambda:Fraction(2)
    refs=SentenceTextSpanReferences({('jarga','jargb','jarge'):'x😀,'},{('jarga','jargb',1,2,'jarge'):'degree'})
    values.update(refs.handlers())
    assert run(doc,values)==[True]
    with pytest.raises(ValueError,match='Unknown sentence text span'):
        run(doc,values|{'jargd':lambda:Fraction(3)})
