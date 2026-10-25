"""Shared witness, accessibility and identification checks on two-element domains."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.shared_discourse import *
from scripts.shared_readings import num

EXAMPLE='examples/v016/scoped-referents-v1.noema'
PEOPLE=('a','b')


def ref(n):return dict(kind='function_ref',symbol=n)
def apply_expr(fn,*args):return dict(kind='apply',function=fn,arguments=list(args))
def seq(*items):return dict(kind='sequence',element=I,items=list(items))
def join(*updates):
    result=updates[-1]
    for item in reversed(updates[:-1]):result=call('sequencediscourse',item,result)
    return result
def introduce(name,distinct=False):return call('distinctreferent' if distinct else 'introducereferent',ref(name))
def test(name,index=0):return call('discoursetest',call('referenttest',num(index),ref(name)))
def holds(update,initial=None):return call('discourseholds',update,empty() if initial is None else initial,call('now'))
def candidate(update,index=0,target='known',initial=None):
    return call('discoursecandidate',update,empty() if initial is None else initial,num(index),call(target),call('now'))
def unique(update,index=0,initial=None):return call('discourseunique',update,empty() if initial is None else initial,num(index),call('now'))


@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    signatures={n:([I,S],T) for n in ('arrived','seated','delivered','opened')}
    signatures.update(helped=([I,I,S],T),now=([],S),known=([],I),other=([],I),source=([],I),reason=([],I),
                      identity=(IDENTITY['parameters'],T))
    d['declarations'] += [dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in signatures.items()]
    return normalize_document(d)


def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies]
    return normalize_document(d)


def unknown(*args):raise ValueError('Unknown interpretation')
def model(**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update(now=lambda:'now',known=lambda:'a',other=lambda:'b',source=lambda:'a',reason=lambda:'b')
    m.update(overrides);return m
def values(document,m):
    return [r['value'] if 'value' in r else r['answers'] for r in evaluate_document(
        document,individuals=PEOPLE,situations=('now','elsewhere'),primitives=m)]


def sets():return [{x for i,x in enumerate(PEOPLE) if mask&(1<<i)} for mask in range(4)]


@lru_cache(maxsize=1)
def introduction_checks():
    count=0
    for first,second in (('arrived','seated'),('delivered','opened')):
        chain=join(introduce(first),test(second))
        d=doc([holds(chain),candidate(chain),candidate(chain,target='other'),unique(chain)])
        for p,q_ in product(sets(),repeat=2):
            surviving=p&q_
            expected=[bool(surviving),'a' in surviving,'b' in surviving,len(surviving)==1]
            m=model(**{first:lambda x,w:x in p and w=='now',second:lambda x,w:x in q_ and w=='now'})
            if values(d,m)!=expected:raise ValueError('Subsequent clause changed existential witness')
            count+=1
    return dict(models=count,domain_size=2,topics=['来訪者と着席','荷物の到着と開封'])


@lru_cache(maxsize=1)
def relation_checks():
    relation=lambda a,b:call('discoursetest',call('referentrelation',num(a),num(b),ref('helped')))
    normal=join(introduce('arrived'),introduce('seated'),relation(0,1))
    reversed_=join(introduce('arrived'),introduce('seated'),relation(1,0))
    distinct=join(introduce('arrived'),introduce('seated',True),relation(0,1))
    d=doc([holds(normal),holds(reversed_),holds(distinct)])
    pairs=list(product(PEOPLE,repeat=2));count=0
    for p,q_,mask in product(sets(),sets(),range(16)):
        edges={pair for i,pair in enumerate(pairs) if mask&(1<<i)}
        expected=[any((a,b) in edges for a in p for b in q_),any((b,a) in edges for a in p for b in q_),
                  any(a!=b and (a,b) in edges for a in p for b in q_)]
        m=model(arrived=lambda x,w:x in p,seated=lambda x,w:x in q_,helped=lambda x,y,w:(x,y) in edges)
        if values(d,m)!=expected:raise ValueError('Subject, object or distinctness changed')
        count+=1
    return dict(models=count,domain_size=2)


@lru_cache(maxsize=1)
def scope_checks():
    intro=introduce('arrived');consequent=test('seated')
    conditional=call('conditionaldiscourse',intro,consequent)
    negative=call('negateddiscourse',intro)
    alternative=call('alternativediscourse',intro,introduce('seated'))
    closed=call('closeddiscourse',join(intro,consequent))
    d=doc([holds(conditional),candidate(conditional),holds(negative),candidate(negative),
           holds(alternative),candidate(alternative),holds(closed),candidate(closed)])
    count=0
    for p,q_ in product(sets(),repeat=2):
        expected=[p<=q_,False,not p,False,bool(p or q_),False,bool(p&q_),False]
        m=model(arrived=lambda x,w:x in p,seated=lambda x,w:x in q_)
        if values(d,m)!=list(map(bool,expected)):raise ValueError('Local referent escaped its scope')
        count+=1
    return dict(models=count,conditional_reading='all successful antecedent assignments',new_referents_exported=False)


def identification():
    return call('identifyreferent',num(0),call('known'),call('source'),call('reason'),ref('identity'))


@lru_cache(maxsize=1)
def identification_bindings():
    chain=join(introduce('arrived'),identification())
    d=doc([holds(chain),unique(chain),candidate(chain),candidate(chain,target='other')]);rows=[]
    wanted=('a','b','a','a','now');other=('b','a','b','b','elsewhere')
    for slot in range(-1,len(wanted)):
        target=list(wanted)
        if slot>=0:target[slot]=other[slot]
        m=model(arrived=lambda *a:True,identity=lambda *a,target=tuple(target):a==target)
        actual=values(d,m);expected=[True,True,True,False] if slot<0 else [False]*4
        if actual!=expected:raise ValueError('Identification provenance changed')
        rows.append(dict(changed_slot=None if slot<0 else slot,values=actual))
    return rows


def example():
    bodies=[]
    for first,second in (('arrived','seated'),('delivered','opened')):
        introduction=introduce(first);chain=join(introduction,test(second))
        bodies.extend([holds(introduction),unique(introduction),holds(chain),unique(chain),candidate(chain),candidate(chain,target='other')])
    ant=introduce('arrived');conditional=call('conditionaldiscourse',ant,test('seated'))
    bodies.extend([holds(conditional),candidate(conditional),holds(call('negateddiscourse',ant)),
                   holds(join(ant,call('aliasreferent',num(0)),test('seated',1))),
                   holds(join(ant,identification())),unique(join(ant,identification()))])
    bodies.extend(call('referentquestion',u,empty(),num(0),call('now')) for u in (ant,join(ant,test('seated'))))
    return doc(bodies)


def example_model():
    return model(arrived=lambda x,w:w=='now',seated=lambda x,w:x=='b' and w=='now',
        delivered=lambda x,w:w=='now',opened=lambda x,w:x=='a' and w=='now',
        identity=lambda s,r,x,y,w:(s,r,x,y,w)==('a','b','a','a','now'))


EXPECTED=[True,False,True,True,False,True,True,False,True,True,True,False,False,False,False,True,True,True,
          [['a'],['b']],[['b']]]


def prepare():
    from scripts.shared_discourse import prepare as prepare_library
    prepare_library();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published scoped example differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published module differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published contracts differ')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Meaning catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Published example differs')
    result=dict(schema='noema-shared-discourse-evidence-1',definitions=19,new_primitives=0,
        introduction=introduction_checks(),relations=relation_checks(),scope=scope_checks(),
        identification_bindings=identification_bindings(),example=values(example(),example_model()))
    if result['example']!=EXPECTED:raise ValueError('Integrated discourse differs')
    paths=[LIBRARY,BASIS,EXAMPLE,'docs/shared-discourse-v1.md','scripts/shared_discourse.py','scripts/check_shared_discourse.py',
        'tests/test_shared_discourse.py','scripts/shared_modality.py','scripts/shared_time.py','scripts/shared_reference.py',
        'scripts/shared_readings.py',*basis()['design_sources']]
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=basis()['limitations']
    return result
