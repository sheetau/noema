"""Check inverse reflection, moving-surface averages and the fixed four-quantity query."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_conductor_cases import sentinel
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_light_energy_ratio import arithmetic
from scripts.check_wave_cycle_frequency import refused
from scripts.check_translated_light_trial import expose
from scripts.check_perfect_mirror_setting import scalar,region
from scripts.compose_reflected_light_inquiry import *
from scripts.read_reflected_light_inquiry import DOC,SOURCE,INVENTORY,READING,PRIOR,build_reading

CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','ri':'case','rd':'author','eirf':'paper','eisrx':'section7','eistk':'section8','eisue':'mirror','eisug':'query'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in SETTING if t=='a'],'other']))
DEPENDENCIES=('reports/perfect-mirror-setting-v1.json','reports/mirror-surface-pressure-v1.json','reports/stationary-mirror-boundary-v1.json','reports/wave-transform-application-v1.json','reports/wave-cycle-frequency-v1.json','reports/radiative-intensity-v1.json')
BOUNDS_MAP={'ekrt':{'ekrf','ekrs','ekq4'},'ekru':{'ekrt','ekc7','sede'},'ekrv':{'ekru'},'ekrw':{'ekrg','ekrt','ekrv'},'ekry':{'ekrx'}}
PS=dict(kind='function',parameters=['individual'],result=RS)

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS_MAP.get(name,set()))
    return extract_document(doc,roots=[name],statement_indices=[]).document

@lru_cache(None)
def fixture(name,mode='native'):
    doc=deepcopy(boundary(name));d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall'},only_sort=RS))==4
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jrli'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jrlicapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jrlicapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native'):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jrlicapture']=capture
    result=evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def normalize(cuts):
    c,r=cuts.make,cuts.read
    points=((0,0,0,0),(-1,2,3,Q(1,2)),(1,-2,-3,2),(0,0,0,2),(0,0,0,-2),(0,10,0,0),(3,0,0,1))
    def norm(x):
        if not isinstance(x,FunctionValue):return x
        if x.parameters==tuple(RS['parameters']) and x.result==RS['result']:return r(x)
        if x.parameters==('individual',):return tuple(norm(x(a)) for a in ('x','y','z','time','body'))
        if x.parameters==(RS,)*4:return tuple(norm(x(*map(c,p))) for p in points)
        if x.parameters==(RS,)*3:return tuple(norm(x(*map(c,p))) for p in ((0,0,0),(2,-3,4),(11,0,0)))
        if x.parameters==(RS,):return tuple(norm(x(c(t))) for t in (-1,0,1,2))
        raise AssertionError(x.parameters)
    return lambda xs:tuple(norm(x) for x in xs)

def settings(cuts):
    c,r=cuts.make,cuts.read;slots=fixture('ekrt')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]
    by=dict(zip((n for n,t in SETTING),values))
    numbers=dict(speed=3,light=5,rate=2,ax=1,ay=0,az=0,ex=0,ey=3,ez=4,hx=0,hy=-4,hz=3,coefficient=2,lower=-4,upper=4,pi=Q(3,4),cycle=Q(3,2),oldperiod=Q(3,4),newperiod=Q(3,2),frequency=Q(4,3),newfrequency=Q(2,3),forcelower=Q(-1,2),ylower=-1,yupper=1,zlower=-2,zupper=2,labcoefficient=2)
    by.update({n:c(x) for n,x in numbers.items()});by.update(frame='K',scope='section7')
    by['sine']=FunctionValue((RS,),RS,lambda t:c(r(t)+1))
    by['space']=FunctionValue((RS,)*3,'truth',lambda x,y,z:abs(r(x))<=10 and abs(r(y))<=9 and abs(r(z))<=8)
    by['force']=FunctionValue((RS,),PS,lambda t:FunctionValue(('individual',),RS,lambda a:c(48 if a=='x' else 0)))
    return [by[n] for n,t in SETTING],by

def changed(values,i,cuts):
    n,t=SETTING[i];sort=fixture('ekrt')[1][i][1];bad=values[:]
    bad[i]=cuts.make(4) if n=='speed' else cuts.make(Q(15,4)) if n=='light' else cuts.make(cuts.read(bad[i])+Q(1,7)) if t==R else sentinel(sort,100+i,cuts)
    return bad

@lru_cache(None)
def return_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    normals=((Q(1),Q(0),Q(0)),(Q(3,5),Q(4,5),Q(0)),(Q(1,3),Q(2,3),Q(2,3)))
    for speed,n,rate in product((0,3,-3),normals,(1,2)):
        a,b,z=n;beta=Q(1) if speed==0 else Q(5,4);ratio=Q(speed,5)
        # Two transverse components, including a genuinely three-dimensional normal.
        E=(2*b+3*z,-2*a,-3*a);H=(b*E[2]-z*E[1],z*E[0]-a*E[2],a*E[1]-b*E[0])
        er=(E[0],-E[1],-E[2]);hr=(-H[0],H[1],H[2]);den=1-ratio*a
        nr=((-a+ratio)/den,b/(beta*den),z/(beta*den));w=beta*rate*den
        el=(er[0],beta*(er[1]+ratio*hr[2]),beta*(er[2]-ratio*hr[1]));hl=(hr[0],beta*(hr[1]-ratio*er[2]),beta*(hr[2]+ratio*er[1]))
        values=list(map(c,(5,speed,rate,*n,*E,*H)))
        assert r(run('ekrk',values,m))==w;cases+=1
        for name,expected in [('ekrl',nr),('ekrm',el),('ekrn',hl)]:
            vector=run(name,values,m)
            for axis,x in zip(('x','y','z'),expected):assert r(vector(axis))==x;cases+=1
            assert r(vector('time'))==0;cases+=1
        assert sum(x*x for x in nr)==1 and sum(x*y for x,y in zip(nr,el))==0;cases+=1
        assert r(run('ekrq',values+[c(Q(3,2))],m))==Q(3,2)/w;cases+=1
        profile=FunctionValue((RS,),RS,lambda t:c(r(t)+1))
        fields=[run(name,[profile,*values],m) for name in ('ekro','ekrp')]
        for x,y,z,t in ((0,0,0,0),(1,2,-3,Q(1,2)),(-2,3,1,-1)):
            x,y,z,t=map(Q,(x,y,z,t));kpoint=(beta*(x-speed*t),y,z,beta*(t-Q(speed,25)*x))
            phase=rate*(kpoint[3]-(-a*kpoint[0]+b*y+n[2]*z)/5)
            assert phase==w*(t-sum(a*p for a,p in zip(nr,(x,y,z)))/5);cases+=1
            for field,coefs in zip(fields,(el,hl)):
                for axis,coef in zip(('x','y','z'),coefs):assert r(field(axis)(*map(c,(x,y,z,t))))==coef*(1+phase);cases+=1
        for tau in (-1,0,2):assert r(run('ekrr',list(map(c,(5,speed,tau))),m))==beta*tau;cases+=1
    # A reflected ray can have positive K x-direction while receding from the moving mirror.
    vals=list(map(c,(5,3,1,Q(1,3),Q(2,3),Q(2,3),4,-2,-2,0,2,-2)))
    assert r(run('ekrl',vals,m)('x'))==Q(1,3) and 5*Q(1,3)<3;cases+=1
    unknowns(lambda model:run('ekrk',values,model),m,('soy','sjd','be'))
    return dict(cases=cases,both_polarizations_and_all_three_directions_returned=True,same_four_coordinate_phase_under_inverse_boost=True,mirror_clock_interval_distinct_from_stationary_detector_period=True)

@lru_cache(None)
def coverage_checks():
    cuts,m=arithmetic();c=cuts.make;cases=0
    reg=region(cuts,lambda x,y,z,t:x==0 and -1<=y<=1 and -2<=z<=2 and -1<=t<=2)
    values=[reg,*map(c,(-1,2,-1,1,-2,2))]
    for point in ((0,0,0,0),(0,-1,-2,-1),(0,1,2,2),(1,0,0,0),(0,3,0,0),(0,0,0,3)):
        assert run('ekrs',values+list(map(c,point)),m,'instance');cases+=1
        missing=region(cuts,lambda *p,point=point:p!=point)
        outside=point in ((1,0,0,0),(0,3,0,0),(0,0,0,3))
        assert run('ekrs',[missing,*values[1:],*map(c,point)],m,'instance')==outside;cases+=1
    for lo,hi in ((1,2),(3,4),(5,6)):
        bad=values[:];bad[hi]=bad[lo];assert not run('ekrs',bad+list(map(c,(0,0,0,0))),m,'instance');cases+=1
    refused(lambda:run('ekrs',values,m));cases+=1
    unknowns(lambda model:run('ekrs',values+list(map(c,(0,0,0,0))),model,'instance'),m,('ba','bg','sca'))
    unknown_region=FunctionValue((RS,)*4,'truth',forbidden)
    try:run('ekrs',[unknown_region,*values[1:],*map(c,(0,0,0,0))],m,'instance')
    except ValueError as exc:assert 'Unknown' in str(exc)
    else:raise AssertionError('Unknown illumination accepted')
    cases+=1
    return dict(cases=cases,every_patch_point_through_whole_mirror_cycle_required=True,empty_area_and_zero_duration_rejected=True,native_real_quantifiers_retained=True)

@lru_cache(None)
def setting_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;values,by=settings(cuts);norm=normalize(cuts);cases=0
    def field(coefs,w,normal):
        return FunctionValue(('individual',),dict(kind='function',parameters=[RS]*4,result=RS),lambda a:scalar(cuts,lambda x,y,z,t:dict(zip(('x','y','z'),coefs)).get(a,0)*(1+w*(t-normal*x/5))))
    inc=[field((0,3,4),2,1),field((0,-4,3),2,1)];ref=[field((0,Q(-3,4),-1),Q(1,2),-1),field((0,-1,Q(3,4)),Q(1,2),-1)]
    def inside_k(x,y,z,t):return abs(Q(5,4)*(x+3*t))<=10 and abs(y)<=9 and abs(z)<=8 and -4<=Q(5,4)*(t+Q(3,25)*x)<=4 and -1<=t<=1
    edge=region(cuts,lambda x,y,z,t:inside_k(x,y,z,t) and x==0)
    front=region(cuts,lambda x,y,z,t:inside_k(Q(5,4)*(x-3*t),y,z,Q(5,4)*(t-Q(3,25)*x)) and x<=3*t)
    shared=by|dict(frame='K',scope='section8',coefficient=by['labcoefficient'])
    force=shared|dict(process=by['interaction'],lower=c(Q(-5,8)),upper=c(Q(5,4)))
    physical=shared|dict(incidentE=inc[0],incidentH=inc[1],reflectedE=ref[0],reflectedH=ref[1],region=front)
    rows={'ekrf':norm(values[:len(PRIOR_SETTING)]),'ekrs':norm([edge,by['forcelower'],c(1),*[by[n] for n,t in BOUNDS]]),'ekq4':norm([force[n] for n,t in FORCE_SETTING]),'eiste':norm([shared[n] for n,t in COEFFICIENT]),'eisuc':norm([physical[n] for n,t in INTERACTION])}
    m|={'tc':lambda:c(5),'eisls':lambda f,u,ctx:c(-1),'eislt':lambda f,u,ctx:c(1)}
    mm=m|{n:lambda *xs,row=row:norm(xs)==row for n,row in rows.items()}
    assert run('ekrt',values,mm);cases+=1
    for i in range(len(SETTING)):assert not run('ekrt',changed(values,i,cuts),mm),(i,SETTING[i]);cases+=1
    for n in rows:assert not run('ekrt',values,mm|{n:lambda *xs:False});cases+=1
    for n in ('ra','eisrx'):assert not run('ekrt',values,mm|{n:lambda:'other'});cases+=1
    assert not run('ekrt',values,mm|{'tc':lambda:c(6)});cases+=1
    unknowns(lambda model:run('ekrt',values,model),mm,(*rows,'tc','eisls','eislt'))
    assert len(values)==74 and not {n for n,t in ANSWERS}&{n for n,t in SETTING};cases+=1
    return dict(cases=cases,all_74_roles_shared_outside_candidates=True,same_interaction_force_patch_and_boosted_interval=True,resting_frame_calibration_and_same_reflected_model=True,no_known_answer_in_condition=True)

@lru_cache(None)
def candidate_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;values,by=settings(cuts);norm=normalize(cuts);target=norm(values);cases=0
    answer=(6,-1,0,0,Q(1,3),Q(325,32))
    # A polynomial profile is only a diagnostic for the integral wiring.
    # The manuscript's normalized sine/least period remains an explicit boundary.
    wave_row=norm([by[n] for n,t in HARMONIC]+list(map(c,(Q(1,2),0,3,Q(1,3)))))
    def integral(lo,hi,profile,total):
        if (r(lo),r(hi))==(Q(-5,8),Q(5,4)):
            return r(total)==90 and all(r(profile(c(t)))==48 for t in (-1,0,1,2))
        if (r(lo),r(hi))==(0,3):
            return r(total)==Q(975,32) and all(r(profile(c(t)))==Q(25,8)*(1+Q(1,2)*t)**2 for t in (-1,0,1,2))
        return False
    mm=m|{'ekrt':lambda *xs:norm(xs)==target,'ekc7':lambda *xs:norm(xs)==wave_row,'sede':integral}
    args=values+list(map(c,answer));assert run('ekru',args,mm);cases+=1
    for i in range(6):
        bad=args[:];bad[len(values)+i]=c(answer[i]+Q(1,7));assert not run('ekru',bad,mm),(i,answer[i]);cases+=1
    for i in range(len(SETTING)):assert not run('ekru',changed(values,i,cuts)+list(map(c,answer)),mm),(i,SETTING[i]);cases+=1
    for n in ('ekrt','ekc7','sede'):assert not run('ekru',args,mm|{n:lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekru',args,model),mm,('ekrt','ekc7','sede','sca','soy'))
    # Do not equate the mirror interval 15/8 with the stationary K period 3.
    assert Q(5,4)*Q(3,2)==Q(15,8)!=3;cases+=1
    return dict(cases=cases,pressure_direction_frequency_intensity_all_constrained=True,moving_surface_average_and_stationary_wave_cycle_separate=True,progression_normal_flux_not_mirror_crossing_flux=True,polynomial_integral_diagnostic_not_a_sine_period_proof=True)

@lru_cache(None)
def question_checks():
    cuts,m=arithmetic();c=cuts.make;values,by=settings(cuts);norm=normalize(cuts);target=norm(values);cases=0
    a=(Q(6),Q(-1),Q(0),Q(0),Q(1,3),Q(2));b=(Q(3),Q(0),Q(1),Q(0),Q(4),Q(5));other=(Q(1),)*6
    for accepted in (set(),{a},{a,b}):
        mm={'ekru':lambda *xs:norm(xs[:-6])==target and norm(xs[-6:]) in accepted}
        question=run('ekrv',values,mm);assert isinstance(question,QuestionValue);cases+=1
        for candidate in (a,b,other):assert question.function(*map(c,candidate))==(candidate in accepted);cases+=1
        for i in range(len(SETTING)):
            altered=run('ekrv',changed(values,i,cuts),mm);assert not altered.function(*map(c,a));cases+=1
    question=run('ekrv',values,{'ekru':forbidden})
    try:question.function(*map(c,a))
    except ValueError as exc:assert 'Unknown' in str(exc)
    else:raise AssertionError('Unknown candidate accepted')
    cases+=1
    return dict(cases=cases,all_six_candidates_share_fixed_74_role_setting=True,empty_single_multiple_answers_do_not_change_question_act=True,question_construction_does_not_execute_candidates=True)

@lru_cache(None)
def presentation_checks():
    rows={'eisuf':{('query','author','mirror','ekrg','ekrt','ekrv','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda model:run('ekrw',[],model),mm,rows)
    outer={'eir3':{('query','author','paper','ekrx','case')},'ue':{('mirror','query','case')}}
    mm={n:relation(rs) for n,rs in outer.items()};cases+=perturb(lambda model:run('ekry',[],model),mm,outer)
    assert not run('ekry',[],{n:lambda *xs:True for n in outer}|{'eisug':lambda:'mirror'});cases+=1
    return dict(cases=cases,same_prior_mirror_hypothesis_and_question_family_presented=True,closed_conditions_and_questions_not_executed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==396 and new.document['statements'][:395]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[394])==selection_binding(old,[394])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/perfect-mirror-setting-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'ekrf','ekq3','ekq4','ekc7','ekjh','eiste','eisuc','eisuf'}<=deps
    assert not {'ekbw','ekbx','ekby','ekbz'}&deps
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['selection']==selection_binding(new,[INDEX]) and reading['reviewed_prose_characters']==125 and reading['reviewed_math_elements']==0
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,all_395_previous_statements_and_meanings_preserved=True,second_sentence_125_prose_characters_under_explicit_reading=True,whole_unit_review_separate=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('return',return_checks),('coverage',coverage_checks),('setting',setting_checks),('candidate',candidate_checks),('question',question_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_perfect_mirror_setting','compose_stationary_mirror_boundary','compose_mirror_surface_pressure','compose_observed_intensity','compose_wave_cycle_frequency','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_light_energy_ratio','check_wave_cycle_frequency','check_translated_light_trial','check_perfect_mirror_setting','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{READING,DOC,*DEPENDENCIES,'scripts/compose_reflected_light_inquiry.py','scripts/read_reflected_light_inquiry.py','scripts/check_reflected_light_inquiry.py','tests/test_reflected_light_inquiry.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_reflected_light_four_quantity_question_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
