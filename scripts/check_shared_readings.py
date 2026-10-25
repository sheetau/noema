"""Unevaluated alternatives, typed ellipsis bindings and revision evidence."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.shared_readings import (ROOT,LIBRARY,BASIS,I,S,T,U,D,DI,DS,READINGS,TEMPLATE,CHANGE,COVERAGE,LICENSE,
    composed,basis,prepare as prepare_library,v,call,op,truth,lam,definition,apply_description)
from scripts.shared_time import q

EXAMPLE='examples/v016/ellipsis-readings-v1.noema'
HISTORY='examples/v016/reading-revisions-v1.noema'


def ref(n):return dict(kind='function_ref',symbol=n)
def quote(body,rank=0):return dict(kind='quote',body=body,**({'rank':rank} if rank else {}))
def seq(*items):return dict(kind='sequence',element=D,items=list(items))
def evaluate(description):
    return dict(kind='evaluate',content=dict(kind='message_content',message=dict(kind='disquote',description=description)),
                situation=call('now'))


@lru_cache(maxsize=1)
def base():
    doc=deepcopy(composed())
    primitives={'aki':([],I),'nao':([],I),'now':([],S),'then':([],S),
        'mentor':([I,I,S],T),'praise':([I,I,S],T),'reportof':([I,I,S],T),'revise':([I,I,S],T),
        'source':([],I),'target':([],I),'context':([],I),'reason':([],I),'nextreason':([],I),
        'change':(CHANGE['parameters'],T),'coverage':(COVERAGE['parameters'],T),'license':(LICENSE['parameters'],T)}
    doc['declarations'].extend(dict(kind='primitive',name=n,parameters=p,result=r) for n,(p,r) in primitives.items())
    for name,relation,action in (('praising','mentor','praise'),('revising','reportof','revise')):
        body=dict(kind='message',force='assert',content=dict(kind='content',variable='world',body=
            q('exists','object',I,op('and',call(relation,v('object'),v('related'),v('anchor')),
                                   call(action,v('subject'),v('object'),v('world'))))))
        doc['declarations'].append(definition(name,[('subject',I),('related',I),('anchor',S)],U,body))
    return normalize_document(doc)


def result(topic='praising',subject='nao',related='aki',anchor='now'):
    return call('ellipsisresult',quote(ref(topic)),quote(call(subject)),quote(call(related)),quote(call(anchor)))
def literal(topic='praising',subject='nao',related='aki',anchor='now'):
    return quote(dict(kind='apply',function=ref(topic),arguments=[call(subject),call(related),call(anchor)]))
def negative(topic='praising'):
    # A distinct closed message description, preserving the inner message as
    # a structural child. The body is not evaluated during record comparison.
    return quote(dict(kind='message',force='assert',content=dict(kind='content',variable='world',body=op('not',
        dict(kind='evaluate',content=dict(kind='message_content',message=dict(kind='apply',function=ref(topic),
             arguments=[call('nao'),call('aki'),call('now')])),situation=v('world'))))))
def doc(bodies,extra=()):
    d=deepcopy(base());d['declarations'].extend(extra)
    d['statements']=[dict(kind='ask',body=b) for b in bodies]
    return normalize_document(d)


def model(*,execute=False,success=(),changes=True,coverage=True,license=True,overrides=None):
    def unknown(*args):raise ValueError('Unknown quoted content was executed')
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update(source=lambda:'first',target=lambda:'second',context=lambda:'first',reason=lambda:'second',nextreason=lambda:'first',
             change=lambda *args:changes,coverage=lambda *args:coverage,license=lambda *args:license)
    if execute:
        m.update(aki=lambda:'first',nao=lambda:'second',now=lambda:'now',then=lambda:'then',
            mentor=lambda obj,owner,anchor:obj==owner+'target' and anchor=='now',
            reportof=lambda obj,owner,anchor:obj==owner+'target' and anchor=='now',
            praise=lambda actor,obj,world:(actor,obj,world) in success,
            revise=lambda actor,obj,world:(actor,obj,world) in success)
    if overrides:m.update(overrides)
    return m
def values(document,**kwargs):
    return [r['value'] for r in evaluate_document(document,individuals=('first','second','firsttarget','secondtarget'),
                situations=('now','then'),primitives=model(**kwargs))]


def licensed(topic='praising',result_value=None):
    return call('ellipsislicensed',call('source'),call('target'),call('context'),call('reason'),
        quote(ref(topic)),quote(call('nao')),quote(call('aki')),quote(call('now')),
        result(topic) if result_value is None else result_value,ref('license'))


@lru_cache(maxsize=1)
def example():
    statements=[]
    for topic in ('praising','revising'):
        strict=result(topic);sloppy=result(topic,related='nao');readings=seq(strict,sloppy)
        statements.extend([op('equal',strict,literal(topic)),op('not',op('equal',strict,sloppy)),
            call('readingsambiguous',readings),call('readingsresolved',seq(strict),truth(False)),
            call('readingsresolved',seq(strict),truth(True)),licensed(topic)])
    return doc(statements)


@lru_cache(maxsize=1)
def candidate_checks():
    items=[result(),result(related='nao')]
    rows=[]
    for length in range(4):
        for indices in product(range(2),repeat=length):
            candidate=seq(*(items[i] for i in indices));distinct=len(set(indices))
            expressions=[call('readingcontains',candidate,item) for item in items]
            expressions += [call(n,candidate) for n in ('readingsempty','readingssingle','readingsambiguous')]
            expressions += [call(n,candidate,truth(closed)) for closed in (False,True) for n in ('readingsabsence','readingsresolved')]
            expected=[0 in indices,1 in indices,not indices,distinct==1,distinct>1,False,False,not indices,distinct==1]
            actual=values(doc(expressions))
            if actual!=expected:raise ValueError('Candidate sequence status differs')
            rows.append(dict(indices=indices,values=actual))
    return rows


def topic_checks():
    rows=[]
    for topic in ('praising','revising'):
        d=doc([op('equal',result(topic),result(topic,related='nao')),
               evaluate(result(topic)),evaluate(result(topic,related='nao'))])
        for first,second in product((False,True),repeat=2):
            success={('second',obj,'now') for obj,flag in (('firsttarget',first),('secondtarget',second)) if flag}
            actual=values(d,execute=True,success=success)
            if actual!=[False,first,second]:raise ValueError('Strict/sloppy role binding differs')
            rows.append(dict(topic=topic,related_first=first,related_second=second,values=actual))
    return rows


def revision(before,after,beforeclosed=False,afterclosed=False,reason='reason'):
    return call('readingrevision',call('source'),call('context'),before,truth(beforeclosed),after,truth(afterclosed),
                call(reason),ref('change'),ref('coverage'))


@lru_cache(maxsize=1)
def revision_checks():
    expressions=[result(),result(related='nao')];sets=[(),(0,),(1,),(0,1)]
    rows=0;positive=0
    for before,after,closed_before,closed_after,changes,coverage in product(sets,sets,(False,True),(False,True),(False,True),(False,True)):
        changed=set(before)!=set(after) or closed_before!=closed_after
        needs_changes=set(before)!=set(after)
        needs_coverage=closed_after or closed_before!=closed_after
        expected=changed and (changes or not needs_changes) and (coverage or not needs_coverage)
        d=doc([revision(seq(*(expressions[i] for i in before)),seq(*(expressions[i] for i in after)),closed_before,closed_after)])
        actual=values(d,changes=changes,coverage=coverage)[0]
        if actual!=expected:raise ValueError('Revision permission or coverage differs')
        rows+=1;positive+=actual
    return dict(models=rows,accepted=positive)


def history():
    states=[seq(result(),result(related='nao')),seq(result()),seq(result(),negative())]
    definitions=[definition(n,[],READINGS,state) for n,state in zip(('original','selected','reopened'),states)]
    first=revision(call('original'),call('selected'),False,True)
    second=revision(call('selected'),call('reopened'),True,False,reason='nextreason')
    link=call('readinglinked',call('source'),call('context'),call('selected'),truth(True),
              call('source'),call('context'),call('selected'),truth(True))
    return doc([first,second,link,call('readingsresolved',call('selected'),truth(True)),
                call('readingsresolved',call('reopened'),truth(False)),call('readingnarrowing',call('selected'),call('reopened'))],definitions)


def binding_diagnostics():
    rows=[]
    # Every slot is changed with the other arguments fixed. Description slots
    # use two closed expressions, not an enumeration of all descriptions.
    expected=('first','second','first','second','praising','nao','aki','now')
    replacements=('second','first','second','first','revising','aki','nao','then')
    def key(arg):
        if not hasattr(arg,'syntax'):return arg
        node=json.loads(arg.syntax);return node['symbol']
    for slot in range(-1,8):
        target=list(expected)
        if slot>=0:target[slot]=replacements[slot]
        target=tuple(target)
        predicate=lambda *args,wanted=target:tuple(key(a) for a in args)==wanted
        actual=values(doc([licensed()]),overrides={'license':predicate})[0]
        if actual!=(slot==-1):raise ValueError('Ellipsis provenance slot changed')
        rows.append(dict(changed_slot=None if slot<0 else slot,value=actual))
    return rows


def prepare():
    prepare_library()
    for path,d in ((EXAMPLE,example()),(HISTORY,history())):
        target=ROOT/path;text=format_graph(d)+'\n'
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published readings example differs')
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published definitions differ')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published contracts differ')
    for path,d in ((EXAMPLE,example()),(HISTORY,history())):
        if parse((ROOT/path).read_text(encoding='utf-8'))!=d:raise ValueError('Published example differs')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Meaning catalog mismatch')
    result=dict(schema='noema-shared-readings-evidence-1',definitions=14,new_primitives=0,
        construction_without_execution=values(example()),candidate_models=candidate_checks(),
        topic_models=topic_checks(),revision_models=revision_checks(),history=values(history()),
        binding_diagnostics=binding_diagnostics())
    paths=[LIBRARY,BASIS,EXAMPLE,HISTORY,'docs/shared-readings-v1.md','scripts/shared_readings.py','scripts/check_shared_readings.py',
           'scripts/shared_reference.py','scripts/shared_time.py','scripts/shared_modality.py','tests/test_shared_readings.py',*basis()['design_sources']]
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=basis()['limitations']
    return result
