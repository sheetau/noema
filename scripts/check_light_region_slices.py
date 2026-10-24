"""Check closed interiors, simultaneous slicing and physical identity bindings."""
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
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_aberration_line import setup as previous_setup
from scripts.check_wave_transform_application import point
from scripts.check_radiative_density import CONSTANTS,DOMAIN as PRIOR_DOMAIN
from scripts.compose_light_region_slices import *

DOC='docs/light-region-slices-v1.md';SOURCE='data/einstein-radiative-density-reading-v1.json'
DEPENDENCIES=('reports/density-unit-scope-v1.json','reports/geometric-volumes-v1.json','reports/transported-contents-v1.json')
DOMAIN=tuple(dict.fromkeys([*PRIOR_DOMAIN,*[n for n,t in PAIR if t=='a']]))
BOUNDS={'ekl4':{'ekl3','sede'},'ekl5':set()}

def setup():
    cuts,m=previous_setup()
    return cuts,m|{'be':lambda x:cuts.make(-cuts.read(x))}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if mode=='binding':bounds|={'ekl3','sedp'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jlrs'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jlrscapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jlrscapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native'):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jlrscapture']=capture
    result=evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def gate(xs,ys,slots,cuts):return len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,slots))
def beta(speed):return Q(1) if speed==0 else Q(5,4)
def inverse(p,s):
    x,y,z,t=map(Q,p);b=beta(s)
    return (b*(x+s*t),y,z,b*(t+s*x/25))
def inside(p,n,R):
    x,y,z,t=map(Q,p)
    return sum((pos-5*a*t)**2 for pos,a in zip((x,y,z),n))<=R*R

@lru_cache(None)
def geometry_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    directions=((1,0,0),(0,1,0),(0,0,-1),(Q(1,3),Q(2,3),Q(2,3)))
    points=((0,0,0,0),(1,0,0,0),(Q(4,5),Q(3,5),0,0),(1,2,-1,Q(1,3)),(-2,1,3,-1))
    for s,n,R in product((-3,0,3),directions,(1,2)):
        values=list(map(c,(5,s,*n,R)))
        old=run('eklw',[values[i] for i in (0,2,3,4,5)],m);new=run('eklx',values,m)
        assert run('eklz',values,m);cases+=1
        for p in points:
            assert old(*map(c,p))==inside(p,n,R);cases+=1
            assert new(*map(c,p))==inside(inverse(p,s),n,R);cases+=1
            xyz=p[:3];actual=run('ekl2',values+list(map(c,xyz)),m)
            sl=run('ekly',[new,c(0)],m)
            assert actual==sl(*map(c,xyz))==inside(inverse((*xyz,0),s),n,R);cases+=1
        for t in (-1,Q(1,3),2):
            sl=run('ekly',[new,c(t)],m)
            for xyz in ((0,0,0),(1,2,-1)):
                assert sl(*map(c,xyz))==new(*map(c,(*xyz,t)));cases+=1
    # The same spatial tuple cannot be pulled back while keeping old t=0.
    p=(Q(4,5),Q(3,5),0,0);old=inverse(p,3)
    assert inside(old,(0,1,0),1) and not inside((*old[:3],0),(0,1,0),1);cases+=1
    values=list(map(c,(5,3,0,1,0,1)));new=run('eklx',values,m)
    assert new(*map(c,p)) and run('ekl2',values+list(map(c,p[:3])),m);cases+=1
    # Positive volume includes interior points, not just the boundary.
    assert new(*map(c,(0,0,0,0)));cases+=1
    for bad in ((5,5,0,1,0,1),(5,-5,0,1,0,1),(0,0,0,1,0,1),(5,3,1,1,0,1),(5,3,0,1,0,0),(5,3,0,1,0,-1)):
        assert not run('eklz',list(map(c,bad)),m);cases+=1
    unknowns(lambda model:run('ekl2',values+list(map(c,p[:3])),model),m,('soy','sjd','bc'))
    return dict(cases=cases,closed_interior_not_only_surface=True,inverse_map_includes_time=True,slices_fix_their_own_frame_time=True,signed_and_zero_speed_checked=True,finite_samples_not_full_real_domain=True)

@lru_cache(None)
def physical_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    n=(0,1,0);R0=2;s=3
    values=[name if t=='a' else 'case' if t=='d' else c(q) for (name,t),q in zip(PAIR,[0]*9+[5,s,*n,R0])]
    probes=((0,0,0,0),(1,0,0,0),(2,1,0,0),(0,5,0,1),(1,2,-1,Q(1,3)))
    allowed={'frame','newframe'};calibrated=[True]
    def allocation(portion,wave,process,frame,lu,tu,region,scope,ctx):
        if (portion,wave,process,lu,tu,scope,ctx)!=('portion','wave','process','lengthunit','timeunit','scope','case') or frame not in allowed:return False
        return all(region(*map(c,p))==inside(inverse(p,s) if frame=='newframe' else p,n,R0) for p in probes)
    def calibration(first,second,lu,tu,mapping,ctx):
        if not calibrated[0] or (first,second,lu,tu,ctx)!=('frame','newframe','lengthunit','timeunit','case'):return False
        for p in probes:
            mapped=mapping(point(c,p));x,y,z,t=map(Q,p);expected=(Q(5,4)*(x-s*t),y,z,Q(5,4)*(t-s*x/25))
            if any(r(mapped(axis))!=value for axis,value in zip(('x','y','z','t'),expected)):return False
        return True
    mm=m|{'va':lambda f:f in ('frame','newframe'),'eisqt':calibration,'eistm':allocation}
    assert run('ekl3',values,mm);cases+=1
    for i,(name,t) in enumerate(PAIR[:9]):
        bad=values[:];bad[i]='other'
        assert not run('ekl3',bad,mm),(i,name);cases+=1
    for missing in ('frame','newframe'):
        allowed.remove(missing);assert not run('ekl3',values,mm);allowed.add(missing);cases+=1
    calibrated[0]=False;assert not run('ekl3',values,mm);cases+=1;calibrated[0]=True
    bad=values[:];bad[4]='frame';assert not run('ekl3',bad,mm|{'va':lambda f:True,'eisqt':lambda *xs:True,'eistm':lambda *xs:True});cases+=1
    unknowns(lambda model:run('ekl3',values,model),mm,('eistm','eisqt','va'))
    return dict(cases=cases,same_portion_wave_process_scope_and_units_in_both_frames=True,all_four_calibrated_coordinate_components_checked=True,unknown_allocation_not_inferred_from_geometry=True,model_assignment_not_conservation_proof=True)

@lru_cache(None)
def binding_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;slots=fixture('ekl4','binding')[1];cases=0
    values=[n if t=='a' else 'case' if t=='d' else sentinel(sort,i+1,cuts) for i,((n,t),(_,sort)) in enumerate(zip(VOLUMES,slots))]
    body=[values[i] for i in range(len(PAIR))];geo=values[9:]
    mm=m|{'ekl3':lambda *xs:gate(xs,body,slots[:len(PAIR)],cuts),'sedp':lambda *xs:gate(xs,geo,slots[9:],cuts)}
    assert run('ekl4',values,mm,'binding');cases+=1
    for i,(_,sort) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts);assert not run('ekl4',bad,mm,'binding'),i;cases+=1
    unknowns(lambda model:run('ekl4',values,model,'binding'),mm,('ekl3','sedp'))
    return dict(cases=cases,all_18_roles_bound=True,same_radius_pi_and_two_volumes=True,volume_ratio_not_assumed=True)

@lru_cache(None)
def volume_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;observed=[]
    for s,n,R0 in product((-3,0,3),((1,0,0),(0,1,0),(Q(1,3),Q(2,3),Q(2,3))),(1,2)):
        pi=Q(3,4);D=beta(s)*(1-Q(s,5)*n[0]);S=Q(4,3)*pi*R0**3;newS=S/D
        values=[name if t=='a' else 'case' if t=='d' else c(q) for (name,t),q in zip(VOLUMES,[0]*9+[5,s,*n,R0,pi,S,newS])]
        seen=[]
        def integral(lo,hi,f,value):
            lo,hi,value=map(r,(lo,hi,value));samples=tuple(r(f(c(x))) for x in (0,Q(1,3),1))
            seen.append((lo,hi,samples,value))
            return any((lo,hi)==(-R0/factor,R0/factor) and value==S/factor and samples==tuple(pi*(R0**2-(factor*x)**2) for x in (0,Q(1,3),1)) for factor in (1,D))
        mm=m|{'ekl3':lambda *xs:True,'sedi':lambda x:r(x)==pi,'sede':integral}
        assert run('ekl4',values,mm);cases+=1
        assert len(seen)==2 and seen[0][:2]==(-R0,R0) and seen[1][:2]==(-R0/D,R0/D);cases+=1
        assert run('ekl5',values,mm);cases+=1
        assert run('ekl6',[c(S),c(newS)],m)==(D==1);cases+=1
        assert run('ekl7',[c(S),c(newS)],m)==(D!=1);cases+=1
        for i in (14,15,16,17):
            bad=values[:];bad[i]=c(r(bad[i])+Q(1,7));assert not run('ekl4',bad,mm);cases+=1
        assert not run('ekl4',values,mm|{'sede':lambda *xs:False});cases+=1
        if s==3 and n[0]==Q(1,3):
            assert D==1 and S==newS;observed.append(dict(speed='3',light='5',direction=['1/3','2/3','2/3'],radius=str(R0),factor=str(D),volume=str(S)))
        unknowns(lambda model:run('ekl4',values,model),mm,('sedi','sede','ekl3'))
    for name in ('ekl6','ekl7'):
        for pair in ((0,0),(-1,1),(1,0)):
            assert not run(name,list(map(c,pair)),m);cases+=1
    return dict(cases=cases,equal_volume_at_nonzero_speed=observed,both_integral_bounds_and_integrands_bound=True,pi_is_diagnostic_oracle_not_actual_pi=True,volume_formula_not_universal_integral_proof=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==386
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[385])==selection_binding(old,[385])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/density-unit-scope-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names={d['name'] for d in extract_document(new.document,roots=['ekl4'],statement_indices=[]).document['declarations']}
    assert {'eistm','eisqt','secc','s6m','sedi','sedp'}<=names
    assert not {'sech','sefa','segi','ekk6','ekl6','ekl7'}&names
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),all_386_statements_and_judgments_preserved=True,no_new_sentence_or_whole_unit_certification=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('geometry',geometry_checks),('physical',physical_checks),('binding',binding_checks),('volume',volume_checks),('structure',structure_checks)]}
    helpers=('compose_density_unit_scope','compose_field_equations','compose_material_relative_frame','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_aberration_line','check_wave_transform_application','check_radiative_density','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,*DEPENDENCIES,'scripts/compose_light_region_slices.py','scripts/check_light_region_slices.py','tests/test_light_region_slices.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_radiation_portion_simultaneous_volume_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
