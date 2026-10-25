"""Finite diagnostics for shared temporal definitions; no manuscript mutation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product,permutations
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.shared_time import (ROOT,LIBRARY,BASIS,PERSISTENCE,TRANSITIONS,OLD_NAMES,S,I,T,
                                WINDOW,ORDER,EVENTS,TRACE,ROLES,composed,basis,prepare as prepare_library,v,call,lam,op)
from scripts.shared_modality import renamed

POINTS=('early','middle','late')
INDIVIDUALS=('first','second')
DEFAULT_ORDER={(a,b) for i,a in enumerate(POINTS) for b in POINTS[i+1:]}
EXAMPLE='examples/v016/temporal-anchor-contrasts-v1.noema'


@lru_cache(maxsize=16)
def harness(names):
    doc=deepcopy(composed())
    signatures={'history':WINDOW,'order':ORDER,'window':WINDOW,'left':WINDOW,'right':WINDOW,
        'trace':TRACE,'culmination':TRACE,'events':EVENTS,'periods':EVENTS,'windows':TRACE,
        'process':dict(kind='function',parameters=[I,S,S],result=T),
        'anchor':S,'event':I,'earlier':S,'later':S,'state':WINDOW}
    for name,t in signatures.items():
        if isinstance(t,dict):params,result=t['parameters'],t['result']
        else:params,result=[],t
        doc['declarations'].append(dict(kind='primitive',name='input'+name,parameters=params,result=result))
    for name in names:
        args=[]
        for role in ROLES[name]:
            if role=='content':arg=dict(kind='content',variable='point',body=call('inputstate',v('point')))
            elif isinstance(signatures[role],dict):arg=dict(kind='function_ref',symbol='input'+role)
            else:arg=call('input'+role)
            args.append(arg)
        doc['statements'].append(dict(kind='ask',body=call(name,*args)))
    return normalize_document(doc)


def interpret(names,*,history=POINTS,order=None,window=POINTS,left=POINTS,right=POINTS,anchor='middle',
              event='first',trace=None,culmination=(),events=INDIVIDUALS,periods=(),windows=None,
              earlier='early',later='late',process=(),state=POINTS,points=POINTS,individuals=INDIVIDUALS,
              overrides=None,document=None):
    if any(x is None for x in (history,window,left,right,culmination,events,periods,state)):
        raise ValueError('Missing interpretation is not an empty relation')
    order=DEFAULT_ORDER if order is None else order
    trace={'first':POINTS,'second':()} if trace is None else trace
    windows={} if windows is None else windows
    model={'inputhistory':lambda p:p in history,'inputorder':lambda a,b:(a,b) in order,
        'inputwindow':lambda p:p in window,'inputleft':lambda p:p in left,'inputright':lambda p:p in right,
        'inputanchor':lambda:anchor,'inputevent':lambda:event,'inputearlier':lambda:earlier,'inputlater':lambda:later,
        'inputtrace':lambda e,p:p in trace.get(e,()),'inputculmination':lambda e,p:(e,p) in culmination,
        'inputevents':lambda e:e in events,'inputperiods':lambda p:p in periods,
        'inputwindows':lambda period,p:p in windows.get(period,()),
        'inputprocess':lambda e,a,b:(e,a,b) in process,'inputstate':lambda p:p in state}
    if overrides:model.update(overrides)
    results=evaluate_document(harness(tuple(names)) if document is None else document,
                              individuals=individuals,situations=points,primitives=model)
    return dict(zip(names,(r['value'] for r in results)))


def subsets(values):return [tuple(x for i,x in enumerate(values) if mask & (1<<i)) for mask in range(1<<len(values))]
def interval(window,points=POINTS):
    return bool(window) and set(window)<=set(points) and list(window)==list(points[points.index(window[0]):points.index(window[-1])+1])


@lru_cache(maxsize=1)
def window_checks():
    pairs=[(a,b) for a in POINTS for b in POINTS if a!=b]
    orders=[{(a,b) for i,a in enumerate(p) for b in p[i+1:]} for p in permutations(POINTS)]
    accepted=0
    for edges in subsets(pairs):
        observed=interpret(('chronology',),order=set(edges))['chronology']
        expected=set(edges) in orders
        if observed!=expected:raise ValueError('Chronology differs from independent permutation order')
        accepted+=observed
    anchor_cases=[]
    for window,anchor in product(subsets(POINTS),POINTS):
        valid=interval(window)
        wanted=(valid,valid and all(POINTS.index(p)<POINTS.index(anchor) for p in window),
                valid and all(POINTS.index(p)>POINTS.index(anchor) for p in window),valid and anchor in window)
        values=interpret(('timewindow','windowbefore','windowafter','windowat'),window=window,anchor=anchor)
        if tuple(values.values())!=wanted:raise ValueError('Window/anchor condition differs')
        anchor_cases.append(dict(window=window,anchor=anchor,values=values))
    for left,right in product(subsets(POINTS),repeat=2):
        valid=interval(left) and interval(right)
        wanted=(valid and bool(set(left)&set(right)),valid and set(left)<=set(right))
        values=interpret(('windowoverlap','windowwithin'),left=left,right=right)
        if tuple(values.values())!=wanted:raise ValueError('Window relation differs')
    return dict(order_models=64,accepted_orders=accepted,anchor_cases=anchor_cases,window_pairs=64)


@lru_cache(maxsize=1)
def aspect_checks():
    cases=0
    for extent,ends,anchor in product(subsets(POINTS),subsets(POINTS),POINTS):
        valid=interval(extent)
        earlier=[p for p in extent if POINTS.index(p)<POINTS.index(anchor)]
        by=[p for p in ends if POINTS.index(p)<=POINTS.index(anchor)]
        underway=valid and anchor in extent and bool(earlier) and not by
        complete=valid and any(p in extent and p in by and p==extent[-1] for p in ends)
        got=interpret(('eventunderway','eventcompleteby'),trace={'first':extent},
                      culmination={('first',p) for p in ends},anchor=anchor)
        if tuple(got.values())!=(underway,complete):raise ValueError('Aspect differs from endpoint/set condition')
        cases+=1
    return dict(models=cases,points=3,description='All extent subsets, culmination subsets and three anchors for one event')


@lru_cache(maxsize=1)
def recurrence_checks():
    once=0
    for first,second in product(subsets(POINTS),repeat=2):
        observed=interpret(('eventonce',),trace={'first':first,'second':second},window=('middle',))['eventonce']
        expected=interval(first) and interval(second) and sum('middle' in t for t in (first,second))==1
        if observed!=expected:raise ValueError('Unique event condition differs')
        once+=1
    rows=[]
    windowmap={'first':('early',),'second':('late',)}
    for selected in subsets(INDIVIDUALS):
        for first,second in product(subsets(POINTS),repeat=2):
            traces={'first':first,'second':second}
            expected=bool(selected) and all(any(interval(t) and set(t)<=set(windowmap[p]) for t in traces.values()) for p in selected)
            actual=interpret(('eventevery',),trace=traces,periods=selected,windows=windowmap)['eventevery']
            if actual!=expected:raise ValueError('Period-wise occurrence differs')
            rows.append(actual)
    return dict(unique_event_models=once,period_models=len(rows),period_positive_models=sum(rows))


@lru_cache(maxsize=1)
def contexts():
    cases=[
      ('running_in_progress','走行','一周する走行の途中',dict(trace={'first':POINTS},culmination={('first','late')}),[True,False]),
      ('running_interrupted','走行','翌時点で中断し、一周しなかった走行の途中',dict(trace={'first':('early','middle')}),[True,False]),
      ('running_finished','走行','一周を終えた後',dict(trace={'first':POINTS},culmination={('first','late')},anchor='late'),[False,True]),
      ('drafting_before_report','文書作成','報告内の当時、原稿を書いていた',dict(trace={'first':('early','middle')}),[True,False]),
      ('drafting_at_utterance','文書作成','後の発話時には書いていない',dict(trace={'first':('early','middle')},anchor='late'),[False,False]),
      ('draft_completed','文書作成','同じ原稿を完成した後',dict(trace={'first':('early','middle')},culmination={('first','middle')},anchor='late'),[False,True]),
      ('other_event_completed','文書作成','別原稿の完成では対象原稿は完成しない',dict(trace={'first':POINTS},culmination={('second','middle')}),[True,False]),
    ]
    rows=[]
    for name,topic,reading,kwargs,wanted in cases:
        actual=interpret(('eventunderway','eventcompleteby'),**kwargs)
        if list(actual.values())!=wanted:raise ValueError('Context contrast differs: '+name)
        rows.append(dict(name=name,topic=topic,reading=reading,values=actual))
    return rows


def anchor_document():
    """One document keeps the reported reference time and utterance time apart."""
    doc=deepcopy(harness(('eventunderway','eventunderway','eventcompleteby')))
    for index,row in enumerate(doc['statements']):
        row['body']['arguments'][4]=call('inputearlier' if index==0 else 'inputlater')
    reference=lam('point',S,op('equal',v('point'),call('inputearlier')))
    precedes=call('windowbefore',dict(kind='function_ref',symbol='inputhistory'),
        dict(kind='function_ref',symbol='inputorder'),reference,call('inputlater'))
    doc['statements'][0]['body']=op('and',precedes,doc['statements'][0]['body'])
    return normalize_document(doc)


def anchor_examples():
    doc=anchor_document();rows=[]
    for name,kwargs,wanted in (
        ('interrupted',dict(trace={'first':('early','middle')}),[True,False,False]),
        ('finished_later',dict(trace={'first':POINTS},culmination={('first','late')}),[True,False,True]),
        ('reference_reversed',dict(trace={'first':POINTS},earlier='late',later='middle'),[False,True,False])):
        inputs=dict(earlier='middle',later='late');inputs.update(kwargs)
        values=interpret(('reported_stage','utterance_stage','utterance_completion'),document=doc,**inputs)
        if list(values.values())!=wanted:raise ValueError('Independent reference/utterance binding differs')
        rows.append(dict(name=name,values=values))
    return rows


def prepare():
    prepare_library()
    text=format_graph(anchor_document())+'\n';path=ROOT/EXAMPLE
    if path.exists() and path.read_text(encoding='utf-8')!=text:raise ValueError('Published anchor example differs')
    if not path.exists():path.write_text(text,encoding='utf-8',newline='\n')


@lru_cache(maxsize=1)
def binding_diagnostics():
    # Instantiate other witnesses; vary each slot over two values. Not a proof
    # over the product of all large tuple domains.
    cases=[]
    for name,arity,target,replacements in (
        ('process',3,('first','early','late'),('second','late','early')),
        ('trace',2,('first','late'),('second','early')),
        ('culmination',2,('first','late'),('second','early'))):
        for slot in range(-1,arity):
            wanted=list(target)
            if slot>=0:wanted[slot]=replacements[slot]
            wanted=tuple(wanted)
            inputs=dict(points=('early','late'),history=('early','late'),order={('early','late')},
                        anchor='late',trace={'first':('late',)},culmination={('first','late')})
            query='processextent' if name=='process' else 'eventcompleteby'
            value=interpret((query,),**inputs,overrides={'input'+name:lambda *args,t=wanted:args==t})[query]
            if value!=(slot==-1):raise ValueError('Binding differs: '+name+' '+str(slot))
            cases.append(dict(relation=name,changed_slot=None if slot<0 else slot,value=value))
    return cases


def source_checks():
    shared={d['name']:d for d in composed()['declarations']}
    rows=[]
    for path,mapping in basis()['source_renamings'].items():
        original={d['name']:d for d in parse((ROOT/path).read_text(encoding='utf-8'))['declarations']}
        for old,new in mapping.items():
            if renamed(shared[new],{v:k for k,v in OLD_NAMES.items()})!=original[old]:raise ValueError('Old temporal body changed')
            rows.append(dict(source=path,old=old,shared=new,body_preserved=True))
    return rows


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published temporal source differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published contracts differ')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=anchor_document():raise ValueError('Published anchor example differs')
    catalog=load_catalog(ROOT,BASIS)
    if catalog.document!=composed():raise ValueError('Meaning catalog refers to a different temporal module')
    evidence=dict(schema='noema-shared-time-evidence-1',definitions=14,new_primitives=0,
        source_preservation=source_checks(),windows=window_checks(),aspects=aspect_checks(),
        recurrence=recurrence_checks(),contexts=contexts(),anchor_examples=anchor_examples(),binding_diagnostics=binding_diagnostics())
    paths=[LIBRARY,BASIS,EXAMPLE,PERSISTENCE,TRANSITIONS,'data/persistence-basis-v1.json','data/transitions-basis-v1.json',
           'scripts/shared_time.py','scripts/check_shared_time.py','scripts/shared_modality.py',
           'tests/test_shared_time.py','docs/shared-time-v1.md']
    import sys
    from pathlib import Path
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:
            paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    evidence['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    evidence['limits']=basis()['limitations']
    return evidence
