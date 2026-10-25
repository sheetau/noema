"""Independent finite conditions and two composed uses of plural predicates."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_plurality import *

EXAMPLE='examples/v016/collective-distributive-v1.noema'
PEOPLE=('a','b')


def ref(name):return dict(kind='function_ref',symbol=name)
def unknown(*args):raise ValueError('Unknown interpretation')


@lru_cache(maxsize=1)
def base():
    doc=deepcopy(composed())
    signatures={n:([I],T) for n in ('actors','targets','pianos','machines')}
    signatures.update(occurs=([I,S],T),participates=([I,I,S],T),affects=([I,I,S],T),
        lifted=([I,I,S],T),checked=([I,I,S],T),related=([I,I,S],T),paired=([I,I],T),
        assignment=([I],I),now=([],S))
    signatures.update({n:([],I) for n in ('alice','bob','piano','machinea','machineb','eventa','eventb','eventc')})
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in signatures.items()]
    return normalize_document(doc)


def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies]
    return normalize_document(d)
def model(**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update(alice=lambda:'a',bob=lambda:'b',now=lambda:'now');m.update(overrides)
    return m
def values(d,m,people=PEOPLE):
    return [r['value'] if 'value' in r else r['answers'] for r in evaluate_document(
        d,individuals=people,situations=('now','elsewhere'),primitives=m)]
def subsets(items):
    return [{x for i,x in enumerate(items) if mask&(1<<i)} for mask in range(1<<len(items))]
def action_args(affects='affects'):
    return [call('now'),ref('occurs'),ref('participates'),ref(affects)]
def object_call(name,targets='targets',affects='affects'):
    middle=[ref('assignment')] if name in ('assignedobjects','distinctobjects','exclusiveobjects') else []
    return call(name,ref('actors'),ref(targets),*middle,*action_args(affects))
def action_call(name):return call(name,ref('actors'),*action_args()[:-1])


@lru_cache(maxsize=1)
def membership_checks():
    count=0
    for length in range(5):
        for items in product(('alice','bob'),repeat=length):
            s=seq(*(call(n) for n in items));distinct=len(set(items))==len(items)
            d=doc([call('distinctmembers',s),call('membercount',s,num(length)),
                   call('memberof',s,call('alice')),call('memberof',s,call('bob'))])
            if values(d,model())!=[distinct,distinct,'alice' in items,'bob' in items]:raise ValueError('Sequence membership differs')
            count+=1
    return dict(sequences=count,max_length=4,alphabet_size=2)


@lru_cache(maxsize=1)
def action_checks():
    d=doc([action_call('collectiveaction'),action_call('distributedaction')]);count=0
    for occurring,participation in product(subsets(PEOPLE),subsets(list(product(PEOPLE,repeat=2)))):
        common=any(e in occurring and all((a,e) in participation for a in PEOPLE) for e in PEOPLE)
        separate=all(any(e in occurring and (a,e) in participation for e in PEOPLE) for a in PEOPLE)
        m=model(actors=lambda x:True,occurs=lambda e,w:e in occurring and w=='now',
                participates=lambda a,e,w:(a,e) in participation and w=='now')
        if values(d,m)!=[common,separate]:raise ValueError('Event quantifier scope differs')
        count+=1
    return dict(models=count,domain_size=2)


@lru_cache(maxsize=4)
def assignment_checks(assignment):
    selected=dict(zip(PEOPLE,assignment))
    d=doc([call(n,ref('actors'),ref('assignment'),*action_args()[:-1]) for n in ('assignedactions','distinctactions')])
    count=0
    for occurring,participation in product(subsets(PEOPLE),subsets(list(product(PEOPLE,repeat=2)))):
        m=model(actors=lambda x:True,assignment=lambda x:selected[x],occurs=lambda e,w:e in occurring,
            participates=lambda a,e,w:(a,e) in participation)
        assigned=all(selected[a] in occurring and (a,selected[a]) in participation for a in PEOPLE)
        if values(d,m)!=[assigned,assigned and len(set(assignment))==2]:raise ValueError('Event assignment differs')
        count+=1
    return dict(assignment=list(assignment),models=count,domain_size=2)


@lru_cache(maxsize=1)
def object_checks():
    names=['collectiveobject','eachobject','sameobject','assignedobjects','distinctobjects','exclusiveobjects']
    d=doc([object_call(n) for n in names]);count=0
    edges=subsets(list(product(PEOPLE,repeat=2)))
    for participating,affecting in product(edges,repeat=2):
        related=lambda a,t:any((a,e) in participating and (e,t) in affecting for e in PEOPLE)
        common=any((e,t) in affecting and all((a,e) in participating for a in PEOPLE) for t in PEOPLE for e in PEOPLE)
        each_=all(any(related(a,t) for t in PEOPLE) for a in PEOPLE)
        same=any(all(related(a,t) for a in PEOPLE) for t in PEOPLE)
        assigned=all(related(a,a) for a in PEOPLE)
        exclusive=assigned and all(not related(a,t) for a in PEOPLE for t in PEOPLE if a!=t)
        m=model(actors=lambda x:True,targets=lambda x:True,occurs=lambda e,w:w=='now',assignment=lambda x:x,
            participates=lambda a,e,w:(a,e) in participating and w=='now',
            affects=lambda e,t,w:(e,t) in affecting and w=='now')
        if values(d,m)!=[common,each_,same,assigned,assigned,exclusive]:raise ValueError('Target or event witness changed')
        count+=1
    return dict(models=count,domain_size=2,assignment='identity witness; not a quantification over all functions')


@lru_cache(maxsize=1)
def coverage_checks():
    d=doc([call('coveredgroups',ref('actors'),ref('targets'),ref('paired'))]);count=0
    for actors,targets,edges in product(subsets(PEOPLE),subsets(PEOPLE),subsets(list(product(PEOPLE,repeat=2)))):
        expected=bool(actors and targets) and all(any((a,t) in edges for t in targets) for a in actors) and all(
            any((a,t) in edges for a in actors) for t in targets)
        m=model(actors=lambda x:x in actors,targets=lambda x:x in targets,paired=lambda a,t:(a,t) in edges)
        if values(d,m)!=[expected]:raise ValueError('Coverage changed to all pairs or lost a role')
        count+=1
    return dict(models=count,domain_size=2)


@lru_cache(maxsize=1)
def reciprocal_checks():
    people=('a','b','c');pairs=[(a,b) for a in people for b in people if a!=b]
    names=('reciprocalall','reciprocalneighbors','reciprocalpairs')
    d=doc([call(n,ref('actors'),ref('related'),call('now')) for n in names]);count=0
    for edges in subsets(pairs):
        expected=[all((a,b) in edges for a,b in pairs),
            all(any((a,b) in edges for b in people if b!=a) and any((b,a) in edges for b in people if b!=a) for a in people),
            all(any((a,b) in edges and (b,a) in edges for b in people if b!=a) for a in people)]
        m=model(actors=lambda x:True,related=lambda a,b,w:(a,b) in edges and w=='now')
        if values(d,m,people)!=expected:raise ValueError('Reciprocal readings collapsed')
        count+=1
    return dict(models=count,domain_size=3,reason='Three members distinguish directed cycles, mutual neighbors and all pairs')


@lru_cache(maxsize=1)
def binding_diagnostics():
    # Direct native body check with all individual witnesses instantiated.
    d=doc([call('actionobject',call('alice'),call('bob'),call('alice'),*action_args())])
    expected={'occurs':('b','now'),'participates':('a','b','now'),'affects':('b','a','now')}
    rows=[]
    for field,wanted in expected.items():
        for slot in range(-1,len(wanted)):
            target=list(wanted)
            if slot>=0:target[slot]='elsewhere' if target[slot]=='now' else 'b' if target[slot]=='a' else 'a'
            callbacks={n:(lambda *xs,t=t:xs==t) for n,t in expected.items()}
            callbacks[field]=lambda *xs,t=tuple(target):xs==t
            actual=values(d,model(**callbacks))
            if actual!=[slot<0]:raise ValueError('Action/object tuple binding differs')
            rows.append(dict(relation=field,changed_slot=None if slot<0 else slot,value=actual[0]))
    return rows


def example():
    group=seq(call('alice'),call('bob'))
    bodies=[call('membercount',group,num(2)),call('membercount',seq(call('piano')),num(1))]
    bodies += [object_call(n,'pianos','lifted') for n in ('collectiveobject','eachobject','sameobject')]
    bodies += [object_call(n,'machines','checked') for n in ('collectiveobject','eachobject','sameobject','assignedobjects','distinctobjects','exclusiveobjects')]
    bodies += [call('exactparticipants',ref('actors'),call('eventa'),call('now'),ref('participates')),
               op('not',object_call('collectiveobject','machines','checked'))]
    return doc(bodies)


EXAMPLE_PEOPLE=('a','b','piano','machinea','machineb','eventa','eventb','eventc')
EXPECTED=[True,True,True,True,True,False,True,False,True,True,True,True,True]
def example_model():
    m=model(actors=lambda x:x in PEOPLE,pianos=lambda x:x=='piano',machines=lambda x:x in ('machinea','machineb'),
        occurs=lambda e,w:e in ('eventa','eventb','eventc') and w=='now',
        participates=lambda a,e,w:(a,e) in {('a','eventa'),('b','eventa'),('a','eventb'),('b','eventc')} and w=='now',
        lifted=lambda e,t,w:(e,t,w)==('eventa','piano','now'),
        checked=lambda e,t,w:(e,t) in {('eventb','machinea'),('eventc','machineb')} and w=='now',
        assignment=lambda a:'machineb' if a=='b' else 'machinea')
    m.update({n:(lambda n=n:n) for n in EXAMPLE_PEOPLE if n not in PEOPLE})
    return m


def prepare():
    from scripts.shared_plurality import prepare as prepare_library
    prepare_library();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published plurality example differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published module differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published contracts differ')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Meaning catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Published example differs')
    result=dict(schema='noema-shared-plurality-evidence-1',definitions=len(MEANINGS),new_primitives=0,
        membership=membership_checks(),actions=action_checks(),objects=object_checks(),coverage=coverage_checks(),
        event_assignments=[assignment_checks(a) for a in product(PEOPLE,repeat=2)],
        reciprocal=reciprocal_checks(),binding_diagnostics=binding_diagnostics(),example=values(example(),example_model(),EXAMPLE_PEOPLE))
    if result['example']!=EXPECTED:raise ValueError('Integrated plurality differs')
    paths=[LIBRARY,BASIS,EXAMPLE,SOURCE,'docs/shared-plurality-v1.md','scripts/shared_plurality.py',
        'scripts/check_shared_plurality.py','tests/test_shared_plurality.py','scripts/shared_modality.py',
        'scripts/shared_time.py','scripts/shared_reference.py','scripts/shared_readings.py',*basis()['design_sources']]
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=basis()['limitations']
    return result
