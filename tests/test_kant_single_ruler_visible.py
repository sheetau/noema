"""Preserve the ruler aside, exact preceding block and opaque quotation ranks."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_single_ruler_visible as check
from scripts.shared_modality import call,renamed
from scripts.moving_trip_visible_profile import MovingTextReferences
import test_kant_role_commands_visible as parent

REFERENCES={n:'single-ruler-'+n for n in ('h234i','h234j')}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())


def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=parent.parent.SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]


def quotation(body,rank=1):return ('quote',rank,json.dumps(body,sort_keys=True))


def expectations():
    q=lambda n:quotation(call(n))
    aspect=quotation(dict(kind='apply',function=dict(kind='function_ref',symbol='r2uq'),arguments=[call('h232v')]),0)
    return [('hzon',('h234i','wa',q('r2uo'),'h232o')),
        ('h222q',('h234i','wa','h234j',q('r2up'),'h234i',q('r2uo'),aspect,'h232o')),
        ('h234k',('h234i','wa','h234j','h232o')),('ue',('h233o','h234i','h232o'))]


def model(doc,omitted=None,seen=None):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']]
    def sentence(context,paragraph,index):
        if (context,paragraph,index)==('closing',5,6):return REFERENCES['h234i']
        return oldsentence(context,paragraph,index)
    refs=MovingTextReferences({('document',parent.REFERENCES['h233m'],parent.REFERENCES['h233o'],'closing'):REFERENCES['h234j']},{})
    values[voc._symbols['sentencereference']]=sentence
    values[voc._symbols['sentencespanreference']]=refs.span
    labels={v:k for k,v in (parent.REFERENCES|REFERENCES).items()}|{'author':'wa',parent.parent.parent.CONTEXT:'h232o'}
    expected=expectations()
    def normalized(value):
        if isinstance(value,str):return labels.get(value,value)
        if hasattr(value,'syntax'):return quotation(renamed(json.loads(value.syntax),inverse),value.rank)
        raise AssertionError(type(value))
    def handler(name,previous):
        def relation(*args):
            if not any(isinstance(a,str) and a in REFERENCES.values() for a in args):return previous(*args)
            row=(name,tuple(normalized(a) for a in args))
            if row in expected:
                index=expected.index(row)
                if seen is not None:seen.add(index)
                return index!=omitted
            return False
        return relation
    for name in {n for n,_ in expected}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values


def selection(start=48):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc


def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:48]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert len(doc['statements'])==49 and len(check.source_excerpt()['declarations'])==1451
    added=set(ds)-{d['name'] for d in old['declarations']}
    assert len(added)==52+(check.vocabulary()._symbols['sentencespanreference'] in added)
    current=selection(43)
    assert evaluate(current,model(current))==[True]*6


def find_call(value,name):
    if isinstance(value,dict):
        if value.get('kind')=='call' and value.get('symbol')==name:return value
        for child in value.values():
            found=find_call(child,name)
            if found is not None:return found
    elif isinstance(value,list):
        for child in value:
            found=find_call(child,name)
            if found is not None:return found


def test_each_attribution_contrast_aside_and_order_slot_is_bound():
    doc=selection();seen=set();assert evaluate(doc,model(doc,seen=seen),memo=False)==[True]
    assert seen==set(range(4))
    for index in range(4):assert evaluate(doc,model(doc,omitted=index))==[False]
    substitutions={'h234i':'h234j','h234j':'h234i','wa':'h234j','h232o':'hzp3','h233o':'h233m',
        'r2uo':'r2up','r2up':'r2uo','h232v':'h232o'}
    m=check.mapping()
    for name,_ in expectations():
        original=find_call(next(d for d in doc['declarations'] if d['name']==m['r2ur'])['body'],m[name])
        for slot,arg in enumerate(original['arguments']):
            changed=deepcopy(doc);body=next(d for d in changed['declarations'] if d['name']==m['r2ur'])['body']
            replacement=renamed(arg,{m[a]:m[b] for a,b in substitutions.items()})
            assert replacement!=arg,(name,slot)
            find_call(body,m[name])['arguments'][slot]=replacement
            assert evaluate(changed,model(changed))==[False],(name,slot)


def test_unknown_presentations_refused_and_world_contents_not_executed():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified single-ruler relation')
    for name,_ in expectations():
        with pytest.raises(ValueError,match='Unspecified single-ruler'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{'h234k'}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True]


def reference_questions():
    doc=selection();m=check.mapping()
    doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[n]),call('jexpected')])) for n in REFERENCES]
    return doc


def test_sentence_and_contiguous_block_references_remain_distinct():
    doc=reference_questions();m=check.mapping()
    for index,target in enumerate(REFERENCES.values()):
        assert evaluate(doc,model(doc)|{'jexpected':lambda target=target:target})==[i==index for i in range(2)]
    for slot,replacement in ((0,call(m['wa'])),(1,call(m['h233n'])),(2,call(m['h233n'])),(3,call(m['h232o']))):
        changed=deepcopy(doc);next(d for d in changed['declarations'] if d['name']==m['h234j'])['body']['arguments'][slot]=replacement
        with pytest.raises(ValueError,match='Unknown sentence span'):evaluate(changed,model(changed)|{'jexpected':lambda:'other'})
    changed=deepcopy(doc);args=next(d for d in changed['declarations'] if d['name']==m['h234j'])['body']['arguments']
    args[1],args[2]=args[2],args[1]
    with pytest.raises(ValueError,match='Unknown sentence span'):evaluate(changed,model(changed)|{'jexpected':lambda:'other'})


def test_unknown_reference_operations_are_refused():
    doc=reference_questions();voc=check.vocabulary()
    def unknown(*args):raise ValueError('Unspecified single-ruler reference')
    for name in ('sentencereference','sentencespanreference'):
        with pytest.raises(ValueError,match='Unspecified single-ruler reference'):
            evaluate(doc,model(doc)|{voc._symbols[name]:unknown,'jexpected':lambda:'other'})


def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)
