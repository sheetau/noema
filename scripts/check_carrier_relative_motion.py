"""Check carrier/host separation, native projections and force-event binding."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import NUM,RS,FS,BASE,IDENTITY,rotate,axes
from scripts.check_electric_action import setup as electric_setup
from scripts.compose_carrier_relative_motion import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,FIELDS,INSTANT,WITNESS,ACTION,HISTORY,build

DOC='docs/carrier-relative-motion-v1.md';PRIOR='data/einstein-author-credit-review-v1.json';SOURCE='data/einstein-opening-obligations-v1.json'
DOMAIN=('body','carrier','o','g','h','s','frame','event','lengthunit','timeunit','chargerecord','forcerecord','chargeunit','fieldunit','forceunit','chargekind','forcekind','x','y','z','t','other')

def forbidden(*args):raise ValueError('Unknown carrier-motion input')

@lru_cache(None)
def fixture(symbol,force_boundary=False):
    doc=parse(read(CORE));doc['statements']=[]
    boundaries={'eiaq','se'}|({'eibv'} if symbol in ('eibw','eibx') else set())|({'eibs'} if force_boundary else set())
    abstract(doc,NUM|boundaries)
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jcrm'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots

def run(symbol,values,model,force_boundary=False):
    doc,slots=fixture(symbol,force_boundary);assert len(slots)==len(values);model=dict(model)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={n:model.get(n,forbidden) for n in names},
        max_steps=600000,memoize_definitions=False,memoize_expressions=False)[0]['value']

def same(x,y,sort,cuts):
    if isinstance(sort,str):return x==y
    if sort==RS:return cuts.read(x)==cuts.read(y)
    domains=[DOMAIN if s=='individual' else ('case','other') if s=='situation' else [cuts.make(t) for t in (0,2,4,8)] for s in sort['parameters']]
    return all(same(x(*ps),y(*ps),sort['result'],cuts) for ps in product(*domains))

@lru_cache(None)
def sorts(symbol):return [p['sort'] for p in next(d for d in parse(read(CORE))['declarations'] if d['name']==symbol)['parameters']]

def setup(scenario='relative'):
    cuts,model,electric=electric_setup();r=cuts.read;c=cuts.make
    def transform(p,t):
        if scenario=='common_translation':return tuple(x+d*t for x,d in zip(p,(1,-2,3)))
        if scenario in ('common_rotation','rotating_relative'):return rotate(p,t/8)
        return p
    def local(t):
        shift=t/4-1 if scenario in ('relative','rotating_relative') else t*(8-t)/16 if scenario=='return' else Q(0)
        return (1+shift,Q(2),Q(3))
    def family(host,i):
        return FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,
            lambda t:c(transform(tuple(map(Q,BASE.get(p,(0,0,0)))) if host else local(r(t)) if p=='carrier' else (Q(99),)*3,r(t))[i])))
    basis=lambda t:axes(t/8) if scenario in ('common_rotation','rotating_relative') else IDENTITY
    f=dict(electric,body='body',lengthunit='lengthunit',timeunit='timeunit',lower=c(0),upper=c(8),
        members=lambda p:p in ('o','g','h','s'),origin='o',guide='g',plane='h',first=c(0),second=c(8),time=c(4),actiontime=c(4))
    for i,a in enumerate(('x','y','z')):f[a]=family(True,i);f['carrier'+a]=family(False,i)
    for i,p in enumerate(('u','v','w')):
        for j,a in enumerate(('x','y','z')):f[p+a]=FunctionValue((RS,),RS,lambda t,i=i,j=j:c(basis(r(t))[i][j]))
    expected=[f[n] for n,_ in FIELDS]
    def bound(xs,ys,types):return len(xs)==len(ys) and all(same(x,y,t,cuts) for x,y,t in zip(xs,ys,types))
    model['eiaq']=lambda *xs:bound(xs,[f[n] for n,_ in HISTORY],sorts('eiaq'))
    trajectory=[f[n] for n in ('carrier','frame','context','lengthunit','timeunit','lower','upper')]+[f['carrier'+a]('carrier') for a in ('x','y','z')]
    model['se']=lambda *xs:bound(xs,trajectory,sorts('se'))
    model['eibv']=lambda *xs:bound(xs,expected,sorts('eibv'))
    def occupied(body,frame,ctx,length,timeunit,x,y,z,t):
        # Physical domain in this fixture: a material-filled prism, boundary included.
        if (body,frame,ctx,length,timeunit)!=('body','frame','case','lengthunit','timeunit'):return False
        point=(r(x),r(y),r(z));time=r(t)
        if scenario=='common_translation':point=tuple(x-d*time for x,d in zip(point,(1,-2,3)))
        if scenario in ('common_rotation','rotating_relative'):point=rotate(point,-time/8)
        return all(lo<=x<=hi for x,lo,hi in zip(point,(0,0,0),(3,4,4)))
    model['eiro']=occupied
    model['zzbv']=lambda carrier,event,ctx:(carrier,event,ctx)==('carrier','event','case')
    def coordinates(event,frame,ctx,length,timeunit,t,x,y,z):
        return (event,frame,ctx,length,timeunit)==('event','frame','case','lengthunit','timeunit') and r(t)==4 and (r(x),r(y),r(z))==transform(local(Q(4)),Q(4))
    model['zzbu']=coordinates
    return cuts,model,f

def values(f,fields):return [f[n] for n,_ in fields]

@lru_cache(None)
def history_checks():
    cuts,model,f=setup();assert run('eibt',values(f,FIELDS),model)
    # Host material points deliberately exclude the carrier.
    assert not f['members']('carrier')
    for n in ('eiaq','se'):
        assert not run('eibt',values(f,FIELDS),dict(model,**{n:lambda *xs:False}))
    assert not run('eibt',values(dict(f,carrier='body'),FIELDS),model)
    for n in ('eiaq','se','eiro'):
        try:run('eibu',values(f,INSTANT),dict(model,**{n:forbidden}))
        except ValueError as e:assert 'Unknown carrier-motion' in str(e)
        else:raise AssertionError(n)
    count=0
    for t in (-4,-1,0,2,4,8,9,12):
        f['time']=cuts.make(t);assert run('eibu',values(f,INSTANT),model)==(0<=t<=8);count+=1
    assert not run('eibu',values(dict(f,time=cuts.make(4)),INSTANT),dict(model,eiro=lambda *xs:False))
    # Full time quantification remains native, and must not be sampled.
    try:run('eibv',values(f,FIELDS),model)
    except ValueError as e:assert 'rational number domain' in str(e)
    else:raise AssertionError('Full real interval sampled')
    return dict(instant_cases=count,carrier_excluded_from_host_members=True,missing_and_unknown_history_rejected=True,
        full_interval_refused=True,history_boundaries=['eiaq','se'])

@lru_cache(None)
def motion_checks():
    count=0
    for scenario in ('static','common_translation','common_rotation','relative','rotating_relative','return'):
        cuts,model,f=setup(scenario)
        for first,second in product((-1,0,2,4,8,9),repeat=2):
            f.update(first=cuts.make(first),second=cuts.make(second))
            expected=0<=first<second<=8 and (scenario in ('relative','rotating_relative') or scenario=='return' and first*(8-first)!=second*(8-second))
            assert run('eibw',values(f,WITNESS),model)==expected,(scenario,first,second);count+=1
    cuts,model,f=setup()
    assert not run('eibw',values(f,WITNESS),dict(model,eibv=lambda *xs:False))
    return dict(witness_cases=count,common_translation_and_rotation_rejected=True,return_midcourse_detected=True,
        native_projection_and_difference=True,full_containment_boundary='eibv')

def changed_value(n,t,value,cuts):
    if t in ('a','d'):return 'other'
    if t=='b':return Q(2)
    if t=='h[b] c':return cuts.make(cuts.read(value)+1)
    if n=='members':return lambda p:False
    if n in ('x','y','z','carrierx','carriery','carrierz'):return FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,lambda t:cuts.make(99)))
    if n in ('electricfield','magneticfield'):return lambda a:FunctionValue(tuple([RS]*4),RS,lambda *xs:cuts.make(99))
    if n=='region':return lambda *xs:False
    return lambda *xs:cuts.make(99)

@lru_cache(None)
def binding_checks():
    cuts,model,f=setup();assert run('eibx',values(f,ACTION),model)
    for n,t in ACTION:
        changed=dict(f);changed[n]=changed_value(n,t,f[n],cuts)
        # Ordered witness times need an invalid or coincident value, not a still-valid interior time.
        if n in ('first','second'):changed[n]=cuts.make(10)
        assert not run('eibx',values(changed,ACTION),model),n
    for n in ('zzbu','zzbv','eibv','eirl'):
        assert not run('eibx',values(f,ACTION),dict(model,**{n:lambda *xs:False})),n
    # Accept the electric-action subformula explicitly to isolate the event/coordinate bridge.
    permissive=dict(model,eibs=lambda *xs:True)
    assert run('eibx',values(f,ACTION),permissive,True)
    for axis in ('x','y','z','t'):
        changed=dict(f,point=lambda a:cuts.make(cuts.read(f['point'](a))+(a==axis)))
        assert not run('eibx',values(changed,ACTION),permissive,True),axis
    assert not run('eibx',values(dict(f,charge=cuts.make(0)),ACTION),permissive,True)
    assert run('eibx',values(dict(f,charge=cuts.make(2)),ACTION),permissive,True)
    return dict(argument_mutations=len(ACTION),missing_connections=4,coordinate_bridge_mutations=4,
        native_sb_and_electric_action=True,zero_charge_rejected=True,both_charge_signs_supported=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=5,new_primitives=1,preserved_statements=207,author_review_preserved=True,core_roundtrips=['compact','full','v2'])

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

def build_report():
    results=dict(history=history_checks(),motion=motion_checks(),binding=binding_checks(),structure=structure_checks())
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,PRIOR,SOURCE,
        'scripts/compose_carrier_relative_motion.py','scripts/check_carrier_relative_motion.py','scripts/compose_limits.py',
        'scripts/compose_material_relative_frame.py','scripts/compose_electric_action.py','scripts/compose_field_equations.py',
        'scripts/check_material_relative_frame.py','scripts/check_electric_action.py','scripts/check_tau_differential.py',
        'scripts/check_coordinate_correspondence.py','tests/test_carrier_relative_motion.py'}
    return dict(status='carrier_relative_motion_dependency_checked',document=FULL,**results,
        causal_response_or_conductor_classification_proved=False,source_text_coverage_added=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
