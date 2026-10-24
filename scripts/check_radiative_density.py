"""Check density units, cycle means and relative flux without source certification."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from noema.polynomial_proofs import verify_universal
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_aberration_line import setup
from scripts.check_observed_intensity import CONSTANTS,DOMAIN
from scripts.check_radiative_intensity import cross,dot
from scripts.check_real_products import assertion,MEANINGS as POLYNOMIAL
from scripts.compose_radiative_density import *

DOC='docs/radiative-density-v1.md';SOURCE='data/einstein-radiative-density-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p913-0.jpg'
DEPENDENCIES=('reports/seventh-section-heading-v1.json','reports/observed-intensity-v1.json','reports/radiative-intensity-v1.json','reports/observed-amplitude-v1.json','reports/geometric-volumes-v1.json')
BOUNDS={'ekk3':{'sede'},'ekk4':{'ekjz','ekk3'},'eklb':{'eket','ekkz','ekk4'}}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*(n for n,t in DENSITY_MODEL if t=='a')]))

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'bg','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jrdf'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jrdfcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jrdfcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model):
    doc,slots=fixture(name);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jrdfcapture']=capture
    result=evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def values_for(fields,cuts,root):return [n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(fields,fixture(root)[1]))]
def gate(xs,ys,slots,cuts):return len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,slots))

@lru_cache(None)
def density_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for coef,V,E,H in product((Q(1,3),Q(2)),(Q(5),Q(2,3)),((0,0,0),(1,2,-3)),((0,0,0),(4,-2,1))):
        values=list(map(c,(coef,V,*E,*H)));expected=coef*(dot(E,E)+dot(H,H))/(2*V)
        assert r(run('ekkw',values,m))==expected;cases+=1
        profile=FunctionValue((RS,),RS,lambda t:c(2*r(t)-1));fn=run('ekkx',values+[profile],m)
        for t in (-1,0,Q(1,2),2):assert r(fn(c(t)))==expected*(2*t-1)**2;cases+=1
    directions=((1,0,0),(-1,0,0),(0,0,1),(Q(3,5),Q(4,5),0))
    for n,V,pi,A in product(directions,(Q(5),Q(2,3)),(Q(3),Q(4)),(Q(0),Q(2),Q(5))):
        coef=V/(4*pi);E=(-A*n[1],A*n[0],0) if not n[2] else (A,0,0);H=cross(n,E);rho=A*A/(8*pi)
        values=list(map(c,(coef,V,pi,*n,*E,*H,A,rho)));mm=m|{'sedi':lambda x:r(x)==pi}
        assert run('ekk5',values,mm);assert run('sedr',list(map(c,(pi,A*A,rho))),mm);cases+=2
        for i in (0,1,2,12,13):
            bad=values[:];bad[i]=c(r(bad[i])+Q(1,7));assert not run('ekk5',bad,mm);cases+=1
        if A:
            wrong=values[:];wrong[9:12]=map(c,(-x for x in H));assert not run('ekk5',wrong,mm);cases+=1
    mm=m|{'sedi':lambda x:r(x)==4};good=list(map(c,(Q(5,16),5,4)))
    assert run('ekk2',good,mm);cases+=1
    for bad in [(0,5,4),(-1,5,4),(1,-1,4),(1,0,4),(1,5,4)]:
        assert not run('ekk2',list(map(c,bad)),mm);cases+=1
    unknowns(lambda model:run('ekk2',good,model),mm,('sedi','shv','sca'))
    return dict(cases=cases,electric_and_magnetic_contributions_kept=True,gaussian_coefficient_and_mean_not_confused_with_peak=True,zero_amplitude_allowed=True,diagnostic_pi_not_the_actual_circle_constant=True)

@lru_cache(None)
def average_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    density=(Q(2),Q(5),Q(1),Q(2),Q(3),Q(4),Q(5),Q(6));K=density[0]*sum(x*x for x in density[2:])/(2*density[1])
    for slope,offset,lo,hi in ((0,1,0,2),(1,0,0,3),(2,-1,-2,1),(-1,3,1,4)):
        profile=FunctionValue((RS,),RS,lambda t,a=slope,b=offset:c(a*r(t)+b));integral=K*(Q(slope*slope,3)*(hi**3-lo**3)+slope*offset*(hi**2-lo**2)+offset*offset*(hi-lo));mean=integral/(hi-lo)
        values=[*map(c,density),profile,*map(c,(lo,hi,integral,mean))]
        def integrated(a,b,function,value):return r(a)==lo and r(b)==hi and r(value)==integral and all(r(function(c(t)))==K*(slope*t+offset)**2 for t in (-2,0,1,3))
        mm=m|{'sede':integrated};assert run('ekk3',values,mm);cases+=1
        for i in range(len(values)):
            bad=values[:];bad[i]=FunctionValue((RS,),RS,lambda t:c(r(profile(t))+1)) if i==8 else c(r(bad[i])+Q(1,7))
            assert not run('ekk3',bad,mm),(slope,offset,i);cases+=1
        for lower,upper in ((hi,lo),(lo,lo)):
            bad=values[:];bad[9:11]=map(c,(lower,upper));assert not run('ekk3',bad,mm);cases+=1
        unknowns(lambda model:run('ekk3',values,model),mm,('sede',))
    # Capture the exact native time profile and the period-dependent integral.
    sine=FunctionValue((RS,),RS,lambda t:c(1 if r(t)%2<1 else 0));cosine=FunctionValue((RS,),RS,lambda t:c(1 if (r(t)+Q(1,2))%2<1 else 0))
    for rate,offset in ((Q(1),Q(0)),(Q(3),Q(1,3))):
        period=2/rate;rho=K/2;tw=[sine,cosine,*map(c,(1,2,rate,offset,period,1/period))];values=[*map(c,density),*tw,c(rho)]
        def mean(*xs):
            return gate(xs[:8],values[:8],fixture('ekkw')[1],cuts) and tuple(map(r,xs[9:]))==(0,period,period*rho,rho) and all(r(xs[8](c(t)))==r(sine(c(rate*t+offset))) for t in (Q(0),Q(1,7),Q(2,3)))
        mm=m|{'ekjz':lambda *xs:gate(xs,tw,fixture('ekjz')[1],cuts),'ekk3':mean}
        assert run('ekk4',values,mm);cases+=1
        for i,(_,s) in enumerate(fixture('ekk4')[1]):
            bad=values[:];bad[i]=sentinel(s,100+i,cuts);assert not run('ekk4',bad,mm);cases+=1
        unknowns(lambda model:run('ekk4',values,model),mm,('ekjz','ekk3'))
    return dict(cases=cases,same_profile_interval_integral_and_mean=True,distinct_period_and_offset_preserved=True,periodic_diagnostics_not_sine_integral_proofs=True)

@lru_cache(None)
def physical_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    values=values_for(DENSITY_MODEL,cuts,'ekkz');pos={n:i for i,(n,t) in enumerate(DENSITY_MODEL)}
    for n,value in dict(coefficient=2,light=5,ex=1,ey=2,ez=3,hx=4,hy=5,hz=6).items():values[pos[n]]=c(value)
    sine=FunctionValue((RS,),RS,lambda x:c(r(x)+1));phase=FunctionValue((RS,RS,RS,RS),RS,lambda x,y,z,t:c(r(x)+2*r(y)+3*r(z)+5*r(t)))
    values[pos['sine']]=sine;values[pos['phase']]=phase;field=run('ekky',[values[pos[n]] for n,t in SCALAR],m)
    for point in ((0,0,0,0),(1,2,-1,3),(-2,1,4,-1)):
        assert r(field(*map(c,point)))==Q(91,5)*(sum(a*b for a,b in zip(point,(1,2,3,5)))+1)**2;cases+=1
    def calibration(*xs):return gate(xs,[values[pos[n]] for n,t in COEFFICIENT],[(n,fixture('ekkz')[1][pos[n]][1]) for n,t in COEFFICIENT],cuts)
    def density(wave,process,frame,lu,tu,eu,region,actual,scope,ctx):
        if (wave,process,frame,lu,tu,eu,scope,ctx)!=('wave','process','frame','lengthunit','timeunit','energyunit','scope','case'):return False
        return same_value(region,values[pos['region']],fixture('ekkz')[1][pos['region']][1],cuts) and all(r(actual(*map(c,point)))==r(field(*map(c,point))) for point in ((0,0,0,0),(1,2,-1,3)))
    mm=m|{'eiste':calibration,'eistj':density};assert run('ekkz',values,mm);cases+=1
    for i,(_,s) in enumerate(fixture('ekkz')[1]):
        bad=values[:];bad[i]=sentinel(s,100+i,cuts);assert not run('ekkz',bad,mm),(i,DENSITY_MODEL[i]);cases+=1
    unknowns(lambda model:run('ekkz',values,model),mm,('eiste','eistj','shv'))
    return dict(cases=cases,same_wave_process_frame_units_region_and_density_field=True,work_calibration_reused=True,physical_correspondence_not_inferred_from_numbers=True)

@lru_cache(None)
def transport_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    sine=FunctionValue((RS,),RS,lambda t:c(r(t)+1));phase=FunctionValue((RS,RS,RS,RS),RS,lambda x,y,z,t:c(r(x)-r(y)+2*r(z)-3*r(t)))
    directions=((1,0,0),(-1,0,0),(0,0,1),(Q(3,5),Q(4,5),0));points=((0,0,0,0),(1,2,3,4),(-2,1,0,-1))
    for n,V,coef,A in product(directions,(Q(5),Q(2,3)),(Q(2),Q(1,7)),(Q(0),Q(3))):
        E=(-A*n[1],A*n[0],0) if not n[2] else (A,0,0);H=cross(n,E)
        values=[*map(c,(coef,V,*E,*H)),sine,phase,*map(c,n)];rel=run('ekla',values,m)
        for axis,point in product(('x','y','z','body'),points):assert r(rel(axis)(*map(c,point)))==0;cases+=1
        if A:
            base=[*map(c,(coef,V,*E,*H)),sine,phase];density=run('ekky',base,m);flux=run('ekka',[c(coef),sine,phase,*map(c,(*E,*H))],m)
            for factor in (0,-1,Q(1,2)):
                velocity=run('ekk7',list(map(c,(V*factor,*n))),m);relative=run('ekk6',[flux,density,velocity],m)
                for axis,component in zip(('x','y','z'),n):
                    actual=r(relative(axis)(*map(c,(0,0,0,0))));assert actual==coef*A*A*component*(1-factor);cases+=1
    nonplane=[*map(c,(2,5,1,0,0,0,1,0)),sine,phase,*map(c,(1,0,0))];rel=run('ekla',nonplane,m)
    assert [r(rel(axis)(*map(c,(0,0,0,0)))) for axis in ('x','y','z')]==[-2,0,2];cases+=1
    unknowns(lambda model:run('ekla',nonplane,model)('x')(*map(c,(0,0,0,0))),m,('shv','bf'))
    return dict(cases=cases,zero_relative_flux_in_all_components_for_transverse_wave=True,wrong_boundary_velocity_and_nontransverse_field_distinguished=True,nonspatial_extension_zero=True,no_surface_normal_assumed_equal_to_wave_normal=True)

@lru_cache(None)
def setting_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;values=values_for(SETTING,cuts,'eklb');slots=fixture('eklb')[1];pos={n:i for i,(n,t) in enumerate(SETTING)}
    for n,value in dict(light=5,speed=3,rate=1,ax=0,ay=1,az=0,ex=0,ey=0,ez=5,hx=5,hy=0,hz=0,amplitude=5,newamplitude=Q(25,4),coefficient=Q(5,16),density=Q(25,32),newdensity=Q(625,512),pi=4,cycle=8,oldperiod=8,newperiod=Q(32,5),frequency=Q(1,8),newfrequency=Q(5,32),newoffset=2).items():values[pos[n]]=c(value)
    models=[];averages=[]
    def collect(target):
        def accept(*xs):target.append(xs);return True
        return accept
    mm=m|{'sedi':lambda x:r(x)==4,'eket':lambda *xs:gate(xs,values[:60],slots[:60],cuts),'ekkz':collect(models),'ekk4':collect(averages)}
    assert run('eklb',values,mm);assert len(models)==len(averages)==2;cases+=1
    mp={n:i for i,(n,t) in enumerate(DENSITY_MODEL)};ap={n:i for i,(n,t) in enumerate(CYCLE)}
    for i in range(2):
        assert models[i][mp['frame']]==('frame' if i==0 else CONSTANTS['zbm']);cases+=1
        expected=(0,0,5,5,0,0) if i==0 else (0,0,Q(25,4),5,Q(15,4),0)
        assert tuple(r(models[i][mp[n]]) for n in ('ex','ey','ez','hx','hy','hz'))==expected;cases+=1
        assert tuple(r(averages[i][ap[n]]) for n in ('light','coefficient','rate','offset','period','frequency','density'))==((5,Q(5,16),1,0,8,Q(1,8),Q(25,32)) if i==0 else (5,Q(5,16),Q(5,4),2,Q(32,5),Q(5,32),Q(625,512)));cases+=1
        assert tuple(r(averages[i][ap[n]]) for n in ('ex','ey','ez','hx','hy','hz'))==expected;cases+=1
    mm=m|{'sedi':lambda x:r(x)==4,'eket':lambda *xs:gate(xs,values[:60],slots[:60],cuts),'ekkz':lambda *xs:any(gate(xs,row,fixture('ekkz')[1],cuts) for row in models),'ekk4':lambda *xs:any(gate(xs,row,fixture('ekk4')[1],cuts) for row in averages)}
    assert run('eklb',values,mm);cases+=1
    for i,(_,s) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(s,100+i,cuts)
        try:actual=run('eklb',bad,mm)
        except (ValueError,ZeroDivisionError):pass
        else:assert not actual,(i,SETTING[i])
        cases+=1
    assert run('eklc',values,mm) and run('ekld',values,mm);cases+=2
    for name,field in [('eklc','density'),('ekld','newdensity')]:
        bad=values[:];bad[pos[field]]=c(1);assert not run(name,bad,mm);cases+=1
    unknowns(lambda model:run('eklb',values,model),mm,('eket','ekkz','ekk4','sedi'))
    return dict(cases=cases,all_66_roles_shared_between_frames=True,non_head_on_example_keeps_distinct_amplitude_period_and_density=True,no_old_printed_amplitude_law_added_to_premise=True)

@lru_cache(None)
def polynomial_checks():
    base='n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'
    z='n p a b';two='n p c b';four='n p e b';eight='n p i b';one='n p b b'
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sub=lambda a,b:add(a,k('ac',b));eq=lambda a,b:op('e',a,b);lt=lambda a,b:k('aa',a,b)
    dotp=lambda a,b:add(mul(a[0],b[0]),add(mul(a[1],b[1]),mul(a[2],b[2])))
    crossp=lambda a,b:[sub(mul(a[1],b[2]),mul(a[2],b[1])),sub(mul(a[2],b[0]),mul(a[0],b[2])),sub(mul(a[0],b[1]),mul(a[1],b[0]))]
    n=[v(s) for s in ('nx','ny','nz')];E=[v(s) for s in ('ex','ey','ez')];H=crossp(n,E);d=dotp(n,E);e2=dotp(E,E)
    claims={'cross_norm_identity':assertion('nx ny nz ex ey ez',eq(dotp(H,H),sub(mul(dotp(n,n),e2),mul(d,d))))}
    X=crossp(E,H)
    claims['triple_product_identity']=assertion('nx ny nz ex ey ez',both(*(eq(X[i],sub(mul(n[i],e2),mul(E[i],d))) for i in range(3))))
    V,coef,pi,power,mean,peak=map(v,('light','coefficient','pi','power','mean','peak'))
    claims['gaussian_cycle_mean_density']=assertion('light coefficient pi power mean peak',op('y',both(lt(z,V),eq(mul(mul(four,pi),coef),V),eq(mul(mul(two,V),peak),mul(coef,mul(two,power))),eq(mul(two,mean),peak)),eq(mul(mul(eight,pi),mean),power)))
    h2,nx,p2,rho,flux=map(v,('magnetic','nx','profile','density','flux'))
    claims['same_light_speed_boundary_zero_flux']=assertion('light coefficient power magnetic nx profile density flux',op('y',both(lt(z,V),eq(h2,power),eq(mul(mul(two,V),rho),mul(mul(coef,add(power,h2)),p2)),eq(flux,mul(mul(mul(coef,nx),power),p2))),eq(sub(flux,mul(mul(V,nx),rho)),z)))
    rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),POLYNOMIAL,timeout_ms=20000)[0];assert result['status']=='valid',(name,result);rows[name]=result
    return dict(lemmas=rows,real_integral_or_physical_conservation_automatically_proved=False)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][202:205];math={x['id']:x for x in inv['math']}
    expected={'M0349':'A2/8π','M0350':'A′2/8π','M0351':'A′2/A2','M0352':'K','M0353':'k','M0354':'a,b,c','M0355':'(x−Vat)2+(y−Vbt)2+(z−Vct)2=R2','M0356':'k','M0357':'k'}
    for name,plain in expected.items():assert ''.join(ET.fromstring(math[name]['mathml']).itertext()).strip()==plain
    for u in units:assert digest(u['text'].encode())==u['text_sha256']
    return dict(status='density_and_relative_flux_dependencies_source_presentation_pending',units=[dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],math=[dict(id=n,sha256=math[n]['sha256'],mathml=math[n]['mathml']) for n in u['math_ids']]) for u in units],observations=LIMITS,unresolved=[LIMITS[-1]],interpretation_references=['https://www.feynmanlectures.caltech.edu/II_27.html'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==385 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/seventh-section-heading-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),all_385_statements_and_judgments_preserved=True,no_new_source_completion_claim=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('density',density_checks),('average',average_checks),('physical',physical_checks),('transport',transport_checks),('setting',setting_checks),('polynomial',polynomial_checks),('structure',structure_checks)]}
    helpers=('compose_seventh_section_heading','compose_observed_intensity','compose_wave_transform_application','compose_field_equations','compose_material_relative_frame','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_aberration_line','check_observed_intensity','check_radiative_intensity','check_real_products','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_radiative_density.py','scripts/check_radiative_density.py','tests/test_radiative_density.py','noema/polynomial_proofs.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='radiative_density_and_relative_boundary_flux_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
