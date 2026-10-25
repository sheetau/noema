"""Finite state-set oracles, social tuple diagnostics and a retained history."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_conversation import *
from scripts.shared_speech import OCCURS,PRESENTS,CONVEYS

EXAMPLE='examples/v016/accepted-corrected-withdrawn-v1.noema'
PEOPLE=('a','b')


def ref(n):return dict(kind='function_ref',symbol=n)
def quote(body):return dict(kind='quote',body=body)
def seq(sort,items):return dict(kind='sequence',element=sort,items=list(items))
def claim(name='firstform',subject='aki'):return call('utteranceinstance',quote(ref(name)),quote(call(subject)))
def state(entries):return [seq(I,[call(owner) for owner,form in entries]),seq(D,[claim(form) for owner,form in entries])]
def unknown(*a):raise ValueError('Unknown interpretation')
def subsets(xs):return [set(x for i,x in enumerate(xs) if mask&(1<<i)) for mask in range(1<<len(xs))]
def describe(x):
    if not hasattr(x,'syntax'):return x
    d=json.loads(x.syntax)
    if d['kind']=='function_ref':return ('function',d['symbol'])
    if d['kind']=='apply':return ('form',d['function']['symbol'],d['arguments'][0]['symbol'])
    return x.syntax


@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    signatures={n:([],I) for n in ('aki','nao')}
    signatures.update(now=([],S),then=([],S),payload=([I,S],T))
    signatures.update({n:(sort['parameters'],T) for n,sort in [('occurs',OCCURS),('presents',PRESENTS),
        ('conveys',CONVEYS),('receives',CONVEYS),('understands',CONVEYS),('accepts',CONVEYS),
        ('withdraws',WITHDRAW),('corrects',CORRECT),('before',BEFORE)]})
    d['declarations'] += [dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in signatures.items()]
    for name in ('firstform','secondform'):
        d['declarations'].append(definition(name,[('subject',I)],U,dict(kind='message',force='assert',
            content=dict(kind='content',variable='world',body=call('payload',v('subject'),v('world'))))))
    return normalize_document(d)


def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def expected_slots():
    reception=('a','b','a',('function','firstform'),'now')
    return dict(occurs=('a','now'),presents=('a','a','now'),conveys=reception,receives=reception,
        understands=reception,accepts=reception,
        withdraws=('b','a',('form','firstform','aki'),'a','now'),
        corrects=('b','a',('form','firstform','aki'),('form','secondform','aki'),'a','now'),before=('now','later'))
def model(**overrides):
    m={x['name']:unknown for x in base()['declarations'] if x['kind']=='primitive'}
    m.update(rationaladd=lambda a,b:a+b,aki=lambda:'a',nao=lambda:'b',now=lambda:'now',then=lambda:'later')
    for n,wanted in expected_slots().items():m[n]=lambda *xs,wanted=wanted:tuple(describe(x) for x in xs)==wanted
    m.update(overrides);return m
def values(d,m,situations=('now','later')):
    return [r['value'] for r in evaluate_document(d,individuals=PEOPLE,situations=situations,primitives=m,max_steps=1000000)]


def structural_queries(before,after):
    change=state(sorted(before))+state(sorted(after))
    bodies=[call('commitmentsame',*change),call('commitmentsubset',*change)]
    for owner in ('aki','nao'):
        for form in ('firstform','secondform'):
            bodies += [call(name,*change,call(owner),claim(form)) for name in ('commitmentincluded','commitmentadded','commitmentremoved')]
            other='secondform' if form=='firstform' else 'firstform'
            bodies.append(call('commitmentreplaced',*change,call(owner),claim(form),claim(other)))
    return bodies


@lru_cache(maxsize=1)
def state_checks():
    pairs=list(product(('aki','nao'),('firstform','secondform')));sets=subsets(pairs);count=0
    for before,after in product(sets,repeat=2):
        expected=[before==after,before<=after]
        for owner,form in pairs:
            item=(owner,form);other=(owner,'secondform' if form=='firstform' else 'firstform')
            expected += [after==before|{item},item not in before and after==before|{item},
                item in before and after==before-{item},item in before and after==(before-{item})|{other}]
        if values(doc(structural_queries(before,after)),model())!=expected:raise ValueError('State relation differs')
        count+=1
    return dict(models=count,people=2,descriptions=2,checks_per_model=18)


INITIAL=[('aki','secondform')]
ADOPTED=INITIAL+[('nao','firstform')]
CORRECTED=INITIAL+[('nao','secondform')]


def accepted(before=INITIAL,after=ADOPTED):
    return call('commitmentaccepted',*state(before),*state(after),call('aki'),call('aki'),call('nao'),call('aki'),
        quote(ref('firstform')),call('now'),*(ref(n) for n in ('occurs','presents','conveys','receives','understands','accepts')),quote(call('aki')))
def withdrawn(before=ADOPTED,after=INITIAL):
    return call('commitmentwithdrawn',*state(before),*state(after),call('nao'),claim(),call('aki'),call('aki'),call('now'),ref('withdraws'))
def corrected(before=ADOPTED,after=CORRECTED):
    return call('commitmentcorrected',*state(before),*state(after),call('nao'),claim(),claim('secondform'),call('aki'),call('aki'),call('now'),ref('corrects'))
def linked(left=ADOPTED,right=ADOPTED):
    return call('conversationlinked',call('aki'),call('aki'),*state(left),*state(right),call('now'),call('then'),ref('before'))


@lru_cache(maxsize=1)
def grounded_checks():
    pairs=list(product(('aki','nao'),('firstform','secondform')));count=0
    for bits,after in product(product((False,True),repeat=3),subsets(pairs)):
        d=doc([accepted(after=sorted(after)),withdrawn(after=sorted(after)),corrected(after=sorted(after))])
        m=model(accepts=lambda *xs,b=bits[0]:b,withdraws=lambda *xs,b=bits[1]:b,corrects=lambda *xs,b=bits[2]:b)
        expected=[bits[0] and after==set(ADOPTED),bits[1] and after==set(INITIAL),bits[2] and after==set(CORRECTED)]
        if values(d,m)!=expected:raise ValueError('Grounding and state change conflated')
        count+=1
    return dict(models=count,explicit_social_flags=3,possible_after_states=16)


@lru_cache(maxsize=1)
def binding_diagnostics():
    rows=[]
    for relation,wanted in expected_slots().items():
        query=withdrawn() if relation=='withdraws' else corrected() if relation=='corrects' else linked() if relation=='before' else accepted()
        d=doc([query])
        if values(d,model())!=[True]:raise ValueError('Unchanged tuple fails')
        for slot,item in enumerate(wanted):
            if isinstance(item,tuple):
                other=list(item);other[1]='secondform' if item[1]=='firstform' else 'firstform';other=tuple(other)
            elif item in PEOPLE:other='b' if item=='a' else 'a'
            else:other='later' if item=='now' else 'now'
            changed=list(wanted);changed[slot]=other
            m=model(**{relation:lambda *xs,changed=tuple(changed):tuple(describe(x) for x in xs)==changed})
            actual=values(d,m)
            if actual!=[False]:raise ValueError('Mismatched tuple accepted')
            rows.append(dict(relation=relation,slot=slot,result=False))
    return rows


def matching(sort,expected):
    ps=[('arg'+chr(97+i),t) for i,t in enumerate(sort['parameters'])]
    return lam(ps,allof(*(eq(v(n),e) for (n,t),e in zip(ps,expected))))


@lru_cache(maxsize=1)
def example():
    from scripts.shared_answers import composed as answers,matches
    d=deepcopy(composed());d['declarations']+=deepcopy(answers()['declarations'])
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=t) for n,t in [('aki',I),('nao',I),('now',S),('then',S),('last',S)]]
    one=lam([('candidate',I)],eq(v('candidate'),call('aki')))
    both=lam([('candidate',I)],op('or',eq(v('candidate'),call('aki')),eq(v('candidate'),call('nao'))))
    empty=lam([('candidate',I)],truth(False));question=dict(kind='question',function=both)
    for name,condition in [('firstform',call('answercomplete',question,one,empty,truth(True))),
                           ('secondform',call('answerpartial',question,one,empty,truth(False)))]:
        d['declarations'].append(definition(name,[('subject',I)],U,dict(kind='message',force='assert',
            content=dict(kind='content',variable='world',body=condition))))
    expected=[call('aki'),call('nao'),call('aki'),quote(ref('firstform')),call('now')]
    uptake=[matching(OCCURS,[call('aki'),call('now')]),matching(PRESENTS,[call('aki'),call('aki'),call('now')])]
    uptake += [matching(CONVEYS,expected) for _ in range(4)]
    reception=call('commitmentaccepted',*state(INITIAL),*state(ADOPTED),call('aki'),call('aki'),call('nao'),call('aki'),
        quote(ref('firstform')),call('now'),*uptake,quote(call('aki')))
    correction=call('commitmentcorrected',*state(ADOPTED),*state(CORRECTED),call('nao'),claim(),claim('secondform'),
        call('aki'),call('nao'),call('then'),matching(CORRECT,[call('nao'),call('aki'),claim(),claim('secondform'),call('nao'),call('then')]))
    withdrawal=call('commitmentwithdrawn',*state(CORRECTED),*state(INITIAL),call('nao'),claim('secondform'),
        call('nao'),call('aki'),call('last'),matching(WITHDRAW,[call('nao'),call('nao'),claim('secondform'),call('aki'),call('last')]))
    before=lam([('first',S),('second',S)],op('or',op('and',eq(v('first'),call('now')),eq(v('second'),call('then'))),
        op('and',eq(v('first'),call('then')),eq(v('second'),call('last')))))
    link=lambda entries,start,end:call('conversationlinked',call('aki'),call('aki'),*state(entries),*state(entries),call(start),call(end),before)
    evaluate=lambda form:dict(kind='evaluate',content=dict(kind='message_content',message=dict(kind='disquote',description=claim(form))),situation=call('last'))
    bodies=[reception,correction,withdrawal,link(ADOPTED,'now','then'),link(CORRECTED,'then','last'),
        call('commitmenthas',*state(INITIAL),call('nao'),claim()),call('commitmenthas',*state(ADOPTED),call('nao'),claim()),
        call('commitmenthas',*state(CORRECTED),call('nao'),claim()),call('commitmenthas',*state(CORRECTED),call('nao'),claim('secondform')),
        call('commitmenthas',*state(INITIAL),call('nao'),claim('secondform')),call('commitmenthas',*state(INITIAL),call('aki'),claim('secondform')),
        evaluate('firstform'),evaluate('secondform'),call('commitmentsame',*state(INITIAL),*state(INITIAL))]
    d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)


EXAMPLE_RESULTS=[True,True,True,True,True,False,True,False,True,False,True,False,True,True]
def example_model():return dict(rationaladd=lambda a,b:a+b,aki=lambda:'a',nao=lambda:'b',now=lambda:'start',then=lambda:'middle',last=lambda:'end')


def prepare():
    from scripts.shared_conversation import prepare as prepare_library
    prepare_library();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published conversation history differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Conversation definitions differ')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Conversation basis differs')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Conversation catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Conversation history differs')
    actual=values(example(),example_model(),('start','middle','end'))
    if actual!=EXAMPLE_RESULTS:raise ValueError('Conversation history meaning differs')
    result=dict(schema='noema-shared-conversation-evidence-1',definitions=19,new_definitions=14,preserved_definitions=5,
        preserved_primitives=1,new_primitive_declarations=0,state_sets=state_checks(),grounded_changes=grounded_checks(),
        single_slot_binding_diagnostics=binding_diagnostics(),example=actual)
    paths=[LIBRARY,BASIS,EXAMPLE,'scripts/shared_conversation.py','scripts/check_shared_conversation.py',
        'tests/test_shared_conversation.py','docs/shared-conversation-v1.md','scripts/shared_readings.py',
        'scripts/shared_reference.py','scripts/shared_modality.py','scripts/shared_time.py','scripts/shared_speech.py','scripts/shared_answers.py']
    for source in SOURCES:paths.extend((source['document'],source['basis']))
    for report in ('reports/shared-speech-v1.json','reports/shared-answers-v1.json'):
        hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend((report,*hashes))
        for path,digest in hashes.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Earlier evidence changed: '+path)
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=LIMITS;return result
