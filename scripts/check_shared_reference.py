"""Finite contrasts for explicit referents, projection and speech packages."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.shared_reference import (ROOT,LIBRARY,BASIS,I,S,T,C,U,CANDIDATES,ASSIGNMENT,TIME_ASSIGNMENT,
    composed,basis,prepare as prepare_library,v,call,op,content,evaluate,truth,lam)
from scripts.shared_time import composed as time_composed,q,allof

PEOPLE=('first','second');WORLDS=('now','other')
EXAMPLE='examples/v016/reference-presupposition-contrasts-v1.noema'
AGAIN_EXAMPLE='examples/v016/repetitive-presupposition-v1.noema'


def ref(name):return dict(kind='function_ref',symbol=name)
def document(primitives,bodies,definitions=()):
    doc=deepcopy(composed())
    doc['declarations'].extend(deepcopy(definitions))
    for name,(params,result) in primitives.items():
        doc['declarations'].append(dict(kind='primitive',name=name,parameters=params,result=result))
    doc['statements']=[dict(kind='ask',body=body) for body in bodies]
    return normalize_document(doc)
def values(doc,model,people=PEOPLE,worlds=WORLDS):
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=worlds,primitives=model)]
def diagnostic(pair):
    return [call(n,pair,call('inputworld')) for n in ('licensedpositive','licensednegative','unsupported')]


@lru_cache(maxsize=1)
def reference_document():
    p=call('definitestatement',ref('inputcandidates'),ref('inputproperty'))
    background=call('presupposed',p);issue=call('atissue',p)
    question=dict(kind='message',force='ask',content=issue)
    assertion=dict(kind='message',force='assert',content=issue)
    package=call('speechpackage',background,question)
    checks=[call(n,ref('inputcandidates'),call('inputworld')) for n in
            ('referenceexists','referencemissing','referenceunique','referenceambiguous')]
    checks+=[call('referencevalue',ref('inputcandidates'),call('inputworld'),call('inputreferent'))]
    checks+=diagnostic(p)+diagnostic(call('presuppnegate',p))
    checks+=[call('speechvalid',package,call('inputworld')),
             call('speechmatches',package,question),call('speechmatches',package,assertion)]
    return document({'inputcandidates':([I,S],T),'inputproperty':([I,S],T),
                     'inputworld':([],S),'inputreferent':([],I)},checks)


def reference_values(candidates,properties,referent='first',world='now'):
    if candidates is None or properties is None:raise ValueError('Missing candidate/property interpretation')
    model={'inputcandidates':lambda x,w:x in candidates if w=='now' else x not in candidates,
           'inputproperty':lambda x,w:x in properties if w=='now' else x not in properties,
           'inputworld':lambda:world,'inputreferent':lambda:referent}
    return values(reference_document(),model)


def subsets(items):return [tuple(x for i,x in enumerate(items) if mask & (1<<i)) for mask in range(1<<len(items))]


@lru_cache(maxsize=1)
def reference_checks():
    rows=[]
    for candidates,properties,referent,world in product(subsets(PEOPLE),subsets(PEOPLE),PEOPLE,WORLDS):
        selected=set(candidates) if world=='now' else set(PEOPLE)-set(candidates)
        prop=set(properties) if world=='now' else set(PEOPLE)-set(properties)
        unique=len(selected)==1;positive=unique and bool(selected&prop);negative=unique and not bool(selected&prop)
        expected=[bool(selected),not selected,unique,len(selected)>1,unique and referent in selected,
                  positive,negative,not unique,negative,positive,not unique,unique,True,False]
        observed=reference_values(candidates,properties,referent,world)
        if observed!=expected:raise ValueError('Reference/presupposition differs from independent set condition')
        rows.append(dict(candidates=candidates,properties=properties,referent=referent,world=world,values=observed))
    return dict(models=len(rows),statement_order=['exists','missing','unique','ambiguous','value',
        'positive','negative','unsupported','negated_positive','negated_negative','negated_unsupported',
        'question_valid','is_question','is_assertion'],cases=rows)


@lru_cache(maxsize=1)
def projection_document():
    p=lambda n:content(call(n,v('world')))
    left=call('presupposition',p('leftbackground'),p('leftissue'))
    right=call('presupposition',p('rightbackground'),p('rightissue'))
    bodies=[]
    for name in ('presuppif','presuppglobalif','presuppand'):
        pair=call(name,left,right)
        bodies.extend([evaluate(call('presupposed',pair),call('inputworld')),
                       evaluate(call('atissue',pair),call('inputworld'))])
    return document({**{n:([S],T) for n in ('leftbackground','leftissue','rightbackground','rightissue')},
                     'inputworld':([],S)},bodies)


@lru_cache(maxsize=1)
def projection_checks():
    rows=[]
    for p1,a1,p2,a2 in product((False,True),repeat=4):
        flags=(p1,a1,p2,a2)
        model={n:(lambda w,b=b:b if w=='now' else not b) for n,b in
               zip(('leftbackground','leftissue','rightbackground','rightissue'),flags)}
        model['inputworld']=lambda:'now'
        actual=values(projection_document(),model)
        expected=[p1 and (not a1 or p2),not a1 or a2,p1 and p2,not a1 or a2,
                  p1 and (not a1 or p2),a1 and a2]
        if actual!=expected:raise ValueError('Projection scope differs')
        rows.append(dict(input=flags,values=actual))
    return rows


@lru_cache(maxsize=1)
def anaphora_document():
    params={'inputmention':([],I),'inputcontext':([],I),'inputreferent':([],I),
            'accessible':([I,I,I],T),'denotes':([I,I,I],T),'compatible':([I,I,I],T),'inputworld':([],S)}
    candidate=lambda target:call('anaphoriccandidate',call('inputmention'),call('inputcontext'),target,
                                 ref('accessible'),ref('denotes'),ref('compatible'))
    selector=lam([('target',I),('world',S)],candidate(v('target')))
    bodies=[candidate(call('inputreferent'))]+[call(n,selector,call('inputworld')) for n in
            ('referenceexists','referenceunique','referenceambiguous')]
    return document(params,bodies)


def anaphora_values(accessible,denotes,compatible):
    return values(anaphora_document(),{'inputmention':lambda:'first','inputcontext':lambda:'first',
        'inputreferent':lambda:'second','inputworld':lambda:'now',
        'accessible':lambda *args:args in accessible,'denotes':lambda *args:args in denotes,
        'compatible':lambda *args:args in compatible})


@lru_cache(maxsize=1)
def anaphora_checks():
    access={('first',x,'first') for x in PEOPLE};compat={('first',x,'first') for x in PEOPLE}
    same={('first','second','first'),('second','second','first')}
    different={('first','first','first'),('second','second','first')}
    rows=[dict(name='two_mentions_one_referent',values=anaphora_values(access,same,compat)),
          dict(name='two_mentions_two_referents',values=anaphora_values(access,different,compat)),
          dict(name='no_accessible_mention',values=anaphora_values(set(),different,compat)),
          dict(name='incompatible_referents',values=anaphora_values(access,different,set()))]
    if [r['values'] for r in rows]!=[[True,True,True,False],[True,True,False,True],[False,False,False,False],[False,False,False,False]]:
        raise ValueError('Anaphoric candidate range differs')
    return rows


@lru_cache(maxsize=1)
def binding_diagnostics():
    targets={'accessible':('first','second','first'),'denotes':('second','second','first'),
             'compatible':('first','second','first')}
    rows=[]
    for relation,target in targets.items():
        for slot in range(-1,3):
            data={k:{v} for k,v in targets.items()}
            changed=list(target)
            if slot>=0:changed[slot]='second' if changed[slot]=='first' else 'first'
            data[relation]={tuple(changed)}
            result=anaphora_values(**data)[0]
            if result!=(slot==-1):raise ValueError('Anaphora binding changed: '+relation+' '+str(slot))
            rows.append(dict(relation=relation,changed_slot=None if slot<0 else slot,value=result))
    return rows


def context_checks():
    primitives={'assignedperson':([I,I,I],T),'assignedtime':([I,I,S],T)}
    for n in ('outer','inner','speaker','place','time','alice','bob','home','office'):primitives['input'+n]=([],I)
    for n in ('now','then'):primitives['input'+n]=([],S)
    bodies=[]
    for ctx,role,target in (('outer','speaker','alice'),('inner','speaker','bob'),('inner','speaker','alice'),
                            ('outer','place','office'),('inner','place','home'),('inner','place','office')):
        bodies.append(call('individualrole',*(call('input'+n) for n in (ctx,role,target)),ref('assignedperson')))
    for ctx,target in (('outer','now'),('inner','then'),('inner','now')):
        bodies.append(call('situatedrole',call('input'+ctx),call('inputtime'),call('input'+target),ref('assignedtime')))
    doc=document(primitives,bodies)
    entries={('outer','speaker','alice'),('inner','speaker','bob'),('outer','place','office'),('inner','place','home')}
    times={('outer','time','now'),('inner','time','then')}
    model={'input'+n:(lambda x=n:x) for n in ('outer','inner','speaker','place','time','alice','bob','home','office','now','then')}
    model.update(assignedperson=lambda *args:args in entries,assignedtime=lambda *args:args in times)
    people=('outer','inner','speaker','place','time','alice','bob','home','office')
    observed=values(doc,model,people,('now','then'))
    if observed!=[True,True,False,True,True,False,True,True,False]:raise ValueError('Deictic context changed')
    entries.add(('inner','speaker','alice'));times.add(('inner','time','now'))
    ambiguous=values(doc,model,people,('now','then'))
    if ambiguous!=[True,False,False,True,True,False,True,False,False]:raise ValueError('Ambiguous role silently selected')
    return dict(distinct_contexts=observed,ambiguous_roles=ambiguous)


def contexts():
    rows=[]
    for topic in ('王の来訪','文書の受領'):
        for label,candidates,properties in (('no_referent',(),()),('two_candidates',PEOPLE,PEOPLE),
                                            ('unique_positive',('first',),('first',)),('unique_negative',('first',),())):
            result=reference_values(candidates,properties)
            rows.append(dict(topic=topic,case=label,positive=result[5],negative=result[6],unsupported=result[7],
                             negated_positive=result[8],question_valid=result[11]))
    return rows


def again_document():
    # Construct prior occurrence from the same actor, history and strict order;
    # do not introduce a primitive for the entire "has come before" condition.
    prior=content(allof(call('chronology',ref('history'),ref('order')),call('history',v('world')),
        q('exists','earlier',S,allof(call('history',v('earlier')),call('order',v('earlier'),v('world')),
                                    call('occurs',call('actor'),v('earlier'))))))
    current=content(call('occurs',call('actor'),v('world')))
    pair=call('presupposition',prior,current)
    return document({'occurs':([I,S],T),'history':([S],T),'order':([S,S],T),'actor':([],I),'inputworld':([],S)},
                    diagnostic(pair)+diagnostic(call('presuppnegate',pair)),
                    [d for d in time_composed()['declarations'] if d['name']=='chronology'])


def again_values(before,now,other_actor=False):
    target='second' if other_actor else 'first'
    return values(again_document(),{'history':lambda w:True,'order':lambda a,b:(a,b)==('early','now'),
        'actor':lambda:'first','inputworld':lambda:'now',
        'occurs':lambda a,w:a==target and (before if w=='early' else now)},worlds=('early','now'))


def again_checks():
    rows=[]
    for before,now in product((False,True),repeat=2):
        result=again_values(before,now)
        expected=[before and now,before and not now,not before,before and not now,before and now,not before]
        if result!=expected:raise ValueError('Prior occurrence disappeared under negation')
        rows.append(dict(prior=before,current=now,values=result))
    return rows


def prepare():
    prepare_library()
    for name,doc in ((EXAMPLE,reference_document()),(AGAIN_EXAMPLE,again_document())):
        path=ROOT/name;text=format_graph(doc)+'\n'
        if path.exists() and path.read_text(encoding='utf-8')!=text:raise ValueError('Published reference example differs: '+name)
        if not path.exists():path.write_text(text,encoding='utf-8',newline='\n')


def build_report():
    from noema.meaning_catalog import load_catalog
    if parse((ROOT/LIBRARY).read_text(encoding='utf-8'))!=composed():raise ValueError('Published reference definitions differ')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Published reference contracts differ')
    if parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))!=reference_document():raise ValueError('Published reference example differs')
    if parse((ROOT/AGAIN_EXAMPLE).read_text(encoding='utf-8'))!=again_document():raise ValueError('Published repetitive example differs')
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Meaning catalog refers to another module')
    result=dict(schema='noema-shared-reference-evidence-1',definitions=22,new_primitives=0,
        reference_checks=reference_checks(),projection_checks=projection_checks(),
        anaphora=anaphora_checks(),deictic_contexts=context_checks(),topics=contexts(),again=again_checks(),
        binding_diagnostics=binding_diagnostics())
    paths=[LIBRARY,BASIS,EXAMPLE,AGAIN_EXAMPLE,'examples/v016/shared-time-v1.noema','scripts/shared_reference.py','scripts/check_shared_reference.py',
           'scripts/shared_modality.py','scripts/shared_time.py','docs/shared-reference-v1.md','tests/test_shared_reference.py']
    paths.extend(row['path'] for row in basis()['design_sources'])
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=basis()['limitations']
    return result
