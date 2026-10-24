"""Check the whole moving surface and every interior material path."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_resting_charge_force import retag
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_light_region_slices import setup
from scripts.check_volume_denial import CONSTANTS as PRIOR,DOMAIN as PREVIOUS
from scripts.check_wave_cycle_frequency import refused
from scripts.compose_moving_ball_transport import *
from noema.polynomial_proofs import verify_universal
from scripts.check_real_products import assertion,MEANINGS as POLYNOMIAL
from scripts.check_radiative_intensity import cross,dot

CONSTANTS=PRIOR
DOMAIN=tuple(dict.fromkeys([*PREVIOUS,*CONSTANTS.values(),*[n for n,t in FRAME if t=='a']]))
DOC='docs/moving-ball-transport-v1.md';SOURCE='data/einstein-radiative-density-reading-v1.json'
DEPENDENCIES=('reports/volume-denial-v1.json','reports/radiative-density-v1.json','reports/light-region-slices-v1.json','reports/transported-contents-v1.json')
BOUNDS={'eknn':{'eknj','ekkb','ekkz'},'ekno':{'eknn','eknk','eknm'},'eknp':{'ekmo','eknn'},'eknq':{'ekno'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if mode=='binding':bounds|=({'sege','eknh'} if name=='ekni' else {'eknj','eknl','secc','ba'})
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
        n='jmbt'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jmbtcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jmbtcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jmbtcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result


def gate(xs,ys,slots,cuts):return len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,slots))
def scalar(cuts,fn):return FunctionValue((RS,RS,RS,RS),RS,lambda *xs:cuts.make(fn(*map(cuts.read,xs))))
def field(cuts,vector):
    ss=fixture('eknd')[1][0][1]
    return FunctionValue(('individual',),ss['result'],lambda axis:scalar(cuts,lambda *xs:vector[('x','y','z').index(axis)] if axis in ('x','y','z') else 0))
def plane(cuts,n=(0,1,0),A=3,profile=None):
    n=tuple(map(Q,n));E=(-Q(A)*n[1],Q(A)*n[0],Q(0)) if not n[2] else (Q(A),Q(0),Q(0));H=cross(n,E)
    sine=FunctionValue((RS,),RS,lambda x:cuts.make((profile or (lambda q:q+1))(cuts.read(x))))
    values=[*map(cuts.make,(2,5,*E,*H)),sine,*map(cuts.make,(Q(3,2),*n,2))]
    return values
def surface_fields(cuts,m,values):
    pos={n:i for i,(n,t) in enumerate(PLANE)};actual=dict(zip((n for n,t in PLANE),values))
    actual['phase']=run('ekbf',[actual[n] for n in ('light','rate','ax','ay','az')],m)
    density=run('ekky',[actual[n] for n,t in SCALAR],m);flux=run('ekka',[actual[n] for n,t in VECTOR],m)
    return [flux,density,*[values[pos[n]] for n,t in OLD]]


@lru_cache(None)
def surface_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    normals=((1,0,0),(0,-1,0),(0,0,1),(Q(3,5),Q(4,5),0))
    for n,time,R0,normal in product(((0,1,0),(Q(3,5),Q(4,5),0)),(-1,0,Q(2,3)),(1,2),normals):
        p=tuple(5*a*time+R0*b for a,b in zip(n,normal))+(time,);geo=list(map(c,(5,*n,R0,*p)))
        actual=run('eknc',geo,m)
        assert tuple(r(actual(axis)) for axis in ('x','y','z'))==tuple(map(Q,normal));cases+=1
        assert r(actual('body'))==0;cases+=1
        rho=Q(2);base=tuple(rho*5*a for a in n)
        for extra in ((0,0,0),(1,-2,3)):
            flux=field(cuts,tuple(a+b for a,b in zip(base,extra)));density=scalar(cuts,lambda *xs:rho)
            values=[flux,density,*geo];expected=dot(extra,normal)
            assert r(run('eknd',values,m))==expected;cases+=1
            assert r(run('ekne',values,m))==max(expected,0);cases+=1
            assert r(run('eknf',values,m))==max(-expected,0);cases+=1
            assert run('ekng',values,m)==(expected==0);cases+=1
    # Constant residual flux has equal and opposite transfers at opposite faces.
    residual=field(cuts,(1,10,0));rho=scalar(cuts,lambda *xs:2)
    for x,sign in ((2,1),(-2,-1)):
        values=[residual,rho,*map(c,(5,0,1,0,2,x,0,0,0))]
        assert r(run('eknd',values,m))==sign and not run('ekng',values,m);cases+=1
    # A surface condition does not claim that the interior point is on the surface.
    values=[residual,rho,*map(c,(5,0,1,0,2,0,0,0,0))]
    assert run('eknh',values,m) and not run('ekng',values,m);cases+=1
    unknowns(lambda model:run('eknd',[residual,rho,*map(c,(5,0,1,0,2,2,0,0,0))],model),m,('sjd','shv'))
    return dict(cases=cases,sphere_normal_distinct_from_wave_normal=True,signed_inward_and_outward_transfers_checked=True,opposite_surface_cancellation_not_accepted=True,surface_and_interior_distinguished=True)


@lru_cache(None)
def plane_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for n,A in product(((0,1,0),(0,0,1),(Q(3,5),Q(4,5),0)),(0,3)):
        values=plane(cuts,n,A);assert run('eknj',values,m);cases+=1
        surface=surface_fields(cuts,m,values)
        for normal,time in product(((1,0,0),(0,1,0),(0,0,-1)),(-1,Q(2,3))):
            p=tuple(5*a*time+2*b for a,b in zip(n,normal))+(time,)
            assert run('ekng',surface+list(map(c,p)),m);cases+=1
            assert r(run('eknd',surface+list(map(c,p)),m))==0;cases+=1
        # Setting the sphere speed to a different value changes its motion.
        if A and n==(0,1,0):
            wrong=surface[:];wrong[2]=c(4);p=(0,2,0,0)
            assert not run('ekng',wrong+list(map(c,p)),m);cases+=1
        for name in ('coefficient','rate'):
            bad=values[:];bad[next(i for i,(n0,t) in enumerate(PLANE) if n0==name)]=c(0)
            assert not run('eknj',bad,m);cases+=1
    values=plane(cuts);bad=values[:];bad[7]=c(r(bad[7])+1)
    assert not run('eknj',bad,m);cases+=1
    refused(lambda:run('ekni',surface_fields(cuts,m,values),m));cases+=1
    return dict(cases=cases,instantaneous_fields_used_together=True,zero_amplitude_allowed=True,wrong_boundary_speed_and_nontransverse_field_rejected=True,full_surface_domain_not_replaced_by_samples=True)


@lru_cache(None)
def advection_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0
    for n,profile in product(((0,1,0),(0,0,1),(Q(3,5),Q(4,5),0)),(lambda x:x+1,lambda x:x*x-2)):
        values=plane(cuts,n,3,profile);surface=surface_fields(cuts,m,values);density=surface[1]
        phase=run('ekbf',list(map(c,(5,Q(3,2),*n))),m)
        for initial,time in product(((0,0,0),(1,-1,Q(1,3)),(0,2,0),(3,0,0)),(-2,0,Q(2,3))):
            actual=tuple(Q(x)+5*Q(a)*time for x,a in zip(initial,n))+(time,)
            assert run('eknl',values+list(map(c,(*initial,time))),m);cases+=1
            assert r(phase(*map(c,actual)))==r(phase(*map(c,(*initial,0))));cases+=1
            assert r(density(*map(c,actual)))==r(density(*map(c,(*initial,0))));cases+=1
        # At a fixed spatial point a nonconstant wave generally changes.
        before=r(density(*map(c,(0,0,0,0))));after=r(density(*map(c,(0,0,0,1))))
        assert before!=after;cases+=1
    bad=plane(cuts);pos={n:i for i,(n,t) in enumerate(PLANE)};bad[pos['ax']]=c(1)
    assert not run('eknl',bad+list(map(c,(0,0,0,1))),m);cases+=1
    values=plane(cuts);refused(lambda:run('eknm',values,m));cases+=1
    unknowns(lambda model:run('eknl',values+list(map(c,(1,-1,0,1))),model),m,('shv','sjd','sca'))
    return dict(cases=cases,all_interior_paths_not_only_boundary_prepared=True,phase_and_instantaneous_density_follow_same_path=True,fixed_spatial_point_not_confused_with_material_path=True,nonunit_wave_normal_rejected=True,full_time_domain_refused=True)


@lru_cache(None)
def quantifier_checks():
    cases=0;domain=('a','b')
    for root,fields,body in [('ekni',SURFACE,'eknh'),('eknm',PLANE,'eknl')]:
        values=['a' if i%2==0 else 'b' for i in range(len(fields))]
        mm={'bb':lambda n:'a','sege':lambda *xs:True,'eknj':lambda *xs:xs==tuple(values),'ba':lambda x:True,'secc':lambda *xs:True,body:lambda *xs:xs[:len(values)]==tuple(values)}
        assert run(root,values,mm,'binding',domain);cases+=1
        for point in product(domain,repeat=4):
            row=tuple(values)+point
            assert not run(root,values,mm|{body:lambda *xs,row=row:xs!=row},'binding',domain);cases+=1
        for i in range(len(fields)):
            bad=values[:];bad[i]='b' if bad[i]=='a' else 'a'
            assert not run(root,bad,mm,'binding',domain);cases+=1
        if root=='eknm':
            assert run(root,values,mm|{'secc':lambda *xs:False,body:lambda *xs:False},'binding',domain);cases+=1
            unknowns(lambda model:run(root,values,model,'binding',domain),mm,('eknj','eknl','secc','ba'))
        else:unknowns(lambda model:run(root,values,model,'binding',domain),mm,('sege','eknh'))
    return dict(cases=cases,all_four_spacetime_or_initial_position_time_slots_checked=True,two_value_domain_not_large_tuple_enumeration=True,interior_scope_not_discarded=True,unknown_inputs_rejected=True)


@lru_cache(None)
def physical_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;cases=0;slots=fixture('eknn')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(FRAME,slots))]
    pos={n:i for i,(n,t) in enumerate(FRAME)};pv=plane(cuts)
    for (n,t),value in zip(PLANE,pv):values[pos[n]]=value
    actual=dict(zip((n for n,t in FRAME),values));actual['phase']=run('ekbf',[actual[n] for n in ('light','rate','ax','ay','az')],m);actual['region']=run('eklw',[actual[n] for n,t in OLD],m)
    probes=((0,0,0,0),(3,0,0,0),(0,5,0,1),(2,5,0,1),(0,0,0,1))
    decl={d['name']:d for d in fixture('eknn')[0]['declarations']}
    def match(xs,fields,symbol):
        if not gate(xs,[actual[n] for n,t in fields],[('',s) for s in decl[symbol]['parameters']],cuts):return False
        for n,t in fields:
            if n not in ('phase','region'):continue
            i=next(i for i,(nn,t) in enumerate(fields) if nn==n)
            for p in probes:
                left=xs[i](*map(c,p));right=actual[n](*map(c,p))
                if (r(left)!=r(right)) if n=='phase' else (left!=right):return False
        return True
    mm=m|{'eknj':lambda *xs:gate(xs,pv,fixture('eknj')[1],cuts),'ekkb':lambda *xs:match(xs,MODEL,'ekkb'),'ekkz':lambda *xs:match(xs,DENSITY_MODEL,'ekkz'),'eistm':lambda *xs:match(xs,LOCATION,'eistm')}
    assert run('eknn',values,mm);cases+=1
    for p in probes:
        x,y,z,t=map(Q,p)
        assert actual['region'](*map(c,p))==(x*x+(y-5*t)**2+z*z<=4);cases+=1
        assert r(actual['phase'](*map(c,p)))==Q(3,2)*(t-y/5);cases+=1
    for i,(_,sort) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts)
        assert not run('eknn',bad,mm),(i,FRAME[i]);cases+=1
    for name in ('ekkb','ekkz','eistm'):
        assert not run('eknn',values,mm|{name:lambda *xs:False});cases+=1
    unknowns(lambda model:run('eknn',values,model),mm,('eknj','ekkb','ekkz','eistm'))
    # The combined condition needs both the surface and the interior conditions.
    combined=m|{'eknn':lambda *xs:gate(xs,values,slots,cuts),**{name:lambda *xs:gate(xs,pv,fixture('eknj')[1],cuts) for name in ('eknk','eknm')}}
    assert run('ekno',values,combined);cases+=1
    for name in ('eknn','eknk','eknm'):
        assert not run('ekno',values,combined|{name:lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekno',values,model),combined,('eknn','eknk','eknm'))
    return dict(cases=cases,all_26_physical_roles_bound=True,whole_history_region_and_phase_checked=True,same_flux_density_work_units_portion_and_scope=True,global_model_not_inferred_from_local_approximation=True,surface_and_interior_both_required=True)


@lru_cache(None)
def adapter_checks():
    cuts,m=setup();slots=fixture('eknp')[1];cases=0
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(TOTAL,slots))]
    actual=dict(zip((n for n,t in TOTAL),values));actual['scope']=CONSTANTS['eistk'];frame=[actual[n] for n,t in FRAME]
    mm={'ekmo':lambda *xs:gate(xs,values,slots,cuts),'eknn':lambda *xs:gate(xs,frame,fixture('eknn')[1],cuts),'ekno':lambda *xs:gate(xs,frame,fixture('eknn')[1],cuts)}
    assert run('eknp',values,mm) and run('eknq',values,mm);cases+=2
    for i,(_,sort) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts)
        assert not run('eknp',bad,mm);cases+=1
        used=TOTAL[i][0] in {n for n,t in FRAME}-{'scope'}
        assert run('eknq',bad,mm)==(not used);cases+=1
    unknowns(lambda model:run('eknp',values,model),mm,('ekmo','eknn'))
    unknowns(lambda model:run('eknq',values,model),mm,('ekno',))
    return dict(cases=cases,same_70_role_background_preserved=True,same_rest_frame_plane_and_portion_selected=True,section8_scope_fixed=True,irrelevant_new_frame_values_not_used_for_rest_frame_transport=True)


@lru_cache(None)
def polynomial_checks():
    base='n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'
    z='n p a b';one='n p b b';mul=lambda a,b:k('ad',a,b);add=lambda a,b:k('ab',a,b);sub=lambda a,b:add(a,k('ac',b))
    V,w,t,phase,initial=map(v,('light','rate','time','phase','initial'));n=[v(s) for s in ('nx','ny','nz')];x=[v(s) for s in ('ox','oy','oz')]
    dotp=lambda a,b:add(mul(a[0],b[0]),add(mul(a[1],b[1]),mul(a[2],b[2])))
    moved=[add(a,mul(mul(V,b),t)) for a,b in zip(x,n)]
    premises=both(k('aa',z,V),op('e',dotp(n,n),one),op('e',mul(V,phase),mul(w,sub(mul(V,t),dotp(n,moved)))),op('e',mul(V,initial),mul(w,k('ac',dotp(n,x)))))
    claim=assertion('light rate time phase initial nx ny nz ox oy oz',op('y',premises,op('e',phase,initial)))
    result=verify_universal(parse(base+claim),POLYNOMIAL,timeout_ms=20000)[0];assert result['status']=='valid',result
    return dict(phase_constant_on_unit_normal_characteristics=result,rational_polynomial_only=True,physical_global_validity_and_measure_transport_not_automatically_proved=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==388
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for index in (385,386,387):assert selection_binding(new,[index])==selection_binding(old,[index])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/volume-denial-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names={d['name'] for d in extract_document(core(),roots=['eknq'],statement_indices=[]).document['declarations']}
    assert {'eistj','eistf','eiste','eistm','secb','secc','segb','segf','ekbf','ekk6'}<=names
    assert not {'segi','sefa','sefb','ekle','ekk4','sedp','sech'}&names
    assert len(FRAME)==26 and len(PLANE)==14
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,all_388_statements_and_judgments_preserved=True,no_new_sentence_or_whole_unit_certification=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('surface',surface_checks),('plane',plane_checks),('advection',advection_checks),('quantifiers',quantifier_checks),('physical',physical_checks),('adapters',adapter_checks),('polynomial',polynomial_checks),('structure',structure_checks)]}
    helpers=('compose_volume_denial','compose_light_region_slices','compose_radiative_density','compose_observed_intensity','compose_wave_display','compose_field_equations','compose_material_relative_frame','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_resting_charge_force','check_material_relative_frame','check_light_region_slices','check_volume_denial','check_wave_cycle_frequency','check_real_products','check_radiative_intensity','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,*DEPENDENCIES,'scripts/compose_moving_ball_transport.py','scripts/check_moving_ball_transport.py','tests/test_moving_ball_transport.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='moving_ball_surface_transfer_and_interior_advection_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
