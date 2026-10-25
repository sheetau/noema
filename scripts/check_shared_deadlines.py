"""Finite temporal specifications independent of the Native deadline bodies."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_deadlines import *
from scripts.shared_norms import RECOGNIZED,APPLICABLE,SUPPORTS
from scripts.shared_speech import OCCURS,PRESENTS,CONVEYS,TARGETS,UNDERTAKES

EXAMPLE='examples/v016/late-fulfillment-and-release-v1.noema'
PEOPLE=('a','b');TIMES=('start','middle','deadline','after')
CONSTANTS=dict(source='a',person='b',role='a',performance='b',authority='a',reason='b',activity='a',recipient='a',subject='b')


def ref(n):return dict(kind='function_ref',symbol=n)
def quote(body):return dict(kind='quote',body=body)
def unknown(*xs):raise ValueError('Unknown deadline interpretation')
def subsets(xs):return [set(x for i,x in enumerate(xs) if mask&(1<<i)) for mask in range(1<<len(xs))]
def describe(x):
    if not hasattr(x,'syntax'):return x
    d=json.loads(x.syntax)
    if d['kind']=='function_ref':return ('function',d['symbol'])
    if d['kind']=='apply' and d['function'].get('symbol')=='deadlineclause':return ('deadline',*(a['symbol'] for a in d['arguments']))
    return x.syntax


@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed());sig={n:([],I) for n in CONSTANTS}
    sig.update({n:([],S) for n in ('issued','due','assessment','releasepoint')})
    sig.update(history=([S],T),order=([S,S],T),perform=([I,S],T))
    sig.update({n:(sort['parameters'],T) for n,sort in [('recognized',RECOGNIZED),('applicable',APPLICABLE),('supports',SUPPORTS),
        ('authorized',AUTH),('releases',RELEASE),('occurs',OCCURS),('presents',PRESENTS),('conveys',CONVEYS),('targets',TARGETS),('undertakes',UNDERTAKES)]})
    d['declarations'] += [dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in sig.items()]
    for name in ('actform','otheractform'):
        d['declarations'].append(definition(name,[('actor',I)],C,dict(kind='content',variable='world',body=call('perform',v('actor'),v('world')))))
    d['declarations'].append(definition('promiseform',[('subject',I)],'message',dict(kind='message',force='assert',content=call('actform',v('subject')))))
    return normalize_document(d)


def arguments(parameters,**overrides):
    replacements=dict(actor=call('person'),operation=ref('actform'),action=quote(ref('actform')),message=quote(ref('promiseform')),
        performancedescription=quote(call('performance')),historydescription=quote(ref('history')),orderdescription=quote(ref('order')),
        issueddescription=quote(call('issued')),duedescription=quote(call('due')),context=call('issued'),point=call('releasepoint'),
        required=call('groundedrule',ref('recognized'),ref('applicable'),ref('supports')),complete=truth(True))
    replacements.update(overrides)
    return [replacements.get(n,ref(n) if isinstance(t,dict) and t.get('kind')=='function' else call(n)) for n,t in parameters]
def query(name,**overrides):
    d=next(d for d in raw()['declarations'] if d['name']==name)
    return call(name,*arguments([(p['name'],p['sort']) for p in d['parameters']],**overrides))
def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def values(d,m):return [r['value'] for r in evaluate_document(d,individuals=PEOPLE,situations=TIMES,primitives=m,max_steps=2000000)]
def expected_slots():
    description=('deadline','actform','history','order','issued','due','performance')
    common=('a','b','a','b',description,'start','middle')
    return dict(recognized=('a','a','start'),applicable=('a','b','a','start'),
        supports=('a','b','a','b','a','b',description,True,'start'),authorized=('a',*common),releases=('a','b',*common),
        occurs=('a','start'),presents=('b','a','start'),conveys=('a','a','b',('function','promiseform'),'start'),
        targets=('a','b',('function','promiseform'),'b',('function','actform'),'start'),
        undertakes=('b','a','a',('function','actform'),'start'))
def model(performed=(),released=(),assessment='after',**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update({n:(lambda value=value:value) for n,value in CONSTANTS.items()})
    m.update(issued=lambda:'start',due=lambda:'deadline',assessment=lambda:assessment,releasepoint=lambda:'middle',
        history=lambda p:p in TIMES,order=lambda a,b:TIMES.index(a)<TIMES.index(b),perform=lambda actor,point:actor=='b' and point in performed)
    for n,wanted in expected_slots().items():
        if n=='authorized':m[n]=lambda *xs,wanted=wanted:tuple(describe(x) for x in xs[:-1])==wanted[:-1] and xs[-1] in TIMES
        elif n=='releases':m[n]=lambda *xs,wanted=wanted:tuple(describe(x) for x in xs[:-1])==wanted[:-1] and xs[-1] in released
        else:m[n]=lambda *xs,wanted=wanted:tuple(describe(x) for x in xs)==wanted
    m.update(overrides);return m


def status_queries():
    names=('deadlinerequired','deadlinefulfilled','deadlinereleased','deadlinepending','deadlinebreached','deadlinelate')
    return [query(n) for n in names]+[query(n,complete=truth(False)) for n in names[3:]]+[query('deadlineachieved')]
def oracle(performed,released,assessment):
    index=TIMES.index(assessment);positions={TIMES.index(x) for x in performed};releases={TIMES.index(x) for x in released}
    attained=bool(positions & set(range(1,min(2,index)+1)));timely=bool(positions & {1,2})
    freed=any(x<=index for x in releases);timelyfree=bool(releases & {0,1,2})
    pending=index<=2 and not attained and not freed
    breached=index>2 and not timely and not timelyfree
    late=not timely and bool(positions & set(range(3,index+1)))
    return [True,attained,freed,pending,breached,late,False,False,False,attained]


@lru_cache(maxsize=1)
def temporal_checks():
    d=doc(status_queries());count=0
    for performed,released,assessment in product(subsets(TIMES),subsets(TIMES),TIMES):
        actual=values(d,model(performed,released,assessment))
        if actual!=oracle(performed,released,assessment):raise ValueError('Temporal deadline specification differs')
        count+=1
    return dict(models=count,people=2,time_points=4,checks_per_model=10,complete_flags=[False,True])


@lru_cache(maxsize=1)
def binding_diagnostics():
    rows=[]
    for name,wanted in expected_slots().items():
        if name in ('recognized','applicable','supports'):
            # Fix the norm and reason witnesses. A different supported reason
            # may legitimately satisfy the existential groundedrule.
            body=call('normwitness',call('authority'),call('reason'),call('source'),call('person'),call('role'),
                call('performance'),query('deadlinedescription'),truth(True),call('issued'),ref('recognized'),ref('applicable'),ref('supports'))
        else:body=query('deadlinefreedat' if name in ('authorized','releases') else 'promisedeadline')
        d=doc([body])
        if values(d,model(released={'middle'}))!=[True]:raise ValueError('Original grounded tuple fails: '+name)
        for slot,item in enumerate(wanted):
            if isinstance(item,bool):other=not item
            elif isinstance(item,tuple):
                other=list(item);other[1]='otheractform' if item[0]=='deadline' or item[1]=='actform' else 'actform';other=tuple(other)
            elif item in PEOPLE:other='b' if item=='a' else 'a'
            else:other='after' if item!='after' else 'start'
            changed=list(wanted);changed[slot]=other
            m=model(released={'middle'},**{name:lambda *xs,changed=tuple(changed):tuple(describe(x) for x in xs)==changed})
            if values(d,m)!=[False]:raise ValueError('Misbound tuple accepted: '+name)
            rows.append(dict(relation=name,slot=slot,result=False))
    return rows


@lru_cache(maxsize=1)
def frame_checks():
    normal=lambda a,b:TIMES.index(a)<TIMES.index(b)
    variants=[('ordinary',{},True),('reflexive',dict(order=lambda a,b:normal(a,b) or a==b),False),
        ('incompleteorder',dict(order=lambda a,b:(a,b)==('start','deadline')),False),
        ('cycle',dict(order=lambda a,b:normal(a,b) or (a,b)==('after','start')),False),
        ('missingorigin',dict(history=lambda p:p!='start'),False),('missingdeadline',dict(history=lambda p:p!='deadline'),False),
        ('missingassessment',dict(history=lambda p:p!='after'),False),('coincidentdeadline',dict(due=lambda:'start'),False)]
    d=doc([query('deadlinevalid')]);rows=[]
    for name,changes,expected in variants:
        actual=values(d,model(**changes))
        if actual!=[expected]:raise ValueError('Invalid deadline frame accepted')
        rows.append(dict(case=name,result=expected))
    return rows


def matching(parameters,expected):
    ps=[('arg'+chr(97+i),t) for i,t in enumerate(parameters)]
    return lam(ps,allof(*(eq(v(n),e) for (n,t),e in zip(ps,expected))))


@lru_cache(maxsize=1)
def example():
    # The same late realization and later release are assessed before, at and
    # after the deadline. All interpretation relations are Native definitions.
    d=deepcopy(composed())
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=t) for n,t in
        [('source',I),('person',I),('role',I),('performance',I),('authority',I),('reason',I),('activity',I),('recipient',I),('subject',I),
         ('issued',S),('releasepoint',S),('due',S),('assessment',S)]]
    time_names=('issued','releasepoint','due','assessment')
    history=allof(truth(True),op('or',eq(v('point'),call('issued')),op('or',eq(v('point'),call('releasepoint')),
        op('or',eq(v('point'),call('due')),eq(v('point'),call('assessment'))))))
    edges=[op('and',eq(v('first'),call(a)),eq(v('second'),call(b))) for i,a in enumerate(time_names) for b in time_names[i+1:]]
    order=edges[-1]
    for edge in reversed(edges[:-1]):order=op('or',edge,order)
    d['declarations'] += [definition('history',[('point',S)],T,history),definition('order',[('first',S),('second',S)],T,order),
        definition('actform',[('actor',I)],C,dict(kind='content',variable='world',body=op('and',eq(v('actor'),call('person')),eq(v('world'),call('assessment'))))),
        definition('promiseform',[('subject',I)],'message',dict(kind='message',force='assert',content=call('actform',v('subject'))))]
    desc=query('deadlinedescription');action=quote(ref('actform'));message=quote(ref('promiseform'))
    common=[call(n) for n in ('source','person','role','performance')]+[desc,call('issued')]
    specifications={
        'recognized':(RECOGNIZED,[call('authority'),call('source'),call('issued')]),
        'applicable':(APPLICABLE,[call('authority'),call('person'),call('role'),call('issued')]),
        'supports':(SUPPORTS,[call('authority'),call('reason'),*common[:4],desc,truth(True),call('issued')]),
        'authorized':(AUTH,[call('authority'),*common,call('assessment')]),
        'releases':(RELEASE,[call('authority'),call('reason'),*common,call('assessment')]),
        'occurs':(OCCURS,[call('activity'),call('issued')]),
        'presents':(PRESENTS,[call('person'),call('activity'),call('issued')]),
        'conveys':(CONVEYS,[call('activity'),call('recipient'),call('subject'),message,call('issued')]),
        'targets':(TARGETS,[call('activity'),call('subject'),message,call('person'),action,call('issued')]),
        'undertakes':(UNDERTAKES,[call('person'),call('recipient'),call('activity'),action,call('issued')])}
    for name,(sort,wanted) in specifications.items():
        function=matching(sort['parameters'],wanted)
        d['declarations'].append(definition(name,[(p['name'],p['sort']) for p in function['parameters']],T,function['body']))
    bodies=[query('promisedeadline'),query('deadlinepending',assessment=call('releasepoint')),
        query('deadlinebreached',assessment=call('releasepoint')),query('deadlinepending',assessment=call('due')),
        query('deadlinefulfilled'),query('deadlinereleased'),query('deadlinebreached'),query('deadlinelate'),
        query('deadlinebreached',complete=truth(False)),
        occurred(dict(kind='disquote',description=action),call('person'),call('assessment')),
        dict(kind='evaluate',content=apply(dict(kind='disquote',description=desc),call('person'),call('performance')),situation=call('assessment'))]
    d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)


EXAMPLE_RESULTS=[True,True,False,True,False,True,True,True,False,True,False]
def example_model():
    return {**{n:(lambda value=value:value) for n,value in CONSTANTS.items()},'issued':lambda:'start','releasepoint':lambda:'middle',
        'due':lambda:'deadline','assessment':lambda:'after'}


def prepare():
    from scripts.shared_deadlines import prepare as prepare_library
    prepare_library();target=ROOT/EXAMPLE;text=format_graph(example())+'\n'
    if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published deadline example differs')
    if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published deadlines differ')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Deadline basis differs')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Deadline catalog differs')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=example():raise ValueError('Published deadline example differs')
    actual=values(example(),example_model())
    if actual!=EXAMPLE_RESULTS:raise ValueError('Integrated deadline meaning differs')
    result=dict(schema='noema-shared-deadlines-evidence-1',definitions=22,new_definitions=14,preserved_definitions=8,new_primitive_declarations=0,
        temporal=temporal_checks(),frames=frame_checks(),single_slot_binding_diagnostics=binding_diagnostics(),example=actual)
    paths=[LIBRARY,BASIS,EXAMPLE,'scripts/shared_deadlines.py','scripts/check_shared_deadlines.py','tests/test_shared_deadlines.py',
        'docs/shared-deadlines-v1.md','scripts/shared_time.py','scripts/shared_reference.py','scripts/shared_modality.py','scripts/shared_speech.py','scripts/shared_norms.py']
    for source in SOURCES:paths.extend((source['document'],source['basis']))
    for report in ('reports/shared-time-v1.json','reports/shared-norms-v1.json','reports/shared-speech-v1.json'):
        hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend((report,*hashes))
        for path,digest in hashes.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Earlier evidence changed: '+path)
    import sys
    for n,m in tuple(sys.modules.items()):
        p=getattr(m,'__file__',None)
        if n.startswith('noema.') and p and ROOT in Path(p).resolve().parents:paths.append(Path(p).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=LIMITS;return result
