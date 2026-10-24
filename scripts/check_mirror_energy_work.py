"""Check moving-surface flux, pointwise averages and same-patch mechanical work."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_conductor_cases import sentinel
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_light_energy_ratio import arithmetic
from scripts.check_reflected_light_inquiry import normalize
from scripts.check_reflected_return_quantities import setting as previous_setting
from scripts.check_wave_cycle_frequency import refused
from scripts.compose_mirror_energy_work import *

DOC='docs/mirror-energy-work-v1.md'
DEPENDENCIES=('reports/reflected-return-quantities-v1.json','reports/reflected-light-inquiry-v1.json','reports/radiative-density-v1.json','reports/mirror-surface-pressure-v1.json')
CONSTANTS={'ra':'K','zbm':'k','yn':'x','yo':'y','yp':'z','zc7':'time','ri':'case','eisrx':'section7','eistk':'section8','ta':'length','rb':'duration'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in SETTING if t=='a'],'other','a','b']))
BOUNDARIES={'ektq':{'sede'},'ektr':{'ektq'},'ekts':{'eks3','ekrt','ekk2','ekkb','ekkz'},'ektu':{'sede'},'ektx':{'ekts','ektr','ekq3','ektu'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDARIES.get(name,set()))
    return extract_document(doc,roots=[name],statement_indices=[]).document

@lru_cache(None)
def fixture(name,mode='native'):
    doc=deepcopy(boundary(name));d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        assert name=='ektr';body=d['body']
        # Walk the right-associated conjunction to the all-y/all-z condition.
        while body['kind']=='and':body=body['arguments'][1]
        target=body
        for variable in ('y','z'):
            assert body['kind']=='forall'
            d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        target.clear();target.update(body)
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jmew'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jmewcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jmewcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native'):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jmewcapture']=capture
    result=evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def scalar(cuts,fn):return FunctionValue((RS,)*4,RS,lambda *xs:cuts.make(fn(*map(cuts.read,xs))))
def timefn(cuts,fn):return FunctionValue((RS,),RS,lambda t:cuts.make(fn(cuts.read(t))))

def setting(cuts):
    c=cuts.make;_,by=previous_setting(cuts)
    by.update({n:c(x) for n,x in dict(incoming=35,outgoing=Q(35,4),pressure=6,work=18).items()})
    return [by[n] for n,t in TOTAL],by

def mutate(values,i,fields,slots,cuts):
    n,t=fields[i];sort=slots[i][1];bad=values[:]
    bad[i]=cuts.make(4) if n=='speed' else cuts.make(Q(15,4)) if n=='light' else cuts.make(cuts.read(bad[i])+Q(1,7)) if t==R else not bad[i] if t=='c' else sentinel(sort,100+i,cuts)
    return bad

@lru_cache(None)
def transport_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    sine=timefn(cuts,lambda t:1+2*t)
    for speed,normal in product((-3,0,3),((Q(1),Q(0),Q(0)),(Q(1,3),Q(2,3),Q(2,3)))):
        a,b,z=normal;E=(2*b+3*z,-2*a,-3*a);H=(b*E[2]-z*E[1],z*E[0]-a*E[2],a*E[1]-b*E[0]);phase=scalar(cuts,lambda x,y,z,t:2*(t-(a*x+b*y+normal[2]*z)/5))
        row=dict(zip((n for n,t in MOVING),[*map(c,(2,5,*E,*H)),sine,phase,c(speed)]));relative=run('ekto',[row[n] for n,t in MOVING],m)
        sx=2*(E[1]*H[2]-E[2]*H[1]);rho=Q(1,5)*(sum(x*x for x in E)+sum(x*x for x in H))
        for point in ((0,0,0,0),(1,2,-3,Q(1,2)),(-2,3,1,-1)):
            x,y,z,t=map(Q,point);p=2*(t-sum(a*b for a,b in zip(normal,(x,y,z)))/5)
            assert r(relative(*map(c,point)))==(sx-speed*rho)*(1+2*p)**2;cases+=1
        trace=run('ektp',[relative,c(speed),c(2),c(-3)],m)
        for t in (-1,0,Q(1,2),2):assert r(trace(c(t)))==r(relative(c(speed*t),c(2),c(-3),c(t)));cases+=1
    # A returning ray may still move +x in K; only its speed relative to the
    # moving mirror determines the outward sign.
    n=(Q(1,3),Q(2,3),Q(2,3));E=(4,-1,-1);H=(0,3,-3);phase=scalar(cuts,lambda *xs:0)
    assert sum(a*b for a,b in zip(n,E))==0 and sum(x*x for x in E)==sum(x*x for x in H)
    relative=run('ekto',list(map(c,(2,5,*E,*H)))+[timefn(cuts,lambda t:1),phase,c(3)],m)
    assert r(relative(*map(c,(0,0,0,0))))<0;cases+=1
    badphase=FunctionValue((RS,)*4,RS,forbidden)
    refused_unknown=False
    try:run('ekto',list(map(c,(2,5,*E,*H)))+[sine,badphase,c(3)],m)(*map(c,(0,0,0,0)))
    except ValueError as exc:assert 'Unknown' in str(exc);refused_unknown=True
    assert refused_unknown;cases+=1
    return dict(cases=cases,relative_flux_not_stationary_Jx=True,same_four_coordinates_and_mirror_trace=True,positive_K_direction_can_leave_mirror=True)

@lru_cache(None)
def integral_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    flux=scalar(cuts,lambda x,y,z,t:2*x+3*y+5*z+7*t)
    for speed,y,z,lo,hi in product((-3,0,3),(-2,1),(0,3),(-1,),(2,)):
        slope=2*speed+7;offset=3*y+5*z;mean=slope*(lo+hi)/2+offset
        def integral(a,b,fn,value):return (r(a),r(b),r(value))==(lo,hi,Q(hi-lo)*Q(mean)) and all(r(fn(c(t)))==slope*t+offset for t in (-2,0,1,3))
        values=[flux,*map(c,(speed,y,z,lo,hi,Q(mean)))];mm=m|{'sede':integral}
        assert run('ektq',values,mm);cases+=1
        for i in range(len(values)):assert not run('ektq',mutate(values,i,MEAN,fixture('ektq')[1],cuts),mm),i;cases+=1
        unknowns(lambda model:run('ektq',values,model),mm,('sede',))
    # Work is signed and remains zero at zero velocity even with nonzero force.
    PS=dict(kind='function',parameters=['individual'],result=RS)
    force=FunctionValue((RS,),PS,lambda t:FunctionValue(('individual',),RS,lambda a:c(6+2*r(t) if a=='x' else 17 if a=='y' else -4)))
    lo,hi=Q(-1),Q(2);area=Q(8);meanforce=Q(7)
    for speed in (-3,0,3):
        work=Q(speed)*meanforce/area;values=[force,*map(c,(speed,lo,hi,-1,1,-2,2,work))]
        def integral(a,b,fn,value):return (r(a),r(b),r(value))==(lo,hi,Q(speed)*meanforce*(hi-lo)) and all(r(fn(c(t)))==speed*(6+2*t) for t in (-2,0,1,3))
        mm=m|{'sede':integral};assert run('ektu',values,mm);cases+=1
        for i in range(len(values)):
            if speed==0 and i in (0,4,5,6,7):continue # zero work legitimately loses those numerical dependencies
            assert not run('ektu',mutate(values,i,WORK,fixture('ektu')[1],cuts),mm),i;cases+=1
        unknowns(lambda model:run('ektu',values,model),mm,('sede',))
        assert run('ekt2',list(map(c,(meanforce/area,speed,work))),m);cases+=1
    for P in (0,7,31):assert run('ekt2',list(map(c,(P,0,0))),m);cases+=1
    return dict(cases=cases,same_interval_trace_and_normalization=True,mechanical_work_signed_and_zero_speed_safe=True,tangential_force_not_forced_to_zero=True)

@lru_cache(None)
def coverage_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0;flux=scalar(cuts,lambda x,y,z,t:2*x+3*y+5*z+7*t)
    values=[flux,*map(c,(3,-1,1,-2,2,-1,2,7))];norm=normalize(cuts)
    for y,z in ((0,0),(-1,-2),(1,2),(Q(1,3),Q(4,3)),(2,0),(0,3)):
        expected=norm([flux,*map(c,(3,y,z,-1,2,7))]);inside=-1<=y<=1 and -2<=z<=2
        mm=m|{'ektq':lambda *xs:norm(xs)==expected}
        assert run('ektr',values+list(map(c,(y,z))),mm,'instance');cases+=1
        assert run('ektr',values+list(map(c,(y,z))),mm|{'ektq':lambda *xs:False},'instance')==(not inside);cases+=1
    for lo,hi in ((2,3),(4,5),(6,7)):
        bad=values[:];bad[hi]=bad[lo];assert not run('ektr',bad+list(map(c,(0,0))),m|{'ektq':lambda *xs:True},'instance');cases+=1
    refused(lambda:run('ektr',values,m|{'ektq':lambda *xs:True}));cases+=1
    unknowns(lambda mm:run('ektr',values+list(map(c,(0,0))),mm,'instance'),m|{'ektq':lambda *xs:True},('ektq',))
    return dict(cases=cases,all_real_tangential_positions_retained=True,edge_interior_and_outside_distinguished=True,zero_area_and_duration_rejected=True)

@lru_cache(None)
def binding_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;values,by=setting(cuts);norm=normalize(cuts);cases=0
    def inside_k(x,y,z,t):return abs(Q(5,4)*(x+3*t))<=10 and abs(y)<=9 and abs(z)<=8 and -4<=Q(5,4)*(t+Q(3,25)*x)<=4 and -1<=t<=1
    region=FunctionValue((RS,)*4,'truth',lambda *xs:inside_k(Q(5,4)*(r(xs[0])-3*r(xs[3])),r(xs[1]),r(xs[2]),Q(5,4)*(r(xs[3])-Q(3,25)*r(xs[0]))) and r(xs[0])<=3*r(xs[3]))
    shared=by|dict(frame='K',scope='section8',coefficient=by['labcoefficient'],region=region)
    modelrows=[]
    for wave,process,w,normal,coefs in [('wave','process',2,1,(0,3,4,0,-4,3)),('reflectedwave','reflectedprocess',Q(1,2),-1,(0,Q(-3,4),-1,0,-1,Q(3,4)))]:
        phase=scalar(cuts,lambda x,y,z,t,w=w,normal=normal:w*(t-normal*x/5))
        modelrows.append(shared|dict(wave=by[wave],process=by[process],phase=phase,**{n:c(x) for n,x in zip(('ex','ey','ez','hx','hy','hz'),coefs)}))
    rows={'eks3':[norm([by[n] for n,t in QUANTITIES])],'ekrt':[norm([by[n] for n,t in FORCE_SETTING])],'ekk2':[norm([by['labcoefficient'],by['light'],by['pi']])],
          'ekkb':[norm([row[n] for n,t in MODEL]) for row in modelrows],'ekkz':[norm([row[n] for n,t in DENSITY_MODEL]) for row in modelrows]}
    constants=m|{'eisls':lambda *xs:c(-1),'eislt':lambda *xs:c(1)}
    mm=constants|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    base=[by[n] for n,t in SETTING];assert run('ekts',base,mm);cases+=1
    for i in range(len(base)):assert not run('ekts',mutate(base,i,SETTING,fixture('ekts')[1],cuts),mm),SETTING[i];cases+=1
    for n,rs in rows.items():
        for removed in rs:
            rest=[row for row in rs if row!=removed];assert not run('ekts',base,mm|{n:lambda *xs,rest=rest:norm(xs) in rest});cases+=1
    unknowns(lambda model:run('ekts',base,model),mm,tuple(rows))
    # Assemble the same interval and patch into both flow averages, pressure and work.
    inc=scalar(cuts,lambda x,y,z,t:20*(1+2*(t-x/5))**2);out=scalar(cuts,lambda x,y,z,t:5*(1+Q(1,2)*(t+x/5))**2)
    lo,hi=c(Q(-5,8)),c(Q(5,4));force=by|dict(lower=lo,upper=hi)
    rows={'ekts':[norm(base)],'ektr':[norm([f,by['speed'],*[by[n] for n,t in BOUNDS],lo,hi,by[key]]) for f,key in [(inc,'incoming'),(out,'outgoing')]],'ekq3':[norm([force[n] for n,t in PRESSURE])],'ektu':[norm([force[n] for n,t in WORK])]}
    mm=constants|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    assert run('ektx',values,mm);cases+=1
    for i in range(len(values)):assert not run('ektx',mutate(values,i,TOTAL,fixture('ektx')[1],cuts),mm),TOTAL[i];cases+=1
    for n,rs in rows.items():
        for removed in rs:
            rest=[row for row in rs if row!=removed];assert not run('ektx',values,mm|{n:lambda *xs,rest=rest:norm(xs) in rest});cases+=1
    unknowns(lambda model:run('ektx',values,model),mm,tuple(rows))
    assert len(SETTING)==98 and len(TOTAL)==102;cases+=1
    # The diagnostic setting intentionally does NOT satisfy energy balance or
    # the pressure display: those are conclusions, not candidate selection.
    assert not run('ektz',[by[n] for n in ('incoming','outgoing','work')],m);cases+=1
    assert not run('ekt4',values,m);cases+=1
    return dict(cases=cases,all_98_physical_and_102_shared_roles_checked=True,same_two_physical_models_region_patch_and_period=True,no_energy_balance_or_pressure_display_in_premise=True)

@lru_cache(None)
def printed_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;_,by=setting(cuts);cases=0
    for speed,angle,A in product((-3,0,3),(-1,Q(1,3),1),(2,5)):
        pi=Q(3,4);rho=Q(A*A,8)/pi;ratio=Q(speed,5)
        row=(pi,A,5,speed,angle);incoming=rho*(5*angle-speed);outgoing=rho*(speed-5*angle);P=2*rho*(angle-ratio)**2/(1-ratio*ratio)
        for root,want in [('ektv',incoming),('ektw',outgoing),('ekt3',P)]:assert r(run(root,list(map(c,row)),m))==want;cases+=1
        current=by|{n:c(x) for n,x in dict(pi=pi,amplitude=A,light=5,speed=speed,anglecos=angle,labamplitude=A,labanglecos=angle,incoming=incoming,outgoing=outgoing,pressure=P).items()}
        assert run('ekty',[current[n] for n,t in TOTAL],m) and run('ekt4',[current[n] for n,t in TOTAL],m);cases+=2
        for name in ('incoming','outgoing'):
            bad=current|{name:c(r(current[name])+Q(1,7))};assert not run('ekty',[bad[n] for n,t in TOTAL],m);cases+=1
        assert run('ektz',list(map(c,(incoming,outgoing,incoming-outgoing))),m);cases+=1
    unknowns(lambda mm:run('ekt3',list(map(c,row)),mm),m,('sjd',))
    return dict(cases=cases,source_density_relative_speeds_and_pressure_square_preserved=True,work_balance_separate_from_mechanical_definition=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==402 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[400,401])==selection_binding(old,[400,401])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/reflected-return-quantities-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    assert not {'ekbw','ekbx','ekby','ekbz'}&{d['name'] for d in core()['declarations']}
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,all_402_statements_and_meanings_preserved=True,source_range_not_extended=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('transport',transport_checks),('integrals',integral_checks),('coverage',coverage_checks),('binding',binding_checks),('printed',printed_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_field_equations','compose_observed_intensity','compose_radiative_density','compose_mirror_surface_pressure','compose_reflected_light_inquiry','compose_reflected_return_quantities','compose_doppler_infinity','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_light_energy_ratio','check_reflected_light_inquiry','check_reflected_return_quantities','check_wave_cycle_frequency','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,*DEPENDENCIES,'scripts/compose_mirror_energy_work.py','scripts/check_mirror_energy_work.py','tests/test_mirror_energy_work.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='moving_mirror_energy_and_work_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
