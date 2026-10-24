"""Check pointwise phase means, spatial integrals, physical roles and ratios."""
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
from noema.polynomial_proofs import verify_universal
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_light_region_slices import setup,CONSTANTS,DOMAIN as PREVIOUS
from scripts.check_resting_charge_force import retag
from scripts.check_wave_cycle_frequency import refused
from scripts.check_real_products import assertion,MEANINGS as POLYNOMIAL
from scripts.compose_geometric_volumes import generic_composed
from scripts.compose_mean_light_energy import *

DOC='docs/mean-light-energy-v1.md';SOURCE='data/einstein-radiative-density-reading-v1.json'
DEPENDENCIES=('reports/light-region-slices-v1.json','reports/density-unit-scope-v1.json','reports/radiative-density-v1.json','reports/geometric-volumes-v1.json')
DOMAIN=tuple(dict.fromkeys([*PREVIOUS,*[n for n,t in FRAME+TOTAL if t=='a'],'section8']))
CONSTANTS=CONSTANTS|{'eistk':'section8'}
BOUNDS={'ekmb':{'sede'},'ekmc':{'ekmb'},'ekmd':{'ekmc'},'ekme':{'ekkz','ekc3','ekmd'},'ekmf':{'sede'},'ekmg':{'sede'},'ekmi':{'eklp','eklg','eklh','ekl4','ekme','ekmg'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set()))
    doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name)
        body=d['body']['arguments'][1];pivot=int(mode.split(':')[1]);retained=None
        for i,(n,t) in enumerate(XYZ):
            assert body['kind']=='forall'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']['arguments'][1]=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jmle'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jmlecapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jmlecapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jmlecapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def values_for(fields,cuts,root):return [n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(fields,fixture(root)[1]))]
def gate(xs,ys,slots,cuts):return len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,slots))

@lru_cache(None)
def phase_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    coefficients=(Q(2),Q(5),Q(1),Q(2),Q(3),Q(4),Q(5),Q(6));K=Q(91,5)
    for offset,cycle in product((Q(-2),Q(0),Q(1,3)),(Q(1),Q(3))):
        # Polynomial diagnostic, never certified as the physical sine.
        sine=FunctionValue((RS,),RS,lambda theta:c(r(theta)))
        values=[*map(c,coefficients),sine,c(offset)];fn=run('ekma',values,m)
        for t in (-1,0,Q(2,3),2):assert r(fn(c(t)))==K*(offset+t)**2;cases+=1
        mean=K*(offset*offset+offset*cycle+cycle*cycle/3)
        actual=values+[c(cycle),c(mean)]
        def integrated(lo,hi,f,value):
            return (r(lo),r(hi),r(value))==(0,cycle,cycle*mean) and all(r(f(c(t)))==K*(offset+t)**2 for t in (-1,0,Q(1,3),2))
        mm=m|{'sede':integrated};assert run('ekmb',actual,mm);cases+=1
        for i,(_,sort) in enumerate(fixture('ekmb')[1]):
            bad=actual[:];bad[i]=sentinel(sort,100+i,cuts)
            assert not run('ekmb',bad,mm),(offset,cycle,i);cases+=1
        for cyc in (-1,0):
            bad=actual[:];bad[-2]=c(cyc);assert not run('ekmb',bad,mm);cases+=1
        unknowns(lambda model:run('ekmb',actual,model),mm,('sede','shv'))
    # A fixed point can have zero instantaneous density and a positive phase mean.
    sine=FunctionValue((RS,),RS,lambda theta:c(0 if r(theta)%2<1 else 1))
    values=[*map(c,coefficients),sine,c(0)];fn=run('ekma',values,m)
    assert r(fn(c(0)))==0 and r(fn(c(Q(3,2))))==K;cases+=1
    mm=m|{'sede':lambda lo,hi,f,value:(r(lo),r(hi),r(value))==(0,2,K) and r(f(c(0)))==0 and r(f(c(Q(3,2))))==K}
    assert run('ekmb',values+[c(2),c(K/2)],mm);cases+=1
    return dict(cases=cases,independent_phase_shift_not_time_evolution=True,offset_cycle_integral_and_density_all_bound=True,instantaneous_value_not_used_as_mean=True,diagnostics_not_sine_integral_proofs=True)

@lru_cache(None)
def spatial_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    fields=SPATIAL+XYZ;slots=fixture('ekmc')[1];values=values_for(fields,cuts,'ekmc');pos={n:i for i,(n,t) in enumerate(fields)}
    phase=FunctionValue((RS,RS,RS,RS),RS,lambda x,y,z,t:c(r(x)+2*r(y)+3*r(z)-5*r(t)))
    p=(Q(1),Q(2),Q(-1),Q(3));location=tuple(map(c,p))
    region=FunctionValue((RS,RS,RS,RS),'truth',lambda *xs:tuple(map(r,xs))==p)
    values[pos['phase']]=phase;values[pos['region']]=region;values[pos['portionregion']]=region
    for n,x in zip(('x','y','z','time'),p):values[pos[n]]=c(x)
    expected=[phase(*location) if n=='offset' else values[pos[n]] for n,t in MEAN]
    mm=m|{'ekmb':lambda *xs:gate(xs,expected,fixture('ekmb')[1],cuts)}
    assert run('ekmc',values,mm);cases+=1
    assert not run('ekmc',values,mm|{'ekmb':lambda *xs:False});cases+=1
    wrong=values[:];wrong[pos['region']]=FunctionValue((RS,RS,RS,RS),'truth',lambda *xs:False)
    assert not run('ekmc',wrong,mm);cases+=1
    wrong=values[:];wrong[pos['phase']]=FunctionValue((RS,RS,RS,RS),RS,lambda *xs:c(17))
    assert not run('ekmc',wrong,mm);cases+=1
    wrong=values[:];wrong[pos['portionregion']]=FunctionValue((RS,RS,RS,RS),'truth',lambda *xs:False)
    assert run('ekmc',wrong,mm|{'ekmb':lambda *xs:False});cases+=1
    for i,(n,t) in enumerate(fields):
        if n in ('region','portionregion','phase','x','y','z','time'):continue
        wrong=values[:];wrong[i]=sentinel(slots[i][1],100+i,cuts);assert not run('ekmc',wrong,mm),n;cases+=1
    unknowns(lambda model:run('ekmc',values,model),mm,('ekmb',))
    for pivot in range(3):
        mode=f'slot:{pivot}';base=['a' if i%2 else 'b' for i in range(len(SPATIAL))];other=['a','b'];vals=base+other
        assert run('ekmd',vals,{'ba':lambda x:True,'ekmc':lambda *xs:True},mode,('a','b'));cases+=1
        for target in ('a','b'):
            def condition(*xs,target=target):return xs[len(SPATIAL)+pivot]!=target
            assert not run('ekmd',vals,{'ba':lambda x:True,'ekmc':condition},mode,('a','b'));cases+=1
        assert not run('ekmd',vals,{'ba':lambda x:False,'ekmc':lambda *xs:True},mode,('a','b'));cases+=1
    native=values[:len(SPATIAL)]
    refused(lambda:run('ekmd',native,m|{'ekmc':lambda *xs:True}));cases+=1
    return dict(cases=cases,same_phase_at_all_slice_points=True,portion_must_be_inside_physical_density_region=True,three_universal_slots_each_tested=True,unbounded_cut_domain_refused=True)

@lru_cache(None)
def physical_checks():
    cuts,m=setup();cases=0;values=values_for(FRAME,cuts,'ekme');slots=fixture('ekme')[1];pos={n:i for i,(n,t) in enumerate(FRAME)}
    expected={name:[values[pos[n]] for n,t in fs] for name,fs in [('ekkz',DENSITY_MODEL),('ekc3',HARMONIC),('ekmd',SPATIAL)]}
    fs_by_name=dict(ekkz=DENSITY_MODEL,ekc3=HARMONIC,ekmd=SPATIAL)
    models={name:(lambda *xs,name=name:gate(xs,expected[name],[slots[pos[n]] for n,t in fs_by_name[name]],cuts)) for name in expected}
    loc=[values[pos['portionregion' if n=='region' else n]] for n,t in LOCATION]
    locsorts=[slots[pos['portionregion' if n=='region' else n]] for n,t in LOCATION]
    models['eistm']=lambda *xs:gate(xs,loc,locsorts,cuts)
    mm=m|models;assert run('ekme',values,mm);cases+=1
    for i,(_,sort) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts);assert not run('ekme',bad,mm),(i,FRAME[i]);cases+=1
    for name in models:
        assert not run('ekme',values,mm|{name:lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekme',values,model),mm,tuple(models))
    return dict(cases=cases,density_model_part_assignment_harmonic_and_all_points_required=True,all_29_roles_shared=True,work_energy_units_inherited_through_ekkz=True)

@lru_cache(None)
def integral_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for R0,D,rho in product((Q(1),Q(2)),(Q(1),Q(5,4)),(Q(0),Q(2,3),Q(3))):
        pi=Q(3,4);S=Q(4,3)*pi*R0**3/D;E=rho*S;seen=[]
        def integral(lo,hi,f,value):
            bounds=(r(lo),r(hi));samples=tuple(r(f(c(x))) for x in (0,Q(1,3),1));value=r(value);seen.append((bounds,samples,value))
            return bounds==(-R0/D,R0/D) and any(samples==tuple(weight*pi*(R0**2-D**2*x*x) for x in (0,Q(1,3),1)) and value==weight*S for weight in (Q(1),rho))
        values=list(map(c,(R0,pi,D,rho,E,S)));mm=m|{'sedi':lambda x:r(x)==pi,'sede':integral}
        assert run('ekmg',values,mm);cases+=1
        assert len(seen)==2;cases+=1
        assert run('ekmh',list(map(c,(S,rho,E))),m);cases+=1
        for i in range(6):
            bad=values[:];bad[i]=c(r(bad[i])+Q(1,7));assert not run('ekmg',bad,mm),(R0,D,rho,i);cases+=1
        assert not run('ekmg',values,mm|{'sede':lambda *xs:False});cases+=1
        unknowns(lambda model:run('ekmg',values,model),mm,('sede','sedi'))
    return dict(cases=cases,same_weighted_and_unweighted_spatial_integrals=True,zero_energy_allowed=True,energy_equals_density_times_volume_is_separate_conclusion=True,finite_integral_oracles_not_analytic_proof=True)

@lru_cache(None)
def setting_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;values=values_for(TOTAL,cuts,'ekmi');slots=fixture('ekmi')[1];pos={n:i for i,(n,t) in enumerate(TOTAL)}
    for n,x in dict(light=5,speed=3,ax=0,ay=1,az=0,ex=0,ey=0,ez=5,hx=5,hy=0,hz=0,rate=Q(1,5),radius=2,pi=Q(3,4),amplitude=5,newamplitude=Q(25,4),coefficient=Q(5,3),volume=8,newvolume=Q(32,5),energy=Q(100,3),newenergy=Q(125,3)).items():values[pos[n]]=c(x)
    names=('eklp','eklg','eklh','ekl4','ekme','ekmg');seen={n:[] for n in names}
    captures={n:(lambda *xs,n=n:seen[n].append(xs) or True) for n in names}
    assert run('ekmi',values,m|captures);cases+=1
    assert {n:len(rows) for n,rows in seen.items()}==dict(eklp=1,eklg=1,eklh=1,ekl4=1,ekme=2,ekmg=2)
    for name in ('eklp','eklg','eklh'):assert gate(seen[name][0],values[:len(BASE)],slots[:len(BASE)],cuts)
    pair={n:values[pos[n]] for n,t in TOTAL}|{'newframe':CONSTANTS['zbm'],'scope':'section8'}
    pairslots=[slots[pos[n]] if n not in ('newframe','scope') else ('', 'individual') for n,t in VOLUMES]
    assert gate(seen['ekl4'][0],[pair[n] for n,t in VOLUMES],pairslots,cuts)
    fp={n:i for i,(n,t) in enumerate(FRAME)}
    for row,frame,amps,rho in zip(seen['ekme'],(values[pos['frame']],CONSTANTS['zbm']),((0,0,5,5,0,0),(0,0,Q(25,4),5,Q(15,4),0)),(Q(25,6),Q(625,96))):
        assert row[fp['frame']]==frame and row[fp['scope']]=='section8' and row[fp['portion']]==values[pos['portion']]
        assert tuple(r(row[fp[n]]) for n in ('ex','ey','ez','hx','hy','hz'))==amps
        assert r(row[fp['time']])==0 and r(row[fp['density']])==rho
        # Full spacetime phase and support are inspected, not only function names.
        for p in ((0,0,0,0),(1,2,3,4)):
            x,y,z,t=map(Q,p);old=(Q(5,4)*(x+3*t),y,z,Q(5,4)*(t+3*x/25)) if frame==CONSTANTS['zbm'] else (x,y,z,t)
            assert r(row[fp['phase']](*map(c,p)))==Q(1,5)*(old[3]-old[1]/5)
            assert row[fp['portionregion']](*map(c,p))==(sum((a-b*5*old[3])**2 for a,b in zip(old[:3],(0,1,0)))<=4);cases+=1
    assert [tuple(map(r,row)) for row in seen['ekmg']]==[(Q(2),Q(3,4),Q(1),Q(25,6),Q(100,3),Q(8)),(Q(2),Q(3,4),Q(5,4),Q(625,96),Q(125,3),Q(32,5))]
    # Compare every supplied role at these predicate boundaries. Native derived
    # field/phase/region functions were checked above and in predecessor reports.
    decl={d['name']:d for d in fixture('ekmi')[0]['declarations']}
    sorts={n:[('',s) for s in decl[n]['parameters']] for n in names}
    models={n:(lambda *xs,n=n:any(gate(xs,row,sorts[n],cuts) for row in seen[n])) for n in names}
    assert run('ekmi',values,m|models);cases+=1
    for i,(_,sort) in enumerate(slots):
        # Invalid speed would require evaluating an irrational/out-of-domain boost.
        if TOTAL[i][0] in ('light','speed'):continue
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts);assert not run('ekmi',bad,m|models),(i,TOTAL[i]);cases+=1
    for n in names:
        assert not run('ekmi',values,m|models|{n:lambda *xs:False});cases+=1
    assert run('ekmj',values,m);cases+=1
    for n in ('energy','newenergy','volume','newvolume','amplitude','newamplitude','pi'):
        bad=values[:];bad[pos[n]]=c(r(bad[pos[n]])+Q(1,7));assert not run('ekmj',bad,m),n;cases+=1
    unknowns(lambda model:run('ekmi',values,model),m|models,names)
    return dict(cases=cases,all_70_roles_shared=True,old_new_coefficients_phases_regions_and_density_not_swapped=True,actual_space_time_phase_and_support_checked=True,both_spatial_integrals_share_original_portion=True,ratio_not_in_premise=True)

@lru_cache(None)
def ratio_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;pi=Q(3,4);mm=m|{'sedi':lambda x:r(x)==pi}
    for A,newA,S,newS in product((Q(1),Q(2)),(Q(0),Q(3)),(Q(1),Q(2)),(Q(1),Q(2),Q(3))):
        E=A*A*S/(8*pi);newE=newA*newA*newS/(8*pi);values=list(map(c,(pi,A,newA,S,newS,E,newE)))
        assert run('ekmk',values,mm);cases+=1
        expected=(newA==0 or S==newS)
        assert run('ekml',list(map(c,(A,newA,E,newE))),m)==expected;cases+=1
        assert run('ekmm',values,mm);cases+=1
    for A,E in ((0,0),(0,1),(1,0),(-1,1),(1,-1)):
        assert not run('ekml',list(map(c,(A,2,E,1))),m);cases+=1
    unknowns(lambda model:run('ekmm',values,model),mm,('sedi','sca'))
    return dict(cases=cases,arbitrary_amplitude_ratio_allowed_under_equal_volume=True,unequal_volume_ratio_counterexamples=True,zero_new_energy_allowed_but_old_denominators_must_be_positive=True,actual_lorentz_volume_law_not_assumed=True)

@lru_cache(None)
def polynomial_checks():
    mul=lambda a,b:k('ad',a,b);sub=lambda a,b:k('ab',a,k('ac',b));sq=lambda a:mul(a,a)
    pi,radius,factor,x,rho=map(v,('pi','radius','factor','x','density'))
    primitive=lambda pi,x:k('seef',pi,radius,factor,x)
    A,B,S,E,N,C=map(v,('amplitude','newamplitude','volume','energy','newenergy','conversion'))
    claims={
      'uniform_density_primitive_linearity':assertion('pi radius factor x density',op('e',primitive(mul(rho,pi),x),mul(rho,primitive(pi,x)))),
      'uniform_density_endpoint_linearity':assertion('pi radius factor x density',op('e',sub(primitive(mul(rho,pi),x),primitive(mul(rho,pi),k('ac',x))),mul(rho,sub(primitive(pi,x),primitive(pi,k('ac',x)))))),
      'equal_volume_energy_ratio':assertion('amplitude newamplitude volume energy newenergy conversion',op('y',both(k('aa','n p a b',C),op('e',mul(C,E),mul(sq(A),S)),op('e',mul(C,N),mul(sq(B),S))),op('e',mul(N,sq(A)),mul(E,sq(B))))),
    }
    base=generic_composed()[0];rows={n:verify_universal(parse(base+s),POLYNOMIAL,timeout_ms=20000)[0] for n,s in claims.items()}
    assert all(r['status']=='valid' for r in rows.values()),rows
    return dict(lemmas=rows,rational_polynomial_only=True,integral_exchange_and_general_real_integration_not_automatically_proved=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==386
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[385])==selection_binding(old,[385])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/light-region-slices-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names={d['name'] for d in extract_document(new.document,roots=['ekmi'],statement_indices=[]).document['declarations']}
    assert {'eistm','eisqt','eiste','eistj','ekc3','sede','sedp','ekmc','ekmd'}<=names
    assert not {'ekmh','ekml','ekmm','sech','ekl6','ekl7'}&names
    independent={d['name'] for d in extract_document(new.document,roots=['ekmm'],statement_indices=[]).document['declarations']}
    assert not {'sech','sedp','ekl4','sdn2','s46'}&independent
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,all_386_statements_and_judgments_preserved=True,conditional_algebra_does_not_assume_actual_volume_transformation=True,no_new_sentence_certification=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('phase',phase_checks),('spatial',spatial_checks),('physical',physical_checks),('integral',integral_checks),('setting',setting_checks),('ratio',ratio_checks),('polynomial',polynomial_checks),('structure',structure_checks)]}
    helpers=('compose_light_region_slices','compose_density_relativity','compose_radiative_density','compose_wave_transform_application','compose_field_equations','compose_material_relative_frame','compose_limits','compose_geometric_volumes','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_light_region_slices','check_resting_charge_force','check_wave_cycle_frequency','check_real_products','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,*DEPENDENCIES,'scripts/compose_mean_light_energy.py','scripts/check_mean_light_energy.py','tests/test_mean_light_energy.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='phase_mean_spatial_energy_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
