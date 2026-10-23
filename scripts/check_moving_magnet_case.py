"""Check first-case bindings, local witnesses, quantifiers and attributed discourse."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.extraction import extract_document
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM,RS,FS
from scripts.check_conductor_cases import sentinel,same_value
from scripts.compose_moving_magnet_case import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,BASE,RESULT,FIELDS,EXAMPLE,MOTION,HISTORY,NEIGHBOR,PRODUCTION,ELIGIBILITY,ENERGY,ENERGY_HISTORY,CURRENT_POINT,COVER,FIELD_POINT,RESPONSE,MEANINGS,motion,history,build

DOC='docs/moving-magnet-case-v1.md';READING='data/moving-magnet-case-reading-v1.json'
PRIOR='data/einstein-author-credit-review-v1.json';PREVIOUS=['data/interaction-example-reading-v1.json','data/observable-contrast-reading-v1.json']
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
DOMAIN=('body','other','frame','unit','section','orientation','x','y','z','t','node','prior','author','paper','view','process')
CONTEXTS=('first','text','other')
def forbidden(*xs):raise ValueError('Unknown moving-magnet input')
def symbol(x):return json.loads(x.syntax)['symbol']
def names(xs):return [x.removeprefix('v ') for x in xs]

def evaluate(doc,model,individuals=DOMAIN):
    ps={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=individuals,situations=CONTEXTS,primitives={n:model.get(n,forbidden) for n in ps},max_steps=1000000,memoize_definitions=False,memoize_expressions=False)

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=set(NUM)
    if name=='eidm':boundaries|={'eic2','eiag','eiah'}
    if name=='eids':boundaries|={'eidn','eido','eidq','eidr','lg'}
    if name=='eidr':boundaries|={'eibf'}
    if name=='eidn':boundaries|={'eiad'}
    if name=='eidt':boundaries|={'eidm','eids'}
    abstract(doc,boundaries)
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='pointwise':
        # Instantiate quantified variables as explicit arguments for local tests.
        # This checks the exact body, not the truth of its universal/existential closure.
        tail=d['body']['arguments'][1]
        while tail['kind'] in ('forall','exists'):
            d['parameters'].append(dict(name=tail['variable'],sort=tail['sort']));tail=tail['body']
        d['body']['arguments'][1]=tail
    slots=[];calls=[]
    for i,p in enumerate(d['parameters']):
        n='jmmc'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        calls.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=calls))]
    return doc,slots

def run(name,values,model,mode='native'):
    doc,slots=fixture(name,mode);assert len(slots)==len(values);model=dict(model)
    for (n,s),value in zip(slots,values):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    return evaluate(doc,model)[0]['value']

def setup(name,fields,mode='native'):
    cuts,base=arithmetic();slots=fixture(name,mode)[1];assert len(fields)==len(slots)
    supplied=[sentinel(s,i+1,cuts) for i,(_,s) in enumerate(slots)];pos={n:i for i,(n,_) in enumerate(fields)}
    def gate(keys,xs,bit=True):return bit and len(xs)==len(keys) and all(same_value(x,supplied[pos[n]],slots[pos[n]][1],cuts) for x,n in zip(xs,keys))
    return cuts,base,slots,supplied,pos,gate

@lru_cache(None)
def binding_checks():
    counts={};coverage=set()
    for name,fields in (('eidm',BASE),('eids',FIELDS)):
        cuts,base,slots,supplied,pos,gate=setup(name,fields)
        if name=='eidm':
            calls={'eisap':[n for n,_ in ELIGIBILITY],'eic2':[n for n,_ in EXAMPLE],'eiag':names(motion('left')),'eiah':names(motion('right'))}
        else:
            calls={'eisal':[n for n,_ in NEIGHBOR],'eisam':[n for n,_ in PRODUCTION],
                'eidn':names(motion('right'))+['region'],'eido':[n for n,_ in FIELD_POINT],
                'eidq':[n for n,_ in ENERGY_HISTORY],'eidr':names(history())+['section','orientation','time'],
                'eisao':[n for n,_ in RESPONSE[:-1]]}
        used={n for row in calls.values() for n in row};coverage|=used
        def local(missing=None):
            m=dict(base,zc7=lambda:'t')
            for callee,keys in calls.items():
                def callback(*xs,callee=callee,keys=keys):
                    if callee=='eisao':assert symbol(xs[-1])=='eica';xs=xs[:-1]
                    return gate(keys,xs,callee!=missing)
                m[callee]=callback
            if name=='eids':
                m['lg']=lambda lower,upper,t:gate(['lower','upper'],(lower,upper)) and cuts.read(t)==cuts.read(supplied[pos['point']]('t')) and missing!='lg'
            return m
        assert run(name,supplied,local())
        for i,(field,_) in enumerate(fields):
            changed=supplied.copy();changed[i]=sentinel(slots[i][1],100+i,cuts)
            assert run(name,changed,local())==(field not in used),(name,field)
            old=supplied[i];supplied[i]=changed[i];assert run(name,changed,local()),(name,field,'distinguishing');supplied[i]=old
        for callee in calls:assert not run(name,supplied,local(callee)),callee
        if name=='eids':assert not run(name,supplied,local('lg'))
        counts[name]=dict(argument_mutations=len(fields),used_arguments=len(used),missing_connections=len(calls)+(name=='eids'))
    assert coverage=={n for n,_ in FIELDS}
    # Native conditional body with explicit witnesses, not enumerated real/function domains.
    cuts,base,slots,supplied,pos,gate=setup('eidt',FIELDS,'pointwise')
    for antecedent,conclusion in product((False,True),repeat=2):
        assert run('eidt',supplied,dict(eidm=lambda *xs:antecedent,eids=lambda *xs:conclusion),'pointwise')==((not antecedent) or conclusion)
    for i,(field,_) in enumerate(FIELDS):
        changed=supplied.copy();changed[i]=sentinel(slots[i][1],100+i,cuts)
        # True antecedent makes every conclusion slot observable.
        assert not run('eidt',changed,dict(eidm=lambda *xs:True,eids=lambda *xs:gate([n for n,_ in FIELDS],xs)),'pointwise'),field
        old=supplied[i];supplied[i]=changed[i]
        assert run('eidt',changed,dict(eidm=lambda *xs:True,eids=lambda *xs:gate([n for n,_ in FIELDS],xs)),'pointwise')
        supplied[i]=old
    return dict(groups=counts,all_case_slots_used=True,conditional_body_cases=4,conditional_witness_slots=len(FIELDS),quantified_closure_not_finitely_proved=True)

@lru_cache(None)
def local_checks():
    cuts,base=arithmetic();c=cuts.make;r=cuts.read
    axes=('x','y','z');m=dict(base,yn=lambda:'x',yo=lambda:'y',yp=lambda:'z',zc7=lambda:'t')
    def vector(values):return FunctionValue(('individual',),RS,lambda axis:c(dict(zip(('x','y','z','t'),values)).get(axis,0)))
    point=vector((1,2,3,4));count=0
    for vals in product((-2,0,2),repeat=3):
        field=lambda a:FunctionValue((RS,RS,RS,RS),RS,lambda x,y,z,t:c(dict(zip(axes,vals)).get(a,0)*(r(x)+r(t))))
        actual=tuple(5*x for x in vals);f=dict(electricfield=field,region=lambda *xs:True,point=point,electric=vector(actual))
        values=lambda f,fields:[f[n] for n,_ in fields]
        assert run('eido',values(f,FIELD_POINT),m)==any(vals);count+=1
        for axis in range(3):
            bad=list(actual);bad[axis]+=1
            assert not run('eido',values(dict(f,electric=vector(bad)),FIELD_POINT),m);count+=1
        assert not run('eido',values(dict(f,region=lambda *xs:False),FIELD_POINT),m)
    # Energy is a physical attribution plus a valid nonnegative value.
    ec,eb,es,ev,ep,eg=setup('eidp',ENERGY);ev[ep['time']]=ec.make(2);ev[ep['value']]=ec.make(3)
    em=dict(eb,eisan=lambda *xs:eg([n for n,_ in ENERGY],xs))
    assert run('eidp',ev,em)
    for i,_ in enumerate(ENERGY):
        changed=ev.copy();changed[i]=sentinel(es[i][1],100+i,ec);assert not run('eidp',changed,em)
        old=ev[i];ev[i]=changed[i];assert run('eidp',changed,em);ev[i]=old
    for amount in (-3,0,5):
        values=ev.copy();values[ep['value']]=ec.make(amount)
        assert run('eidp',values,dict(eb,eisan=lambda *xs:True))==(amount>=0)
    assert not run('eidp',ev,dict(eb,eisan=lambda *xs:False))
    # Native current witness: signed current, membership, interval and valid history.
    cs=fixture('eidr')[1];f={n:sentinel(s,i+1,cuts) for i,((n,_),(_,s)) in enumerate(zip(CURRENT_POINT,cs))}
    f.update(lower=c(0),upper=c(2),sections=lambda sec,ori:(sec,ori)==('section','orientation'),section='section',orientation='orientation')
    def current(sec,ori):return FunctionValue((RS,),RS,lambda t:c(r(t)-1))
    f['current']=current
    for time in (-1,0,1,2,3):
        f['time']=c(time);assert run('eidr',[f[n] for n,_ in CURRENT_POINT],dict(base,eibf=lambda *xs:True))==(time in (0,2))
    f['time']=c(0)
    for field,value in (('section','other'),('orientation','other')):
        changed=dict(f,**{field:value});assert not run('eidr',[changed[n] for n,_ in CURRENT_POINT],dict(base,eibf=lambda *xs:True))
    assert not run('eidr',[f[n] for n,_ in CURRENT_POINT],dict(base,eibf=lambda *xs:False))
    # Unknown real values must not be decoded by sampling.
    bad=ev.copy();bad[ep['value']]=FunctionValue(('number',),'truth',lambda q:True)
    try:run('eidp',bad,em)
    except ValueError as e:assert 'not constructed' in str(e)
    else:raise AssertionError('Unknown energy cut accepted')
    return dict(field_numeric_cases=count,energy_binding_slots=len(ENERGY),energy_sign_cases=3,current_times=5,zero_crossing_and_negative_current_preserved=True,unknown_energy_refused=True)

@lru_cache(None)
def pointwise_checks():
    cuts,base=arithmetic();c=cuts.make;r=cuts.read
    fs=COVER+[('member','a'),('instant','h[b] c')];slots=fixture('eidn','pointwise')[1]
    f={n:sentinel(s,i+1,cuts) for i,((n,_),(_,s)) in enumerate(zip(fs,slots))}
    f.update(lower=c(0),upper=c(2),members=lambda p:p=='body',member='body',instant=c(1))
    for i,axis in enumerate(('x','y','z')):
        f[axis]=lambda member,i=i:FunctionValue((RS,),RS,lambda time:c(i+1+r(time)+(10 if member=='other' else 0)))
    f['region']=lambda x,y,z,t:tuple(map(r,(x,y,z,t)))==(2,3,4,1)
    assert run('eidn',[f[n] for n,_ in fs],dict(base,eiad=lambda *xs:True),'pointwise')
    for axis in ('x','y','z'):
        g=dict(f);g[axis]=lambda member:FunctionValue((RS,),RS,lambda t:c(20))
        assert not run('eidn',[g[n] for n,_ in fs],dict(base,eiad=lambda *xs:True),'pointwise')
    for member,time,inside in product(('body','other'),(-1,1,3),(False,True)):
        g=dict(f,member=member,instant=c(time),region=lambda *xs:inside)
        assert run('eidn',[g[n] for n,_ in fs],dict(base,eiad=lambda *xs:True),'pointwise')==((member!='body' or time!=1) or inside)
    assert not run('eidn',[f[n] for n,_ in fs],dict(base,eiad=lambda *xs:False),'pointwise')
    # Instantiate the original energy-history body with a varying energy function.
    ef=ENERGY_HISTORY+[('instant','h[b] c')];slots=fixture('eidq','pointwise')[1]
    g={n:sentinel(s,i+1,cuts) for i,((n,_),(_,s)) in enumerate(zip(ef,slots))};g.update(lower=c(0),upper=c(2),energy=lambda t:c(r(t)+1))
    for t in (0,1,2):
        g['instant']=c(t)
        def energy(*xs):return r(xs[-2])==t and r(xs[-1])==t+1
        assert run('eidq',[g[n] for n,_ in ef],dict(base,eisan=energy),'pointwise')
    for name,fields,values in (('eidn',COVER,f),('eidq',ENERGY_HISTORY,g)):
        try:run(name,[values[n] for n,_ in fields],dict(base,eiad=lambda *xs:True,eisan=lambda *xs:True))
        except ValueError as e:assert 'rational number domain' in str(e)
        else:raise AssertionError('Real time domain sampled: '+name)
    return dict(coverage_body_cases=12,coordinate_mutations=3,varying_energy_instants=3,full_real_time_quantification_refused=True,local_instantiations_not_universal_proofs=True)

def discourse_model(bits=(True,True,True),bad=None):
    m=dict(eisaq=lambda:'node',eisaj=lambda:'prior',rd=lambda:'author',eirf=lambda:'paper',ri=lambda:'text',eisak=lambda:'view')
    expected={'eir3':('node','author','paper','eidx','text'),'uf':('author','prior','node','text'),'ue':('prior','node','text')}
    for i,(n,row) in enumerate(expected.items()):
        if bad and bad[0]==n:row=tuple('other' if j==bad[1] else x for j,x in enumerate(row))
        m[n]=lambda *xs,row=row,bit=bits[i]:bit and tuple(symbol(x) if hasattr(x,'syntax') else x for x in xs)==row
    return m

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==210
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,index in zip([PRIOR]+PREVIOUS,(206,207,208)):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[index])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    body=ds['eidt']['body'];assert body['kind']=='implies' and body['arguments'][0]['symbol']=='eidm'
    chosen=[p['name'] for p in ds['eidt']['parameters']];tail=body['arguments'][1];quant=[]
    while tail['kind']=='exists':quant.append(tail['variable']);tail=tail['body']
    assert len(quant)==len(RESULT) and tail['symbol']=='eids' and [a['name'] for a in tail['arguments']]==chosen+quant
    tail=ds['eidu']['body']['body'];count=0
    while tail['kind']=='forall':count+=1;tail=tail['body']
    assert count==len(BASE)-4 and tail['symbol']=='eidt'
    dep={d['name'] for d in extract_document(doc,roots=['eids'],statement_indices=[]).document['declarations']}
    assert 'eica' in dep and 'eicd' not in dep
    assert ds['eidx']['body']['kind']=='message' and ds['eidx']['body']['force']=='assert'
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    count=0
    for path in (CORE,FULL):
        presentation=parse(read(path));presentation['statements']=presentation['statements'][-1:]
        for bits in product((False,True),repeat=3):assert evaluate(presentation,discourse_model(bits))[0]['value']==all(bits);count+=1
        for n,arity in (('eir3',5),('uf',4),('ue',3)):
            for slot in range(arity):assert not evaluate(presentation,discourse_model(bad=(n,slot)))[0]['value'];count+=1
    source=deepcopy(doc);source['statements']=[]
    view=parse(format_graph(source,'compact')+'q[t[k eidw[]][k ri[]]].')
    for usual,account in product((False,True),repeat=2):
        m=discourse_model();m.update(eisah=lambda v,p,r:usual and (v,p,r)==('view','paper','text'),eisai=lambda v,d,r:account and (v,symbol(d),r)==('view','eidv','text'))
        # Content construction is evaluated at all points, so return false off text.
        assert evaluate(view,m)[0]['value']==(usual and account)
    closure=parse(format_graph(source,'compact')+'q[t[k eidv[]][k ri[]]].');m=discourse_model();m.update(eisaa=lambda:'body',eisab=lambda:'other',eisac=lambda:'body')
    try:evaluate(closure,m,individuals=('body','other'))
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Full case domain sampled')
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003');reading=json.loads(read(READING))
    validate_hashes(ROOT,reading['source_sha256']);assert unit['text'][550:770]==reading['source'] and reading['selection']==selection_binding(new,[INDEX])
    return dict(new_definitions=13,new_primitives=6,preserved_statements=209,existential_result_slots=len(RESULT),universal_case_slots=len(BASE)-4,presentation_cases=count,usual_view_cases=4,quoted_physics_not_executed=True,source_range=[550,770],prior_reviews_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_moving_magnet_case import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

def build_report():
    results=dict(binding=binding_checks(),local=local_checks(),pointwise=pointwise_checks(),structure=structure_checks())
    unit=next(u for u in json.loads(read(INVENTORY))['units'] if u['id']=='einstein-1905:u0003')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,READING,PRIOR,*PREVIOUS,INVENTORY,
        'scripts/compose_moving_magnet_case.py','scripts/check_moving_magnet_case.py','scripts/review_moving_magnet_case.py','tests/test_moving_magnet_case.py',
        'scripts/compose_interaction_example.py','scripts/compose_material_body_motion.py','scripts/compose_current_distribution.py','scripts/compose_electric_response.py','scripts/compose_field_equations.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py',
        'scripts/check_conductor_cases.py','scripts/check_material_relative_frame.py','scripts/check_coordinate_correspondence.py','scripts/check_tau_differential.py'}
    return dict(status='moving_magnet_case_content_and_presentation_checked',document=FULL,**results,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[550,770],source=unit['text'][550:770],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
