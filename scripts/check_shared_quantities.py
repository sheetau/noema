"""Exact rational checks, explicit measurement inputs and finite partitions."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_quantities import *

EXAMPLE='examples/v016/containers-and-amounts-v1.noema'
PEOPLE=('a','b','c')
ARITH={'rationalbelow':lambda a,b:a<b,'rationaladd':lambda a,b:a+b,
       'rationalnegate':lambda a:-a,'rationalmultiply':lambda a,b:a*b}


def ref(name):return dict(kind='function_ref',symbol=name)
def rational(value):
    value=Fraction(value);return dict(kind='number',numerator=value.numerator,denominator=value.denominator)
def unknown(*args):raise ValueError('Unknown interpretation')
def declare(signatures):return [dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in signatures.items()]


@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    signatures={n:([],I) for n in ('leftsubject','rightsubject','leftkind','rightkind','leftunit','rightunit','whole')}
    signatures.update({n:([],N) for n in ('leftscale','rightscale','left','right')})
    signatures.update({n:([I],N) for n in ('leftdim','rightdim')})
    signatures.update(now=([],S),registry=(REGISTER['parameters'],T),measurement=(MEASURE['parameters'],T),
        readings=(READINGS['parameters'],N),assignment=([I],I),partof=(RELATION['parameters'],T),
        disjoint=(RELATION['parameters'],T),complete=(COVERAGE['parameters'],T),contains=(RELATION['parameters'],T))
    d['declarations']+=declare(signatures);return normalize_document(d)


def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def values(d,m,people=PEOPLE):
    return [r['value'] if 'value' in r else r['answers'] for r in evaluate_document(
        d,individuals=people,situations=('now','elsewhere'),primitives=m)]
def model(**overrides):
    readings={'a':Fraction(2),'b':Fraction(3),'c':Fraction(5)}
    scales={'a':Fraction(1),'b':Fraction(2)}
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update(ARITH)
    m.update(leftsubject=lambda:'a',rightsubject=lambda:'b',whole=lambda:'c',leftkind=lambda:'a',rightkind=lambda:'a',
        leftunit=lambda:'a',rightunit=lambda:'b',leftscale=lambda:Fraction(1),rightscale=lambda:Fraction(2),
        left=lambda:Fraction(2),right=lambda:Fraction(3,2),now=lambda:'now',
        leftdim=lambda a:Fraction(a=='a'),rightdim=lambda a:Fraction(a=='a'),
        registry=lambda u,k,d,s,w:u in scales and k=='a' and s==scales[u] and w=='now' and all(d(a)==int(a=='a') for a in PEOPLE),
        measurement=lambda o,k,u,n,w:k=='a' and u in scales and n*scales[u]==readings[o] and w=='now',
        readings=lambda o,w:readings[o],assignment=lambda c:c,
        partof=lambda p,o,w:p in ('a','b') and o=='c' and w=='now',
        disjoint=lambda p,q,w:(p,q) in (('a','b'),('b','a')) and w=='now',
        complete=lambda ps,o,w:set(ps.items)=={'a','b'} and o=='c' and w=='now',
        contains=lambda p,c,w:p==c and c in ('a','b') and w=='now')
    m.update(overrides);return m
def comparison_args():
    return [call(n) for n in ('leftsubject','rightsubject','leftkind','rightkind','leftunit','rightunit')]+[
        ref('leftdim'),ref('rightdim')]+[call(n) for n in ('leftscale','rightscale','left','right','now')]+[ref('registry'),ref('measurement')]
def unit_args():return [call('leftkind'),call('leftunit'),ref('leftdim'),call('leftscale')]
def evidence_args():return [call('now'),ref('registry'),ref('measurement')]
def amount_call():return call('amountat',call('leftsubject'),*unit_args(),call('left'),*evidence_args())
def parts():return seq(call('leftsubject'),call('rightsubject'))
def sum_args():
    return [call('whole'),*unit_args(),ref('readings'),*evidence_args(),ref('partof'),ref('disjoint'),ref('complete')]
def sum_call(ps=None):return call('amountsum',parts() if ps is None else ps,*sum_args())
def partition_call(ps=None):
    return call('partitionof',parts() if ps is None else ps,call('whole'),call('now'),ref('partof'),ref('disjoint'),ref('complete'))
def counted_call(ps=None,count=2):
    return call('countedcontainers',parts() if ps is None else ps,num(count),ref('assignment'),call('now'),ref('contains'))
def container_call():return call('containeramount',parts(),num(2),ref('assignment'),*sum_args(),ref('contains'))


@lru_cache(maxsize=1)
def conversion_checks():
    compat=[call('leftkind'),call('rightkind'),ref('leftdim'),ref('rightdim'),call('leftscale'),call('rightscale')]
    d=doc([call('quantityequal',*compat,call('left'),call('right'))]);count=0
    numbers=(Fraction(0),Fraction(1,2),Fraction(1),Fraction(2))
    for kindmatch,dimmatch,ls,rs,left,right in product((False,True),(False,True),(-1,0,1,2),(-1,0,1,2),numbers,numbers):
        m=model(rightkind=lambda:'a' if kindmatch else 'b',rightdim=lambda a:Fraction(a==('a' if dimmatch else 'b')),
            leftscale=lambda:Fraction(ls),rightscale=lambda:Fraction(rs),left=lambda:left,right=lambda:right)
        expected=kindmatch and dimmatch and ls>0 and rs>0 and ls*left==rs*right
        if values(d,m)!=[expected]:raise ValueError('Quantity kind, dimension, positive scale or rational conversion differs')
        count+=1
    return dict(models=count,exact_rationals=True)


@lru_cache(maxsize=1)
def measurement_checks():
    d=doc([amount_call()]);count=0
    for registered,measured,scale,value in product((False,True),(False,True),(-1,0,1,2),(-1,0,1)):
        m=model(registry=lambda *xs:registered,measurement=lambda *xs:measured,
            leftscale=lambda:Fraction(scale),left=lambda:Fraction(value))
        expected=registered and measured and scale>0 and value>=0
        if values(d,m)!=[expected]:raise ValueError('Missing measurement or invalid magnitude became true')
        count+=1
    return dict(models=count)


@lru_cache(maxsize=1)
def partition_checks():
    d=doc([partition_call(),sum_call(),counted_call(),container_call()]);count=0
    edges=[('a','c'),('b','c')]
    for mask,apart,covered,contained,balanced in product(range(4),(False,True),(False,True),(False,True),(False,True)):
        included={p for i,p in enumerate(edges) if mask&(1<<i)}
        amounts={'a':Fraction(2),'b':Fraction(3),'c':Fraction(5 if balanced else 6)}
        m=model(partof=lambda p,o,w:(p,o) in included,disjoint=lambda *xs:apart,complete=lambda *xs:covered,
            contains=lambda *xs:contained,readings=lambda o,w:amounts[o],
            measurement=lambda o,k,u,n,w:n==amounts[o] and k=='a' and u=='a' and w=='now')
        partition=mask==3 and apart and covered
        expected=[partition,partition and balanced,contained,contained and partition and balanced]
        if values(d,m)!=expected:raise ValueError('Count, coverage, overlap or numerical sum collapsed')
        count+=1
    return dict(models=count,domain_size=3)


@lru_cache(maxsize=1)
def binding_diagnostics():
    # All subject/kind/unit/context/scale witnesses fixed before varying one slot.
    d=doc([amount_call()]);rows=[]
    unit=('a','a',(1,0,0),Fraction(1),'now')
    measured=('a','a','a',Fraction(2),'now')
    alternatives={'registry':('b','b',(0,1,0),Fraction(2),'elsewhere'),
                  'measurement':('b','b','b',Fraction(3),'elsewhere')}
    for name,wanted in (('registry',unit),('measurement',measured)):
        for slot in range(-1,len(wanted)):
            target=list(wanted)
            if slot>=0:target[slot]=alternatives[name][slot]
            def registered(u,k,dim,s,w,target=tuple(target)):
                return (u,k,tuple(dim(a) for a in PEOPLE),s,w)==target
            callback=registered if name=='registry' else lambda *xs,target=tuple(target):xs==target
            actual=values(d,model(**{name:callback}))
            if actual!=[slot<0]:raise ValueError('Measurement/unit tuple binding differs')
            rows.append(dict(relation=name,changed_slot=None if slot<0 else slot,value=actual[0]))
    return rows


@lru_cache(maxsize=1)
def partition_bindings():
    d=doc([partition_call()]);rows=[]
    required={'partof':{('a','c','now'),('b','c','now')},
              'disjoint':{('a','b','now'),('b','a','now')},
              'complete':{(('a','b'),'c','now')}}
    chosen={'partof':('a','c','now'),'disjoint':('a','b','now'),'complete':(('a','b'),'c','now')}
    for name,wanted in chosen.items():
        for slot in range(-1,3):
            allowed=set(required[name]);target=list(wanted)
            if slot>=0:
                target[slot]='elsewhere' if slot==2 else ('a',) if name=='complete' and slot==0 else 'b' if wanted[slot]!='b' else 'a'
                allowed.remove(wanted);allowed.add(tuple(target))
            callback=(lambda ps,o,w,allowed=allowed:(tuple(ps.items),o,w) in allowed) if name=='complete' else (
                lambda *xs,allowed=allowed:xs in allowed)
            actual=values(d,model(**{name:callback}))
            if actual!=[slot<0]:raise ValueError('Partition binding differs')
            rows.append(dict(relation=name,changed_slot=None if slot<0 else slot,value=actual[0]))
    return rows


CONSTANTS=('cupone','cuptwo','waterone','watertwo','waterwhole','bagone','bagtwo','riceone','ricetwo','ricewhole',
    'volumekind','masskind','millilitre','litre','gram','kilogram','lengthaxis','massaxis')
def example():
    d=deepcopy(composed())
    sig={n:([],I) for n in CONSTANTS}
    sig.update(now=([],S),volumedimension=([I],N),massdimension=([I],N),registry=(REGISTER['parameters'],T),
        measurement=(MEASURE['parameters'],T),readings=(READINGS['parameters'],N),assignment=([I],I),
        partof=(RELATION['parameters'],T),disjoint=(RELATION['parameters'],T),complete=(COVERAGE['parameters'],T),contains=(RELATION['parameters'],T))
    d['declarations']+=declare(sig);bodies=[]
    for containers,whole,kind,dimension,unit,otherunit,total in (
        (('cupone','cuptwo'),'waterwhole','volumekind','volumedimension','millilitre','litre',Fraction(750)),
        (('bagone','bagtwo'),'ricewhole','masskind','massdimension','gram','kilogram',Fraction(1000))):
        packed=seq(*(call(n) for n in containers))
        bodies.append(call('countedcontainers',packed,num(2),ref('assignment'),call('now'),ref('contains')))
        bodies.append(call('containeramount',packed,num(2),ref('assignment'),call(whole),call(kind),call(unit),ref(dimension),num(1),
            ref('readings'),*evidence_args(),ref('partof'),ref('disjoint'),ref('complete'),ref('contains')))
        bodies.append(call('sameamount',call(whole),call(whole),call(kind),call(kind),call(unit),call(otherunit),
            ref(dimension),ref(dimension),num(1),num(1000),rational(total),rational(total/1000),*evidence_args()))
    d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)


def example_model():
    numbers=dict(waterone=Fraction(250),watertwo=Fraction(500),waterwhole=Fraction(750),
        riceone=Fraction(400),ricetwo=Fraction(600),ricewhole=Fraction(1000))
    assignments=dict(cupone='waterone',cuptwo='watertwo',bagone='riceone',bagtwo='ricetwo')
    partitions=dict(waterwhole={'waterone','watertwo'},ricewhole={'riceone','ricetwo'})
    units=dict(millilitre=('volumekind',1),litre=('volumekind',1000),gram=('masskind',1),kilogram=('masskind',1000))
    dimension=lambda kind,a:Fraction(3 if kind=='volumekind' and a=='lengthaxis' else 1 if kind=='masskind' and a=='massaxis' else 0)
    def registered(u,k,d,s,w):
        if u not in units:raise ValueError('Unknown unit')
        return (k,s)==units[u] and w=='now' and all(d(a)==dimension(k,a) for a in CONSTANTS)
    def measured(o,k,u,n,w):
        if o not in numbers or u not in units:raise ValueError('Unknown measurement input')
        return k==('volumekind' if o.startswith('water') else 'masskind') and units[u][0]==k and n*units[u][1]==numbers[o] and w=='now'
    m=dict(ARITH)
    m.update({n:(lambda n=n:n) for n in CONSTANTS})
    m.update(now=lambda:'now',volumedimension=lambda a:dimension('volumekind',a),massdimension=lambda a:dimension('masskind',a),
        registry=registered,measurement=measured,readings=lambda o,w:numbers[o],assignment=lambda c:assignments[c],
        partof=lambda p,w,c:w in partitions and p in partitions[w] and c=='now',
        disjoint=lambda p,q,c:p!=q and any({p,q}<=ps for ps in partitions.values()) and c=='now',
        complete=lambda ps,w,c:w in partitions and set(ps.items)==partitions[w] and c=='now',
        contains=lambda p,c,w:assignments.get(c)==p and w=='now')
    return m


def prepare():
    from scripts.shared_quantities import prepare as prepare_library
    prepare_library();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published amount example differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published module differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published contracts differ')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Meaning catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Published example differs')
    result=dict(schema='noema-shared-quantities-evidence-1',reused_arithmetic_primitives=4,reused_quantity_definitions=13,
        reused_plurality_definitions=3,new_composed_definitions=10,new_primitive_meanings=0,
        conversion=conversion_checks(),measurement=measurement_checks(),partition=partition_checks(),
        measurement_bindings=binding_diagnostics(),partition_bindings=partition_bindings(),example=values(example(),example_model(),CONSTANTS))
    if result['example']!=[True]*6:raise ValueError('Integrated quantities differ')
    paths=[LIBRARY,BASIS,EXAMPLE,SOURCE,SOURCE_BASIS,PLURAL,PLURAL_BASIS,'docs/shared-quantities-v1.md',
        'scripts/shared_quantities.py','scripts/check_shared_quantities.py','tests/test_shared_quantities.py',
        'scripts/shared_modality.py','scripts/shared_time.py','scripts/shared_reference.py','scripts/shared_readings.py',
        'scripts/shared_plurality.py','docs/quantities-v1.md']
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=basis()['limitations']
    return result
