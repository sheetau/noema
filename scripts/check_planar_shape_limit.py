"""Check transverse projection, whole-shape neighborhoods and limit attribution."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
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
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused,relations
from scripts.check_material_shape_dimensions import SS
from scripts.check_transverse_time import square_root
from scripts.compose_planar_shape_limit import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build

DOC='docs/planar-shape-limit-v1.md';SOURCE='data/einstein-planar-shape-limit-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-moving-ellipsoid-u0114-review-v1.json'
DEPENDENCIES=('reports/directional-contraction-claim-v1.json','reports/material-shape-dimensions-v1.json','reports/shape-contraction-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zh6':'dimensions','zh7':'plane','eisod':'annotation','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'body','other','a','b')));POINTS=('context','discourse','other')
GRID=tuple(product(map(Q,(-2,0,3,9)),map(Q,(-1,0,2)),map(Q,(0,1))))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sky','sje','sjd','zzbb','zzbd'}|{'ejg6':{'ejg5'},'ejhb':{'ejg6'},'ejhc':{'suo','ejhb'},'ejhd':{'ejha','stv'},'ejhe':{'ejgm','ejhc','ejhd'},'ejhf':{'ejgp','ejhe'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document;d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=SS if name=='ejhf' else RS))=={'ejg5':1,'ejha':1,'ejhb':3,'ejhc':4,'ejhd':4,'ejhe':1,'ejhf':1}[name]
    slots=[]
    def slot(sort):
        n='jpsl'+number_word(len(slots));slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=sort));return dict(kind='call',symbol=n,arguments=[])
    expr=dict(kind='call',symbol=name,arguments=[slot(p['sort']) for p in d['parameters']])
    if name=='stv':expr=dict(kind='apply',function=expr,arguments=[slot(RS) for _ in range(3)])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpslpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpslpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jpslpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    support={tuple(map(Q,p)) for p in ((-2,-1,0),(3,2,1),(9,-1,0))}
    shape=FunctionValue((RS,RS,RS),'truth',lambda *xs:tuple(r(x) for x in xs) in support)
    m|={'sje':lambda a,b:c(r(a)/r(b)) if r(b) else forbidden(),'sjd':lambda a:c(1/r(a)) if r(a) else forbidden(),'sky':lambda x:square_root(cuts,x),'tc':lambda:c(Q(5)),'zzbb':c,'zzbd':lambda a,b:c(r(a)+r(b)),'zzbg':lambda a,b:r(a)<r(b)}
    def norm(xs):
        return tuple(tuple(x(*(c(n) for n in p)) for p in GRID) if isinstance(x,FunctionValue) and x.parameters==(RS,RS,RS) else r(x) if isinstance(x,FunctionValue) else x for x in xs)
    return cuts,m,shape,support,norm

@lru_cache(None)
def projection_checks():
    cuts,m,shape,support,norm=model();c=cuts.make;count=0
    for originx,y,z in GRID:
        assert run('ejg5',[shape,c(y),c(z),c(originx)],m,'instance')==((originx,y,z) in support);count+=1
    projected={p[1:] for p in support}
    rows={'ejg5':{norm([shape,c(y),c(z)]) for y,z in projected}};mm=relations(m,rows,norm)
    for plane,x,y,z in product((0,5),(-1,0,5),(-1,0,2),(0,1)):
        assert run('ejg6',[shape,*[c(Q(n)) for n in (plane,x,y,z)]],mm)==(plane==x and (Q(y),Q(z)) in projected);count+=1
    refused(lambda:run('ejg5',[shape,c(Q(-1)),c(Q(0))],m))
    unknowns(lambda mm:run('ejg6',[shape,*[c(Q(n)) for n in (5,5,-1,0)]],mm),mm,('ejg5','ba','sca'))
    return dict(cases=count,exact_transverse_projection_not_bounding_rectangle=True,disconnected_positions_and_missing_cross_pairs_preserved=True,no_beta_at_limit_plane=True)

@lru_cache(None)
def image_checks():
    cuts,m,shape,support,norm=model();c=cuts.make;count=0
    for speed,factor,time,p in product((0,3,4),(Q(1),Q(4,5),Q(3,5)),(-2,0,2),sorted(support)):
        if factor!={0:Q(1),3:Q(4,5),4:Q(3,5)}[speed]:continue
        x,y,z=p;observed=(factor*x+speed*time,y,z);args=[shape,c(Q(5)),c(Q(time)),c(Q(speed)),*[c(n) for n in observed],c(x)]
        assert run('ejha',args,m,'instance');assert run('stv',[shape,c(Q(5)),c(Q(speed)),c(Q(time)),*[c(n) for n in observed]],m);count+=2
        for i in range(3):
            bad=args[:];bad[4+i]=c(observed[i]+Q(1,7));assert not run('ejha',bad,m,'instance');count+=1
        bad=args[:];bad[-1]=c(x+1);assert not run('ejha',bad,m,'instance');count+=1
    # The physical image relation rejects v=V even though its forward numeric
    # expression has a noninvertible algebraic endpoint. No beta is evaluated.
    assert not run('ejha',[shape,*[c(Q(n)) for n in (5,2,5,10,-1,0,-2)]],m|{'soy':forbidden},'instance');count+=1
    refused(lambda:run('ejha',[shape,*[c(Q(n)) for n in (5,2,3,Q(22,5),-1,0)]],m))
    return dict(cases=count,native_forward_image_matches_native_inverse_substitution=True,same_transverse_pair_and_origin_witness_required=True,light_speed_not_a_regular_image_relation=True)

@lru_cache(None)
def neighborhood_checks():
    cuts,m,shape,support,norm=model();c=cuts.make;count=0
    # Positive rational Pythagorean triples give exact roots close to v=V.
    for t,epsilon,n in ((0,Q(1),100),(2,Q(1),100),(-2,Q(1,10),1000)):
        speed=Q(5*(n*n-1),n*n+1);factor=Q(2*n,n*n+1);M=Q(10)
        delta=min(Q(5)*(epsilon/2)**2/(2*(M*M+(epsilon/2)**2)),epsilon/(2*(abs(t)+1)))
        assert 0<Q(5)-speed<delta
        rows={'ejg6':{norm([shape,c(Q(5*t)),c(Q(5*t)),c(y),c(z)]) for _,y,z in support}}
        mm=relations(m,rows,norm)
        for p in sorted(support):
            args=[shape,c(Q(5)),c(Q(t)),c(epsilon),c(speed),*[c(x) for x in p]]
            assert abs(factor*p[0]+speed*t-5*t)<epsilon
            assert run('ejhb',args,mm,'instance');count+=1
            bad=args[:];bad[3]=c(abs(factor*p[0]+speed*t-5*t)/2);assert not run('ejhb',bad,mm,'instance');count+=1
            # Closeness alone cannot replace belonging to the same target image.
            assert not run('ejhb',args,mm|{'ejg6':lambda *xs:False},'instance');count+=1
        # Outside the source shape is not required to be near the plane.
        assert run('ejhb',[shape,c(Q(5)),c(Q(t)),c(epsilon),c(speed),c(Q(10000)),c(Q(0)),c(Q(0))],mm,'instance');count+=1
    refused(lambda:run('ejhb',[shape,c(Q(5)),c(Q(2)),c(Q(1)),c(Q(3))],m))
    # Quantifier bindings, using one epsilon/delta/speed instance while retaining
    # the universal real syntax in the published body.
    vals=[shape,c(Q(5)),c(Q(2)),c(Q(1,100)),c(Q(1)),c(Q(1,10)),c(Q(4999,1000))]
    rows={'suo':{(Q(5),Q(1,100))},'ejhb':{norm([shape,c(Q(5)),c(Q(2)),c(Q(1)),c(Q(4999,1000))])}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejhc',vals,mm,'instance'),mm,rows,norm)
    for index,value in ((5,0),(5,-1)):
        bad=vals[:];bad[index]=c(Q(value));assert not run('ejhc',bad,mm,'instance');count+=1
    bad=vals[:];bad[-1]=c(Q(4));assert run('ejhc',bad,mm,'instance');count+=1
    refused(lambda:run('ejhc',vals[:3],mm))
    return dict(cases=count,one_neighborhood_for_all_positions_of_fixed_shape=True,positive_neighborhood_and_accumulation_required=True,time_drift_and_nonzero_rest_positions_included=True,native_full_real_limit_refused=True)

@lru_cache(None)
def connection_checks():
    cuts,m,shape,support,norm=model();c=cuts.make;r=cuts.read;count=0
    args=[shape,*[c(Q(n)) for n in (5,2,3,4,2,1)]]
    row=norm([shape,c(Q(5)),c(Q(2)),c(Q(3)),c(Q(4)),c(Q(2)),c(Q(1))])
    def inverse(*xs):
        valid=norm(xs)==norm([shape,c(Q(5)),c(Q(3)),c(Q(2))])
        return FunctionValue((RS,RS,RS),'truth',lambda x,y,z:valid and (r(x),r(y),r(z))==(4,2,1))
    mm=m|{'ejha':lambda *xs:norm(xs)==row,'stv':inverse};assert run('ejhd',args,mm,'instance');count+=1
    assert not run('ejhd',args,mm|{'ejha':lambda *xs:False},'instance');count+=1
    assert not run('ejhd',args,mm|{'stv':lambda *xs:FunctionValue((RS,RS,RS),'truth',lambda *xyz:False)},'instance');count+=1
    unknowns(lambda mm:run('ejhd',args,mm,'instance'),mm,('ejha','stv'))
    refused(lambda:run('ejhd',args[:3],mm))
    m|={'eisls':lambda f,u,s:c(Q(-1)) if (f,u,s)==('K','duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(2)) if (f,u,s)==('K','duration','context') else forbidden()}
    rows={'ejgm':{norm(['body',shape,'context'])},'ejhc':{norm([shape,c(Q(5)),c(Q(1))])},'ejhd':{norm([shape,c(Q(5)),c(Q(1))])}}
    mm=relations(m,rows,norm);args=['body',shape,'context',c(Q(1))];count+=perturb(lambda mm:run('ejhe',args,mm,'instance'),mm,rows,norm)
    for t in (-1,0,2):
        bad=args[:];bad[-1]=c(Q(t));assert not run('ejhe',bad,mm,'instance');count+=1
    refused(lambda:run('ejhe',args[:3],mm))
    for qa,qb,ca,cb in product((False,True),repeat=4):
        qualifying={p for p,b in zip(('a','b'),(qa,qb)) if b};conclusions={p for p,b in zip(('a','b'),(ca,cb)) if b}
        mm={'ejgp':lambda b,s,ctx:b in qualifying and norm([s])==norm([shape]) and ctx=='context','ejhe':lambda b,s,ctx:b in conclusions and norm([s])==norm([shape]) and ctx=='context'}
        assert run('ejhf',[shape],mm,'instance',('a','b'))==((not qa or ca) and (not qb or cb));count+=1
    refused(lambda:run('ejhf',[],mm,domain=('a','b')))
    return dict(cases=count,same_actual_material_shape_and_each_K_time=True,forward_and_inverse_shapes_bidirectionally_bound=True,all_eligible_bodies_and_shapes=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (('ejhg',{'uh':{('plane','author','ejhf','section','discourse')}}),('ejhi',{'eir3':{('plane','author','paper','ejhh','discourse')},'ue':{('dimensions','plane','discourse')}}),('ejhj',{'zfl':{('annotation','author','ejgt','ejhf','section','discourse')}})):
        mm={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run(name,[],mm);count+=perturb(check,mm,rows)
        assert check(mm|{'ejgt':forbidden,'ejhf':forbidden,'ejhh':forbidden});count+=1
    return dict(cases=count,author_statement_and_limit_interpretation_separate=True,quoted_physical_claim_not_executed_by_attribution=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][115];assert u['id']=='einstein-1905:u0116';text=u['text'][271:390]
    assert text=='Für [M0206] schrumpfen alle bewegten Objekte — vom „ruhenden“ System aus betrachtet — in flächenhafte Gebilde zusammen.'
    m=next(m for m in inv['math'] if m['id']=='M0206');assert ''.join(ET.fromstring(m['mathml']).itertext())=='v=V'
    retrieval='artifacts/einstein-sphere-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-planar-shape-limit-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['903'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[271,390],text=text,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text)),math=[dict(id=m['id'],sha256=m['sha256'],reading='v=Vを光速未満からの極限の境界として読む')])],observations=['原刊903頁のFür v=Vからzusammen.までを照合した。全運動対象という範囲と、ruhenden Systemから見た形状という挿入を保持する。','光速そのものの正則変換ではなく、同じ有限な静止形状から得る光速未満の形状族の極限として読む。等号の表記を消さず、追加解釈を著者のメッセージ外へ注記する。','面状化は同じ全元位置の共通精度での平面への接近と、元形状の横射影の保持として記述する。横平面全体への充填や、同じ物体の加速過程を追加しない。','u0116第三文の超光速での適用限界と後続への予告は未完。第一・第二文だけで全単位判断を行わない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==335
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[331])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    claim=extract_document(doc,roots=['ejhf'],statement_indices=[]).document;names={d['name'] for d in claim['declarations']}
    assert {'ejg5','ejg6','ejg7','ejha','ejhb','ejhc','ejhd','ejgm','ejgp','stv','suo'}<=names
    assert not names&{'eje5','ejf7','zhw','zhx','sua','sub','sue','shd','zhu'}
    for root in ('ejg5','ejg6','ejg7','ejha','ejhb','ejhc'):
        assert 'soy' not in {d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert ds['ejhh']['body']['force']=='assert';assert 'zfl' not in json.dumps(ds['ejhg']['body'])
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),only_new_primitive_is_annotation_anchor=True,preserved_statements=333,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('projection',projection_checks),('image',image_checks),('neighborhood',neighborhood_checks),('connection',connection_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_planar_shape_limit.py','scripts/check_planar_shape_limit.py','tests/test_planar_shape_limit.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py','scripts/check_translated_light_trial.py','scripts/check_transverse_segment.py','scripts/check_material_shape_dimensions.py','scripts/check_transverse_time.py','scripts/compose_solid_sphere_geometry.py','scripts/compose_shape_contraction.py','scripts/compose_material_shape_dimensions.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py','scripts/compose_limits.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX,INDEX+1],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='whole_shape_planar_limit_and_interpretation_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0116第三文の適用限界・同じ理論での物理的役割の予告','全三文の通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
