"""Independent set oracles for partial answers and correlation-preserving questions."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.shared_answers import *
from scripts.shared_reference import truth,S,C,U

EXAMPLE='examples/v016/partial-and-paired-answers-v1.noema'
PEOPLE=('a','b')


def ref(name):return dict(kind='function_ref',symbol=name)
def question(function):return dict(kind='question',function=function)
def unknown(*args):raise ValueError('Unknown answer interpretation')
def subsets(xs):return [set(x for i,x in enumerate(xs) if mask&(1<<i)) for mask in range(1<<len(xs))]


@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    for prefix,types in [('single',[I]),('pair',[I,I])]:
        for suffix in ('question','positive','negative'):
            d['declarations'].append(dict(kind='primitive',name=prefix+suffix,parameters=types,result=T))
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=I) for n in ('aki','nao')]
    return normalize_document(d)


def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def model(**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update(aki=lambda:'a',nao=lambda:'b');m.update(overrides);return m
def values(d,m):
    return [r['value'] for r in evaluate_document(d,individuals=PEOPLE,situations=('now','later'),primitives=m,max_steps=1000000)]
def args(pair=False):
    prefix='pair' if pair else 'single'
    return [question(ref(prefix+'question')),ref(prefix+'positive'),ref(prefix+'negative')]


def queries(pair=False):
    prefix='pairanswer' if pair else 'answer';a=args(pair)
    result=[call(prefix+'consistent',*a[1:]),call(prefix+'sound',*a),call(prefix+'informative',*a[1:]),
        call(prefix+'covers',*a[:2])]
    result += [call(prefix+suffix,*a,truth(closed)) for suffix in ('complete','partial') for closed in (False,True)]
    result += [call(prefix+'none',a[0])]
    points=list(product(('aki','nao'),repeat=2)) if pair else [('aki',),('nao',)]
    result += [call(prefix+'unsettled',*a[1:],*(call(n) for n in xs)) for xs in points]
    return result


def oracle(qs,positive,negative,points):
    sound=positive<=qs and not negative&qs
    covers=qs<=positive;informative=bool(positive|negative)
    return [not positive&negative,sound,informative,covers,False,sound and covers,
        sound and informative,False,not qs]+[x not in positive|negative for x in points]


@lru_cache(maxsize=2)
def information_checks(pair=False):
    points=list(product(PEOPLE,repeat=2)) if pair else list(PEOPLE);sets=subsets(points)
    d=doc(queries(pair));prefix='pair' if pair else 'single';count=0
    for qs,positive,negative in product(sets,repeat=3):
        m=model(**{prefix+n:(lambda *xs,s=s:(tuple(xs) if pair else xs[0]) in s)
            for n,s in [('question',qs),('positive',positive),('negative',negative)]})
        if values(d,m)!=oracle(qs,positive,negative,points):raise ValueError('Answer information differs')
        count+=1
    return dict(models=count,candidates=len(points),closed_flags=[False,True],checks_per_model=len(d['statements']))


@lru_cache(maxsize=1)
def projection_checks():
    names=('answerfirstquestion','answersecondquestion','answerafterfirst','answerbeforesecond')
    bodies=[];specs=[]
    for name in names:
        for fixed in ('aki','nao') if name in names[2:] else (None,):
            projection=call(name,args(True)[0],*([call(fixed)] if fixed else []))
            for candidate in ('aki','nao'):
                bodies.append(matches(projection,call(candidate)));specs.append((name,fixed,candidate))
    d=doc(bodies);points=list(product(PEOPLE,repeat=2));count=0
    for qs in subsets(points):
        expected=[];mapping={'aki':'a','nao':'b'}
        for name,fixed,candidate in specs:
            c=mapping[candidate];f=mapping.get(fixed)
            if name==names[0]:expected.append(any(x==c for x,y in qs))
            elif name==names[1]:expected.append(any(y==c for x,y in qs))
            elif name==names[2]:expected.append((f,c) in qs)
            else:expected.append((c,f) in qs)
        if values(d,model(pairquestion=lambda x,y:(x,y) in qs))!=expected:raise ValueError('Projection loses slot order')
        count+=1
    return dict(models=count,point_checks=count*len(specs),all_ordered_pairs=True)


@lru_cache(maxsize=1)
def example():
    d=deepcopy(composed())
    # Reuse the exact two definitions; no new reply-attribution primitive.
    from scripts.shared_speech import composed as speech
    d['declarations'] += [x for x in speech()['declarations'] if x['name'] in ('speechpresented','speechto')]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=I) for n in ('aki','nao')]
    equal=lambda a,b:op('equal',a,b)
    one=lam([('candidate',I)],equal(v('candidate'),call('aki')))
    both=lam([('candidate',I)],op('or',equal(v('candidate'),call('aki')),equal(v('candidate'),call('nao'))))
    empty=lam([('candidate',I)],truth(False));unary=question(both)
    pairs=lam([('first',I),('second',I)],op('and',equal(v('first'),v('second')),
        op('or',equal(v('first'),call('aki')),equal(v('first'),call('nao')))))
    onepair=lam([('first',I),('second',I)],op('and',equal(v('first'),call('aki')),equal(v('second'),call('aki'))))
    nopair=lam([('first',I),('second',I)],truth(False));pairq=question(pairs)
    incomplete=call('answercomplete',unary,one,empty,truth(True))
    d['declarations'].append(definition('replycontent',[('subject',I)],C,dict(kind='content',variable='world',body=incomplete)))
    d['declarations'].append(definition('replyform',[('subject',I)],U,dict(kind='message',force='assert',content=call('replycontent',v('subject')))))
    from scripts.shared_speech import OCCURS,PRESENTS,CONVEYS
    relation=lambda sort:lam([('arg'+chr(97+i),t) for i,t in enumerate(sort['parameters'])],truth(True))
    presentation=call('speechto',call('aki'),call('aki'),call('nao'),call('nao'),dict(kind='quote',body=ref('replyform')),
        v('world'),*(relation(sort) for sort in (OCCURS,PRESENTS,CONVEYS)))
    bodies=[call('answersound',unary,one,empty),call('answerpartial',unary,one,empty,truth(False)),incomplete,
        call('answerpartial',unary,both,empty,truth(False)),call('answercomplete',unary,both,empty,truth(False)),
        call('answercomplete',unary,both,empty,truth(True)),call('answercomplete',question(empty),empty,empty,truth(True)),
        call('answerunsettled',one,empty,call('nao')),
        call('pairanswerpartial',pairq,onepair,nopair,truth(False)),call('pairanswercomplete',pairq,pairs,nopair,truth(True)),
        matches(call('answerfirstquestion',pairq),call('aki')),matches(call('answersecondquestion',pairq),call('nao')),
        matches(pairq,call('aki'),call('nao')),matches(call('answerafterfirst',pairq,call('aki')),call('nao')),
        q('forall','world',S,presentation),q('forall','world',S,dict(kind='evaluate',content=call('replycontent',call('nao')),situation=v('world')))]
    d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)


EXAMPLE_RESULTS=[True,True,False,True,False,True,True,True,True,True,True,True,False,False,True,False]
def example_model():return dict(aki=lambda:'a',nao=lambda:'b')


def prepare():
    from scripts.shared_answers import prepare as prepare_library
    prepare_library();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published answer example differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published answers differ')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published answer basis differs')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Answer catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Published example differs')
    actual=values(example(),example_model())
    if actual!=EXAMPLE_RESULTS:raise ValueError('Integrated answers differ')
    result=dict(schema='noema-shared-answers-evidence-1',definitions=20,new_primitive_declarations=0,
        unary_information=information_checks(),paired_information=information_checks(True),projections=projection_checks(),example=actual)
    preserved='reports/shared-speech-v1.json';hashes=json.loads((ROOT/preserved).read_text(encoding='utf-8'))['source_sha256']
    for path,digest in hashes.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Prior speech evidence changed: '+path)
    paths=[LIBRARY,BASIS,EXAMPLE,'scripts/shared_answers.py','scripts/check_shared_answers.py',
        'tests/test_shared_answers.py','docs/shared-answers-v1.md',preserved,*hashes,
        'scripts/shared_modality.py','scripts/shared_reference.py','scripts/shared_time.py']
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=LIMITS;return result
