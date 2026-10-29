"""Bind both questions without executing their rank-two descriptions or answers."""
from copy import deepcopy
import json
import pytest
from noema.constructed_semantics import evaluate_document
from scripts import check_kant_question_discourse_visible as check
from scripts.shared_modality import call,renamed
import test_kant_everywhere_restriction_visible as parent

REFERENCES={'h235n':'first-restriction-question','h235o':'second-restriction-question','h235p':'following-restriction-answer'}
DOMAIN=parent.DOMAIN+tuple(REFERENCES.values())


def evaluate(doc,values,memo=True):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=parent.parent.parent.parent.SCENES,
        primitives=values,max_steps=25000000,memoize_definitions=memo,memoize_expressions=memo)]


def expectations():
    qa=('quote',2,'call','r2ya');qb=('quote',2,'call','r2yb')
    loss=('quote',2,'function_ref','r2xx');nonloss=('quote',2,'function_ref','r2xy');gain=('quote',2,'function_ref','r2xz')
    return [('r2yc','h235i',('h235n','wa',qa,'h232o')),
        ('r2yc','h235j',('h235n','wa','h234o',('quote',1,'call','r2uz'),qa,'h232o')),
        ('r2yc','ue',('h234o','h235n','h232o')),('r2yc','hzcs',('wa','h235n','h235p','h232o')),
        ('r2yd','h235i',('h235o','wa',qb,'h232o')),
        ('r2yd','h235k',('h235o','wa',loss,gain,qb,'h232o')),
        ('r2yd','h235l',('h235o','wa',gain,qb,'h232o')),
        ('r2yd','h235m',('h235o','wa',nonloss,gain,qb,'h232o')),
        ('r2yd','ue',('h235n','h235o','h232o')),('r2yd','ue',('h235o','h235p','h232o')),
        ('r2yd','hzcs',('wa','h235o','h235p','h232o'))]


def model(doc,omitted=None,seen=None):
    values=parent.model(doc);voc=check.vocabulary();m=check.mapping();inverse={v:k for k,v in m.items()}
    oldsentence=values[voc._symbols['sentencereference']]
    def sentence(context,paragraph,index):
        if context=='closing' and paragraph==5 and index in (8,9,10):return REFERENCES[('h235n','h235o','h235p')[int(index)-8]]
        return oldsentence(context,paragraph,index)
    values[voc._symbols['sentencereference']]=sentence
    labels={v:k for k,v in REFERENCES.items()}|{parent.WHOLE:'h234o','author':'wa',parent.parent.parent.parent.parent.CONTEXT:'h232o'}
    expected=[(name,args) for _,name,args in expectations()]
    def normalized(value):
        if isinstance(value,str):return labels.get(value,value)
        if hasattr(value,'syntax'):
            code=renamed(json.loads(value.syntax),inverse)
            return ('quote',value.rank,code['kind'],code['symbol'])
        raise AssertionError(type(value))
    def handler(name,previous):
        def relation(*args):
            if name=='ue' and not any(isinstance(a,str) and a in REFERENCES.values() for a in args):return previous(*args)
            row=(name,tuple(normalized(a) for a in args))
            if row in expected:
                index=expected.index(row)
                if seen is not None:seen.add(index)
                return index!=omitted
            return False
        return relation
    for name in {n for _,n,_ in expectations()}:values[m[name]]=handler(name,values.get(m[name],lambda *args:False))
    return values


def selection(start=50):
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][start:]
    return doc


def calls(node,symbol):
    result=[]
    if isinstance(node,dict):
        if node.get('kind')=='call' and node.get('symbol')==symbol:result.append(node)
        for value in node.values():result+=calls(value,symbol)
    elif isinstance(node,list):
        for value in node:result+=calls(value,symbol)
    return result


def test_source_and_every_prior_declaration_are_preserved():
    doc=check.restored()['document'];old=check.previous.document()
    assert check.backprojection(doc)==check.source_excerpt()
    assert check.specialized_backprojection(doc)==check.specialized_source()
    assert doc['statements'][:50]==old['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert (len(doc['declarations']),len(doc['statements']))==(1578,52)
    assert len(check.source_excerpt()['declarations'])==1547
    assert check.SOURCE_ORDER[-2:]==[67,68] and 69 not in check.SOURCE_ORDER
    current=selection(43);assert evaluate(current,model(current))==[True]*9


def test_every_question_contrast_focus_and_answer_relation_is_required():
    doc=selection();seen=set();assert evaluate(doc,model(doc,seen=seen),memo=False)==[True,True]
    assert seen==set(range(11))
    for index,(root,_,_) in enumerate(expectations()):
        assert evaluate(doc,model(doc,omitted=index))==([False,True] if root=='r2yc' else [True,False])


def test_each_argument_and_both_text_order_edges_are_bound():
    doc=selection();m=check.mapping()
    substitutions={'h235n':'h235o','h235o':'h235n','h235p':'h234o','h234o':'h235p','wa':'h234o','h232o':'hzp3',
        'r2ya':'r2yb','r2yb':'r2ya','r2uz':'r2uo','r2xx':'r2xy','r2xy':'r2xz','r2xz':'r2xx'}
    occurrences={}
    for root,name,_ in expectations():
        occurrence=occurrences.get((root,name),0);occurrences[root,name]=occurrence+1
        body=next(d for d in doc['declarations'] if d['name']==m[root])['body']
        original=calls(body,m[name])[occurrence]
        for slot,arg in enumerate(original['arguments']):
            replacement=renamed(arg,{m[a]:m[b] for a,b in substitutions.items()})
            # Both questions genuinely share the answer relation. Replacing one
            # with the other is still true in this model; use a non-question.
            if name=='hzcs' and slot==1:replacement=call(m['h234o'])
            assert replacement!=arg
            changed=deepcopy(doc);changed_body=next(d for d in changed['declarations'] if d['name']==m[root])['body']
            calls(changed_body,m[name])[occurrence]['arguments'][slot]=replacement
            assert evaluate(changed,model(changed))==([False,True] if root=='r2yc' else [True,False]),(root,name,occurrence,slot)


def test_unknown_presentations_refused_and_world_questions_not_executed():
    doc=selection();m=check.mapping()
    def unknown(*args):raise ValueError('Unspecified question discourse input')
    for name in {n for _,n,_ in expectations()}:
        with pytest.raises(ValueError,match='Unspecified question'):evaluate(doc,model(doc)|{m[name]:unknown})
    values=model(doc)
    for name in set(check.profile.SOURCE_RELATIONS)-{n for _,n,_ in expectations()}:values[m[name]]=unknown
    assert evaluate(doc,values)==[True,True]


def test_all_three_references_are_exact_and_unknown_addresses_are_refused():
    m=check.mapping();voc=check.vocabulary()
    for name,expected in REFERENCES.items():
        doc=selection();doc['declarations'].append(dict(kind='primitive',name='jexpected',parameters=[],result='individual'))
        doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[call(m[name]),call('jexpected')]))]
        assert evaluate(doc,model(doc)|{'jexpected':lambda:expected})==[True]
        assert evaluate(doc,model(doc)|{'jexpected':lambda:parent.WHOLE})==[False]
        changed=deepcopy(doc);next(d for d in changed['declarations'] if d['name']==m[name])['body']['arguments'][2]['numerator']=7
        assert evaluate(changed,model(changed)|{'jexpected':lambda:expected})==[False]
        changed=deepcopy(doc);next(d for d in changed['declarations'] if d['name']==m[name])['body']['arguments'][2]['numerator']=99
        with pytest.raises(ValueError):evaluate(changed,model(changed)|{'jexpected':lambda:expected})
    def unknown(*args):raise ValueError('Unspecified question reference')
    with pytest.raises(ValueError,match='Unspecified question reference'):
        evaluate(doc,model(doc)|{voc._symbols['sentencereference']:unknown,'jexpected':lambda:expected})


def test_inherited_description_wrapper_mutations_are_refused():
    doc=deepcopy(check.restored()['document']);m=check.mapping()
    next(d for d in doc['declarations'] if d['name']==m['h227c'])['body']['arguments'][0]=call(m['wh'])
    with pytest.raises(ValueError,match='Reused description wrapper differs'):check.backprojection(doc)
