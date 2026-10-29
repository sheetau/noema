"""Keep all four antecedents, their order and restriction attribution after recovery."""
from copy import deepcopy
from itertools import combinations
import json
import pytest
from noema.constructed_semantics import evaluate_document,SequenceValue
from scripts import check_kant_everywhere_restriction_visible as check
from scripts.shared_modality import call,renamed
import test_kant_single_ruler_visible as parent

WHOLE='everywhere-restriction-sentence'
DOMAIN=parent.DOMAIN+(WHOLE,)
NODES=('h233m','h233n','h233o','h234i')


def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=parent.parent.parent.SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]


def expectations():
    return [('hzon',('h234o','wa',('quote',1,'call','r2uz'),'h232o')),
        ('h234p',('h234o','wa',NODES,'h232o')),('ue',('h234i','h234o','h232o'))]


def model(doc,omitted=None,seen=None):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',5,7):return WHOLE
        return oldsentence(context,paragraph,index)
    values[voc._symbols['sentencereference']]=sentence
    labels={v:k for k,v in (parent.parent.REFERENCES|parent.REFERENCES).items()}|{
        WHOLE:'h234o','author':'wa',parent.parent.parent.parent.CONTEXT:'h232o'}
    expected=expectations()
    def normalized(value):
        if isinstance(value,str):return labels.get(value,value)
        if isinstance(value,SequenceValue):return tuple(normalized(x) for x in value.items)
        if hasattr(value,'syntax'):
            code=renamed(json.loads(value.syntax),inverse)
            return ('quote',value.rank,code['kind'],code['symbol'])
        raise AssertionError(type(value))
    def handler(name,previous):
        def relation(*args):
            if name!='h234p' and not any(isinstance(a,str) and a==WHOLE for a in args):return previous(*args)
            row=(name,tuple(normalized(a) for a in args))
            if row in expected:
                index=expected.index(row)
                if seen is not None:seen.add(index)
                return index!=omitted
            return False
        return relation
    for name in {n for n,_ in expected}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values


def selection(start=49):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc


def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:49]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert (len(doc['declarations']),len(doc['statements']))==(1496,50)
    assert len(check.source_excerpt()['declarations'])==1465
    current=selection(43);assert evaluate(current,model(current))==[True]*7


def test_each_attribution_anaphora_and_order_argument_is_bound():
    doc=selection();seen=set();assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]
    assert seen==set(range(3))
    for index in range(3):assert evaluate(doc,model(doc,omitted=index))==[False]
    m=check.mapping();substitutions={'h234o':'h234i','wa':'h234i','h232o':'hzp3','h234i':'h233o','r2uz':'r2uo'}
    for name,_ in expectations():
        original=parent.find_call(next(d for d in doc['declarations'] if d['name']==m['r2va'])['body'],m[name])
        for slot,arg in enumerate(original['arguments']):
            if name=='h234p' and slot==2:continue
            replacement=renamed(arg,{m[a]:m[b] for a,b in substitutions.items()});assert replacement!=arg
            changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['r2va'])['body']
            parent.find_call(body,m[name])['arguments'][slot]=replacement
            assert evaluate(changed,model(changed))==[False],(name,slot)


def test_every_antecedent_and_sequence_position_is_required():
    doc=selection();m=check.mapping()
    original=next(d for d in doc['declarations'] if d['name']==m['r2us'])['body']['items']
    assert original==[call(m[n]) for n in NODES]
    variants=[]
    for index in range(4):
        variants.append(original[:index]+original[index+1:])
        replaced=deepcopy(original);replaced[index]=call(m['h234o']);variants.append(replaced)
    for first,last in combinations(range(4),2):
        swapped=deepcopy(original);swapped[first],swapped[last]=swapped[last],swapped[first];variants.append(swapped)
    for items in variants:
        changed=deepcopy(doc);next(d for d in changed['declarations'] if d['name']==m['r2us'])['body']['items']=items
        assert evaluate(changed,model(changed))==[False]


def test_unknown_presentations_refused_and_world_contents_not_executed():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified restriction relation')
    for name,_ in expectations():
        with pytest.raises(ValueError,match='Unspecified restriction'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{'h234p'}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True]


def test_sentence_reference_is_exact_and_unknown_addresses_are_refused():
    doc=selection();m=check.mapping();voc=check.vocabulary()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m['h234o']),call('jexpected')]))]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:WHOLE})==[True]
    assert evaluate(doc,model(doc)|{'jexpected':lambda:parent.REFERENCES['h234i']})==[False]
    changed=deepcopy(doc);next(d for d in changed['declarations'] if d['name']==m['h234o'])['body']['arguments'][2]['numerator']=6
    assert evaluate(changed,model(changed)|{'jexpected':lambda:WHOLE})==[False]
    changed=deepcopy(doc);next(d for d in changed['declarations'] if d['name']==m['h234o'])['body']['arguments'][2]['numerator']=99
    with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:WHOLE})
    def unknown(*args):raise ValueError('Unspecified restriction reference')
    with pytest.raises(ValueError,match='Unspecified restriction reference'):
        evaluate(doc,model(doc)|{voc._symbols['sentencereference']:unknown,'jexpected':lambda:WHOLE})


def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)
