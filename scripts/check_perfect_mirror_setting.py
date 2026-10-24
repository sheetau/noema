"""Check a shared, lossless mirror supposition and its complete first sentence."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_conductor_cases import sentinel
from scripts.check_resting_charge_force import retag
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_light_energy_ratio import arithmetic
from scripts.check_wave_cycle_frequency import refused
from scripts.check_translated_light_trial import expose
from scripts.compose_perfect_mirror_setting import *
from scripts.read_perfect_mirror_setting import DOC,SOURCE,INVENTORY,READING,PRIOR,build_reading

CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','ri':'case','rd':'author','eirf':'paper','eisrx':'section7','eistk':'section8','eisue':'mirror','eisua':'law','eissc':'waveparameters'}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in SETTING if t=='a'],'other','a','b']))
DEPENDENCIES=('reports/mirror-surface-pressure-v1.json','reports/stationary-mirror-boundary-v1.json','reports/doppler-specialization-v1.json','reports/wave-transform-application-v1.json','reports/observed-intensity-v1.json')
BOUNDS={'ekre':{'ekrb'},'ekrf':{'eket','ekqu','ekqn','ekre'},'ekrg':{'ekrf'},'ekrh':{'ekrg','ekbn'},'ekrj':{'ekri'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set()))
    return extract_document(doc,roots=[name],statement_indices=[]).document

def finite_reals(node):
    if node==RS:return 'individual'
    if isinstance(node,list):return [finite_reals(x) for x in node]
    if isinstance(node,dict):return {k:finite_reals(v) for k,v in node.items()}
    return node

@lru_cache(None)
def fixture(name,mode='native'):
    doc=deepcopy(boundary(name))
    if mode=='finite':doc=finite_reals(doc)
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name);body=d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
        for i,(n,t) in enumerate(VARIABLES):
            assert body['kind']=='exists'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall'},only_sort=RS))==4
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpms'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jpmscapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jpmscapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jpmscapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def scalar(cuts,fn):return FunctionValue((RS,)*4,RS,lambda *xs:cuts.make(fn(*map(cuts.read,xs))))
def region(cuts,fn):return FunctionValue((RS,)*4,'truth',lambda *xs:fn(*map(cuts.read,xs)))

@lru_cache(None)
def flow_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    electric=FunctionValue(('individual',),dict(kind='function',parameters=[RS]*4,result=RS),lambda a:scalar(cuts,lambda x,y,z,t:{'x':x+t,'y':2*y-t,'z':3*z+x}.get(a,0)))
    magnetic=FunctionValue(('individual',),dict(kind='function',parameters=[RS]*4,result=RS),lambda a:scalar(cuts,lambda x,y,z,t:{'x':y-z,'y':z+2*t,'z':x-y+4}.get(a,0)))
    flux=run('ekrc',[c(2),electric,magnetic],m)
    for x,y,z,t in product((-1,2),(0,3),(-2,1),(0,Q(1,2))):
        assert r(flux(*map(c,(x,y,z,t))))==2*((2*y-t)*(x-y+4)-(3*z+x)*(z+2*t));cases+=1
    point=(1,2,3,4)
    for rates,expected in (((10,10,0,0),True),((0,0,0,0),True),((10,9,0,0),False),((10,10,1,-1),False),((10,9,1,0),False),((10,9,0,1),False),((-1,-1,0,0),False),((1,-1,0,0),False),((10,10,-1,1),False)):
        fs=[scalar(cuts,lambda *p,n=n:n) for n in rates]
        assert run('ekrd',fs+list(map(c,point)),m)==expected;cases+=1
    # Each of four functions sees x,y,z,time in that order, at the same point.
    for slot in range(4):
        fs=[scalar(cuts,lambda *p,n=n:10 if n<2 else 0) for n in range(4)]
        fs[slot]=scalar(cuts,lambda *p,slot=slot:(10 if slot<2 else 0)+(p!=point))
        assert run('ekrd',fs+list(map(c,point)),m);cases+=1
        for i in range(4):
            p=list(point);p[i]+=1;assert not run('ekrd',fs+list(map(c,p)),m);cases+=1
    unknowns(lambda model:run('ekrd',fs+list(map(c,point)),model),m,('ba','bc','sca','bd'))
    return dict(cases=cases,same_coordinate_cross_product_and_sign=True,transmission_and_body_transfer_separately_zero=True,offsetting_hidden_channels_rejected=True)

@lru_cache(None)
def region_checks():
    cuts,m=arithmetic();c=cuts.make;cases=0
    reg=region(cuts,lambda x,y,z,t:abs(y)<=2 and abs(z)<=3 and -1<=t<=1)
    front=run('ekq7',[reg],m);edge=run('ekra',[reg],m)
    for x,y,z,t in product((-1,0,1),(0,3),(0,4),(0,2)):
        inside=abs(y)<=2 and abs(z)<=3 and -1<=t<=1
        assert front(*map(c,(x,y,z,t)))==(inside and x<=0);assert edge(*map(c,(x,y,z,t)))==(inside and x==0);cases+=2
    fm={'ba':lambda x:True,'bb':lambda n:'a','sca':lambda a,b:a==b}
    for point in product(('a','b'),repeat=4):
        reg2=FunctionValue(('individual',)*4,'truth',lambda *p,point=point:p==point)
        assert run('ekrb',[reg2],fm,'finite',('a','b'))==(point[0]=='a');cases+=1
    assert not run('ekrb',[FunctionValue(('individual',)*4,'truth',lambda *p:False)],fm,'finite',('a','b'));cases+=1
    refused(lambda:run('ekrb',[reg],m));cases+=1
    fs=[scalar(cuts,lambda *p,n=n:10 if n<2 else 0) for n in range(4)]
    for point in ((0,0,0,0),(1,0,0,0),(0,3,0,0),(0,0,0,2)):
        values=[edge,*fs,*map(c,point)];mm=m|{'ekrb':lambda reg:True}
        assert run('ekre',values,mm,'instance');cases+=1
        bad=values[:];bad[3]=scalar(cuts,lambda *p:1)
        assert run('ekre',bad,mm,'instance')==(point!=(0,0,0,0));cases+=1
        assert not run('ekre',values,mm|{'ekrb':lambda reg:False},'instance');cases+=1
    refused(lambda:run('ekre',[edge,*fs],mm));cases+=1
    unknowns(lambda model:run('ekre',[edge,*fs,*map(c,(0,0,0,0))],model,'instance'),mm,('ekrb','ba','sca'))
    return dict(cases=cases,front_boundary_and_empty_intersection_distinguished=True,all_four_coordinate_slots_bound=True,full_real_quantification_not_finite_sampling=True)

@lru_cache(None)
def physical_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0;slots=fixture('ekrf')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]
    by=dict(zip((n for n,t in SETTING),values))
    numbers=dict(speed=3,light=5,rate=2,ax=1,ay=0,az=0,ex=0,ey=3,ez=4,hx=0,hy=-4,hz=3,coefficient=2,lower=-4,upper=4,pi=Q(3,4),cycle=Q(3,2),oldperiod=Q(3,4),newperiod=Q(3,2),frequency=Q(4,3),newfrequency=Q(2,3))
    by.update({n:c(x) for n,x in numbers.items()})
    by['sine']=FunctionValue((RS,),RS,lambda t:c(r(t)+1))
    by['space']=FunctionValue((RS,)*3,'truth',lambda x,y,z:abs(r(x))<=10 and abs(r(y))<=9 and abs(r(z))<=8)
    values=[by[n] for n,t in SETTING]
    probes=((0,0,0,0),(-1,2,3,Q(1,2)),(1,-2,-3,2),(0,0,0,2),(0,0,0,-2),(0,10,0,0))
    def norm(x):
        if not isinstance(x,FunctionValue):return x
        if x.parameters==tuple(RS['parameters']) and x.result==RS['result']:return r(x)
        if x.parameters==('individual',):return tuple(norm(x(a)) for a in ('x','y','z','time','body'))
        if x.parameters==(RS,)*4:return tuple(norm(x(*map(c,p))) for p in probes)
        if x.parameters==(RS,)*3:return tuple(norm(x(*map(c,p))) for p in ((0,0,0),(2,-3,4),(11,0,0)))
        if x.parameters==(RS,):return tuple(norm(x(c(t))) for t in (-1,0,1))
        raise AssertionError(x.parameters)
    normalize=lambda xs:tuple(norm(x) for x in xs)
    def field(coeffs,normal):
        return FunctionValue(('individual',),dict(kind='function',parameters=[RS]*4,result=RS),lambda a:scalar(cuts,lambda x,y,z,t:dict(zip(('x','y','z'),coeffs)).get(a,0)*(1+t-normal*x/5)))
    inc=[field((0,Q(3,2),2),1),field((0,-2,Q(3,2)),1)]
    ref=[field((0,Q(-3,2),-2),-1),field((0,-2,Q(3,2)),-1)]
    def inside(x,y,z,t):
        return abs(Q(5,4)*(x+3*t))<=10 and abs(y)<=9 and abs(z)<=8 and -4<=Q(5,4)*(t+Q(3,25)*x)<=4 and -1<=t<=1
    front=region(cuts,lambda x,y,z,t:inside(x,y,z,t) and x<=0);edge=region(cuts,lambda x,y,z,t:inside(x,y,z,t) and x==0)
    rates=[scalar(cuts,lambda x,y,z,t:Q(25,2)*(1+t-x/5)**2),scalar(cuts,lambda x,y,z,t:Q(25,2)*(1+t+x/5)**2),scalar(cuts,lambda *p:0),scalar(cuts,lambda *p:0)]
    numeric=by|{n:c(x) for n,x in dict(rate=1,ax=1,ay=0,az=0,ex=0,ey=Q(3,2),ez=2,hx=0,hy=-2,hz=Q(3,2)).items()}|dict(period=by['newperiod'],frequency=by['newfrequency'])
    shared=by|dict(frame='k',scope='section8')
    interaction=shared|dict(incidentE=inc[0],incidentH=inc[1],reflectedE=ref[0],reflectedH=ref[1],region=front)
    budget=shared|dict(region=edge,**dict(zip((n for n,t in RATES),rates)))
    rows={'eket':normalize([by[n] for n,t in EXTENDED]),'ekqu':normalize([by['body'],by['light'],by['speed'],'case']),'ekqn':normalize([numeric[n] for n,t in HARMONIC_MODEL]),'eiste':normalize([shared[n] for n,t in COEFFICIENT]),'eisuc':normalize([interaction[n] for n,t in INTERACTION]),'eisud':normalize([budget[n] for n,t in BUDGET]),'ekre':normalize([edge,*rates])}
    m|={'eisls':lambda f,u,ctx:c(-1),'eislt':lambda f,u,ctx:c(1)}
    mm=m|{n:lambda *xs,row=row:normalize(xs)==row for n,row in rows.items()}
    assert run('ekrf',values,mm);cases+=1
    for i,((n,t),(_,sort)) in enumerate(zip(SETTING,slots)):
        # Keep the rational arithmetic fixture's square roots exact while
        # changing velocity/light independently; other real slots use 1/7.
        bad=values[:];bad[i]=c(4) if n=='speed' else c(Q(15,4)) if n=='light' else c(r(bad[i])+Q(1,7)) if t==R else sentinel(sort,100+i,cuts)
        assert not run('ekrf',bad,mm),(i,n);cases+=1
    for n in rows:assert not run('ekrf',values,mm|{n:lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekrf',values,model),mm,(*rows,'eisls','eislt'))
    # The material history's interval must be requested in k with its time unit.
    for name in ('eisls','eislt'):
        seen=[];fn=mm[name]
        assert run('ekrf',values,mm|{name:lambda *xs,fn=fn:(seen.append(xs),fn(*xs))[1]})
        assert seen and all(xs==('k','duration','case') for xs in seen);cases+=1
    return dict(cases=cases,all_66_settings_share_same_physical_model=True,independent_boost_fields_and_reflected_flow_routes=True,body_time_interval_clips_same_optical_region=True,prior_approximation_not_replaced_with_zero_error=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for pivot,(var,sort) in enumerate(VARIABLES):
        mode=f'slot:{pivot}';base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(VARIABLES)};values=[base[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
        for target in ('a','b'):
            assigned=base|{var:target,'frame':'a','light':'a','scope':'b','context':'case'};row=tuple(assigned[n] for n,t in SETTING)
            mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekrf':lambda *xs,row=row:xs==row}
            assert run('ekrg',values,mm,mode,('a','b'));cases+=1
            assert not run('ekrg',values,mm|{'ekrf':lambda *xs:False},mode,('a','b'));cases+=1
            wrong=assigned|{var:'unavailable'};other=tuple(wrong[n] for n,t in SETTING)
            assert not run('ekrg',values,mm|{'ekrf':lambda *xs,row=other:xs==row},mode,('a','b'));cases+=1
        unknowns(lambda model:run('ekrg',values,model,mode,('a','b')),mm,('ekrf',))
    cuts,m=arithmetic();refused(lambda:run('ekrg',[],m|{'tc':lambda:cuts.make(5),'ekrf':lambda *xs:True}));cases+=1
    return dict(cases=cases,all_62_existential_roles_share_one_assignment=True,native_function_domains_refused=True)

@lru_cache(None)
def presentation_checks():
    rows={'eislz':{('mirror','author','ekrg','section8','case')},'ug':{('mirror','author','ekrg','section8','case')},'eisov':{('mirror','author','section7','ekbn','paper','case')},'eisra':{('mirror','author','paper','waveparameters','ekbn','ekrg','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda model:run('ekrh',[],model),mm,rows)
    outer={'eir3':{('mirror','author','paper','ekri','case')},'ue':{('law','mirror','case')}}
    mm={n:relation(rs) for n,rs in outer.items()};cases+=perturb(lambda model:run('ekrj',[],model),mm,outer)
    assert not run('ekrj',[],{n:lambda *xs:True for n in outer}|{'eisue':lambda:'law'});cases+=1
    return dict(cases=cases,supposition_and_adoption_not_actual_experiment=True,previous_numbered_section_and_same_wave_reference=True,quoted_contents_not_executed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==395 and new.document['statements'][:394]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/mirror-surface-pressure-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'eket','ekqu','ekqn','eiste','eisuc','eisud'}<=deps
    assert not {'ekbw','ekbx','ekby','ekbz'}&deps
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['selection']==selection_binding(new,[INDEX]) and reading['reviewed_prose_characters']==130 and reading['reviewed_math_elements']==1 and reading['verified_full_units']==0
    return dict(new_definitions=len(MEANINGS),new_general_relations=2,all_394_previous_statements_and_meanings_preserved=True,first_sentence_130_prose_characters_one_math_under_explicit_reading=True,whole_unit_completion_deferred=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('flow',flow_checks),('region',region_checks),('physical',physical_checks),('quantifiers',quantifier_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_mirror_surface_pressure','compose_doppler_specialization','compose_stationary_mirror_boundary','compose_observed_intensity','compose_wave_transform_application','compose_rod_methods','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_resting_charge_force','check_material_relative_frame','check_light_energy_ratio','check_wave_cycle_frequency','check_translated_light_trial','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{READING,DOC,*DEPENDENCIES,'scripts/compose_perfect_mirror_setting.py','scripts/read_perfect_mirror_setting.py','scripts/check_perfect_mirror_setting.py','tests/test_perfect_mirror_setting.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='perfect_mirror_supposition_sentence_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
