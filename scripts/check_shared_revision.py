"""Independent set comparisons, state adapters and explicit revision examples."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_revision import *
from scripts.shared_plurality import seq

PEOPLE=('a','b');TIMES=('before','after')
EXAMPLES={n:'examples/v016/revision-'+n+'-v1.noema' for n in ('filter','reversal','repeat','supportgain','misleading')}
CONSTANTS=dict(agent='a',holder='a',source='b',event='a',record='b',reason='b',first='a',second='b',priorholder='a',nextholder='a')
STAGES=dict(before='before',after='after',assessment='before',priorafter='after',nextbefore='after')
SIGNATURES=dict(payload=function_sort([I,S],T),corpus=CORPUS,supported=CORPUS,alternatives=ALTERNATIVES,aware=AWARE,
    received=RECEIVED,available=AVAILABLE,precedence=PRECEDENCE,adopts=ADOPTS,edge=function_sort([S,I,I],T),validrecord=function_sort([S,I],T),
    scope=GROUP,comparisons=WINDOW)

def ref(n):return dict(kind='function_ref',symbol=n)
def quote(body):return dict(kind='quote',body=body)
def claim(n='secondform'):return quote(call(n))
def unknown(*a):raise ValueError('Unknown revision interpretation')
def subsets(xs):return [set(x for i,x in enumerate(xs) if mask&(1<<i)) for mask in range(1<<len(xs))]
def describe(value):
    if hasattr(value,'syntax'):
        node=json.loads(value.syntax);return ('description',node['symbol']) if node.get('kind')=='call' else value.syntax
    return value

@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=I) for n in CONSTANTS]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=S) for n in STAGES]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=t['parameters'],result=t['result']) for n,t in SIGNATURES.items()]
    for name,item in [('firstform','first'),('firstalias','first'),('secondform','second')]:
        d['declarations'].append(definition(name,[],C,dict(kind='content',variable='world',body=call('payload',call(item),v('world')))))
    d['declarations'] += [definition('claims',[('item',I)],D,call('claimchoice',eq(v('item'),call('first')),claim('firstform'),claim())),
        definition('recordclaims',[('record',I)],D,call('claims',v('record'))),
        definition('orders',[('stage',S)],MEMBERS,seq(call('first'),call('second'))),
        definition('parents',[('stage',S)],PAIR,lam([('record',I),('premise',I)],call('edge',v('stage'),v('record'),v('premise')))),
        definition('local',[('stage',S)],GROUP,lam([('record',I)],call('validrecord',v('stage'),v('record'))))]
    return normalize_document(d)

def arguments(ps,**overrides):
    replacements=dict(description=claim(),claims=ref('claims'),recordclaims=ref('recordclaims'),contents=call('claimcontents',ref('claims')),
        priorclaims=ref('claims'),nextclaims=ref('claims'),priorcorpus=ref('corpus'),nextcorpus=ref('corpus'),
        priorsupported=ref('supported'),nextsupported=ref('supported'))
    replacements.update(overrides)
    return [replacements.get(n,ref(n) if isinstance(t,dict) and t.get('kind')=='function' else call(n)) for n,t in ps]
def query(name,**overrides):
    d=next(d for d in raw()['declarations'] if d['name']==name)
    ps=OLD_PARAMS.get(name,[(p['name'],p['sort']) for p in d['parameters']])
    return call(name,*arguments(ps,**overrides))
def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def expected_slots():
    p=('description','secondform')
    return dict(received=('a','b','a','b',p,'before','after'),adopts=('a','b',p,'b','before','after'),
        available=('a','b','after'),precedence=('before','after'),aware=('a',p,'after'))
def model(**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update({n:(lambda x=x:x) for n,x in (CONSTANTS|STAGES).items()})
    m.update(claimchoice=lambda c,a,b:a if c else b,payload=lambda item,w:item=='a' or w=='before',scope=lambda i:True,comparisons=lambda w:True,
        corpus=lambda h,i,s:h=='a' and (i=='a' or s=='after'),supported=lambda h,i,s:h=='a' and (i=='a' or s=='after'),
        alternatives=lambda h,s,w:h=='a' and (s=='before' or w=='before'),aware=lambda h,d,s:h=='a',
        edge=lambda s,r,p:False,validrecord=lambda s,r:True)
    for name,wanted in expected_slots().items():
        if name!='aware':m[name]=lambda *xs,wanted=wanted:tuple(describe(x) for x in xs)==wanted
    m.update(overrides);return m
def values(d,m,scenes=TIMES):return [r['value'] for r in evaluate_document(d,individuals=PEOPLE,situations=scenes,primitives=m,max_steps=2000000)]

@lru_cache(maxsize=1)
def candidate_checks():
    names=('candidatesincluded','candidatesame','candidatefiltered','evidencereceived','evidenceused','beliefupdated','beliefadopted','evidencefiltered')
    d=doc([query(n) for n in names]);count=0
    for before,after,truths,awarebefore,awareafter in product(subsets(TIMES),subsets(TIMES),subsets(TIMES),(False,True),(False,True)):
        old=awarebefore and bool(before) and before<=truths;used=awareafter and bool(after) and after<=truths
        filtered=after==before&truths
        expected=[after<=before,after==before,filtered,True,used,used and (before!=after or awarebefore!=awareafter),used and not old,used and filtered]
        m=model(payload=lambda i,w:w in truths,alternatives=lambda h,s,w:h=='a' and w in (before if s=='before' else after),
            aware=lambda h,d,s:h=='a' and (awarebefore if s=='before' else awareafter))
        if values(d,m)!=expected:raise ValueError('Candidate revision specification differs')
        count+=1
    return dict(models=count,situations=2,checks_per_model=8)

def comparison_oracle(truths,old,new,old_support,new_support,scope=set(PEOPLE),comparisons=set(TIMES),assessment='before'):
    good=lambda items,support:items&support&{i for i in scope if (i,assessment) in truths}
    profile=lambda selected:{w for w in comparisons if all((i,w) in truths for i in selected)}
    old_profile=profile(good(old,old_support));new_profile=profile(good(new,new_support))
    preserved=assessment in comparisons and new_profile<=old_profile
    expanded=preserved and bool(old_profile-new_profile)
    errors=lambda items:{tuple((i,w) in truths for w in sorted(comparisons)) for i in items&scope if (i,assessment) not in truths}
    old_errors=errors(old);new_errors=errors(new)
    reduced=preserved and new_errors<=old_errors and bool(old_errors-new_errors)
    return [preserved,expanded,reduced,reduced and not new_errors]

@lru_cache(maxsize=1)
def comparison_checks():
    names=('informationpreserved','informationexpanded','errorsreduced','errorscleared');d=doc([query(n) for n in names]);count=0
    profiles=[(set(PEOPLE),set(PEOPLE)),(set(),set()),({'a'},set(PEOPLE)),(set(PEOPLE),{'a'})]
    for truths,old,new,(old_support,new_support) in product(subsets(list(product(PEOPLE,TIMES))),subsets(PEOPLE),subsets(PEOPLE),profiles):
        m=model(payload=lambda i,w:(i,w) in truths,corpus=lambda h,i,s:h=='a' and i in (old if s=='before' else new),
            supported=lambda h,i,s:h=='a' and i in (old_support if s=='before' else new_support))
        if values(d,m)!=comparison_oracle(truths,old,new,old_support,new_support):raise ValueError('Information comparison differs')
        count+=1
    return dict(models=count,items=2,situations=2,support_profiles=4,checks_per_model=4)

@lru_cache(maxsize=1)
def support_checks():
    d=doc([dict(kind='apply',function=query('evidencebasis'),arguments=[call('agent'),call(i),call(s)])
        for s,i in product(('before','after'),('first','second'))]);count=0
    pairs=list(product(TIMES,PEOPLE))
    for available,valid in product(subsets(pairs),repeat=2):
        expected=[(s,i) in available and all((s,r) in valid for r in PEOPLE) for s,i in pairs]
        m=model(available=lambda h,r,s:h=='a' and (s,r) in available,validrecord=lambda s,r:(s,r) in valid)
        if values(d,m)!=expected:raise ValueError('Stage-specific proof adapter differs')
        count+=1
    return dict(models=count,records=2,stages=2,checks_per_model=4)

@lru_cache(maxsize=1)
def choice_checks():
    cases=[]
    for condition,left,right in product((False,True),('firstform','firstalias','secondform'),('firstform','firstalias','secondform')):
        body=call('claimchoice',truth(condition),claim(left),claim(right))
        d=doc([eq(body,claim(left if condition else right)),eq(body,claim(right if condition else left))])
        result=values(d,model(payload=unknown))
        if result!=[True,left==right]:raise ValueError('Claim choice evaluated or replaced its description')
        cases.append(dict(condition=condition,left=left,right=right,result=result))
    return cases

@lru_cache(maxsize=1)
def binding_diagnostics():
    rows=[]
    for relation,wanted in expected_slots().items():
        name='evidencereceived' if relation in ('received','available','precedence') else 'evidenceused'
        d=doc([query(name)])
        if values(d,model())!=[True]:raise ValueError('Original revision tuple fails: '+relation)
        for slot,item in enumerate(wanted):
            other=('description','firstform') if isinstance(item,tuple) else ('b' if item=='a' else 'a') if item in PEOPLE else ('after' if item=='before' else 'before')
            changed=list(wanted);changed[slot]=other
            m=model(**{relation:lambda *xs,changed=tuple(changed):tuple(describe(x) for x in xs)==changed})
            if values(d,m)!=[False]:raise ValueError('Misbound revision tuple accepted: '+relation)
            rows.append(dict(relation=relation,slot=slot,result=False))
    return rows


def example(mode):
    if mode not in EXAMPLES:raise ValueError('Unknown revision example')
    d=deepcopy(composed())
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=I) for n in CONSTANTS]
    stages=STAGES|dict(otherworld='alternative')
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=S) for n in stages]
    def add(name,ps,result,body):d['declarations'].append(definition(name,ps,result,body))
    add('firstform',[],C,dict(kind='content',variable='world',body=eq(v('world'),call('assessment'))))
    add('secondform',[],C,dict(kind='content',variable='world',body=op('not',eq(v('world'),call('assessment')))))
    add('claims',[('item',I)],D,call('claimchoice',eq(v('item'),call('first')),claim('firstform'),claim()))
    add('recordclaims',[('record',I)],D,call('claims',v('record')))
    selected=claim() if mode=='misleading' else claim('firstform')
    def match(sort,targets):
        ps=[('arg'+chr(97+i),t) for i,t in enumerate(sort['parameters'])]
        return ps,allof(*(eq(v(n),target) for (n,t),target in zip(ps,targets)))
    for name,sort,targets in [
        ('received',RECEIVED,[call(n) for n in ('agent','source','event','record')]+[selected,call('before'),call('after')]),
        ('adopts',ADOPTS,[call('agent'),call('record'),selected,call('reason'),call('before'),call('after')]),
        ('precedence',PRECEDENCE,[call('before'),call('after')])]:
        ps,body=match(sort,targets);add(name,ps,T,body)
    stage=op('or',eq(v('stage'),call('before')),eq(v('stage'),call('after')))
    access=stage if mode=='repeat' else eq(v('stage'),call('after'))
    add('available',[('holder',I),('record',I),('stage',S)],T,allof(eq(v('holder'),call('agent')),eq(v('record'),call('record')),access))
    add('aware',[('holder',I),('description',D),('stage',S)],T,allof(eq(v('holder'),call('agent')),stage,
        op('or',eq(v('description'),claim('firstform')),eq(v('description'),claim()))))
    actual=eq(v('world'),call('assessment'));other=eq(v('world'),call('otherworld'))
    old=other if mode=='reversal' else actual if mode in ('repeat','supportgain') else op('or',actual,other)
    new=other if mode=='misleading' else actual
    add('alternatives',[('holder',I),('stage',S),('world',S)],T,op('and',eq(v('holder'),call('agent')),
        op('or',op('and',eq(v('stage'),call('before')),old),op('and',eq(v('stage'),call('after')),new))))
    add('orders',[('stage',S)],MEMBERS,seq(call('record')))
    add('parents',[('stage',S)],PAIR,lam([('record',I),('premise',I)],truth(False)))
    add('local',[('stage',S)],GROUP,lam([('record',I)],eq(v('record'),call('record'))))
    add('scope',[('item',I)],T,op('or',eq(v('item'),call('first')),eq(v('item'),call('second'))))
    add('comparisons',[('world',S)],T,op('or',actual,other))
    add('corpus',[],CORPUS,call('beliefcorpus',ref('claims'),ref('alternatives'),ref('aware')))
    add('supported',[],CORPUS,query('evidencebasis'))
    common=dict(description=selected,corpus=call('corpus'),supported=call('supported'),
        priorcorpus=call('corpus'),nextcorpus=call('corpus'),priorsupported=call('supported'),nextsupported=call('supported'))
    bodies=[query(n,**common) for n in ('evidencereceived','evidenceused','beliefupdated','beliefadopted','evidencefiltered',
        'candidatesincluded','informationpreserved','informationexpanded','errorsreduced','errorscleared')]
    bodies += [evaluate(selected,call('assessment')),query('informationlinked',**common)]
    bodies += [call('beliefaccepted',call('agent'),selected,call(s),ref('alternatives'),ref('aware')) for s in ('before','after')]
    d['statements']=[dict(kind='ask',body=b) for b in bodies]
    return normalize_document(d)

EXAMPLE_SCENES=('before','after','actual','alternative')
def example_model(mode):
    constants=CONSTANTS|dict(record='b' if mode=='misleading' else 'a')
    stages=STAGES|dict(assessment='actual',otherworld='alternative')
    return {**{n:(lambda x=x:x) for n,x in (constants|stages).items()},'claimchoice':lambda c,a,b:a if c else b}
def example_expected(mode):
    unchanged=mode in ('repeat','supportgain');reversal=mode=='reversal'
    return [True,True,not unchanged,not unchanged,not reversal,not reversal,True,
        mode in ('filter','reversal','supportgain'),reversal,reversal,mode!='misleading',True,unchanged,True]

def prepare():
    from scripts.shared_revision import prepare as prepare_library
    prepare_library()
    for mode,path in EXAMPLES.items():
        target=ROOT/path;text=format_graph(example(mode))+'\n'
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published revision example differs')
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')

def build_report():
    from noema.meaning_catalog import load_catalog
    if load_catalog(ROOT,BASIS).document!=composed():raise ValueError('Revision catalog differs')
    if json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Revision basis differs')
    if load_catalog(ROOT,choice.BASIS).document!=choice.document():raise ValueError('Claim choice catalog differs')
    examples={}
    for mode,path in EXAMPLES.items():
        if parse((ROOT/path).read_text(encoding='utf-8'))!=example(mode):raise ValueError('Revision example differs')
        actual=values(example(mode),example_model(mode),EXAMPLE_SCENES)
        if actual!=example_expected(mode):raise ValueError('Integrated revision meaning differs: '+mode)
        examples[mode]=actual
    result=dict(schema='noema-shared-revision-report-1',definitions=27,newly_shared_definitions=19,
        new_definitions=12,lifted_definitions=7,preserved_shared_definitions=8,new_primitive_declarations=1,
        candidates=candidate_checks(),information=comparison_checks(),support=support_checks(),
        description_choice=choice_checks(),single_slot_binding_diagnostics=binding_diagnostics(),examples=examples)
    paths=[LIBRARY,BASIS,choice.LIBRARY,choice.BASIS,*EXAMPLES.values(),'scripts/shared_revision.py','scripts/shared_claim_choice.py',
        'scripts/check_shared_revision.py','tests/test_shared_revision.py','docs/shared-revision-v1.md']
    for report in ('reports/epistemic-revision-v1.json','reports/shared-evidence-v1.json'):
        hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend((report,*hashes))
        for path,digest in hashes.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Earlier evidence changed: '+path)
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=LIMITS+choice.LIMITS;return result
