"""Small independent belief/graph oracles and grounded evidence diagnostics."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_evidence import *

PEOPLE=('a','b');TIMES=('now','later')
EXAMPLES={n:'examples/v016/evidence-'+n+'-v1.noema' for n in ('relay','separate','inference')}
CONSTANTS=dict(agent='b',record='b',prior='a',rule='a',target='b',left='a',right='b',origin='a',first='a',second='b')
SIGNATURES=dict(alternatives=ALTERNATIVES,aware=AWARE,holders=HOLDERS,recorded=RECORDED,events=HOLDERS,observed=OBSERVED,
    relayed=RELAYED,available=AVAILABLE,inferred=INFERRED,parents=PAIR,local=GROUP,roots=PAIR,comparisons=function_sort([S],T),payload=function_sort([S],T),
    descriptionat=function_sort([I,D,D],D),conclusionpayload=function_sort([S],T))

def ref(n):return dict(kind='function_ref',symbol=n)
def quote(body):return dict(kind='quote',body=body)
def claim(n='claimform'):return quote(call(n))
def records(names):return seq(*(call('first' if n=='a' else 'second') for n in names))
def unknown(*xs):raise ValueError('Unknown evidence interpretation')
def subsets(items):return [set(x for i,x in enumerate(items) if mask&(1<<i)) for mask in range(1<<len(items))]
def describe(value):
    if hasattr(value,'syntax'):
        node=json.loads(value.syntax)
        return ('description',node['symbol']) if node.get('kind')=='call' else value.syntax
    if hasattr(value,'items'):return tuple(describe(x) for x in value.items)
    return value

@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=I) for n in CONSTANTS]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=S) for n in ('context','assessment')]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=t['parameters'],result=t['result']) for n,t in SIGNATURES.items()]
    for name in ('claimform','otherclaimform'):
        d['declarations'].append(definition(name,[],C,dict(kind='content',variable='world',body=call('payload',v('world')))))
    d['declarations'].append(definition('conclusionform',[],C,dict(kind='content',variable='world',body=call('conclusionpayload',v('world')))))
    # This interpretation adapter can only return descriptions already issued
    # by the document. It is not a new shared primitive or a truth evaluator.
    d['declarations'].append(definition('claims',[('item',I)],D,call('descriptionat',v('item'),claim(),claim('otherclaimform'))))
    return normalize_document(d)

def arguments(ps,**overrides):
    replacements=dict(description=claim(),order=records('ab'),premises=records('a'),descriptions=dict(kind='sequence',element=D,items=[claim()]),
        conclusion=claim(),claims=ref('claims'))
    replacements.update(overrides)
    return [replacements.get(n,ref(n) if isinstance(t,dict) and t.get('kind')=='function' else call(n)) for n,t in ps]
def query(name,**overrides):
    d=next(d for d in raw()['declarations'] if d['name']==name)
    return call(name,*arguments([(p['name'],p['sort']) for p in d['parameters']],**overrides))
def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def expected_slots():
    p=('description','claimform')
    return dict(recorded=('b','b',p,'now'),observed=('b','b',p,'now'),relayed=('b','a','b','a',p,'now'),
        available=('b','a','now'),inferred=('b','b',(p,),p,'a','now'),aware=('b',p,'now'))
def model(**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update({n:(lambda x=x:x) for n,x in CONSTANTS.items()})
    m.update(context=lambda:'now',assessment=lambda:'now',holders=lambda n:n,events=lambda n:n,descriptionat=lambda n,a,b:a,
        alternatives=lambda a,c,w:w=='later',payload=lambda w:w=='later',conclusionpayload=lambda w:True,comparisons=lambda w:True,
        parents=lambda n,p:n=='b' and p=='a',local=lambda n:True,roots=lambda n,r:n==r)
    for name,wanted in expected_slots().items():
        m[name]=lambda *xs,wanted=wanted:tuple(describe(x) for x in xs)==wanted
    m['recorded']=lambda n,holder,d,c:n==holder and describe(d)==('description','claimform') and c=='now'
    m.update(overrides);return m
def values(d,m,people=PEOPLE):
    return [r['value'] for r in evaluate_document(d,individuals=people,situations=TIMES,primitives=m,max_steps=2000000)]

@lru_cache(maxsize=1)
def belief_checks():
    names=('beliefnonempty','beliefaccepted','beliefdenied','beliefunsettled','beliefaccurate','beliefmistaken')
    d=doc([query(n) for n in names]);count=0
    for truths,candidates,aware,context,agent in product(subsets(TIMES),subsets(TIMES),(False,True),TIMES,PEOPLE):
        accepted=aware and bool(candidates) and candidates<=truths
        expected=[bool(candidates),accepted,aware and bool(candidates) and not candidates&truths,
            aware and bool(candidates&truths) and bool(candidates-truths),accepted and context in truths,accepted and context not in truths]
        m=model(agent=lambda:agent,context=lambda:context,payload=lambda w:w in truths,
            alternatives=lambda a,c,w:a==agent and c==context and w in candidates,
            aware=lambda a,d,c:aware and a==agent and describe(d)==('description','claimform') and c==context)
        if values(d,m)!=expected:raise ValueError('Belief set specification differs')
        count+=1
    return dict(models=count,people=2,situations=2,checks_per_model=6)

def proof_oracle(order,parents,local):
    proven=set();ancestry={n:set() for n in PEOPLE}
    for n in order:
        required={p for child,p in parents if child==n}
        if n in local and required<=proven:proven.add(n)
        old={p:set(xs) for p,xs in ancestry.items()}
        ancestry[n] |= {n}|set().union(*(old[p] for p in required))
    verified=len(set(order))==len(order) and set(order)<=proven
    return proven,ancestry,verified

@lru_cache(maxsize=1)
def proof_checks():
    edges=list(product(PEOPLE,repeat=2));count=0
    for order in ('','a','b','ab','ba','aa','bb','aba'):
        sequence=records(order)
        bodies=[query('proofverified',order=sequence)]+[query('proofsupports',order=sequence,target=call(n)) for n in ('first','second')]
        bodies += [apply_expr(query('proofstates',order=sequence),call(n)) for n in ('first','second')]
        bodies += [apply_expr(query('proofancestors',order=sequence),call(a),call(b)) for a,b in product(('first','second'),repeat=2)]
        d=doc(bodies)
        for parents,local in product(subsets(edges),subsets(PEOPLE)):
            proven,ancestry,verified=proof_oracle(order,parents,local)
            expected=[verified]+[verified and n in order and n in proven for n in PEOPLE]+[n in proven for n in PEOPLE]
            expected += [b in ancestry[a] for a,b in edges]
            m=model(parents=lambda n,p:(n,p) in parents,local=lambda n:n in local)
            if values(d,m)!=expected:raise ValueError('Finite proof specification differs')
            count+=1
    return dict(models=count,records=2,orders=8,checks_per_model=9)

@lru_cache(maxsize=1)
def origin_checks():
    edges=list(product(PEOPLE,repeat=2));count=0
    for order in ('ab','ba'):
        bodies=[query(n,order=records(order)) for n in ('proofsharedorigin','proofseparateorigins','proofcorroborates')]
        bodies += [query('prooforigin',order=records(order),target=call(a),origin=call(b)) for a,b in product(('first','second'),repeat=2)]
        d=doc(bodies)
        for parents,assignment in product(subsets(edges),product((None,'a','b'),repeat=2)):
            root={n:({assignment[i]} if assignment[i] else set()) for i,n in enumerate(PEOPLE)}
            proven,ancestry,verified=proof_oracle(order,parents,set(PEOPLE))
            found={n:set().union(*(root[a] for a in ancestry[n])) for n in PEOPLE}
            overlap=bool(found['a']&found['b']);separate=bool(found['a']) and bool(found['b']) and not overlap
            expected=[verified and overlap,verified and separate,verified and separate]
            expected += [verified and b in found[a] for a,b in edges]
            m=model(parents=lambda n,p:(n,p) in parents,roots=lambda n,r:r in root[n])
            if values(d,m)!=expected:raise ValueError('Provenance specification differs')
            count+=1
    return dict(models=count,records=2,origins=2,checks_per_model=7)

@lru_cache(maxsize=1)
def binding_diagnostics():
    rows=[]
    names=dict(recorded='evidenceobserved',observed='evidenceobserved',relayed='evidencereported',
        available='evidenceinferred',inferred='evidenceinferred',aware='beliefaccepted')
    for relation,wanted in expected_slots().items():
        d=doc([query(names[relation])])
        if values(d,model())!=[True]:raise ValueError('Unchanged evidence tuple fails: '+relation)
        for slot,item in enumerate(wanted):
            if isinstance(item,tuple):
                other=(('description','otherclaimform'),) if item and isinstance(item[0],tuple) else ('description','otherclaimform')
            elif item in PEOPLE:other='b' if item=='a' else 'a'
            else:other='later' if item=='now' else 'now'
            changed=list(wanted);changed[slot]=other
            m=model(**{relation:lambda *xs,changed=tuple(changed):tuple(describe(x) for x in xs)==changed})
            if values(d,m)!=[False]:raise ValueError('Misbound evidence tuple accepted: '+relation)
            rows.append(dict(relation=relation,slot=slot,result=False))
    return rows

@lru_cache(maxsize=1)
def entailment_checks():
    count=0
    for size in (0,1,2):
        descriptions=dict(kind='sequence',element=D,items=[claim()]*size)
        d=doc([query('evidenceentails',descriptions=descriptions,conclusion=claim('conclusionform')),
            query('evidencepremisestrue',descriptions=descriptions)])
        for premise,conclusion,comparisons in product(subsets(TIMES),repeat=3):
            expected=[bool(comparisons) and all((size>0 and w not in premise) or w in conclusion for w in comparisons),size==0 or 'now' in premise]
            m=model(payload=lambda w:w in premise,conclusionpayload=lambda w:w in conclusion,comparisons=lambda w:w in comparisons)
            if values(d,m)!=expected:raise ValueError('Scoped entailment differs')
            count+=1
    return dict(models=count,situations=2,premise_lengths=[0,1,2],checks_per_model=2)

def matching(sort,wanted):
    ps=[('arg'+chr(97+i),t) for i,t in enumerate(sort['parameters'])]
    return lam(ps,allof(*(eq(v(n),e) for (n,t),e in zip(ps,wanted))))

@lru_cache(maxsize=3)
def example(mode):
    d=deepcopy(composed())
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=I) for n in CONSTANTS]+[dict(kind='primitive',name='third',parameters=[],result=I)]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=S) for n in ('context','assessment','laterpoint')]
    d['declarations'].append(definition('claimform',[],C,dict(kind='content',variable='world',body=eq(v('world'),call('laterpoint')))))
    d['declarations'] += [definition('holders',[('item',I)],I,v('item')),definition('claims',[('item',I)],D,claim()),
        definition('events',[('item',I)],I,v('item'))]
    p=claim();now=call('context');a=call('first');b=call('second');c=call('third')
    relations={
        'recorded':lam([('item',I),('holder',I),('description',D),('point',S)],allof(eq(v('item'),v('holder')),eq(v('description'),p),eq(v('point'),now))),
        'alternatives':lam([('person',I),('point',S),('world',S)],eq(v('world'),call('laterpoint'))),
        'aware':lam([('person',I),('description',D),('point',S)],op('and',eq(v('description'),p),eq(v('point'),now))),
        'comparisons':lam([('point',S)],truth(True)),
        'available':lam([('person',I),('item',I),('point',S)],allof(eq(v('person'),c),eq(v('point'),now),op('or',eq(v('item'),a),eq(v('item'),b))))}
    observed=[matching(OBSERVED,[a,a,p,now])]
    if mode=='separate':observed.append(matching(OBSERVED,[c,c,p,now]))
    relayed=[matching(RELAYED,[b,a,b,a,p,now])]
    if mode=='relay':relayed.append(matching(RELAYED,[c,b,c,b,p,now]))
    def combine(functions):
        body=functions[0]['body']
        for function in functions[1:]:body=op('or',body,function['body'])
        return dict(kind='lambda',parameters=functions[0]['parameters'],body=body)
    relations['observed']=combine(observed);relations['relayed']=combine(relayed)
    inferred=matching(INFERRED,[c,c,dict(kind='sequence',element=D,items=[p,p]),p,a,now])
    if mode!='inference':inferred['body']=truth(False)
    relations['inferred']=inferred
    edges=[(b,a)]+([(c,b)] if mode=='relay' else [(c,a),(c,b)] if mode=='inference' else [])
    relations['parents']=combine([matching(PAIR,[x,y]) for x,y in edges])
    rootrecords=[a]+([c] if mode=='separate' else [])
    relations['roots']=combine([matching(PAIR,[r,r]) for r in rootrecords])
    for name,function in relations.items():
        d['declarations'].append(definition(name,[(p['name'],p['sort']) for p in function['parameters']],T,function['body']))
    node=v('node');prior=v('earlier');empty=seq();premises=seq(a,b)
    observed=op('and',query('evidenceparents',record=node,premises=empty),query('evidenceobserved',record=node))
    reported=q('exists','earlier',I,op('and',query('evidenceparents',record=node,premises=seq(prior)),query('evidencereported',record=node,prior=prior)))
    inferred=allof(eq(node,c),query('evidenceparents',record=node,premises=premises),query('evidenceinferred',record=node,premises=premises),
        query('evidenceentails',descriptions=call('evidencepremises',premises,ref('claims')),conclusion=call('claims',node)))
    d['declarations'].append(definition('local',[('node',I)],T,op('or',observed,op('or',reported,inferred))))
    order=seq(a,b,c);common=dict(order=order,target=c,agent=c,left=b,right=c)
    bodies=[query(n,**common) for n in ('proofverified','proofsupports','proofsharedorigin','proofseparateorigins','proofcorroborates',
        'beliefmistaken','beliefgrounded','beliefgroundedtrue')]
    descriptions=call('evidencepremises',premises,ref('claims'))
    bodies += [query('evidencepremisestrue',descriptions=descriptions),query('evidenceentails',descriptions=descriptions),
        query('evidenceinferred',record=c,premises=premises),query('proofsupports',order=seq(c,b,a),target=c),
        query('proofsupports',order=seq(a,b,c,c),target=c),query('prooforigin',order=order,target=c,origin=a)]
    d['statements']=[dict(kind='ask',body=x) for x in bodies];return normalize_document(d)

def example_model():return {**{n:(lambda x=x:x) for n,x in CONSTANTS.items()},'third':lambda:'c',
    'context':lambda:'now','assessment':lambda:'now','laterpoint':lambda:'later'}
def example_expected(mode):
    separate=mode=='separate'
    return [True,True,not separate,separate,separate,True,True,False,False,True,mode=='inference',False,False,not separate]

def prepare():
    from scripts.shared_evidence import prepare as prepare_library
    prepare_library()
    for mode,path in EXAMPLES.items():
        target=ROOT/path;text=format_graph(example(mode))+'\n'
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published evidence example differs')
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')

def build_report():
    from noema.meaning_catalog import load_catalog
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Evidence catalog differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Evidence basis differs')
    examples={}
    for mode,path in EXAMPLES.items():
        if parse((ROOT/path).read_text(encoding='utf-8'))!=example(mode):raise ValueError('Evidence example differs')
        actual=values(example(mode),example_model(),('a','b','c'))
        if actual!=example_expected(mode):raise ValueError('Integrated evidence meaning differs: '+mode)
        examples[mode]=actual
    result=dict(schema='noema-shared-evidence-report-1',definitions=31,new_definitions=25,preserved_definitions=6,new_primitive_declarations=0,
        belief=belief_checks(),proof=proof_checks(),origins=origin_checks(),entailment=entailment_checks(),
        single_slot_binding_diagnostics=binding_diagnostics(),examples=examples)
    paths=[LIBRARY,BASIS,*EXAMPLES.values(),'scripts/shared_evidence.py','scripts/check_shared_evidence.py','tests/test_shared_evidence.py',
        'docs/shared-evidence-v1.md','scripts/shared_modality.py','scripts/shared_reference.py','scripts/shared_time.py','scripts/shared_plurality.py']
    paths.extend(basis()['design_sources'])
    for source in SOURCES:paths.extend((source['document'],source['basis']))
    for report in ('reports/shared-modality-v1.json','reports/shared-plurality-v1.json'):
        hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend((report,*hashes))
        for path,digest in hashes.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Earlier evidence changed: '+path)
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=LIMITS;return result
