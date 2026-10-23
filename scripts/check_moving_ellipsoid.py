"""Check arbitrary centers, complete ellipsoid occupation and general scope."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS,FS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import model as body_model,DOMAIN as BODY_DOMAIN,refused,relations
from scripts.check_final_transform_claim import final_model
from scripts.compose_moving_ellipsoid import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/moving-ellipsoid-v1.md';SOURCE='data/einstein-moving-ellipsoid-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-sphere-zero-slice-u0112-review-v1.json'
DEPENDENCIES=('reports/sphere-zero-slice-v1.json','reports/solid-sphere-geometry-v1.json','reports/sphere-slice-v1.json','reports/rod-geometry-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zh3':'shape','zh2':'slice','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*BODY_DOMAIN,*CONSTANTS.values())));POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky'}|{'ejf7':{'eje5','eje7','eipf','eioj'},'ejga':{'stg','sth','soy','ejf6','eiyx','ejfa','ejf4'},'ejgb':{'ejf7','ejga'},'ejgc':{'ejfv','ejfx'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall'},only_sort=RS))=={'ejf6':3,'ejga':1,'ejgb':4}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jme'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jmepoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jmepoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jmepoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def division(cuts):return lambda a,b:cuts.make(cuts.read(a)/cuts.read(b)) if cuts.read(b) else forbidden()

@lru_cache(None)
def geometry_checks():
    cuts,m=numbers();c=cuts.make;m['sje']=division(cuts);count=0
    for center,x,yz in product(((0,0,0),(2,-1,3)),(-4,0,4),((0,0),(5,0),(0,5),(3,4),(-4,3),(1,0),(6,0))):
        xyz=(x,*yz);point=[p+q for p,q in zip(center,xyz)];value=Q(x*x,16)+Q(yz[0]**2+yz[1]**2,25);args=[c(Q(n)) for n in (*point,*center,4,5)]
        assert run('ejf4',args,m)==(value==1);assert run('ejf5',args,m)==(value<=1);count+=2
    for axes in ((8,5,5),(4,4,4),(5,4,5),(-4,5,5),(4,5,5)):
        cuts,m,*_=final_model();c=cuts.make;assert run('stg',[c(Q(n)) for n in (5,*axes)],m)==(axes==(4,5,5));count+=1
    cuts,m,pos,members,fs,pop,fields,norm=body_model();c=cuts.make;m['sje']=division(cuts)
    members.clear();members.update(('p','q'));pos['p']=[Q(2),Q(-1),Q(3)];pos['q']=[Q(6),Q(-1),Q(3)]
    args=[pop,*fs,c(Q(1)),*[c(Q(n)) for n in (2,-1,3,4,5)]]
    for xyz,expected in (((2,-1,3),True),((6,-1,3),True),((3,-1,3),False),((2,4,3),False),((7,-1,3),True)):
        assert run('ejf6',args+[c(Q(n)) for n in xyz],m,'instance',('p','q'))==expected;count+=1
    pos['q'][0]=Q(7);assert not run('ejf6',args+[c(Q(n)) for n in (2,-1,3)],m,'instance',('p','q'));count+=1
    members.remove('q');assert run('ejf6',args+[c(Q(n)) for n in (2,-1,3)],m,'instance',('p','q'));count+=1
    refused(lambda:run('ejf6',args,m,domain=('p','q')))
    unknowns(lambda mm:run('ejf6',args+[c(Q(n)) for n in (2,-1,3)],mm,'instance',('p','q')),m,('sje','ba','bc','sca'))
    return dict(cases=count,translated_center_and_equal_transverse_axes=True,semiaxes_not_diameters_or_isotropic_contraction=True,containment_and_full_volume_coverage_distinct=True,unbounded_position_domain_refused=True)

@lru_cache(None)
def setting_checks():
    cuts,m,pos,members,fs,pop,fields,norm=body_model();c=cuts.make;count=0;center=[c(Q(n)) for n in (2,-1,3)];radius=c(Q(5));speed=c(Q(3))
    moving=fields[:];moving[1]='K';moving[6]=c(Q(3))
    m|={'eisls':lambda f,u,s:c(Q(0)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(3 if f=='K' else 2)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislu':lambda b,f,lu,tu,a,s:fs[('x','y','z').index(a)] if b=='body' and f in ('K','k') and (lu,tu,s)==('length','duration','context') and a in ('x','y','z') else forbidden(),'zb7':lambda:speed,'eislc':lambda f,g,lu,tu,a,s:c(Q(3 if a=='x' else 0)) if (f,g,lu,tu,s)==('K','k','length','duration','context') and a in ('x','y','z') else forbidden()}
    rows={'eje5':{norm(fields+center+[radius])},'eje7':{('body',f,'context') for f in ('K','k')},'eipf':{norm(moving+[speed])},'eioj':{('K','k','length','duration','context')}}
    m=relations(m,rows,norm);args=['body',radius,*center,'context'];check=lambda mm:run('ejf7',args,mm)
    count+=perturb(check,m,rows,norm);unknowns(check,m,('eirh','eislu','eisls','eislt','eislc'))
    for i in range(3):
        bad=args[:];bad[i+2]=c(Q(0));assert not run('ejf7',bad,m);count+=1
    assert check(m|{'zbv':forbidden,'eixu':forbidden,'zhw':forbidden});count+=1
    return dict(cases=count,arbitrary_rest_center_same_body_and_radius=True,both_current_histories_and_full_material_translation_required=True,no_origin_center_or_specific_body_restriction=True)

def shape_model():
    # Four individuals are needed for four distinct coordinate roles. Only
    # the two event/record quantifiers range over them (16 pairs).
    domain=('a','b','c','d');cuts,m=numbers();c=cuts.make;r=cuts.read
    fs=[FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t:c(Q(domain.index(p)+i)+(3*r(t) if i==0 else 0)))) for i in range(3)]
    pop=FunctionValue(('individual',),'truth',lambda p:p in ('a','b'))
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return x
            if x.parameters==('number',):return r(x)
            if x.result=='truth':return tuple(x(p) for p in domain)
            if x.result==FS:return tuple(r(x(p)(c(Q(t)))) for p in domain for t in (0,1,2))
            forbidden()
        return tuple(one(x) for x in xs)
    table={p:[Q(0),Q(0),Q(0),Q(0)] for p in domain};table['a']=[Q(43,5),Q(-1),Q(3),Q(1)]
    m|={'ra':lambda:'a','yn':lambda:'a','yo':lambda:'b','yp':lambda:'c','zc7':lambda:'d','ta':lambda:'c','rb':lambda:'d','tc':lambda:c(Q(5)),'zb7':lambda:c(Q(3)),'soy':lambda a,b:c(Q(5,4)) if (r(a),r(b))==(5,3) else forbidden(),'sth':lambda rad:c(Q(4)) if r(rad)==5 else forbidden(),'sje':division(cuts),'eisls':lambda *xs:c(Q(-1)),'eislt':lambda *xs:c(Q(2)),'eirh':lambda b,p,s:(b,s)==('b','context') and p in ('a','b'),'eislu':lambda b,f,lu,tu,a,s:fs[domain.index(a)] if (b,f,lu,tu,s)==('b','a','c','d','context') and a in domain[:3] else forbidden(),'zc6':lambda rec,role:c(table[rec][domain.index(role)])}
    return domain,cuts,m,fs,pop,norm,table

@lru_cache(None)
def shape_checks():
    domain,cuts,m,fs,pop,norm,table=shape_model();c=cuts.make;count=0
    args=['b',c(Q(5)),c(Q(2)),c(Q(-1)),c(Q(3)),'context'];rows={'stg':{(Q(5),Q(4),Q(5),Q(5))},'eiyx':{('b','a','a','context')},'ejfa':{('b','b','a','a','context')},'ejf4':{(Q(43,5),Q(-1),Q(3),Q(23,5),Q(-1),Q(3),Q(4),Q(5))},'ejf6':{norm([pop,*fs,c(Q(1)),c(Q(23,5)),c(Q(-1)),c(Q(3)),c(Q(4)),c(Q(5))])}}
    mm=relations(m,rows,norm);check=lambda mm:run('ejga',args+[c(Q(1))],mm,'instance',domain)
    # eiyx is a domain boundary: removing it is not itself a failed shape.
    checked={n:rs for n,rs in rows.items() if n!='eiyx'};count+=perturb(check,mm,checked,norm)
    unknowns(check,mm,('eiyx','eislu','eirh','zc6','soy','sth','zb7'))
    for t in (-1,0,2,3):
        snap=norm([pop,*fs,c(Q(t)),c(Q(8,5)+3*t),c(Q(-1)),c(Q(3)),c(Q(4)),c(Q(5))])
        local=relations(m,rows|{'ejf6':{snap}},norm)
        assert run('ejga',args+[c(Q(t))],local,'instance',domain);count+=1
        if t<=2:
            assert not run('ejga',args+[c(Q(t))],mm,'instance',domain);count+=1
    for i in range(3):
        table['a'][i]+=1;assert not check(mm|{'ejf4':lambda *xs:False});table['a'][i]-=1;count+=1
    refused(lambda:run('ejga',args,mm,domain=domain))
    return dict(cases=count,center_cx_over_beta_plus_vt_at_all_times=True,whole_population_snapshot_and_current_surface_both_required=True,nonzero_record_time_and_arbitrary_center_checked=True,native_individual_quantifiers_real_time_instances=True)

@lru_cache(None)
def general_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0;domain=('a','b');args=[c(Q(n)) for n in (5,2,-1,3)]
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    for qa,qb,ca,cb in product((False,True),repeat=4):
        allowed={p for p,ok in zip(domain,(qa,qb)) if ok};concluded={p for p,ok in zip(domain,(ca,cb)) if ok}
        mm={'ejf7':lambda *xs:norm(xs) in {(p,Q(5),Q(2),Q(-1),Q(3),'context') for p in allowed},'ejga':lambda *xs:norm(xs) in {(p,Q(5),Q(2),Q(-1),Q(3),'context') for p in concluded}}
        assert run('ejgb',args,mm,'instance',domain)==((not qa or ca) and (not qb or cb));count+=1
    refused(lambda:run('ejgb',[],mm,domain=domain))
    for bits in product((False,True),repeat=2):
        mm={n:lambda b=b:Content(POINTS,(b,b,b)) for n,b in zip(('ejfv','ejfx'),bits)};assert run('ejgc',[],mm)==all(bits);count+=1
    for name,rows in (('ejgd',{'zc':{('shape','author','ejgc','ejgb','section','discourse')}}),('ejgf',{'eir3':{('shape','author','paper','ejge','discourse')},'ue':{('slice','shape','discourse')}})):
        mm={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run(name,[],mm);count+=perturb(check,mm,rows)
        assert check(mm|{'ejgb':forbidden,'ejgc':forbidden,'ejga':forbidden});count+=1
    return dict(cases=count,all_qualifying_bodies_not_only_one_example=True,full_radius_and_center_quantifiers_retained=True,author_consequence_not_automatic_general_proof=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[];eq=ET.fromstring(math['M0200']['mathml']);flat=re.sub(r'\s','', ''.join(eq.itertext()));assert flat=='R1−(vV)2,R,R.'
    ns={'m':'http://www.w3.org/1998/Math/MathML'};assert len(eq.findall('.//m:msqrt',ns))==1 and len(eq.findall('.//m:mfrac',ns))==1
    for number in (114,115):
        u=inv['units'][number-1];assert u['id']==f'einstein-1905:u{number:04d}'
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading='R√(1−(v/V)²), R, R.',mathml_flat=flat) for n in u['math_ids']]))
    retrieval='artifacts/einstein-sphere-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-moving-ellipsoid-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['903'],segments=segments,observations=['原刊903頁で、零時刻の表面式の直後のEin starrer Körperからmit den Achsenと三値・句点まで再読した。一般的な物体の言い方、静止時の形状、also、運動状態、Kからの記述という挿入を保持する。','三つの表示値は縦半軸R√(1−(v/V)²)と横二半軸R,Rである。Achsenはこの値に合わせて半軸として読み、端から端までの直径に置き換えない。','Kから見る形状は同時刻座標による形状として読む。任意の物体・半径・中心と全対象時刻へ量化し、特定一例・原点中心・時刻零だけに範囲を縮めない。','次のWährend also以降の横二寸法と縦寸法、任意形状、光速極限などの記述は後続単位へ残す。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS);assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==332
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[330])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));generic=extract_document(doc,roots=['ejgb'],statement_indices=[]).document;names={d['name'] for d in generic['declarations']}
    assert {'eje5','eje7','eipf','ejf6','ejfa','stg'}<=names;assert not names&{'zhw','zhx','ejfr','stl','stm','shd','zhu','zhv','eipc','eipe'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE));return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=331,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('geometry',geometry_checks),('setting',setting_checks),('shape',shape_checks),('general',general_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_moving_ellipsoid.py','scripts/check_moving_ellipsoid.py','tests/test_moving_ellipsoid.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_final_transform_claim.py','scripts/check_four_coordinate_claim.py','scripts/check_material_relative_frame.py','scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py','scripts/compose_limits.py','scripts/compose_rod_methods.py','scripts/compose_solid_sphere_geometry.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='general_moving_spherical_bodies_full_ellipsoid_and_semiaxes_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0114–u0115の全文判断と登録','u0116以降の寸法変化・極限・時計'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
