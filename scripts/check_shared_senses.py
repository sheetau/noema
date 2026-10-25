"""Independent finite checks for contextual lexical senses."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_senses import *
from scripts.shared_reference import content

PEOPLE=('a','b');TIMES=('now','later')
CONSTANTS=dict(first='a',second='b',worda='a',wordb='b',contexta='a',contextb='b',sensea='a',senseb='b',occurrence='a',reason='b',agentrole='a',patientrole='b')
STAGES=dict(now='now',later='later')
SIGNATURES=dict(payload=function_sort([I,MEMBERS,S],T),worlds=WINDOW,selected=CHOSEN,licensed=SYNONYM,related=RELATED,unrelated=RELATED,permitted=REPLACE)
EXAMPLES={name:'examples/v016/senses-'+name+'-v1.noema' for name in ('selection','context','synonym','classification')}

def seq(items,element=I):return dict(kind='sequence',element=element,items=list(items))
def number(n):return dict(kind='number',numerator=n,denominator=1)
def argument(names=('first',)):return quote(seq(call(n) for n in names))
def meaning(name='firstmeaning'):return quote(ref(name))
def cases(names=(('first',),('second',))):return seq((argument(ns) for ns in names),ARGUMENTS)
def entry(word='worda',context='contexta',sense='sensea',body='firstmeaning',arity=1,roles=('agentrole',)):
    return call('senseentry',call(word),call(context),call(sense),meaning(body),number(arity),seq(call(n) for n in roles))
def entries(*items):return seq(items,ENTRY)
def frame(name='extensionalframe'):return quote(ref(name),1)
def ev(body,world='now'):return evaluate(body,call(world))
def unknown(*a):raise ValueError('Unknown lexical interpretation')

@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=I) for n in CONSTANTS]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=S) for n in STAGES]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=t['parameters'],result=t['result']) for n,t in SIGNATURES.items()]
    for name,item in [('firstmeaning','first'),('aliasmeaning','first'),('secondmeaning','second')]:
        d['declarations'].append(definition(name,[('items',MEMBERS)],C,content(call('payload',call(item),v('items'),v('world')))))
    d['declarations'] += [definition('extensionalframe',[('word',I),('meaning',MEANING)],C,
        disquote(call('senseapplication',v('meaning'),argument()))),
        definition('wordframe',[('word',I),('meaning',MEANING)],C,content(eq(v('word'),call('worda')))),
        definition('descriptionframe',[('word',I),('meaning',MEANING)],C,content(eq(v('meaning'),meaning())))]
    return normalize_document(d)

def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def query(name,**overrides):
    declaration=next(d for d in raw()['declarations'] if d['name']==name)
    default=dict(entries=entries(entry()),entry=entry(),word=call('worda'),context=call('contexta'),sense=call('sensea'),meaning=meaning(),
        arity=number(1),roles=seq([call('agentrole')]),complete=truth(True),arguments=argument(),result=call('senseapplication',meaning(),argument()),
        left=entry(),right=entry(word='wordb',body='aliasmeaning'),cases=cases(),frame=frame())
    default.update(overrides)
    return call(name,*[default.get(p['name'],ref(p['name']) if isinstance(p['sort'],dict) and p['sort']['kind']=='function' else call(p['name'])) for p in declaration['parameters']])
def model(**overrides):
    m={n:(lambda x=x:x) for n,x in (CONSTANTS|STAGES).items()}
    m.update(payload=lambda i,a,w:(a.items==('a',))==(w=='now') if i=='a' else False,worlds=lambda w:True,
        selected=lambda *a:True,licensed=lambda *a:True,related=lambda *a:True,unrelated=lambda *a:False,permitted=lambda *a:True)
    m.update(overrides);return m
def values(d,m):return [r['value'] for r in evaluate_document(d,individuals=PEOPLE,situations=TIMES,primitives=m,max_steps=2000000)]
def subsets(items):return [{x for i,x in enumerate(items) if mask&(1<<i)} for mask in range(1<<len(items))]

@lru_cache(maxsize=1)
def candidate_checks():
    count=0
    for included,complete,selected in product(subsets(('a','b')),(False,True),(False,True)):
        pool=entries(*[entry(sense='sense'+x,body='firstmeaning' if x=='a' else 'secondmeaning') for x in sorted(included)])
        bodies=[query(n,entries=pool,complete=truth(complete)) for n in ('sensecandidates','sensepossible','senseunique','senseresolved','sensemultiple','sensechosen','senseinterpreted')]
        expected=[True,'a' in included,included=={'a'},complete and included=={'a'},len(included)>1,selected and 'a' in included,selected and 'a' in included]
        if values(doc(bodies),model(selected=lambda *a:selected))!=expected:raise ValueError('Candidate specification differs')
        count+=1
    return dict(models=count,senses=2,checks_per_model=7)

@lru_cache(maxsize=1)
def meaning_checks():
    points=list(product(PEOPLE,TIMES));d=doc([query(n,left=meaning(),right=meaning('secondmeaning')) for n in ('meaningentails','meaningequivalent')]);count=0
    for left,right,scope in product(subsets(points),subsets(points),subsets(TIMES)):
        expected=[bool(scope) and all(p not in left or p in right for p in points if p[1] in scope),
            bool(scope) and all((p in left)==(p in right) for p in points if p[1] in scope)]
        m=model(payload=lambda i,a,w:(a.items[0],w) in (left if i=='a' else right),worlds=lambda w:w in scope)
        if values(d,m)!=expected:raise ValueError('Meaning specification differs')
        count+=1
    return dict(models=count,argument_cases=2,situations=2,checks_per_model=2)

@lru_cache(maxsize=1)
def classification_checks():
    count=0
    for sameword,samecontext,samesense,samemeaning,related,unrelated in product((False,True),repeat=6):
        other=entry(word='worda' if sameword else 'wordb',context='contexta' if samecontext else 'contextb',sense='sensea' if samesense else 'senseb',body='firstmeaning' if samemeaning else 'secondmeaning')
        d=doc([query(n,right=other) for n in ('sensepolysemous','sensehomonymous')])
        common=sameword and samecontext and not samesense and not samemeaning
        expected=[common and related and not unrelated,common and unrelated and not related]
        if values(d,model(related=lambda *a:related,unrelated=lambda *a:unrelated))!=expected:raise ValueError('Classification specification differs')
        count+=1
    return dict(models=count,independent_conditions=6,checks_per_model=2)

@lru_cache(maxsize=1)
def replacement_checks():
    count=0
    for licensed,permitted,scope in product((False,True),(False,True),subsets(TIMES)):
        d=doc([query('sensesynonymous')]+[query('sensereplaceable',frame=frame(n)) for n in ('extensionalframe','wordframe','descriptionframe')])
        synonymous=licensed and bool(scope)
        expected=[synonymous,synonymous and permitted,False,False]
        if values(d,model(licensed=lambda *a:licensed,permitted=lambda *a:permitted,worlds=lambda w:w in scope))!=expected:raise ValueError('Replacement specification differs')
        count+=1
    return dict(models=count,frames=3,checks_per_model=4)

def frozen(x):
    if hasattr(x,'syntax'):return (x.rank,x.syntax)
    if hasattr(x,'element_type'):return tuple(frozen(y) for y in x.items)
    if isinstance(x,(tuple,list)):return tuple(frozen(y) for y in x)
    return x
def captured(expressions,sorts):
    found=[];d=deepcopy(base());d['declarations'].append(dict(kind='primitive',name='capture',parameters=sorts,result=T))
    d['statements']=[dict(kind='ask',body=call('capture',*expressions))]
    if values(normalize_document(d),model(capture=lambda *a:found.extend(a) or True))!=[True]:raise ValueError('Capture failed')
    return tuple(frozen(x) for x in found)

@lru_cache(maxsize=1)
def binding_diagnostics():
    relationargs=dict(selected=[call('occurrence'),call('worda'),call('contexta'),call('sensea'),meaning(),number(1),seq([call('agentrole')]),call('reason')],
        licensed=[call('contexta'),call('worda'),call('sensea'),call('wordb'),call('sensea'),call('reason')],
        related=[call('worda'),call('contexta'),call('sensea'),meaning(),call('senseb'),meaning('secondmeaning'),call('reason')],
        unrelated=[call('worda'),call('contexta'),call('sensea'),meaning(),call('senseb'),meaning('secondmeaning'),call('reason')],
        permitted=[call('occurrence'),call('contexta'),call('worda'),call('sensea'),call('wordb'),call('sensea'),frame(),call('reason')])
    rows=[]
    for relation,expressions in relationargs.items():
        if relation in ('related','unrelated'):
            body=query('sensepolysemous' if relation=='related' else 'sensehomonymous',right=entry(sense='senseb',body='secondmeaning'))
            extra={'unrelated' if relation=='related' else 'related':lambda *a:False}
        else:body=query(dict(selected='senseinterpreted',licensed='sensesynonymous',permitted='sensereplaceable')[relation]);extra={}
        sorts=SIGNATURES[relation]['parameters'];wanted=captured(expressions,sorts);d=doc([body])
        interpretation=lambda target:lambda *a:tuple(frozen(x) for x in a)==target
        if values(d,model(**extra,**{relation:interpretation(wanted)}))!=[True]:raise ValueError('Original sense binding fails: '+relation)
        for slot,(value,type_) in enumerate(zip(wanted,sorts)):
            if type_==I:other='b' if value=='a' else 'a'
            elif type_==N:other=2
            elif type_==MEMBERS:other=('b',)
            else:other=captured([frame('wordframe') if type_==FRAME else meaning('secondmeaning' if expressions[slot]==meaning() else 'firstmeaning')],[type_])[0]
            changed=list(wanted);changed[slot]=other
            if values(d,model(**extra,**{relation:interpretation(tuple(changed))}))!=[False]:raise ValueError('Misbound sense tuple accepted: '+relation)
            rows.append(dict(relation=relation,slot=slot,result=False))
    return rows

def match(name,targets):
    type_=SIGNATURES[name];ps=[('arg'+chr(97+i),t) for i,t in enumerate(type_['parameters'])]
    return definition(name,ps,T,allof(*(eq(v(n),x) for (n,t),x in zip(ps,targets))))

def example(mode):
    if mode not in EXAMPLES:raise ValueError('Unknown senses example')
    d=deepcopy(base());ds=[x for x in d['declarations'] if x['name'] not in SIGNATURES]
    cut=next(i for i,x in enumerate(ds) if x['name']=='firstmeaning')
    # A fully Native, fictional two-individual example: first meaning holds of
    # the first individual now and the second later; second meaning reverses it.
    condition=op('iff',eq(v('items'),seq([call('first')])),eq(v('point'),call('now')))
    payload=definition('payload',[('item',I),('items',MEMBERS),('point',S)],T,op('iff',eq(v('item'),call('first')),condition))
    ds=ds[:cut]+[payload]+ds[cut:]
    ds += [definition('worlds',[('point',S)],T,truth(True)),
        match('selected',[call('occurrence'),call('worda'),call('contexta'),call('sensea'),meaning(),number(1),seq([call('agentrole')]),call('reason')]),
        match('licensed',[call('contexta'),call('worda'),call('sensea'),call('wordb'),call('sensea'),call('reason')]),
        match('related',[call('worda'),call('contexta'),call('sensea'),meaning(),call('senseb'),meaning('secondmeaning'),call('reason')]),
        definition('unrelated',[('arg'+chr(97+i),t) for i,t in enumerate(RELATED['parameters'])],T,truth(False)),
        match('permitted',[call('occurrence'),call('contexta'),call('worda'),call('sensea'),call('wordb'),call('sensea'),frame(),call('reason')])]
    pool=entries(entry(),entry(sense='senseb',body='secondmeaning'))
    if mode=='selection':
        bodies=[query(n,entries=pool) for n in ('sensecandidates','sensepossible','senseunique','senseresolved','sensemultiple','sensechosen','senseinterpreted')]
        bodies += [ev(disquote(call('senseapplication',meaning(),argument())),p) for p in ('now','later')]
        bodies += [query('senseinterpreted',entries=pool,sense=call('senseb'),meaning=meaning('secondmeaning')),
            query('senseinstantiated',arity=number(2)),query('entrysame',right=entry())]
    elif mode=='context':
        other=entry(context='contextb',body='secondmeaning');mixed=entries(entry(),other)
        bodies=[query('sensecatalog',entries=mixed),query('sensecandidates',entries=mixed),query('sensecandidates',entries=entries(other),context=call('contextb')),
            query('senseunique'),query('senseresolved',complete=truth(False)),query('senseresolved'),
            query('senseunique',entries=entries(entry(),entry())),query('sensemultiple',entries=entries(entry(),entry())),
            query('sensecatalog',entries=entries(entry(),entry(body='secondmeaning'))),query('entrysame',right=other),
            query('entryvalid',entry=entry(arity=2,roles=('agentrole','patientrole'))),query('entryvalid',entry=entry(arity=2,roles=('agentrole','agentrole')))]
    elif mode=='synonym':
        bodies=[eq(meaning(),meaning('aliasmeaning')),query('senseequivalent'),query('sensesynonymous'),query('sensereplaceable'),
            query('sensereplaceable',frame=frame('wordframe')),query('sensereplaceable',frame=frame('descriptionframe')),
            query('senseequivalent',right=entry(word='wordb',body='secondmeaning')),
            query('senseequivalent',right=entry(word='wordb',body='aliasmeaning',roles=('patientrole',))),
            query('sensesynonymous',reason=call('first')),query('sensereplaceable',occurrence=call('second')),
            ev(call('senseframed',frame('wordframe'),call('worda'),meaning())),ev(call('senseframed',frame('wordframe'),call('wordb'),meaning('aliasmeaning')))]
    else:
        other=entry(sense='senseb',body='secondmeaning')
        bodies=[query('sensemultiple',entries=pool),query('sensepolysemous',right=other),query('sensehomonymous',right=other),
            query('sensepolysemous',right=other,related=ref('unrelated')),query('sensepolysemous',right=other,unrelated=ref('related')),
            query('sensehomonymous',right=other,related=ref('unrelated'),unrelated=ref('related')),
            query('sensepolysemous',right=entry(word='wordb',sense='senseb',body='secondmeaning')),
            query('sensepolysemous',right=entry(sense='senseb')),query('sensepossible',entries=pool,sense=call('senseb')),
            query('sensepolysemous',right=other,reason=call('first')),query('entrycompatible',right=other),query('entrysame',right=other)]
    d['declarations']=ds;d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)

def example_model():return {n:(lambda x=x:x) for n,x in (CONSTANTS|STAGES).items()}
def example_expected(mode):return dict(selection=[True,True,False,False,True,True,True,True,False,False,False,True],
    context=[True,False,True,True,False,True,True,False,False,False,True,False],
    synonym=[False,True,True,True,False,False,False,False,False,False,True,False],
    classification=[True,True,False,False,False,True,False,False,True,False,True,False])[mode]

def prepare():
    from scripts.shared_senses import prepare as prepare_library
    prepare_library()
    for mode,path in EXAMPLES.items():
        target=ROOT/path;text=format_graph(example(mode))+'\n'
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published senses example differs')
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')

def build_report():
    from noema.meaning_catalog import load_catalog
    if load_catalog(ROOT,BASIS).document!=composed() or json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Senses basis differs')
    examples={}
    for mode,path in EXAMPLES.items():
        d=example(mode)
        if parse((ROOT/path).read_text(encoding='utf-8'))!=d:raise ValueError('Senses example differs')
        actual=values(d,example_model())
        if actual!=example_expected(mode):raise ValueError('Integrated senses meaning differs: '+mode)
        examples[mode]=actual
    result=dict(schema='noema-shared-senses-report-1',definitions=29,preserved_definitions=4,new_definitions=25,new_primitive_declarations=0,
        candidates=candidate_checks(),meaning=meaning_checks(),classification=classification_checks(),replacement=replacement_checks(),
        single_slot_binding_diagnostics=binding_diagnostics(),examples=examples)
    paths=[LIBRARY,BASIS,*EXAMPLES.values(),'scripts/shared_senses.py','scripts/check_shared_senses.py','tests/test_shared_senses.py','docs/shared-senses-v1.md',*basis()['design_sources']]
    for source in SOURCES:paths.extend((source['document'],source['basis']))
    for name in ('shared-focus','shared-plurality','shared-readings'):
        report='reports/'+name+'-v1.json';hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend((report,*hashes))
        for path,digest in hashes.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Earlier sense evidence changed: '+path)
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=LIMITS;return result
