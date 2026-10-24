"""Check simultaneous source positions, two directions and their distinct angles."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from math import isqrt
import json,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_distant_direction_geometry import arithmetic
from scripts.check_velocity_angle_measure import branch_model
from scripts.check_wave_cycle_frequency import refused
from scripts.check_resting_charge_force import retag
from scripts.check_doppler_specialization import CONSTANTS,DOMAIN
from scripts.compose_aberration_line import *

DOC='docs/aberration-line-v1.md';SOURCE='data/einstein-aberration-line-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p912-0.jpg'
DEPENDENCIES=('reports/doppler-infinity-v1.json','reports/doppler-specialization-v1.json','reports/distant-direction-geometry-v1.json','reports/wave-transform-application-v1.json')
DOMAIN=tuple(dict.fromkeys([*DOMAIN,'body',*(n for n,t in SETTING if t=='a')]))
BOUNDS={'ekgn':{'eket','ekdm','ekgf'},'ekgp':{'ekgn','ekgo'}}
DIRECTIONS=((1,0,0),(-1,0,0),(0,1,0),(0,0,1),(Q(3,5),Q(4,5),0),(Q(-3,5),0,Q(4,5)),(0,Q(3,5),Q(4,5)))
RATIOS=(Q(0),Q(3,5),Q(5,13),Q(15,17))

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sky','soy','szi','shu','ejor','sedi'}|BOUNDS.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) else s for s in d['parameters']]
                if isinstance(d['result'],dict):d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name);body=d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
        for i in range(len(VARIABLES)):
            assert body['kind']=='forall'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jabl'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jablcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jablcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jablcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def setup():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read
    m=m|{'soy':lambda V,speed:c(1/r(m['sky'](c(1-(r(speed)/r(V))**2))))}
    return cuts,m

def rational_root(x):
    x=Q(x);a,b=isqrt(x.numerator),isqrt(x.denominator)
    return Q(a,b) if a*a==x.numerator and b*b==x.denominator else None

@lru_cache(None)
def simultaneity_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for ratio,n,R0,tau in product(RATIOS,DIRECTIONS,(1,7),(-2,0,3)):
        V=Q(5);speed=V*ratio;gamma=1/rational_root(1-ratio*ratio);values=list(map(c,(V,speed,*n,R0,tau)))
        assert run('ekgh',values,m);cases+=1
        p=run('ekga',values,m);assert tuple(r(p(a)) for a in ('x','y','z','t'))==(-R0*n[0]/gamma-speed*tau,-R0*n[1],-R0*n[2],tau);cases+=1
        t=r(run('ekgg',values,m));assert t==tau/gamma-speed*R0*n[0]/(V*V);cases+=1
        family=run('ekgi',values[:5],m);p=family(c(R0))(c(tau))
        assert tuple(r(p(a)) for a in ('x','y','z','t'))==(-R0*n[0]/gamma-speed*tau,-R0*n[1],-R0*n[2],tau);cases+=1
        if ratio and n[0] and tau==0:assert t!=tau;cases+=1
    unknowns(lambda mm:run('ekgh',list(map(c,(5,3,1,0,0,7,2))),mm),m,('soy','sjd','shv','sca'))
    return dict(cases=cases,new_time_solved_before_transforming_source_position=True,all_four_coordinates_and_model_family_agree=True)

@lru_cache(None)
def direction_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;irrational_lengths=0
    for ratio,n in product(RATIOS,DIRECTIONS):
        vals=list(map(c,(5,5*ratio,*n)));gamma=1/rational_root(1-ratio*ratio)
        raw=run('ekgs',vals,m);raw=tuple(r(raw(a)) for a in ('x','y','z'))
        normal=run('ekgd',vals,m);normal=tuple(r(normal(a)) for a in ('x','y','z'))
        assert raw==(n[0]/gamma,n[1],n[2]);cases+=1
        assert sum(x*x for x in normal)==1;cases+=1
        assert sum(x*y for x,y in zip(raw,normal))==1/gamma;cases+=1
        L=rational_root(sum(x*x for x in raw))
        if L is None:
            irrational_lengths+=1
            try:run('ekgb',vals,m)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError('Irrational square root invented')
            continue
        assert r(run('ekgb',vals,m))==L;cases+=1
        line=run('ekgc',vals,m);line=tuple(r(line(a)) for a in ('x','y','z'))
        assert line==tuple(x/L for x in raw) and sum(x*x for x in line)==1;cases+=1
        co=sum(x*y for x,y in zip(normal,line));assert r(run('ekgr',vals,m))==co;cases+=1
        if ratio and n[0]==0:assert co!=normal[0];cases+=1
    assert irrational_lengths>0
    unknowns(lambda mm:run('ekgc',list(map(c,(5,3,0,1,0))),mm)('x'),m,('sky','sjd','soy'))
    return dict(cases=cases,wave_normal_and_simultaneous_line_distinguished=True,unnormalized_dot_product_equals_inverse_gamma=True,unknown_irrational_roots_rejected=irrational_lengths)

@lru_cache(None)
def limit_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for ratio,n,pos,tau in product(RATIOS,((1,0,0),(0,Q(3,5),Q(4,5))),((0,0,0),(1,-2,3)),(-2,0,3)):
        speed=5*ratio;vals=(5,speed,*n,*pos,7,tau)
        assert run('ekgl',list(map(c,vals)),m);cases+=1
        d=run('ekgj',list(map(c,vals)),m)
        g=1/rational_root(1-ratio*ratio)
        assert tuple(r(d(a)) for a in ('x','y','z'))==(pos[0]+7*n[0]/g+speed*tau,pos[1]+7*n[1],pos[2]+7*n[2]);cases+=1
    # Exact 3-4-5 offsets leave the physical distance distinct from rho.
    for ratio in RATIOS:
        speed=5*ratio;gamma=1/rational_root(1-ratio*ratio)
        for parameter in (Q(10),Q(25),Q(50)):
            rho=(parameter**2-25)/(2*parameter);length=(parameter**2+25)/(2*parameter)
            R0=rho*gamma;tau=2;pos=(-speed*tau,3,4)
            for eps in (Q(1),Q(1,2),Q(1,10)):
                expected=max(abs(rho/length-1),Q(4)/length)<eps
                assert run('ekgm',list(map(c,(5,speed,1,0,0,*pos,R0,tau,eps))),m)==expected;cases+=1
    refused(lambda:run('ekdm',list(map(c,(0,1,0))),m))
    return dict(cases=cases,actual_simultaneous_displacement_matches_rescaled_limit=True,finite_position_and_new_time_fixed_before_distance_limit=True,all_real_limit_not_sampled=True)

@lru_cache(None)
def angle_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;mm=branch_model(cuts,m);cases=0
    for n,l in product(DIRECTIONS,DIRECTIONS):
        co=sum(x*y for x,y in zip(n,l));si=rational_root(1-co*co)
        if si is None:continue
        ratio=si/co if co else 0;principal=0 if not ratio else 1 if ratio>0 else -1;angle=2 if not co else principal if co>0 else principal+4
        vals=(*n,*l,co,si,ratio,principal,4,angle)
        assert run('ekgf',list(map(c,vals)),mm);cases+=1
        if si:
            bad=list(vals);bad[7]=-si;assert not run('ekgf',list(map(c,bad)),mm);cases+=1
    for ratio in RATIOS[1:]:
        co=rational_root(1-ratio*ratio);si=ratio
        vals=(5,5*ratio,0,1,0,co,si,si/co,1,4,1)
        assert run('ekgq',list(map(c,vals)),mm);cases+=1
        assert co!=-ratio;cases+=1
        bad=list(vals);bad[5]=-ratio;assert not run('ekgq',list(map(c,bad)),mm);cases+=1
    vals=(5,3,0,1,0,Q(4,5),Q(3,5),Q(3,4),1,4,1)
    for i in range(5,11):
        bad=list(vals);bad[i]+=Q(1,2);assert not run('ekgq',list(map(c,bad)),mm);cases+=1
    unknowns(lambda model:run('ekgq',list(map(c,vals)),model),mm,('ejor','sedi','sca'))
    return dict(cases=cases,actual_angle_not_just_cosine=True,perpendicular_source_case_disagrees_with_printed_formula=True,pi_and_atan_boundary_probes_not_exact_values=True)

@lru_cache(None)
def binding_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;slots=fixture('ekgn')[1];cases=0
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]
    positions={n:i for i,(n,t) in enumerate(SETTING)}
    for n,x in dict(light=5,speed=3,ax=0,ay=1,az=0,pi=4,newanglecos=Q(4,5),newanglesin=Q(3,5),newratio=Q(3,4),newprincipal=1,newangle=1,anglecos=0).items():values[positions[n]]=c(x)
    gate=lambda *xs:all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,values[:60],slots[:60]))
    angle_values=(-Q(3,5),Q(4,5),0,0,1,0,Q(4,5),Q(3,5),Q(3,4),1,4,1)
    def source_model(obj,frame,lu,tu,models,parameters,scope,ctx):
        if (obj,frame,lu,tu,scope,ctx)!=('source','moving','lengthunit','timeunit','scope','case'):return False
        if not parameters(c(2)) or parameters(c(0)) or parameters(c(-1)):return False
        return all(tuple(r(models(c(R0))(c(t))(a)) for a in ('x','y','z','t'))==(-3*t,-R0,0,t) for R0,t in product((2,7),(-1,3)))
    mm=m|{'eket':gate,'ekgf':lambda *xs:tuple(map(r,xs))==angle_values,'ekdm':lambda *xs:tuple(map(r,xs))==(0,1,0),'eissk':source_model}
    assert run('ekgn',values,mm);cases+=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=sentinel(s,100+i,cuts)
        try:result=run('ekgn',changed,mm)
        except ValueError as e:assert 'Unknown' in str(e)
        else:assert not result,(i,n)
        cases+=1
    unknowns(lambda model:run('ekgn',values,model),mm,('eket','ekgf','ekdm','eissk'))
    assert not run('ekgo',values,m);cases+=1
    changed=values[:];changed[positions['newanglecos']]=c(Q(-3,5));assert run('ekgo',changed,m);cases+=1
    for pivot,(name,t) in enumerate(VARIABLES):
        for target in ('a','b','unavailable'):
            expected={n:'a' for n,t in SETTING};expected.update(context='case',scope='b');expected[name]=target
            row=tuple(expected[n] for n,t in SETTING);vals=[expected[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
            base={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekgn':lambda *xs,row=row:tuple(xs)==row,'ekgo':lambda *xs:False}
            assert run('ekgp',vals,base,'slot:'+str(pivot),('a','b'))==(target=='unavailable');cases+=1
            assert run('ekgp',vals,base|{'ekgo':lambda *xs,row=row:tuple(xs)==row},'slot:'+str(pivot),('a','b'));cases+=1
    refused(lambda:run('ekgp',[],m|{'tc':lambda:c(5),'ekgn':lambda *xs:True,'ekgo':lambda *xs:True}))
    return dict(cases=cases,all_setting_roles=65,quantified_roles=61,same_source_in_old_and_new_model_family=True,printed_equality_not_added_to_antecedent=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={x['id']:x for x in inv['math']};units=[]
    for u in inv['units'][192:194]:
        assert digest(u['text'].encode())==u['text_sha256']
        units.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],math=[dict(id=n,sha256=math[n]['sha256'],mathml=math[n]['mathml']) for n in u['math_ids']]))
    assert 'Verbindungslinie' in units[0]['text'] and 'Wellennormale (Strahlrichtung)' in units[0]['text']
    assert 'a' in ''.join(ET.fromstring(math['M0339']['mathml']).itertext())
    return dict(status='literal_line_geometry_prepared_author_presentation_pending',units=units,observations=LIMITS,unresolved=['φ′の命名規則と括弧の同定、a′の式からの書換え提示、コロンと表示への著者帰属、全単位判断。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==375 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert all(d['kind']=='definition' for d in new.document['declarations'][len(old.document['declarations']):])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    doc=core()
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,old_375_statements_and_judgments_preserved=True,no_new_source_completion_claim=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('simultaneity',simultaneity_checks),('direction',direction_checks),('limit',limit_checks),('angle',angle_checks),('binding',binding_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_distant_direction_geometry','check_velocity_angle_measure','check_wave_cycle_frequency','check_resting_charge_force','check_doppler_specialization','compose_doppler_specialization','compose_observed_doppler','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_aberration_line.py','scripts/check_aberration_line.py','tests/test_aberration_line.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='simultaneous_connecting_line_and_wave_normal_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
