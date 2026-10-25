"""Truth-table diagnostics and Native numeric fields for both quantity examples."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_selection import *
from scripts.shared_reference import I,S,truth,lam
from scripts.shared_readings import num
from scripts.shared_plurality import seq
from scripts.check_shared_quantities import (example as quantity_example,example_model as quantity_model,
    CONSTANTS,ARITH,ref,rational)

EXAMPLE='examples/v016/native-measurement-values-v1.noema'
PEOPLE=('a','b')
STANDARD=dict(ARITH,truthindicator=lambda condition:Fraction(int(condition)))


@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    d['declarations'] += [dict(kind='primitive',name=n,parameters=p,result=r) for n,p,r in (
        ('first',[],I),('second',[],I),('property',[I],T),('unknownnumber',[],N))]
    return normalize_document(d)


def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def model(**overrides):
    def unknown(*xs):raise ValueError('Unknown numeric interpretation')
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update({k:v for k,v in STANDARD.items() if k in m});m.update(first=lambda:'a',second=lambda:'b',property=lambda x:x=='a')
    m.update(overrides);return m
def values(d,m,people=PEOPLE):
    return [r['value'] if 'value' in r else r['answers'] for r in evaluate_document(
        d,individuals=people,situations=('now','elsewhere'),primitives=m)]


@lru_cache(maxsize=1)
def selection_checks():
    numbers=(Fraction(-3),Fraction(-1,2),Fraction(0),Fraction(1,3),Fraction(1),Fraction(1000));count=0
    for condition,yes,no in product((False,True),numbers,numbers):
        body=op('equal',call('selectnumber',truth(condition),rational(yes),rational(no)),rational(yes if condition else no))
        if values(doc([body]),model())!=[True]:raise ValueError('Rational selection differs')
        count+=1
    return dict(models=count,exact_rationals=True)


@lru_cache(maxsize=1)
def indicator_checks():
    d=doc([call('indicatorvalid'),call('countselected',seq(call('first')),ref('property'),num(1))]);rows=[]
    for falsevalue,truevalue in product((-1,0,1,2),repeat=2):
        m=model(truthindicator=lambda b:Fraction(truevalue if b else falsevalue))
        expected=falsevalue==0 and truevalue==1
        actual=values(d,m)
        if actual!=[expected,expected]:raise ValueError('Both truth values were not checked')
        rows.append(dict(false=falsevalue,true=truevalue,valid=expected))
    return rows


@lru_cache(maxsize=1)
def count_checks():
    count=0
    for length in range(5):
        for names in product(('first','second'),repeat=length):
            members=seq(*(call(n) for n in names))
            for selected in (set(),{'a'},{'b'},{'a','b'}):
                expected=sum(('a' if n=='first' else 'b') in selected for n in names)
                d=doc([op('equal',call('occurrencecount',members,ref('property')),num(expected)),
                    call('countselected',members,ref('property'),num(expected))])
                if values(d,model(property=lambda x:x in selected))!=[True,len(set(names))==len(names)]:
                    raise ValueError('Occurrence count became a deduplicated individual count')
                count+=1
    return dict(models=count,max_length=4,domain_size=2)


def piecewise(subject,rows,default):
    result=default
    for name,number in reversed(rows):
        result=call('selectnumber',op('equal',subject,call(name)),rational(number),result)
    return result


@lru_cache(maxsize=1)
def example():
    d=quantity_example()
    # Topological merge, with complete equality for already shared declarations.
    merged=[];lookup={}
    for declaration in composed()['declarations']+d['declarations']:
        name=declaration['name']
        if name in lookup:
            if declaration!=lookup[name]:raise ValueError('Shared dependency changed: '+name)
        else:lookup[name]=declaration;merged.append(declaration)
    # Field definitions follow all their constants and shared operations.
    replace={'readings','volumedimension','massdimension'}
    d['declarations']=[x for x in merged if x['name'] not in replace]
    entries=[('waterone',250),('watertwo',500),('waterwhole',750),('riceone',400),('ricetwo',600),('ricewhole',1000)]
    d['declarations'].append(definition('readings',[('object',I),('context',S)],N,
        piecewise(v('object'),entries,num(0))))
    for name,axis,power in (('volumedimension','lengthaxis',3),('massdimension','massaxis',1)):
        d['declarations'].append(definition(name,[('axis',I)],N,
            call('selectnumber',op('equal',v('axis'),call(axis)),num(power),num(0))))
    d['statements'].insert(0,dict(kind='assert',body=call('indicatorvalid')))
    return normalize_document(d)


def example_model():
    m=quantity_model()
    for name in ('readings','volumedimension','massdimension'):m.pop(name)
    m['truthindicator']=STANDARD['truthindicator']
    return m


@lru_cache(maxsize=1)
def field_checks():
    d=deepcopy(example());d['statements']=[]
    expected={'waterone':250,'watertwo':500,'waterwhole':750,'riceone':400,'ricetwo':600,'ricewhole':1000}
    rows=[]
    for name,value in expected.items():
        current=deepcopy(d);current['statements']=[dict(kind='ask',body=op('equal',call('readings',call(name),call('now')),num(value)))]
        if values(current,example_model(),CONSTANTS)!=[True]:raise ValueError('Native measurement field differs')
        rows.append(dict(subject=name,value=value))
    return rows


def prepare():
    from scripts.shared_selection import prepare as prepare_library
    prepare_library();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published numeric fields differ')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published module differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published contracts differ')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Meaning catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Published example differs')
    result=dict(schema='noema-shared-selection-evidence-1',new_shared_symbols=5,reused_indicator_primitive=1,
        reused_indicator_and_count_definitions=2,new_composed_definitions=2,new_primitive_meanings=0,
        selection=selection_checks(),indicator_interpretations=indicator_checks(),counting=count_checks(),
        fields=field_checks(),example=values(example(),example_model(),CONSTANTS),
        replaced_host_functions=['readings','volumedimension','massdimension'])
    if result['example']!=[True]*7:raise ValueError('Native measured quantities differ')
    prior='reports/shared-quantities-v1.json'
    evidence=json.loads((ROOT/prior).read_text(encoding='utf-8'))['source_sha256']
    for p,digest in evidence.items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest:raise ValueError('Preserved quantity evidence changed: '+p)
    paths=[LIBRARY,BASIS,EXAMPLE,SOURCE,SOURCE_BASIS,QUANTITIES,QUANTITY_BASIS,PLURAL,PLURAL_BASIS,prior,*evidence,
        'docs/shared-selection-v1.md','scripts/shared_selection.py','scripts/check_shared_selection.py','tests/test_shared_selection.py']
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=basis()['limitations']+['The integrated quantity example still takes named objects, unit registration, measurement and partition/contents relations as explicit inputs; it is not yet a wholly visible document.']
    return result
