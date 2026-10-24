"""Check native quantity construction, same-point connections and preserved evidence."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,FunctionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_ninth_section_opening as prior
from scripts.check_body_rest_field_method import numbers,point
from scripts.check_material_relative_frame import NUM
from scripts.check_parallel_composition import transform
from scripts.compose_convective_transformed_quantities import *

DOC='docs/convective-transformed-quantities-v1.md'
DEPENDENCIES=('reports/ninth-section-opening-v1.json','reports/density-formula-v1.json','reports/field-transform-v1.json','reports/convection-fields-v1.json')
old=prior.old;fn=old.fn;sort=old.sort;forbidden=old.forbidden
BOUNDS={n:set() for n in ('ekzr','ekzs','ekzt','ekzu','ekzv','ekzw')}
BOUNDS|={'ekzx':{'ekyz','ejsn','ejsj','ekzw','s6k','s6l','s6m','s46'},'ekzy':{'sent','s46','ekzu','ekzv','s6k','s6m'},'ekzz':{'s5u','semf','ejsj','s6k','s6l','s6m','ekzu','ekzv'},'ekz2':{'ekzy','ejsj','s6m'}}
CONSTANTS=prior.CONSTANTS|{'yn':'x','yo':'y','yp':'z','zc7':'t','zbm':'moving'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values()]))
AXES=('x','y','z','t')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in NUM|{'bg','be','bj','szi','sjd','sjt','soy'}|BOUNDS[root]:
            doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root);extras={}
    if mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('forall','exists'):
                names=('jctpa','jctpb') if node['sort']==sort(POINT) else ('jctja','jctjb') if node['sort']==sort(JET) else None
                if names:
                    extras.update({n:node['sort'] for n in names})
                    return dict(kind='and' if node['kind']=='forall' else 'or',arguments=[sample(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in names])
            return {k:sample(x) for k,x in node.items()}
        d['body']=sample(d['body'])
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=t) for n,t in extras.items()]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jctarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jctcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jctcapture',arguments=[expr])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots

def run(root,values,m,mode='sample'):
    doc,slots=fixture(root,mode);assert len(slots)==len(values);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{'jctcapture':capture}|{n:lambda x=x:x for n,x in zip(slots,values)}
    result=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def arithmetic():
    cuts,m=numbers();c,r=cuts.make,cuts.read
    m|={'sjt':lambda x:c(1/r(x)),'sjd':lambda x:c(1/r(x)),'soy':lambda V,s:c(1) if r(V)>0 and r(s)==0 else c(Q(5,4)) if r(V)==5 and abs(r(s))==3 else forbidden()}
    return c,r,m

def expected(V,s,u,rho):
    beta=Q(1) if s==0 else Q(5,4);D=V*V-s*u[0]
    return D,(V*V*(u[0]-s)/D,V*V*u[1]/(beta*D),V*V*u[2]/(beta*D)),beta*D*rho/(V*V)

@lru_cache(None)
def numeric_checks():
    c,r,m=arithmetic();cases=0
    for s in map(Q,(-3,0,3)):
        for u in [(Q(1),Q(-2),Q(3)),(Q(10),Q(7),Q(-11)),(Q(-10),Q(2),Q(6))]:
            for rho in map(Q,(-4,0,6)):
                V=Q(5);D,w,rhop=expected(V,s,u,rho);vs=[c(V),c(s),point(c,(*u,99))]
                assert run('ekzw',vs+[c(rho)],m)
                assert r(run('ekzr',vs,m))==D
                got=run('ekzs',vs,m);assert tuple(r(got(a)) for a in AXES[:3])==w
                assert r(got('t'))==r(got('other'))==0
                assert r(run('ekzt',vs+[c(rho)],m))==rhop;cases+=5
    for V,s,u in [(5,3,(Q(25,3),2,3)),(0,0,(1,2,3)),(5,5,(1,2,3)),(5,-5,(1,2,3))]:
        assert not run('ekzw',[c(V),c(s),point(c,(*u,0)),c(0)],m);cases+=1
    return dict(cases=cases,negative_denominator_and_signed_density_allowed=True,zero_density_keeps_velocity=True,zero_denominator_and_light_boundary_rejected=True,three_components_and_signed_reciprocals_executed=True)

def setup():
    by,m,c,r,parts,_,_,_=prior.setup()
    # Keep inherited scalar values and newly constructed values in one fixture.
    m|={'sjt':lambda x:c(1/r(x)),'sjd':lambda x:c(1/r(x)),'soy':lambda V,s:c(1) if r(V)>0 and r(s)==0 else c(Q(5,4)) if r(V)==5 and abs(r(s))==3 else forbidden()}
    # Independent affine fields distinguish every coordinate and axis.
    def field(coeffs):return fn(sort(FIELD),lambda a:fn(sort(TAU),lambda *xs:c(sum(Q(b)*r(x) for b,x in zip(coeffs[AXES.index(a)][:4],xs))+coeffs[AXES.index(a)][4]) if a in AXES[:3] else c(0)))
    U=((1,2,3,4,1),(2,-3,1,5,-2),(-1,4,-2,3,7))
    E=((1,2,3,4,5),(2,3,4,5,6),(3,4,5,6,7));H=((6,5,4,3,2),(5,4,3,2,1),(4,3,2,1,0))
    by|={n:c(x) for n,x in dict(light=5,speed=3,electricconversion=1,magneticconversion=Q(1,5)).items()}
    by|=dict(velocityfield=field(U),electricfield=field(E),magneticfield=field(H),densityfield=fn(sort(TAU),lambda x,y,z,t:c(2*r(x)-r(y)+3*r(z)-5*r(t)+8)))
    points=[point(c,p) for p in [(1,2,3,4),(7,11,13,17)]];by['point']=points[0]
    jets=[fn(sort(JET),lambda a,b:c(100*(AXES.index(a)+1)+AXES.index(b)+1)) for _ in range(1)]
    jets.append(fn(sort(JET),lambda a,b:c(1000+100*(AXES.index(a)+1)+AXES.index(b)+1)))
    by['newelectricjet']=jets[0];by['newmagneticjet']=jets[1]
    # Own mapping functions are only used in connection fixtures; the actual s46
    # is executed in field_checks below.
    mapping=lambda V,s,p:point(c,transform(tuple(r(p(a)) for a in AXES),r(s),r(V)))
    newregion=fn(sort(REGION),lambda *xs:True)
    newE=field(tuple(tuple(Q(x)*2 for x in row) for row in E));newH=field(tuple(tuple(Q(x)*3 for x in row) for row in H))
    newU=field(tuple(tuple(Q(x)*4 for x in row) for row in U));newrho=fn(sort(TAU),lambda *xs:c(sum((i+2)*r(x) for i,x in enumerate(xs))+23))
    m|={'s46':mapping,'s6k':lambda *xs:newE,'s6l':lambda *xs:newH,'s6m':lambda *xs:newregion,'ekzu':lambda *xs:newU,'ekzv':lambda *xs:newrho,
        'jctpa':lambda:points[0],'jctpb':lambda:points[1],'jctja':lambda:jets[0],'jctjb':lambda:jets[1]}
    def key(x):
        if isinstance(x,(tuple,list)):return tuple(key(y) for y in x)
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result==old.RS:return tuple(r(x(a)) for a in AXES)
        if x.parameters==('individual','individual'):return tuple(r(x(a,b)) for a in AXES[:3] for b in AXES)
        if x.parameters==('individual',) and x.result==sort(TAU):return tuple(key(x(a)) for a in AXES[:3])
        if x.parameters==(sort(POINT),):return tuple(key(x(p)) for p in points)
        if x.parameters==tuple(sort(TAU)['parameters']):return tuple(key(x(*(p(a) for a in AXES))) for p in points)
        # Unused carrier packets are passed unchanged. Do not probe a body-indexed
        # function with coordinate-axis labels or compare evaluator wrappers.
        while isinstance(x,FunctionValue):
            f=x.implementation;code=getattr(f,'__code__',None)
            if code is None:return f
            closed=dict(zip(code.co_freevars,(cell.cell_contents for cell in (getattr(f,'__closure__',None) or ()))))
            if 'raw' not in closed:return f
            x=closed['raw']
        return x
    return by,m,c,r,points,jets,key,(newE,newH,newregion,newU,newrho),U

@lru_cache(None)
def field_checks():
    by,m,c,r,points,jets,key,derived,U=setup();cases=0
    # Native field helpers execute s46, ekzs, ekzt and the lambda composition.
    for speed in (Q(-3),Q(0),Q(3)):
        by['speed']=c(speed);vs=[by[n] for n,t in SETTING]
        vel=run('ekzu',vs,m);rho=run('ekzv',vs,m)
        for p in points:
            coords=tuple(r(p(a)) for a in AXES);oldpoint=coords if speed==0 else transform(coords,-speed,Q(5))
            u=tuple(sum(Q(a)*b for a,b in zip(row[:4],oldpoint))+row[4] for row in U)
            dens=2*oldpoint[0]-oldpoint[1]+3*oldpoint[2]-5*oldpoint[3]+8
            D,w,d=expected(Q(5),speed,u,dens);xs=[p(a) for a in AXES]
            assert tuple(r(vel(a)(*xs)) for a in AXES[:3])==w
            assert r(rho(*xs))==d;cases+=2
            if speed:
                wrong=tuple(sum(Q(a)*b for a,b in zip(row[:4],coords))+row[4] for row in U)
                assert w!=expected(Q(5),speed,wrong,dens)[1];cases+=1
    return dict(cases=cases,native_inverse_coordinates_and_all_components_executed=True,old_coordinate_reuse_distinguished=True)

def contrasts(root,values,m,rows,key):
    relation=lambda rs:lambda *xs:key(xs) in rs
    good=m|{n:relation(rs) for n,rs in rows.items()};assert run(root,values,good),root;cases=1
    for n,rs in rows.items():
        for row in rs:
            assert not run(root,values,good|{n:relation(rs-{row})}),(root,n,'missing');cases+=1
            for i in range(len(row)):
                bad=list(row);bad[i]='wrong';assert not run(root,values,good|{n:relation((rs-{row})|{tuple(bad)})}),(root,n,i);cases+=1
        try:run(root,values,good|{n:forbidden})
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError('Unknown input accepted')
        cases+=1
    return cases

@lru_cache(None)
def connection_checks():
    by,m,c,r,points,jets,key,derived,U=setup();E,H,region,vel,rho=derived;vs=[by[n] for n,t in SETTING];cases=0
    atp=lambda f,p:f(*(p(a) for a in AXES))
    up=lambda f,p:point(c,tuple(r(atp(f(a),p)) for a in AXES[:3])+(0,))
    original=by|dict(frame='moving',electricfield=E,magneticfield=H,region=region)
    maps=[fn(dict(kind='function',parameters=[sort(POINT)],result=sort(POINT)),lambda p,s=s:m['s46'](by['light'],c(s),p)) for s in (3,-3)]
    rows={'ekyz':{key([by[n] for n,t in GLOBAL])},'ejsn':{key([original[n] for n,t in FIELD_SETTING])},'eiscc':{('moving',by['lengthunit'],by['timeunit'],'speedunit','case')},'eisqt':{key([a,b,by['lengthunit'],by['timeunit'],mapping,'case']) for a,b,mapping in [('frame','moving',maps[0]),('moving','frame',maps[1])]},'ekzw':{key([by['light'],by['speed'],up(by['velocityfield'],p),atp(by['densityfield'],p)]) for p in points}}
    cases+=contrasts('ekzx',vs,m|{'ejsj':lambda *xs:True},rows,key)
    # Five equalities use the old values at the inverse image and one new rho.
    p=points[0];back=m['s46'](by['light'],c(-3),p);oldvel=up(by['velocityfield'],back);newvel=up(vel,p)
    row=[by['light'],by['speed'],c(Q(5,4)),atp(by['densityfield'],back),*(oldvel(a) for a in AXES[:3]),atp(rho,p),*(newvel(a) for a in AXES[:3]),jets[0],E,region,p]
    cases+=contrasts('ekzy',vs+[p,jets[0]],m,{'sent':{key(row)}},key)
    rows={'s5u':set(),'semf':set()}
    for p in points:
        rows['s5u'].add(key([E,H,region,p,*jets]));rows['semf'].add(key([by['light'],atp(rho,p),up(vel,p),*jets]))
    cases+=contrasts('ekzz',vs,m|{'ejsj':lambda *xs:True},rows,key)
    rows={'ekzy':{key(vs+[p,jets[0]]) for p in points}}
    cases+=contrasts('ekz2',vs,m|{'ejsj':lambda *xs:True},rows,key)
    for root in ('ekzz','ekz2'):
        assert not run(root,vs,m|{n:lambda *xs:True for n in BOUNDS[root] if n not in ('s6k','s6l','s6m','ekzu','ekzv')}|{'ejsj':lambda *xs:False});cases+=1
        try:run(root,vs,m,'native')
        except ValueError as e:assert any(s in str(e) for s in ('Finite function domain','rational number domain'))
        else:raise AssertionError('Unbounded points enumerated')
        cases+=1
    return dict(cases=cases,same_setting_new_fields_density_velocity_points_and_jets=True,both_charts_and_all_point_domain_preserved=True,unknown_inputs_and_unbounded_evaluation_rejected=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements']==before.document['statements'] and len(after.document['statements'])==410
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(before,[408,409])==selection_binding(after,[408,409]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/ninth-section-opening-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    hyp={d['name'] for d in extract_document(core(),roots=['ekzx'],statement_indices=[]).document['declarations']}
    assert not hyp&{'semh','semf','seme','semd','sent','ekx3','ekyc','ekyl','eiah','ekzu','ekzv'}
    assert not set(MEANINGS)&{'ekz3','ekz4'} and len(SETTING)==33
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,all_410_prior_statements_and_meanings_preserved=True,no_new_velocity_identification_or_equations_in_setting=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('field',field_checks),('connection',connection_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(DEPENDENCIES)|{DOC,'scripts/compose_convective_transformed_quantities.py','scripts/check_convective_transformed_quantities.py','tests/test_convective_transformed_quantities.py','scripts/check_ninth_section_opening.py','scripts/check_body_rest_field_method.py','scripts/check_parallel_composition.py'}
    return dict(status='transformed_quantities_connected_pending_source_presentation',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
