"""Check full vector reflection, boundary fields, flux and shared cycles."""
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
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from noema.polynomial_proofs import verify_universal
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_light_energy_ratio import arithmetic
from scripts.check_wave_cycle_frequency import refused
from scripts.check_resting_charge_force import retag
from scripts.check_radiative_intensity import cross,dot
from scripts.check_real_products import assertion,MEANINGS as POLYNOMIAL
from scripts.compose_stationary_mirror_boundary import *

DOC='docs/stationary-mirror-boundary-v1.md';SOURCE='data/einstein-stationary-mirror-boundary-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p914-0.jpg'
DEPENDENCIES=('reports/energy-frequency-law-v1.json','reports/wave-cycle-frequency-v1.json','reports/observed-intensity-v1.json','reports/mirror-reflection-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'t'}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu'}
    if mode=='binding':bounds|={'ekqf','ekc7','ekql','ekqm','sejm'} if name=='ekqn' else {'ekqk','sejm'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='binding':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jsmb'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jsmbcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jsmbcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=('x','y','z','t','body')):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jsmbcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case',),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def reflection(row):
    a,b,c,ex,ey,ez,hx,hy,hz=row
    return (-a,b,c,ex,-ey,-ez,-hx,hy,hz)

def examples():
    for n in ((1,0,0),(Q(3,5),Q(4,5),0),(Q(3,5),0,Q(-4,5)),(Q(1,3),Q(2,3),Q(2,3))):
        e=(-n[1],n[0],0);h=cross(n,e)
        for p,s in ((2,0),(0,3),(2,-3)):
            E=tuple(p*a+s*b for a,b in zip(e,h));yield (*n,*E,*cross(n,E))

@lru_cache(None)
def vector_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    for row in examples():
        ref=reflection(row);values=list(map(c,(*row,*ref)))
        assert run('ekqe',values,m) and run('ekqg',values,m);cases+=2
        for i in range(18):
            bad=values[:];bad[i]=c(r(bad[i])+Q(1,7));assert not run('ekqe',bad,m),(row,i);cases+=1
        for name,inputs,expected in (('ekqb',row[:3],ref[:3]),('ekqc',row[3:6],ref[3:6]),('ekqd',row[6:],ref[6:])):
            vector=run(name,list(map(c,inputs)),m)
            for axis,want in zip(('x','y','z','t','body'),(*expected,0,0)):
                assert r(vector(axis))==want;cases+=1
        unknowns(lambda mm:run('ekqe',values,mm),m,('ba','be','sca','bg'))
    # Wrong side, grazing, longitudinal, null, or a nonunit direction is not incident radiation.
    invalid=[(-1,0,0,0,1,0,0,0,-1),(0,1,0,1,0,0,0,0,-1),(1,0,0,1,1,0,0,0,1),(1,0,0,0,0,0,0,0,0),(2,0,0,0,1,0,0,0,2)]
    for row in invalid:assert not run('ekqf',list(map(c,row)),m);cases+=1
    return dict(cases=cases,full_direction_and_six_field_components_checked=True,both_polarizations_and_mixed_polarization=True,wrong_side_grazing_longitudinal_null_nonunit_rejected=True)

@lru_cache(None)
def boundary_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0;nonzero_normal_e=False;nonzero_tangent_h=False;nonzero_tangent_flow=False
    for row in examples():
        ref=reflection(row)
        for slope,offset in ((0,1),(2,-1)):
            profile=FunctionValue((RS,),RS,lambda t,a=slope,b=offset:c(a*r(t)+b))
            values=[profile,*map(c,(5,7,*row))];E=run('ekqi',values,m);H=run('ekqj',values,m);phase=run('ekqh',list(map(c,(5,7,*row[:3]))),m)
            for xyz in ((0,0,0,0),(0,2,-3,Q(1,2)),(Q(1,3),2,-3,2)):
                phi=7*(xyz[3]-dot(ref[:3],xyz[:3])/5);p=slope*phi+offset;cs=list(map(c,xyz))
                assert r(phase(*cs))==phi;cases+=1
                for field,amps in ((E,ref[3:6]),(H,ref[6:])):
                    for axis,amp in zip(('x','y','z','t','body'),(*amps,0,0)):
                        assert r(field(axis)(*cs))==amp*p;cases+=1
                assert run('ekqk',values+cs,m)==(xyz[0]==0);cases+=1
                assert run('ekqm',values+[c(Q(2,3))]+cs,m)==(xyz[0]==0);cases+=1
                if xyz[0]==0:
                    nonzero_normal_e |= bool(2*row[3]*p);nonzero_tangent_h |= bool(2*row[7]*p or 2*row[8]*p)
                    nonzero_tangent_flow |= bool(cross(row[3:6],row[6:])[1]*p*p or cross(row[3:6],row[6:])[2]*p*p)
            # Both boundary constraints and flux normalization must survive zero-valued wave samples.
            for coef in (0,-1):assert not run('ekqm',values+[c(coef)]+list(map(c,(0,0,0,0))),m);cases+=1
    assert nonzero_normal_e and nonzero_tangent_h and nonzero_tangent_flow
    # A false validity guard cannot be bypassed by an arbitrary finite inverse at zero.
    for undefined in (0,17):
        cuts,mm=arithmetic(undefined);c=cuts.make
        row=next(examples());profile=FunctionValue((RS,),RS,lambda t:c(1));base=[profile,*map(c,(5,7,*row,0,2,-3,1))]
        for i,value in ((1,0),(1,-5),(2,0),(2,-7)):
            bad=base[:];bad[i]=c(value);assert not run('ekqk',bad,mm);cases+=1
    cuts,m=arithmetic();c=cuts.make;profile=FunctionValue((RS,),RS,lambda t:c(1));values=[profile,*map(c,(5,7,*next(examples()),0,2,-3,1))]
    unknowns(lambda mm:run('ekqk',values,mm),m,('ba','be','sjd','sca'))
    unknowns(lambda mm:run('ekqm',values[:-4]+[c(2)]+values[-4:],mm),m,('bg','shv'))
    refused(lambda:run('ekql',values[:-4],m));cases+=1
    return dict(cases=cases,all_field_components_phase_and_boundary_coordinates_checked=True,normal_electric_and_tangential_magnetic_fields_can_remain=True,tangential_flux_not_forced_to_zero=True,off_plane_and_invalid_light_rate_rejected=True,arbitrary_rational_profiles_not_claimed_as_sine=True,native_unbounded_boundary_refused=True)

@lru_cache(None)
def binding_checks():
    cases=0;values=['a' if i%2==0 else 'b' for i in range(len(HARMONIC_MODEL))];by=dict(zip((n for n,t in HARMONIC_MODEL),values));wave=tuple(by['sine'] if n=='profile' else by[n] for n,t in WAVE)
    rows={'ekqf':tuple(by[n] for n,t in GEOMETRY),'ekc7':tuple(by[n] for n,t in HARMONIC)+(by['rate'],'a',by['period'],by['frequency']),'ekql':wave}
    mm={'bb':lambda x:'a','ba':lambda x:True,'bg':lambda x,y:True,'sejm':lambda *xs:True,'ekqm':lambda *xs:xs[:-4]==wave+(by['coefficient'],)}|{n:lambda *xs,row=row:xs==row for n,row in rows.items()}
    assert run('ekqn',values,mm,'binding',('a','b'));cases+=1
    for i in range(len(values)):
        bad=values[:];bad[i]='a' if bad[i]=='b' else 'b';assert not run('ekqn',bad,mm,'binding',('a','b'));cases+=1
    for n in ('ekqf','ekc7','ekql','ekqm','ba','bg'):
        assert not run('ekqn',values,mm|{n:lambda *xs:False},'binding',('a','b'));cases+=1
    unknowns(lambda m:run('ekqn',values,m,'binding',('a','b')),mm,('ekqf','ekc7','ekql','ekqm'))
    for point in product(('a','b'),repeat=4):
        assert not run('ekqn',values,mm|{'ekqm':lambda *xs,p=point:xs[-4:]!=p},'binding',('a','b'));cases+=1
    # Check each of the 16 boundary points, including the x/time slots and guard.
    values=['a' if i%2==0 else 'b' for i in range(len(WAVE))];row=tuple(values)
    for point in product(('a','b'),repeat=4):
        model={'sejm':lambda *xs,p=point:xs==p,'ekqk':lambda *xs,p=point:xs==row+p}
        assert run('ekql',values,model,'binding',('a','b'));cases+=1
        for i in range(4):
            wrong=list(point);wrong[i]='b' if point[i]=='a' else 'a'
            assert not run('ekql',values,model|{'ekqk':lambda *xs,p=tuple(wrong):xs==row+p},'binding',('a','b'));cases+=1
        assert run('ekql',values,model|{'sejm':lambda *xs:False,'ekqk':lambda *xs:False},'binding',('a','b'));cases+=1
    unknowns(lambda m:run('ekql',values,m,'binding',('a','b')),model,('sejm','ekqk'))
    return dict(cases=cases,all_harmonic_model_roles_share_one_assignment=True,cycle_period_frequency_not_interchanged=True,all_four_universal_coordinate_slots_checked=True,finite_boundary_diagnostics_not_full_real_proof=True)

@lru_cache(None)
def polynomial_checks():
    add=lambda a,b:k('ab',a,b);neg=lambda a:k('ac',a);mul=lambda a,b:k('ad',a,b);eq=lambda a,b:op('e',a,b)
    sub=lambda a,b:add(a,neg(b));dot3=lambda a,b:add(mul(a[0],b[0]),add(mul(a[1],b[1]),mul(a[2],b[2])))
    cross3=lambda a,b:[sub(mul(a[1],b[2]),mul(a[2],b[1])),sub(mul(a[2],b[0]),mul(a[0],b[2])),sub(mul(a[0],b[1]),mul(a[1],b[0]))]
    n=[v(x) for x in ('ax','ay','az')];E=[v(x) for x in ('ex','ey','ez')];H=[v(x) for x in ('hx','hy','hz')]
    nr=[neg(n[0]),*n[1:]];Er=[E[0],neg(E[1]),neg(E[2])];Hr=[neg(H[0]),*H[1:]];names=' '.join(n for n,t in GEOMETRY)
    oldcross=cross3(E,H);newcross=cross3(Er,Hr)
    claims={
      'norms_preserved':assertion(names,both(*(eq(dot3(a,a),dot3(b,b)) for a,b in ((n,nr),(E,Er),(H,Hr))))),
      'transversality_preserved':assertion(names,eq(dot3(nr,Er),neg(dot3(n,E)))),
      'magnetic_cross_product_preserved':assertion(names,op('y',both(*(eq(a,b) for a,b in zip(H,cross3(n,E)))),both(*(eq(a,b) for a,b in zip(Hr,cross3(nr,Er)))))),
      'signed_three_axis_flux':assertion(names,both(*(eq(a,b) for a,b in zip(newcross,[neg(oldcross[0]),*oldcross[1:]])))),
    }
    base='n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'
    rows={name:verify_universal(parse(base+claim),POLYNOMIAL,timeout_ms=20000)[0] for name,claim in claims.items()};assert all(row['status']=='valid' for row in rows.values()),rows
    return dict(lemmas=rows,rational_polynomial_only=True,no_physical_material_or_full_real_analysis_proof=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));unit=inv['units'][214];math=next(m for m in inv['math'] if m['id']=='M0368')
    assert unit['id']=='einstein-1905:u0215' and unit['math_ids']==['M0368']
    assert digest(unit['text'].encode('utf-8'))==unit['text_sha256']
    return dict(status='stationary_boundary_dependencies_only_not_source_completion',unit=unit['id'],text=unit['text'],unit_sha256=unit['text_sha256'],math=dict(id=math['id'],sha256=math['sha256'],reading='ξ=0'),observations=LIMITS,verified_full_units=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==394
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert all(d['kind']=='definition' for d in new.document['declarations'][len(old.document['declarations']):])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/energy-frequency-law-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps={d['name'] for d in extract_document(new.document,roots=['ekqn'],statement_indices=[]).document['declarations']}
    assert {'ekc7','seaj','sejm','sdx2','ekbf','ekjf','ekqh','ekqi','ekqj','ekqk','ekql','ekqm'}<=deps
    assert not {'ekbw','ekbx','ekby','ekbz'}&deps
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,all_394_statements_and_judgments_preserved=True,no_new_source_completion_claim=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('vectors',vector_checks),('boundary',boundary_checks),('bindings',binding_checks),('polynomial',polynomial_checks),('structure',structure_checks)]}
    helpers=('compose_energy_frequency_law','compose_field_equations','compose_wave_cycle_frequency','compose_material_relative_frame','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','check_light_energy_ratio','check_wave_cycle_frequency','check_resting_charge_force','check_radiative_intensity','check_real_products','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_stationary_mirror_boundary.py','scripts/check_stationary_mirror_boundary.py','tests/test_stationary_mirror_boundary.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='stationary_ideal_conductor_boundary_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
