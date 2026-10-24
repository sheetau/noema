"""Check full-time ellipsoid geometry, exact zero-time display and author roles."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from noema.polynomial_proofs import verify_universal
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import NUM
from scripts.check_light_region_slices import setup
from scripts.check_portion_energy_inquiry import CONSTANTS as PRIOR_CONSTANTS,DOMAIN as PRIOR_DOMAIN
from scripts.check_resting_charge_force import retag
from scripts.check_wave_cycle_frequency import refused
from scripts.check_real_products import assertion,MEANINGS as POLYNOMIAL
from scripts.compose_light_complex import generic_composed
from scripts.compose_light_ellipsoid_surface import *
from scripts.read_light_ellipsoid_surface import DOC,SOURCE,INVENTORY,READING,PRIOR,build_reading

CONSTANTS=PRIOR_CONSTANTS|{'eistu':'ellipsoidintro','eistv':'ellipsoiddisplay'}
DOMAIN=tuple(dict.fromkeys([*PRIOR_DOMAIN,*CONSTANTS.values()]))
DEPENDENCIES=('reports/portion-energy-inquiry-v1.json','reports/light-region-slices-v1.json','reports/light-complex-v1.json')
BOUNDS={'ekos':{'ekn7','ekoo'},'ekot':{'ekn7','ekor'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if name in ('ekou','ekow'):bounds|={'ekod','ekos','ekot','ekov'}
    if mode=='points':bounds|={'eklz','ekon','ekoq','sdn2'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode.startswith('slot:') or mode=='points':
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        if mode.startswith('slot:'):
            d=next(d for d in doc['declarations'] if d['name']==name);body=d['body']['body'];pivot=int(mode.split(':')[1]);retained=None
            for i,(n,t) in enumerate(VARIABLES):
                assert body['kind']=='forall'
                if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
                else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
                body=body['body']
            d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jles'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jlescapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jlescapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jlescapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def vector(point,cuts):return tuple(cuts.read(point(a)) for a in ('x','y','z'))

@lru_cache(None)
def affine_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for D,B,C in ((Q(1),0,0),(Q(2),Q(3,5),Q(-4,5)),(Q(1,3),Q(-2),Q(3))):
        for xyz in ((0,0,0),(1,2,3),(-1,Q(1,5),Q(-2,3))):
            args0=list(map(c,(D,B,C,*xyz)))
            assert vector(run('ekoi',args0,m),cuts)==(D*xyz[0],xyz[1]-B*xyz[0],xyz[2]-C*xyz[0]);cases+=1
            assert vector(run('ekoj',args0,m),cuts)==(Q(xyz[0])/D,xyz[1]+B*xyz[0]/D,xyz[2]+C*xyz[0]/D);cases+=1
            assert run('ekok',args0,m);cases+=1
        for center in ((0,0,0),(1,-2,Q(1,3))):
            for q in ((2,0,0),(0,2,0),(0,0,-2),(Q(6,5),Q(8,5),0),(0,0,0),(3,0,0)):
                xyz=(center[0]+Q(q[0])/D,center[1]+q[1]+B*q[0]/D,center[2]+q[2]+C*q[0]/D)
                actual=run('ekol',list(map(c,(D,B,C,2,*center,*xyz))),m)
                assert actual==(sum(x*x for x in q)==4);cases+=1
    for name,values in [('ekok',[1,2,3,4,5,6]),('ekol',[1,2,3,2,0,0,0,2,4,6])]:
        unknowns(lambda mm:run(name,list(map(c,values)),mm),m,('ba','shv','sca'))
        for invalid in (0,-1):
            bad=values[:];bad[0]=invalid
            for undefined in (0,17):
                mm=m|{'sjd':lambda x:c(1/r(x) if r(x)>0 else undefined)}
                assert not run(name,list(map(c,bad)),mm);cases+=1
    for radius in (0,-2):assert not run('ekol',list(map(c,(1,0,0,radius,0,0,0,0,0,0))),m);cases+=1
    return dict(cases=cases,both_inverse_orders_all_three_components=True,sheared_centered_surface_not_solid_interior=True,positive_factor_and_radius_required=True)

@lru_cache(None)
def geometry_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;wrong_zero=0;changed_centers=0;unchanged_axial_centers=0
    directions=((1,0,0),(0,1,0),(Q(1,3),Q(2,3),Q(2,3)),(Q(-3,5),Q(4,5),0))
    for speed,n,time in product((-3,0,3),directions,(-1,0,Q(2,3))):
        V=Q(5);beta=Q(5,4) if speed else Q(1);ratio=Q(speed)/V;a,b,d=n;D=beta*(1-a*ratio);B=b*beta*ratio;C=d*beta*ratio
        geo=(V,speed,*n,2);target=(beta*(V*a-speed)*time,V*b*beta*time,V*d*beta*time)
        center=(target[0]/D,target[1]+B*target[0]/D,target[2]+C*target[0]/D)
        assert vector(run('ekom',list(map(c,(*geo,time))),m),cuts)==center;cases+=1
        boundary=run('secd',list(map(c,geo)),m)
        for q in ((2,0,0),(0,2,0),(0,0,0),(3,0,0)):
            x=center[0]+Q(q[0])/D;y=center[1]+q[1]+B*q[0]/D;z=center[2]+q[2]+C*q[0]/D
            xyz=(x,y,z);expected=sum(u*u for u in q)==4
            assert boundary(*map(c,(*xyz,time)))==expected;cases+=1
            assert run('ekol',list(map(c,(D,B,C,2,*center,*xyz))),m)==expected;cases+=1
            assert run('ekon',list(map(c,(*geo,*xyz,time))),m);cases+=1
            if time==0:
                assert r(run('ekop',list(map(c,(*geo,*xyz))),m))==sum(u*u for u in q);cases+=1
                assert run('ekoq',list(map(c,(*geo,*xyz))),m);cases+=1
                assert run('sece',list(map(c,(*geo,*xyz))),m)==expected;cases+=1
                old=(beta*x,y,z,beta*ratio*x/V)
                wrong=run('secb',list(map(c,(V,*n,2,*old[:3],0))),m)
                if wrong!=expected:wrong_zero+=1
        if time!=0 and speed!=0:
            # Matching coordinate values can occur along the invariant axial light ray.
            actual=vector(run('ekom',list(map(c,(*geo,time))),m),cuts)
            if n==(1,0,0):
                assert actual==(V*a*time,V*b*time,V*d*time);unchanged_axial_centers+=1
            elif actual!=(V*a*time,V*b*time,V*d*time):changed_centers+=1
            cases+=1
    assert wrong_zero>0
    assert changed_centers>0 and unchanged_axial_centers>0
    geo=(5,3,0,1,0,2);xyz=(Q(8,5),Q(6,5),0)
    # Corrupt one center component: the actual boundary no longer has the predicted shape.
    for axis in range(3):
        good=run('ekom',list(map(c,(*geo,1))),m)
        from noema.finite_semantics import FunctionValue
        corrupt=FunctionValue(good.parameters,good.result,lambda a,axis=axis:c(r(good(a))+(1 if a==('x','y','z')[axis] else 0)))
        center=vector(good,cuts);point=tuple(x+y for x,y in zip(center,xyz))
        # Abstract just the center at a local boundary to test all three uses.
        doc,slots=fixture('ekon');from copy import deepcopy
        altered=deepcopy(doc);abstract(altered,{'ekom'})
        mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{'ekom':lambda *xs:corrupt}|{n:lambda x=x:x for (n,s),x in zip(slots,map(c,(*geo,*point,1)))}
        result=evaluate_document(altered,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in altered['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
        assert not result;cases+=1
    for name,values in [('ekon',(*geo,*xyz,0)),('ekoq',(*geo,*xyz))]:
        unknowns(lambda mm:run(name,list(map(c,values)),mm),m,('soy','sjd','sca'))
    for name in ('ekoo','ekor'):refused(lambda:run(name,list(map(c,geo)),m));cases+=1
    return dict(cases=cases,all_time_centers_and_inverse_lorentz_surface_checked=True,surface_interior_exterior_distinguished=True,zero_new_time_not_zero_old_time_examples=wrong_zero,changed_center_examples=changed_centers,unchanged_axial_center_examples=unchanged_axial_centers,literal_display_checked=True,native_real_quantification_refused=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for name,target in [('ekos','ekoo'),('ekot','ekor')]:
        for pivot,(var,sort) in enumerate(VARIABLES):
            mode=f'slot:{pivot}';base={n:'a' if i%2==0 else 'b' for i,(n,t) in enumerate(VARIABLES)};values=[base[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot]
            for value in ('a','b'):
                assigned=base|{var:value,'frame':'a','light':'a','scope':'b','portion':'b','context':'case'};row=tuple(assigned[n] for n,t in SETTING);geometry=tuple(assigned[n] for n,t in GEOMETRY)
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','zvaa':lambda:'b','ekn7':lambda *xs,row=row:xs==row,target:lambda *xs,row=geometry:xs==row}
                assert run(name,values,mm,mode,('a','b'));cases+=1
                assert not run(name,values,mm|{target:lambda *xs:False},mode,('a','b'));cases+=1
                bad=assigned|{var:'a' if value=='b' else 'b'};wrong=tuple(bad[n] for n,t in GEOMETRY)
                assert run(name,values,mm|{target:lambda *xs,row=wrong:xs==row},mode,('a','b'))==(var not in {n for n,t in GEOMETRY});cases+=1
            assert run(name,values,mm|{'ekn7':lambda *xs:False,target:lambda *xs:False},mode,('a','b'));cases+=1
            unknowns(lambda mod:run(name,values,mod,mode,('a','b')),mm,('ekn7',target))
        refused(lambda:run(name,[],{'ekn7':lambda *xs:False,target:lambda *xs:True,'tc':lambda:'a'}));cases+=1
    for name,target,arity in [('ekoo','ekon',4),('ekor','ekoq',3)]:
        values=['a','b','a','b','a','b'];mm={'bb':lambda n:'a','ba':lambda x:True,'bg':lambda *xs:True,'sdn2':lambda *xs:'a','eklz':lambda *xs:xs==tuple(values),target:lambda *xs:xs[:6]==tuple(values)}
        assert run(name,values,mm,'points',('a','b'));cases+=1
        for point in product(('a','b'),repeat=arity):
            row=tuple(values)+point;assert not run(name,values,mm|{target:lambda *xs,row=row:xs!=row},'points',('a','b'));cases+=1
        unknowns(lambda mod:run(name,values,mod,'points',('a','b')),mm,('eklz',target))
    return dict(cases=cases,all_63_context_roles_bound=True,same_geometry_in_shape_and_display=True,all_four_spacetime_and_three_zero_slice_roles_bound=True,native_unbounded_domains_refused=True)

@lru_cache(None)
def polynomial_checks():
    mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sub=lambda a,b:add(a,k('ac',b));eq=lambda a,b:op('e',a,b)
    D,B,C,H,x,y,z=map(v,('factor','sy','sz','reciprocal','x','y','z'));one='n p b b'
    forward=lambda x,y,z:(mul(D,x),sub(y,mul(B,x)),sub(z,mul(C,x)))
    inverse=lambda x,y,z:(mul(H,x),add(y,mul(B,mul(H,x))),add(z,mul(C,mul(H,x))))
    premise=eq(mul(D,H),one);claims={}
    for name,point in [('inverse_after_forward',inverse(*forward(x,y,z))),('forward_after_inverse',forward(*inverse(x,y,z)))]:
        claims[name]=assertion('factor sy sz reciprocal x y z',op('y',premise,both(*(eq(a,b) for a,b in zip(point,(x,y,z))))))
    beta,ratio,a,b,c,u=map(v,('beta','ratio','ax','ay','az','scaledtime'));D0=k('sebf',beta,ratio,a)
    oldx=mul(beta,add(x,mul(ratio,u)));oldvt=mul(beta,add(u,mul(ratio,x)))
    shifted=(add(mul(D0,x),mul(mul(beta,sub(ratio,a)),u)),sub(sub(y,mul(mul(mul(b,beta),ratio),x)),mul(mul(b,beta),u)),sub(sub(z,mul(mul(mul(c,beta),ratio),x)),mul(mul(c,beta),u)))
    claims['full_time_inverse_lorentz_quadratic']=assertion('beta ratio ax ay az x y z scaledtime',eq(k('sebd',one,a,b,c,oldx,y,z,oldvt),k('seaa',*shifted)))
    base=generic_composed()[0];rows={n:verify_universal(parse(base+s),POLYNOMIAL,timeout_ms=20000)[0] for n,s in claims.items()}
    assert all(r['status']=='valid' for r in rows.values()),rows
    return dict(lemmas=rows,rational_polynomial_only=True,principal_axis_and_real_topology_theorems_not_automatically_proved=True)

@lru_cache(None)
def presentation_checks():
    rows={'uh':{('ellipsoidintro','author','ekos','section8','case')},'eisox':{('ellipsoiddisplay','ekot','case')},'uf':{('author','ellipsoidintro','ellipsoiddisplay','case')},'ue':{('ellipsoidintro','ellipsoiddisplay','case')},'eisra':{('ellipsoidintro','author','paper','energyquestion','ekod','ekos','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mod:run('ekou',[],mod),mm,rows)
    assert run('ekou',[],mm|{'ekos':forbidden,'ekot':forbidden,'ekod':forbidden});cases+=1
    rows={'eir3':{('ellipsoidintro','author','paper','ekov','case')},'ue':{('energyquestion','ellipsoidintro','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda mod:run('ekow',[],mod),mm,rows)
    for name,value in [('eistu','energyquestion'),('eistv','ellipsoidintro')]:assert not run('ekow',[],{n:lambda *xs:True for n in rows}|{name:lambda:value});cases+=1
    return dict(cases=cases,claim_colon_display_and_back_reference_preserved=True,quoted_geometric_contents_not_executed=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==391 and new.document['statements'][:390]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[389])==selection_binding(old,[389]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/portion-energy-inquiry-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'secd','eistm','eisqt','ekn7','eknw','eisox'}<=names
    assert not {'sech','ekml','eje3','ejga'}&names
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['selection']==selection_binding(new,[INDEX]);assert reading['reviewed_math_elements']==2
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=2,all_390_statements_and_judgments_preserved=True,reviewed_prose_characters=reading['reviewed_prose_characters'],reviewed_math_elements=2)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('affine',affine_checks),('geometry',geometry_checks),('quantifiers',quantifier_checks),('polynomial',polynomial_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_portion_energy_inquiry','compose_light_region_slices','compose_equal_volume_supposition','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_doppler_infinity','compose_limits','compose_light_complex','check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','check_light_region_slices','check_portion_energy_inquiry','check_resting_charge_force','check_wave_cycle_frequency','check_real_products','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{DOC,SOURCE,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_light_ellipsoid_surface.py','scripts/check_light_ellipsoid_surface.py','scripts/read_light_ellipsoid_surface.py','tests/test_light_ellipsoid_surface.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_light_boundary_ellipsoid_and_zero_time_display_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
