"""Independent finite specifications for generality and degree distinctions."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_generality import *

EXAMPLE='examples/v016/generic-and-degree-readings-v1.noema'
PEOPLE=('a','b');THREE=('a','b','c')


def ref(n):return dict(kind='function_ref',symbol=n)
def unknown(*args):raise ValueError('Unknown interpretation')
def subsets(xs):return [set(x for i,x in enumerate(xs) if mask&(1<<i)) for mask in range(1<<len(xs))]


@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    signatures={n:([I],T) for n in ('cases','secondcases','response','scale','positive','negative','criterion','near')}
    signatures.update(preferred=([I,I],T),less=([I,I],T),assignment=([I],I))
    signatures.update({n:([],I) for n in ('alice','bob','charlie','low','middle','high')})
    signatures.update({n:([S],T) for n in ('situations','goal','othergoal','condition')})
    d['declarations'] += [dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in signatures.items()]
    return normalize_document(d)


def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def model(**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update(alice=lambda:'a',bob=lambda:'b',charlie=lambda:'c',low=lambda:'a',middle=lambda:'b',high=lambda:'c')
    m.update(overrides);return m
def values(d,m,people=PEOPLE):
    return [r['value'] for r in evaluate_document(d,individuals=people,situations=('now','later'),primitives=m,max_steps=1000000)]
def generic(name='casegeneric',cases='cases'):return call(name,ref(cases),ref('preferred'),ref('response'))
def scale_args():return [ref('scale'),ref('less')]
def degree(name,subject='alice'):return call(name,call(subject),ref('assignment'),*scale_args(),ref('positive'),ref('negative'))
def compare(name,left='alice',right='bob'):return call(name,call(left),call(right),ref('assignment'),*scale_args())


def normal_spec(cases,edges,response):
    normal={x for x in cases if not any((y,x) in edges for y in cases)}
    ordered=not any((x,x) in edges for x in cases) and all((x,z) in edges
        for x,y,z in product(cases,repeat=3) if (x,y) in edges and (y,z) in edges)
    smooth=all(x in normal or any((y,x) in edges for y in normal) for x in cases)
    return normal,ordered and smooth,bool(normal) and ordered and smooth and normal<=response


@lru_cache(maxsize=1)
def generic_checks():
    d=doc([call('normalcase',call('alice'),ref('cases'),ref('preferred')),
        call('normalorder',ref('cases'),ref('preferred')),generic(),
        call('caseuniversal',ref('cases'),ref('response')),call('caseexception',call('alice'),ref('cases'),ref('response'))])
    count=0
    for cases,edges,response in product(subsets(PEOPLE),subsets(list(product(PEOPLE,repeat=2))),subsets(PEOPLE)):
        normal,ordered,general=normal_spec(cases,edges,response)
        m=model(cases=lambda x:x in cases,preferred=lambda x,y:(x,y) in edges,response=lambda x:x in response)
        expected=['a' in normal,ordered,general,cases<=response,'a' in cases-response]
        if values(d,m)!=expected:raise ValueError('Normal-case specification differs')
        count+=1
    return dict(models=count,domain_size=2,checks_per_model=5)


@lru_cache(maxsize=1)
def kind_checks():
    d=doc([call('kindwisegeneric',ref('cases'),ref('secondcases'),ref('preferred'),ref('response'))]);count=0
    for first,second,edges,response in product(subsets(PEOPLE),subsets(PEOPLE),subsets(list(product(PEOPLE,repeat=2))),subsets(PEOPLE)):
        expected=normal_spec(first,edges,response)[2] and normal_spec(second,edges,response)[2]
        m=model(cases=lambda x:x in first,secondcases=lambda x:x in second,
            preferred=lambda x,y:(x,y) in edges,response=lambda x:x in response)
        if values(d,m)!=[expected]:raise ValueError('Kind-local generalization differs')
        count+=1
    return dict(models=count,domain_size=2)


def order_spec(scale,edges):
    return bool(scale) and not any((x,x) in edges for x in scale) and all(
        (x,y) in edges or (y,x) in edges for x,y in product(scale,repeat=2) if x!=y) and all(
        (x,z) in edges for x,y,z in product(scale,repeat=3) if (x,y) in edges and (y,z) in edges)


@lru_cache(maxsize=1)
def order_checks():
    d=doc([call('scaleordered',*scale_args()),call('boundedscale',*scale_args(),call('low'),call('high'))])
    count=accepted=bounded=0
    for edges in subsets(list(product(THREE,repeat=2))):
        ordered=order_spec(set(THREE),edges)
        end=ordered and all(x=='a' or ('a',x) in edges for x in THREE) and all(x=='c' or (x,'c') in edges for x in THREE)
        m=model(scale=lambda x:True,less=lambda x,y:(x,y) in edges)
        if values(d,m,THREE)!=[ordered,end]:raise ValueError('Qualitative order differs')
        count+=1;accepted+=ordered;bounded+=end
    return dict(models=count,domain_size=3,accepted=accepted,bounded_accepted=bounded)


def criterion_spec(scale,edges,criterion,up=True):
    return criterion<=scale and all(y in criterion for x in criterion for y in scale
        if ((x,y) if up else (y,x)) in edges)


@lru_cache(maxsize=1)
def criterion_checks():
    d=doc([call('uppercriterion',*scale_args(),ref('criterion')),call('lowercriterion',*scale_args(),ref('criterion'))]);count=0
    edges={('a','b'),('a','c'),('b','c')}
    for scale,criterion in product(subsets(THREE),repeat=2):
        m=model(scale=lambda x:x in scale,less=lambda x,y:(x,y) in edges,criterion=lambda x:x in criterion)
        if values(d,m,THREE)!=[criterion_spec(scale,edges,criterion),criterion_spec(scale,edges,criterion,False)]:
            raise ValueError('Criterion closure differs')
        count+=1
    return dict(models=count,domain_size=3)


@lru_cache(maxsize=1)
def standard_checks():
    bodies=[call('standardsvalid',*scale_args(),ref('positive'),ref('negative'))]
    bodies += [degree(name,subject) for subject in ('alice','bob','charlie')
        for name in ('degreepositive','degreenegative','degreeborderline')]
    d=doc(bodies);count=0;edges={('a','b'),('a','c'),('b','c')}
    for positive,negative in product(subsets(THREE),repeat=2):
        valid=criterion_spec(set(THREE),edges,positive) and criterion_spec(set(THREE),edges,negative,False) and not positive&negative
        expected=[valid]+[valid and result for x in THREE for result in (x in positive,x in negative,x not in positive|negative)]
        m=model(scale=lambda x:True,less=lambda x,y:(x,y) in edges,assignment=lambda x:x,
            positive=lambda x:x in positive,negative=lambda x:x in negative)
        if values(d,m,THREE)!=expected:raise ValueError('Degree classification differs')
        count+=1
    return dict(models=count,domain_size=3,checks_per_model=10)


@lru_cache(maxsize=1)
def comparison_checks():
    d=doc([compare(n) for n in ('degreemore','degreeequal','degreenotless')]+[
        call('degreeenough',call('alice'),ref('assignment'),*scale_args(),ref('criterion'))]);count=0
    for left,right,threshold in product(THREE,THREE,range(4)):
        criterion=set(THREE[threshold:]);m=model(scale=lambda x:True,less=lambda x,y:x<y,
            assignment=lambda x:left if x=='a' else right,criterion=lambda x:x in criterion)
        if values(d,m,THREE)!=[left>right,left==right,left>=right,left in criterion]:raise ValueError('Comparative or purpose differs')
        count+=1
    return dict(models=count,domain_size=3)


@lru_cache(maxsize=1)
def modal_checks():
    d=doc([call('modaldegree',ref('situations'),ref('goal'),ref('scale'),call('middle'),call('low'),call('high'))])
    count=0
    for candidates,goals,assigned in product(subsets(('now','later')),subsets(('now','later')),THREE):
        expected=bool(candidates) and ((assigned=='a')==(not bool(candidates&goals))) and ((assigned=='c')==(candidates<=goals))
        m=model(situations=lambda w:w in candidates,goal=lambda w:w in goals,scale=lambda x:True,middle=lambda:assigned)
        if values(d,m,THREE)!=[expected]:raise ValueError('Preserved modal endpoints differ')
        count+=1
    return dict(models=count,domain_size=3,situations=2)


@lru_cache(maxsize=1)
def modal_composition_checks():
    from scripts import check_graded_modality as old
    mapping=SOURCES[1]['names'];d=renamed(old.document(),mapping)
    shared={x['name']:x for x in composed()['declarations']}
    d['declarations']=[deepcopy(shared[x['name']]) if x['name'] in shared else x for x in d['declarations']]
    rows=[]
    for name in old.VARIANTS:
        data=old.interpretation(name);actual=old.evaluate(old.model(data),doc=d)
        if actual!=old.oracle(data):raise ValueError('Shared modal composition differs: '+name)
        rows.append(dict(case=name,result=actual))
    return rows


@lru_cache(maxsize=1)
def example():
    # a is a normal flying bird case; b is a less normal nonflying case.
    # a/b/c also name three subject slots with low/middle/high assigned heights;
    # equality of their fixture codes is not an equation between roles.
    return doc([generic(),call('caseuniversal',ref('cases'),ref('response')),
        call('caseexception',call('bob'),ref('cases'),ref('response')),
        degree('degreepositive','bob'),degree('degreenegative','bob'),degree('degreeborderline','bob'),
        compare('degreemore','bob','alice'),call('degreeenough',call('bob'),ref('assignment'),*scale_args(),ref('criterion')),
        degree('degreepositive','charlie'),compare('degreeequal','alice','alice')])


def example_model():
    return model(cases=lambda x:x in PEOPLE,preferred=lambda x,y:(x,y)==('a','b'),response=lambda x:x=='a',
        scale=lambda x:x in THREE,less=lambda x,y:x<y,assignment=lambda x:x,
        positive=lambda x:x=='c',negative=lambda x:x=='a',criterion=lambda x:x in ('b','c'))


def prepare():
    from scripts.shared_generality import prepare as prepare_library
    prepare_library();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published readings differ')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published module differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published basis differs')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Published readings differ')
    result=dict(schema='noema-shared-generality-evidence-1',definitions=23,preserved_definitions=10,new_primitive_meanings=0,
        generic=generic_checks(),kindwise=kind_checks(),order=order_checks(),criteria=criterion_checks(),
        standards=standard_checks(),comparisons=comparison_checks(),modal=modal_checks(),modal_composition=modal_composition_checks(),
        example=values(example(),example_model(),THREE))
    if result['example']!=[True,False,True,False,False,True,True,True,True,True]:raise ValueError('Integrated readings differ')
    paths=[LIBRARY,BASIS,EXAMPLE,'scripts/shared_generality.py','scripts/check_shared_generality.py',
        'tests/test_shared_generality.py','docs/shared-generality-v1.md','scripts/check_graded_modality.py']
    for source in SOURCES:paths.extend((source['document'],source['basis']))
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=basis()['limitations'];return result
