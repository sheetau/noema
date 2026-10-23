"""Check physical application, permitted histories, boundary roles and forecast."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_rod_methods import value
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused,relations,model as body_model,DOMAIN as BODY_DOMAIN
from scripts.check_material_shape_dimensions import SS
from scripts.compose_speed_boundary_forecast import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build

DOC='docs/speed-boundary-forecast-v1.md';SOURCE='data/einstein-speed-boundary-forecast-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-moving-ellipsoid-u0114-review-v1.json'
DEPENDENCIES=('reports/planar-shape-limit-v1.json','reports/directional-contraction-claim-v1.json','reports/material-shape-dimensions-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zh7':'plane','zia':'caveat','eisoh':'supplement','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'view','other','body','a','b')));POINTS=('context','alternate','other','discourse')
PROBES=tuple(map(Q,(-1,0,1,2,3,4,5,6,10,11)))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','zzbb','zzbd'}|{'srd':{'soy'},'ejhk':{'eiyx','sre'},'ejhl':{'ejgt','ejhf'},'ejhm':{'srd'},'ejho':{'eipf'},'ejhp':{'ejhn','ejho'},'ejhq':{'ejhn'},'ejhr':{'ejhq','ejgp','ejhp'},'ejht':{'ejhm','ejhs'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=SS if name=='ejhr' else RS))=={'ejhm':2,'ejhn':5,'ejhp':1,'ejhr':1}[name]
    slots=[]
    def slot(sort):
        n='jsbf'+number_word(len(slots));slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=sort));return dict(kind='call',symbol=n,arguments=[])
    expr=dict(kind='call',symbol=name,arguments=[slot(p['sort']) for p in d['parameters']])
    if name=='ejho':expr=dict(kind='apply',function=expr,arguments=[slot(RS)])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jsbfpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jsbfpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jsbfpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    m|={'tc':lambda:c(Q(5)),'sje':lambda a,b:c(r(a)/r(b)) if r(b) else forbidden(),'zzbb':c,'zzbd':lambda a,b:c(r(a)+r(b)),'zzbg':lambda a,b:r(a)<r(b)}
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.parameters==(RS,) and x.result==RS:return tuple(r(x(c(t))) for t in PROBES)
            if x.parameters==(RS,) and x.result=='truth':return tuple(x(c(t)) for t in PROBES)
            if x.parameters==(RS,RS):return tuple(x(c(s),c(t)) for s,t in product(PROBES,repeat=2))
            if x.parameters==(RS,RS,RS):return tuple(x(c(s),c(t),c(u)) for s,t,u in product((Q(0),Q(1)),repeat=3))
            forbidden()
        return tuple(one(x) for x in xs)
    return cuts,m,norm

@lru_cache(None)
def equation_checks():
    cuts,m,norm=model();c=cuts.make;count=0
    one=FunctionValue((RS,),RS,lambda t:c(Q(1)))
    # Two individuals distinguish every tuple position without a cubic large domain.
    for event,first,second in product(('a','b'),repeat=3):
        rows={'eiyx':{(event,first,'a','context'),(event,second,'b','context')},'sre':{norm([first,second,c(Q(5)),c(Q(3)),one])}}
        mm=relations(m|{'ra':lambda:'a','zbm':lambda:'b'},rows,norm)
        check=lambda mm:run('ejhk',[c(Q(3))],mm,domain=('a','b'))
        count+=perturb(check,mm,rows,norm)
        # Different event identities do not form a correspondence.
        opposite='b' if event=='a' else 'a'
        assert not check(mm|{'eiyx':relation({(event,first,'a','context'),(opposite,second,'b','context')})});count+=1
    from noema.finite_semantics import Content
    for a,b in product((False,True),repeat=2):
        mm={'ejgt':lambda a=a:Content(POINTS,(a,)*len(POINTS)),'ejhf':lambda b=b:Content(POINTS,(b,)*len(POINTS))}
        assert run('ejhl',[],mm)==(a and b);count+=1
    return dict(cases=count,same_event_all_records_and_unit_phi=True,both_previous_considerations_required=True)

@lru_cache(None)
def caveat_checks():
    cuts,m,norm=model();c=cuts.make;count=0
    row=norm(['view','ejhl','ejhk',c(Q(6)),'discourse'])
    for candidate,application in product((False,True),repeat=2):
        mm=m|{'srd':lambda *xs,candidate=candidate:candidate,'eisof':lambda *xs,application=application:application and norm(xs)==row}
        assert run('ejhm',['view','discourse',c(Q(6)),c(Q(1))],mm,'instance')==(not candidate and not application);count+=1
    mm=m|{'srd':lambda *xs:False,'eisof':lambda *xs:norm(xs)==row}
    assert not run('ejhm',['view','discourse',c(Q(6)),c(Q(1))],mm,'instance');count+=1
    for i in range(len(row)):
        bad=tuple('wrong' if j==i else x for j,x in enumerate(row))
        assert run('ejhm',['view','discourse',c(Q(6)),c(Q(1))],mm|{'eisof':lambda *xs,bad=bad:norm(xs)==bad},'instance');count+=1
    # Each numeric argument is bound to the same light speed, speed and beta.
    target=(Q(5),Q(6),Q(2));mm=m|{'eisof':lambda *xs:False,'srd':lambda *xs:norm(xs)==target}
    assert not run('ejhm',['view','discourse',c(Q(6)),c(Q(2))],mm,'instance');count+=1
    for i in range(3):
        bad=tuple(Q(9) if i==j else x for j,x in enumerate(target))
        assert run('ejhm',['view','discourse',c(Q(6)),c(Q(2))],mm|{'srd':lambda *xs,bad=bad:norm(xs)==bad},'instance');count+=1
    for speed in (0,3,5):
        assert run('ejhm',['view','discourse',c(Q(speed)),c(Q(1))],m|{'srd':lambda *xs:True,'eisof':lambda *xs:True},'instance');count+=1
    # Eager evaluation visits soy even outside its admissible speed domain.
    # Supply the candidate explicitly there; native srd guards and the squared
    # equation still reject it. This is not a square root at a negative input.
    for speed,beta in product((6,10),(-2,0,1,2)):
        mm=m|{'soy':lambda a,b,speed=speed,beta=beta:c(Q(beta)) if (cuts.read(a),cuts.read(b))==(5,speed) else forbidden()}
        assert not run('srd',[c(Q(5)),c(Q(speed)),c(Q(beta))],mm);count+=1
    mm=m|{'eisof':lambda *xs:False,'srd':lambda *xs:False}
    refused(lambda:run('ejhm',['view','discourse'],mm))
    unknowns(lambda mm:run('ejhm',['view','discourse',c(Q(6)),c(Q(2))],mm,'instance'),mm,('eisof','srd','ba','bg'))
    return dict(cases=count,numerical_failure_and_physical_inapplicability_separate=True,same_family_considerations_view_and_reference=True,strict_superluminal_scope=True)

@lru_cache(None)
def endpoint_checks():
    cuts,m,norm=model();c=cuts.make;r=cuts.read;count=0
    finite=FunctionValue((RS,),'truth',lambda x:0<r(x)<5)
    near=FunctionValue((RS,RS),'truth',lambda e,x:0<r(e) and 5-r(e)<r(x)<5)
    infinite=FunctionValue((RS,),'truth',lambda x:0<=r(x))
    above=FunctionValue((RS,RS),'truth',lambda b,x:0<r(b)<r(x))
    cases=[(finite,near,(2,1,Q(9,2),2,1),True),(finite,near,(2,1,3,2,1),False),(finite,near,(2,1,Q(9,2),Q(49,10),Q(1,5)),False),(finite,near,(2,1,Q(9,2),Q(49,10),Q(1,100)),True),(infinite,above,(0,10,11,4,5),True),(infinite,above,(0,10,4,4,5),False),(infinite,above,(0,10,11,4,3),False),(finite,near,(2,1,Q(9,2),2,0),False)]
    for domain,nearby,ns,expected in cases:
        assert run('ejhn',[domain,nearby,*[c(Q(n)) for n in ns]],m,'instance')==expected;count+=1
    empty=FunctionValue((RS,),'truth',lambda x:False)
    assert not run('ejhn',[empty,near,*[c(Q(n)) for n in (2,1,Q(9,2),2,1)]],m,'instance');count+=1
    truncated=FunctionValue((RS,),'truth',lambda x:0<=r(x)<=10)
    assert not run('ejhn',[truncated,above,*[c(Q(n)) for n in (0,10,11,4,5)]],m,'instance');count+=1
    refused(lambda:run('ejhn',[finite,near],m))
    return dict(cases=count,nonempty_approachable_unattained_endpoint=True,finite_boundary_and_unbounded_comparison_distinguished=True,native_real_quantifiers_retained=True)

@lru_cache(None)
def permission_checks():
    cuts,m,pos,members,fs,pop,fields,norm=body_model();c=cuts.make;r=cuts.read;count=0
    def family(b,f,lu,tu,axis,ctx):
        if (b,f,lu,tu)!=('body','K','length','duration') or ctx not in POINTS or axis not in ('x','y','z'):forbidden()
        return fs[('x','y','z').index(axis)]
    m|={'eislu':family,'eisls':lambda f,u,s:c(Q(0)) if (f,u)==('K','duration') and s in POINTS else forbidden(),'eislt':lambda f,u,s:c(Q(2)) if (f,u)==('K','duration') and s in POINTS else forbidden(),'eirh':lambda b,p,s:b=='body' and s in POINTS and p in members}
    actual=fields[:];actual[1:3]=['K','alternate']
    rows={'eisoe':{('body','context','alternate')},'eipf':{norm(actual+[c(Q(3))])}}
    mm=relations(m,rows,norm);check=lambda mm:run('ejho',['body','body','context',c(Q(3))],mm,domain=BODY_DOMAIN)
    count+=perturb(check,mm,rows,norm)
    for p in ('p','q','r','other'):
        assert not check(mm|{'eirh':lambda b,x,s,p=p:b=='body' and ((x in members) != (s=='alternate' and x==p))});count+=1
    for speed in (-1,0,4):assert not run('ejho',['body','body','context',c(Q(speed))],mm,domain=BODY_DOMAIN);count+=1
    unknowns(check,mm,('eirh','eisls','eislt','eislu'))
    return dict(cases=count,physical_permission_and_same_complete_membership_required=True,full_history_frame_units_coordinates_and_speed_bound=True)

@lru_cache(None)
def role_checks():
    cuts,m,norm=model();c=cuts.make;r=cuts.read;count=0
    domain=FunctionValue((RS,),'truth',lambda x:0<r(x)<5)
    near=FunctionValue((RS,RS),'truth',lambda e,x:0<r(e) and 5-r(e)<r(x)<5)
    def allowed(view,body,base):
        if (view,body,base)!=('view','body','context'):forbidden()
        return domain
    rows={'ejhn':{norm([domain,near])}};mm=relations(m|{'ejho':allowed},rows,norm)
    count+=perturb(lambda mm:run('ejhp',['view','body','context',c(Q(3))],mm,'instance'),mm,rows,norm)
    for speed in (5,6):
        bad=FunctionValue((RS,),'truth',lambda x,speed=speed:r(x)==speed)
        assert not run('ejhp',['view','body','context',c(Q(speed))],m|{'ejho':lambda *xs:bad,'ejhn':lambda *xs:True},'instance');count+=1
    for light in (-1,0):
        assert not run('ejhp',['view','body','context',c(Q(3))],mm|{'tc':lambda light=light:c(Q(light))},'instance');count+=1
    refused(lambda:run('ejhp',['view','body','context'],mm))
    infinite=FunctionValue((RS,),'truth',lambda x:r(x)>=0);above=FunctionValue((RS,RS),'truth',lambda b,x:0<r(b)<r(x))
    rows={'ejhn':{norm([infinite,above])}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejhq',[],mm),mm,rows,norm)
    shape=FunctionValue((RS,RS,RS),'truth',lambda x,y,z:(r(x),r(y),r(z))==(0,0,0))
    for qa,qb,ca,cb,theory,infinity in product((False,True),repeat=6):
        eligible={b for b,t in zip(('a','b'),(qa,qb)) if t};bounded={b for b,t in zip(('a','b'),(ca,cb)) if t}
        mm={'eiscv':lambda *xs:theory and tuple(value(x) for x in xs)==('a','paper','eigj','discourse'),'ejhq':lambda:infinity,'ejgp':lambda b,s,ctx:b in eligible and norm([s])==norm([shape]) and ctx=='context','ejhp':lambda v,b,ctx:v=='a' and b in bounded and ctx=='context'}
        assert run('ejhr',['a','discourse',shape],mm,'instance',('a','b','paper'))==(theory and infinity and (not qa or ca) and (not qb or cb));count+=1
    refused(lambda:run('ejhr',['a','discourse'],mm,domain=('a','b','paper')))
    return dict(cases=count,same_endpoint_role_with_physical_upper_bound=True,all_eligible_bodies_under_same_theory=True,forecast_not_numeric_reparameterization=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,args,rows in (('ejhs',['view','discourse'],{'eisdb':{('view','ejhr','paper','discourse')}}),('ejhv',[],{'eir3':{('caveat','author','paper','ejhu','discourse')},'ue':{('plane','caveat','discourse')}})):
        mm={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run(name,args,mm)
        count+=perturb(check,mm,rows)
        assert check(mm|{'ejhr':forbidden,'ejhu':forbidden});count+=1
    rows={'eiscv':{('a','paper','eigj','discourse')},'ejhm':{('a','discourse')},'ejhs':{('a','discourse')},'eisog':{('supplement','author','a','ejhm','ejhs','section','discourse')}}
    mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('ejht',[],mm),mm,rows)
    for a,b in product(('a','b'),repeat=2):
        mm={'eiscv':lambda *xs:True,'ejhm':lambda v,p:v==a and p=='discourse','ejhs':lambda v,p:v==b and p=='discourse','eisog':lambda *xs:True}
        assert run('ejht',[],mm)==(a==b);count+=1
    return dict(cases=count,same_view_for_caveat_and_forecast=True,supplement_not_logical_inference=True,quoted_future_claim_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][115];assert u['id']=='einstein-1905:u0116';text=u['text'][391:634]
    assert text=='Für Überlichtgeschwindigkeiten werden unsere Überlegungen sinnlos; wir werden übrigens in den folgenden Betrachtungen finden, daß die Lichtgeschwindigkeit in unserer Theorie physikalisch die Rolle der unendlich großen Geschwindigkeiten spielt.'
    retrieval='artifacts/einstein-sphere-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-speed-boundary-forecast-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['903'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[391,634],text=text,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text)),math=[])],observations=['原刊903頁のFür Überlichtgeschwindigkeitenからspielt.までを照合する。同じ考察への適用限界、übrigensの補足、後続で見出すという予告、同じ理論における物理的な役割を保持する。','超光速での有限βの不存在と物理的適用の不成立を共に述べ、前者だけから後者を導かない。','光速の役割は、§4の有限寸法を持つ物質的対象の許容運動状態における到達不能な上限として読む。全有限上限を超える比較速度の端と同じ役割の型を使い、無限大を実数値にせず、現に予告内容が成立するとは主張しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==336
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[331])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert ds['ejhu']['body']['force']=='assert';assert len(PRIMITIVES)==4 and len(MEANINGS)==12
    assert 'ejhr' in json.dumps(ds['ejhs']['body']) and ds['ejhs']['body']['symbol']=='eisdb'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=335,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('equations',equation_checks),('caveat',caveat_checks),('endpoint',endpoint_checks),('permission',permission_checks),('role',role_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_speed_boundary_forecast.py','scripts/check_speed_boundary_forecast.py','tests/test_speed_boundary_forecast.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_translated_light_trial.py','scripts/check_transverse_segment.py','scripts/check_material_shape_dimensions.py','scripts/compose_planar_shape_limit.py','scripts/compose_ether_dispensability.py','scripts/compose_material_shape_dimensions.py','scripts/compose_solid_sphere_geometry.py','scripts/compose_shape_contraction.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py','scripts/compose_limits.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='superluminal_caveat_and_physical_boundary_forecast_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['全三文の通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
