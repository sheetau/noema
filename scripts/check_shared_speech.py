"""Distinguish stated force, uptake and realization with exact slot binding."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_speech import *

EXAMPLE='examples/v016/requests-promises-v1.noema'
PEOPLE=('a','b')
CONSTANTS={'person':'a','activity':'a','recipient':'b','subject':'b','reason':'a','role':'b','other':'b'}


def ref(n):return dict(kind='function_ref',symbol=n)
def quote(n):return dict(kind='quote',body=ref(n))
def key(x):return json.loads(x.syntax)['symbol'] if hasattr(x,'syntax') else x
def unknown(*args):raise ValueError('Unknown interpretation')


@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed());signatures={n:([],I) for n in CONSTANTS}
    signatures.update(context=([],S),outcome=([],S),perform=([I,S],T),achieve=([I,S],T),
        occurs=(OCCURS['parameters'],T),presents=(PRESENTS['parameters'],T),conveys=(CONVEYS['parameters'],T),
        receives=(CONVEYS['parameters'],T),understands=(CONVEYS['parameters'],T),accepts=(CONVEYS['parameters'],T),
        declines=(CONVEYS['parameters'],T),targets=(TARGETS['parameters'],T),solicits=(SOLICITS['parameters'],T),
        supports=(SUPPORTS['parameters'],T),reasonshown=(REASONSHOWN['parameters'],T),undertakes=(UNDERTAKES['parameters'],T),
        claims=(AUTHORITY['parameters'],T),before=(BEFORE['parameters'],T))
    d['declarations'] += [dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in signatures.items()]
    for name,relation in [('actionform','perform'),('otheraction','perform'),('goalform','achieve')]:
        d['declarations'].append(definition(name,[('actor',I)],C,
            dict(kind='content',variable='world',body=call(relation,v('actor'),v('world')))))
    for name,force in [('questionform','ask'),('directiveform','direct'),('promiseform','assert'),('otherquestion','ask')]:
        d['declarations'].append(definition(name,[('subject',I)],U,
            dict(kind='message',force=force,content=call('actionform',v('subject')))))
    return normalize_document(d)


def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def arguments(ps,*,promise=False):
    replacements={'message':quote('promiseform' if promise else 'questionform'),'action':quote('actionform'),
        'goal':quote('goalform'),'actor':call('person' if promise else 'recipient')}
    return [replacements.get(n,ref(n) if isinstance(t,dict) and t.get('kind')=='function' else call(n)) for n,t in ps]
def query(name,*,promise=False):
    d=next(d for d in raw()['declarations'] if d['name']==name)
    return call(name,*arguments([(p['name'],p['sort']) for p in d['parameters']],promise=promise))
def values(d,m):return [r['value'] for r in evaluate_document(d,individuals=PEOPLE,situations=('now','later'),primitives=m,max_steps=1000000)]


def expected_slots(promise=False):
    message='promiseform' if promise else 'questionform';actor='a' if promise else 'b'
    received=('a','b','b',message,'now')
    return dict(occurs=('a','now'),presents=('a','a','now'),conveys=received,receives=received,understands=received,
        accepts=received,declines=received,targets=('a','b',message,actor,'actionform','now'),
        solicits=('a','a','b','actionform','now'),supports=('a','a','b','actionform','goalform','now'),
        reasonshown=('a','b','a','now'),undertakes=('a','b','a','actionform','now'),claims=('a','b','a','b','actionform','now'),
        before=('now','later'))


def model(*,promise=False,**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update({n:(lambda x=x:x) for n,x in CONSTANTS.items()});m.update(context=lambda:'now',outcome=lambda:'later')
    for name,expected in expected_slots(promise).items():m[name]=lambda *xs,expected=expected:tuple(key(x) for x in xs)==expected
    m.update(perform=lambda actor,w:actor==('a' if promise else 'b') and w=='later',achieve=unknown)
    m.update(overrides);return m


@lru_cache(maxsize=1)
def uptake_checks():
    names=['speechto','speechreceived','speechunderstood','speechaccepted','speechdeclined']
    d=doc([query(n) for n in names]);count=0
    flags=('occurs','presents','conveys','receives','understands','accepts','declines')
    for bits in product((False,True),repeat=len(flags)):
        m=model();m.update({n:(lambda *a,b=b:b) for n,b in zip(flags,bits)})
        presented=all(bits[:3]);received=presented and bits[3];understood=received and bits[4]
        if values(d,m)!=[presented,received,understood,understood and bits[5],understood and bits[6]]:
            raise ValueError('Uptake stages differ')
        count+=1
    return dict(models=count,conditions=len(flags),domain_size=2)


@lru_cache(maxsize=1)
def force_checks():
    count=0
    for promise,names,flags in [(False,['speechrequest','speechadvice','speechcommand'],
        ('occurs','presents','conveys','targets','solicits','supports','reasonshown','claims')),
        (True,['speechpromise'],('occurs','presents','conveys','targets','undertakes'))]:
        d=doc([query(n,promise=promise) for n in names])
        for bits in product((False,True),repeat=len(flags)):
            m=model(promise=promise);m.update({n:(lambda *a,b=b:b) for n,b in zip(flags,bits)})
            shared=all(bits[:4]);expected=[shared and bits[4]] if promise else [shared and bits[4],shared and bits[5] and bits[6],shared and bits[7]]
            if values(d,m)!=expected:raise ValueError('Speech profile differs')
            count+=1
    return dict(models=count,profiles=4)


@lru_cache(maxsize=1)
def realization_checks():
    count=0
    for promise,name,relation in [(False,'requestrealized','solicits'),(True,'promiserealized','undertakes')]:
        d=doc([query(name,promise=promise)])
        for committed,ordered,recipientacts,speakeracts in product((False,True),repeat=4):
            m=model(promise=promise);m[relation]=lambda *a:committed;m['before']=lambda *a:ordered
            m['perform']=lambda actor,w:w=='later' and (speakeracts if actor=='a' else recipientacts)
            if values(d,m)!=[committed and ordered and (speakeracts if promise else recipientacts)]:raise ValueError('Realization actor differs')
            count+=1
    return dict(models=count,domain_size=2,checks_actual_actor=True)


@lru_cache(maxsize=1)
def binding_diagnostics():
    # Each relation is checked against an exact tuple. Change a single expected
    # slot while holding the others fixed; no large tuple-domain enumeration.
    rows=[]
    uses=[('speechaccepted',False,('occurs','presents','conveys','receives','understands','accepts')),
        ('speechdeclined',False,('declines',)),('speechrequest',False,('targets','solicits')),
        ('speechadvice',False,('supports','reasonshown')),('speechcommand',False,('claims',)),
        ('speechpromise',True,('targets','undertakes'))]
    for name,promise,relations in uses:
        d=doc([query(name,promise=promise)]);m=model(promise=promise)
        if values(d,m)!=[True]:raise ValueError('Exact tuple baseline differs')
        for relation in relations:
            expected=expected_slots(promise)[relation]
            for slot,value in enumerate(expected):
                changed=list(expected)
                changed[slot]={'a':'b','b':'a','now':'later','questionform':'otherquestion','promiseform':'questionform',
                    'actionform':'otheraction','goalform':'actionform'}[value]
                altered=dict(m);altered[relation]=lambda *xs,changed=tuple(changed):tuple(key(x) for x in xs)==changed
                if values(d,altered)!=[False]:raise ValueError('Speech slot was not bound: '+relation)
                rows.append(dict(profile=name,relation=relation,slot=slot,result=False))
    return rows


@lru_cache(maxsize=1)
def example():
    return doc([query(n) for n in ('speechto','speechreceived','speechunderstood','speechaccepted','speechdeclined',
        'speechrequest','speechadvice','speechcommand','requestrealized')]+[query(n,promise=True) for n in ('speechpromise','promiserealized')])


def example_model():
    m=model(receives=lambda *a:False,understands=lambda *a:False,accepts=lambda *a:False,declines=lambda *a:False,
        claims=lambda *a:False,perform=lambda actor,w:actor=='b' and w=='later')
    for relation in ('conveys','targets'):
        tuples=[expected_slots(p)[relation] for p in (False,True)]
        m[relation]=lambda *xs,tuples=tuples:tuple(key(x) for x in xs) in tuples
    return m


def prepare():
    from scripts.shared_speech import prepare as prepare_library
    prepare_library();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published speech example differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published module differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published contracts differ')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Published example differs')
    result=dict(schema='noema-shared-speech-evidence-1',definitions=19,preserved_definitions=7,new_primitive_declarations=0,
        explicit_interpretive_inputs=['targets','solicits','supports','reasonshown','undertakes','claims','receives','understands','accepts','declines'],
        uptake=uptake_checks(),force=force_checks(),realization=realization_checks(),binding=binding_diagnostics(),
        example=values(example(),example_model()))
    if result['example']!=[True,False,False,False,False,True,True,False,True,True,False]:raise ValueError('Integrated speech example differs')
    paths=[LIBRARY,BASIS,EXAMPLE,SOURCE,SOURCE_BASIS,'scripts/shared_speech.py','scripts/check_shared_speech.py',
        'tests/test_shared_speech.py','docs/shared-speech-v1.md']
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=basis()['limitations'];return result
