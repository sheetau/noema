"""Check calibrated transverse trials, shared backgrounds, and physical responses."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_kinetic_energy_consequences as prior
from scripts.check_electron_transformed_dynamics import Model,Rational,fn,sort
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_deflection_response import *

DOC='docs/electron-deflection-response-v1.md';SOURCE='data/einstein-electron-deflection-response-obligations-v1.json'
INVENTORY=prior.INVENTORY;FACSIMILE=prior.FACSIMILE
DEPENDENCIES=('reports/kinetic-energy-consequences-v1.json','reports/deflection-ratio-v1.json','reports/electron-transformed-dynamics-v1.json','reports/magnetic-action-v1.json','reports/point-particle-dynamics-v1.json')
CONSTANTS=prior.CONSTANTS
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*[n for n,t in CASE+BACKGROUND+WITNESSES if t=='a']]))
SCENES=('case','other','electriccase','magneticcase','combinedcase')
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk;scalarize=prior.scalarize
BOUNDS={'eqh':{'ejsn','ek3n','ek3o','ek3u','ek3q','eibs','eico'},'eqi':{'eqh'},'eqj':{'eqi'},'eqk':{'eqj','eqi'},'eql':{'eqk'},'eqm':{'eqj'},'eqn':{'eqm'},'eqo':{'eqm'},'eqp':{'eqm'},'eqq':{'eqm'},'eqr':{'eqp'},'sepp':{'seob','senz','sjs','sepn'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='boundary'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=prior.prior.physical.NUM|BOUNDS.get(root,set())
    if mode=='native':cuts=cuts-{'seob','senz','sjs','sepn'}
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if root=='eqq' and mode=='instance':
        d=next(d for d in doc['declarations'] if d['name']==root);node=d['body']
        for _ in WITNESSES:d['parameters'].append(dict(name=node['variable'],sort=node['sort']));node=node['body']
        d['body']=node
    return doc
@lru_cache(None)
def fixture(root,mode='boundary'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jdfarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jdfprobe',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jdfprobe',arguments=[expr])
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='boundary'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=SCENES,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(speed=3,charge=-3,Y=3,N=5):
    a=Model(speed,0,0,0);c,r=a.c,a.r
    for n,t in SHARED:
        if n not in a.by:a.by[n]=n if t=='a' else Q(1) if t=='b' else c(0)
    a.by.update(light=c(5),speed=c(speed),charge=c(charge),mass=c(2),view='view',context='other',electricstrength=c(Y),magneticstrength=c(N),scene='case',location=a.point((0,0,0,0)),electricrecord='electricrecord',magneticrecord='magneticrecord')
    a.m['bc']=lambda x,y:r(x)<=r(y);a.m['ad']=lambda x,y:x*y
    def trace(y,n,scene):
        beta=Q(1) if speed==0 else Q(5,4);ay=Q(charge)*(Q(y)-Q(speed)*Q(n)/5)/(2*beta)
        polynomials=[Rational((0,speed)),Rational((0,0,ay/2)),Rational((0,)),Rational((0,1))]
        return dict(event='event',scene=scene,domain=a.register_domain(-1,1),curve=a.register_curve(polynomials),location=a.point((0,0,0,0)),**{name:a.register_function(p.derivative()) for (name,t),p in zip(PROFILES,polynomials)},ax=c(0),ay=c(ay),az=c(0),electricfield=a.field(lambda ax,p:Q(y) if ax=='y' else 0),magneticfield=a.field(lambda ax,p:Q(n) if ax=='z' else 0),region=fn(sort(REGION),lambda *xs:True),chargerecord='chargerecord',electricrecord='electricrecord',magneticrecord='magneticrecord')
    a.by.update(trace(Y,N,'case'));a.by['point']=a.by['location']
    for pre,y,n in [('electric',Y,0),('magnetic',0,N),('combined',Y,N)]:a.by.update({pre+k:v for k,v in trace(y,n,pre+'case').items()})
    a.by.update(electricresponse=c(abs(Q(charge))/(2*a.beta)),magneticresponse=c(abs(Q(charge))*Q(speed)/(10*a.beta)))
    return a
def keyed(a,rows):return {n:lambda *xs,row=row:a.key(xs)==a.key(row) for n,row in rows.items()}
def expected_case(a,pre,y,n):return [a.c(y) if name=='electricstrength' else a.c(n) if name=='magneticstrength' else a.by[pre+name] if name in dict(TRACE) else a.by[name] for name,t in CASE]

@lru_cache(None)
def numeric_checks():
    cases=0
    for speed in (0,3):
        for charge in (-3,3):
            for Y,N in ((1,1),(3,5),(7,2)):
                a=model(speed,charge,Y,N);c,r=a.c,a.r
                assert run('eqi',a.values(CASE),a.m|{'eqh':lambda *xs:True});cases+=1
                bad=a.values(CASE);bad[[n for n,t in CASE].index('ay')]=c(r(a.by['ay'])+1)
                assert not run('eqi',bad,a.m|{'eqh':lambda *xs:True});cases+=1
                values=a.values(RESPONSE);mm=a.m|{'eqj':lambda *xs:True}
                assert run('eqm',values,mm);assert run('eqn',values,a.m|{'eqm':lambda *xs:True});assert run('eqo',values,a.m|{'eqm':lambda *xs:True});cases+=3
                for name in ('electricresponse','magneticresponse','electricay','magneticay'):
                    bad=values.copy();pos=[n for n,t in RESPONSE].index(name);bad[pos]=c(r(bad[pos])+1)
                    assert not run('eqm',bad,mm);cases+=1
                assert run('eqp',values+[c(speed)],a.m|{'eqm':lambda *xs:True});assert not run('eqp',values+[c(speed+1)],a.m|{'eqm':lambda *xs:True});cases+=2
    for speed,Y,N in ((3,3,5),(0,0,5),(3,0,0)):
        a=model(speed,-3,Y,N);mm=a.m|{'eqk':lambda *xs:True};assert run('eql',a.values(TRIPLE),mm);cases+=1
        for name in ('electricay','magneticay','combineday'):
            bad=a.values(TRIPLE);pos=[n for n,t in TRIPLE].index(name);bad[pos]=a.c(a.r(bad[pos])+1)
            assert not run('eql',bad,mm);cases+=1
    a=model();vs=a.values(RESPONSE);mm=a.m|{'eqj':lambda *xs:True}
    for name in ('electricstrength','magneticstrength','electricresponse'):
        bad=vs.copy();bad[[n for n,t in RESPONSE].index(name)]=a.c(0);assert not run('eqm',bad,mm);cases+=1
    return dict(cases=cases,signed_charge_and_zero_speed=True,unequal_positive_field_strengths_normalized=True,opposite_equal_acceleration_and_zero_combined=True,actual_speed_recovered_without_free_gain=True)

@lru_cache(None)
def physical_checks():
    a=model();by=a.by;c=a.c;ctx=by['scene'];V=by['light'];q=by['charge'];Y=by['electricstrength'];N=by['magneticstrength'];speed=by['speed'];vec=a.point
    values=by|dict(context=ctx,point=by['location'],carrier=by['matter'],electricconversion=c(1),magneticconversion=c(Q(1,5)))
    ea=values|dict(forcerecord=by['electricrecord'],fieldunit=by['electricunit'],electric=vec((0,a.r(Y),0,0)),force=vec((0,a.r(q)*a.r(Y),0,0)),conversion=c(1))
    ma=values|dict(forcerecord=by['magneticrecord'],magnetic=vec((0,0,a.r(N),0)),velocity=vec((a.r(speed),0,0,0)),force=vec((0,-a.r(q)*a.r(speed)*a.r(N)/5,0,0)),conversion=c(Q(1,5)))
    rows={symbol:[values[n] for n,t in fields] for symbol,fields in [('ejsn',FIELDS),('ek3n',UNITS),('ek3o',MASS),('ek3u',CHARGE),('ek3q',KINEMATIC)]}
    rows|={'eibs':[ea[n] for n,t in ELECTRIC],'eico':[ma[n] for n,t in MAGNETIC],'eisqd':[by['matter'],by['frame'],by['event'],by['lengthunit'],by['timeunit'],by['location'],ctx]}
    mm=a.m|keyed(a,rows);vs=a.values(CASE);assert run('eqh',vs,mm);cases=1
    for symbol in rows:
        assert not run('eqh',vs,mm|{symbol:lambda *xs:False});reject(lambda:run('eqh',vs,mm|{symbol:forbidden}));cases+=2
    for n,t in CASE:
        if t in ('a','d','b'):
            bad=vs.copy();bad[[x for x,ty in CASE].index(n)]='other' if t=='d' else 'a' if t=='a' else by[n]+1
            assert not run('eqh',bad,mm);cases+=1
    for field in ('electricfield','magneticfield'):
        old=by[field]
        for axis in ('x','y','z'):
            bad=vs.copy();bad[[n for n,t in CASE].index(field)]=a.field(lambda ax,p:a.r(old(ax)(*map(c,p)))+(ax==axis))
            assert not run('eqh',bad,mm|{'ejsn':lambda *xs:True,'eibs':lambda *xs:True,'eico':lambda *xs:True});cases+=1
    # Execute the actual derivative composition with retained rational histories.
    from scripts.compose_material_acceleration import AT
    actual=by|dict(context='case',point=by['location']);actual_values=[actual[n] for n,t in AT]
    assert run('sepp',actual_values,a.m);cases+=1
    for n,t in ACCEL:
        bad=actual_values.copy();bad[[x for x,ty in AT].index(n)]=c(a.r(by[n])+1)
        assert not run('sepp',bad,a.m);cases+=1
    reject(lambda:run('sepp',actual_values,a.m,'native'));cases+=1
    assert 'setk' not in {d['name'] for d in boundary('eqh')['declarations']};cases+=1
    return dict(cases=cases,physical_roles_and_both_force_signs=True,all_field_components_and_units=True,actual_second_derivatives_checked_separately=True,equation_not_hidden_in_physical_setup=True)

@lru_cache(None)
def shared_checks():
    a=model();r=a.r;rows=[a.key(expected_case(a,pre,y,n)) for pre,y,n in [('electric',3,0),('magnetic',0,5)]]
    allowed=lambda view,source,target:(view,source,target) in {('view','other','electriccase'),('view','other','magneticcase'),('view','other','combinedcase')}
    mm=a.m|{'eqi':lambda *xs:a.key(xs) in rows,'eisoe':allowed};vs=a.values(PAIR);assert run('eqj',vs,mm);cases=1
    for n,t in BACKGROUND+STRENGTHS:
        bad=vs.copy();pos=[x for x,ty in PAIR].index(n);bad[pos]='case' if t=='d' else 'a' if t=='a' else bad[pos]+1 if t=='b' else a.c(r(bad[pos])+1)
        assert not run('eqj',bad,mm);cases+=1
    for name in ('electriccurve','magneticcurve','electricevent','magneticevent','electricscene','magneticscene'):
        bad=vs.copy();pos=[n for n,t in PAIR].index(name);bad[pos]=a.by['combinedcurve'] if name.endswith('curve') else 'case' if name.endswith('scene') else 'a'
        assert not run('eqj',bad,mm);cases+=1
    for symbol in ('eqi','eisoe'):reject(lambda:run('eqj',vs,mm|{symbol:forbidden}));cases+=1
    row=a.key(expected_case(a,'combined',3,5));mm=a.m|{'eqj':lambda *xs:a.key(xs)==a.key(vs),'eqi':lambda *xs:a.key(xs)==row,'eisoe':allowed}
    assert run('eqk',a.values(TRIPLE),mm);cases+=1
    bad=a.values(TRIPLE);bad[[n for n,t in TRIPLE].index('combinedscene')]='other';assert not run('eqk',bad,mm);cases+=1
    # An observed response and a possible pair do not assert measurement or a true ratio by fiat.
    row=a.key(a.values(RESPONSE));mm=a.m|{'eqm':lambda *xs:a.key(xs)==row}
    assert run('eqq',a.values(POSSIBLE+WITNESSES),mm,'instance');cases+=1
    reject(lambda:run('eqq',a.values(POSSIBLE),mm));cases+=1
    return dict(cases=cases,shared_particle_speed_mass_charge_units=True,distinct_allowed_trials_and_complete_traces=True,possible_pair_not_actual_readout_or_all_speed_availability=True)

@lru_cache(None)
def binding_checks():
    doc=boundary('eqq');d=next(d for d in doc['declarations'] if d['name']=='eqq');names={n:dict(kind='variable',name=p['name']) for (n,t),p in zip(POSSIBLE,d['parameters'])};node=d['body']
    for n,t in WITNESSES:assert node['kind']=='exists';names[n]=dict(kind='variable',name=node['variable']);node=node['body']
    assert node['arguments']==[names[n] for n,t in RESPONSE];cases=1
    # Instantiate all other witnesses; vary each remaining binder over two values.
    compact=collapse(scalarize(doc))
    for pivot,(field,typ) in enumerate(WITNESSES):
        f,dd,slots,name,body=lifted(compact,'eqq',pivot,len(WITNESSES),'exists');env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']};special='other' if typ=='d' else 'b';row=tuple((env|{name:special})[x['name']] for x in body['arguments'])
        for permitted in (False,True):
            mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}|{'eqm':lambda *xs:permitted and xs==row}
            assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=30000)[0]['value']==permitted;cases+=1
    # Both physical cases reuse exactly the same public background arguments.
    d=next(d for d in core()['declarations'] if d['name']=='eqj');names={n:p['name'] for (n,t),p in zip(PAIR,d['parameters'])}
    calls=[x for x in walk(d['body']) if x.get('kind')=='call' and x.get('symbol')=='eqi'];assert len(calls)==2
    for call in calls:assert call['arguments'][:len(SHARED)]==[dict(kind='variable',name=names[n]) for n,t in SHARED];cases+=1
    return dict(cases=cases,all_34_witness_slots_diagnosed_with_two_values=True,same_background_outside_each_trial=True)

@lru_cache(None)
def source_record():
    d=json.loads(read(INVENTORY));units=d['units'][264:268]
    return dict(version='einstein-electron-deflection-response-obligations-v1',units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256']) for u in units],facsimile_pages=[920],meaning_review_complete=False,scope=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==432 and after.document['statements']==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[430,431])==selection_binding(before,[430,431]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,new_statements=0,all_432_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numerical',numeric_checks),('physical',physical_checks),('shared',shared_checks),('bindings',binding_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_deflection_response.py','scripts/check_electron_deflection_response.py','tests/test_electron_deflection_response.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='same_electron_transverse_trials_and_response_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
