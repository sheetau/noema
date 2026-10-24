"""Check real angle construction without replacing all-real integrals by samples."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_velocity_angle_measure import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/velocity-angle-measure-v1.md';SOURCE='data/einstein-velocity-angle-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/einstein-velocity-magnitude-source-reading-v1.json'
PRIOR='data/einstein-velocity-magnitude-u0136-review-v1.json'
DEPENDENCIES=('reports/velocity-magnitude-claim-v1.json','reports/geometric-volumes-v1.json','reports/direction-angles-v1.json')
LEGACY='examples/v014/einstein-direction-angles.noema';LEGACY_BASIS='data/direction-angles-basis-v1.json'
CONSTANTS={'ra':'K','zbm':'k','zkb':'point'};DOMAIN=('K','k','point','other');POINTS=('context','other')
BOUNDS={'ejor':{'sede'},'ejos':{'ejor','sedi'},'ejot':{'ejor','sedi'},'ejou':{'ejor','sedi'},'ejov':{'ejm2','ejoj','ejou'},'ejow':{'ejm2','ejoj','ejou','ejos'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(FULL)) if name=='s2h' else core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sjt','sky','zzbb','zzbd'}
    if mode!='native':bounds|=BOUNDS.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert name in ('ejov','ejow') and len(expose(d,{'exists'},only_sort=RS))==3
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvam'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']==RS:
        doc['declarations'].append(dict(kind='primitive',name='jvamresult',parameters=[RS],result='truth'));expr=dict(kind='call',symbol='jvamresult',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots


def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots));values=[]
    def capture(value):values.append(value);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jvamresult':capture}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    result=evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return values[0] if values else result


def arithmetic():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    def reciprocal(x):
        if r(x)==0:forbidden()
        return c(1/r(x))
    return cuts,m|{'sjd':reciprocal}


def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}


@lru_cache(None)
def integral_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read;norm=norm_factory(cuts,(-2,0,1,3));count=0
    for t in (Q(-3),Q(-1),Q(0),Q(1,2),Q(1),Q(2)):
        assert r(run('sedh',[c(t)],m))==1/(1+t*t);count+=1
    profile=tuple(1/(1+Q(t)**2) for t in (-2,0,1,3))
    # A is an abstract boundary value, not an exact rational atan(2).
    for ratio,A in ((2,1),(-2,-1)):
        row=(Q(0),Q(2),profile,Q(1)) if ratio>0 else (Q(-2),Q(0),profile,Q(1))
        rows={'sede':{row}};mm=relations(m,rows,norm);args=[c(ratio),c(A)]
        count+=perturb(lambda mm:run('ejor',args,mm),mm,rows,norm)
        for bad in ((ratio,-A),(-ratio,A),(ratio+1,A),(ratio,A+2)):
            assert not run('ejor',list(map(c,bad)),mm);count+=1
        refused(lambda:run('ejor',args,m,'native'))
    assert run('ejor',[c(0),c(0)],m|{'sede':lambda *xs:False});count+=1
    assert not run('ejor',[c(0),c(1)],m|{'sede':lambda *xs:False});count+=1
    unknowns(lambda mm:run('ejor',[c(2),c(1)],mm),relations(m,{'sede':{(Q(0),Q(2),profile,Q(1))}},norm),('sede','sjd','ba'))
    refused(lambda:run('sedi',[c(4)],m,'native'))
    # Native reciprocal values on a shared rational grid, exact rectangle sums.
    enclosures=[]
    for endpoint in (Q(1,2),Q(1),Q(2)):
        grid={i:r(run('sedh',[c(endpoint*i/32)],m)) for i in range(33)};previous=None
        for n in (4,8,16,32):
            stride=32//n;lower=endpoint/n*sum(grid[i*stride] for i in range(1,n+1));upper=endpoint/n*sum(grid[i*stride] for i in range(n))
            assert upper-lower==endpoint/n*(1-1/(1+endpoint*endpoint))
            if previous:assert previous[0]<lower<upper<previous[1]
            previous=lower,upper;count+=1
            enclosures.append(dict(endpoint=str(endpoint),cells=n,lower=str(lower),upper=str(upper)))
    return dict(cases=count,negative_interval_bounds_and_value_sign_checked=True,zero_separate=True,native_integrand_exact_rational_values=True,rectangle_enclosures=enclosures,finite_bounds_not_exact_atan=True,native_real_integral_and_pi_refuse_enumeration=True)


def branch_model(cuts,m):
    r=cuts.read
    # ONLY an abstracted boundary model: P=4 and A=sign(q) are NOT pi/atan.
    return m|{'ejor':lambda q,a:r(a)==(0 if r(q)==0 else 1 if r(q)>0 else -1),'sedi':lambda p:r(p)==4}


@lru_cache(None)
def branch_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));mm=branch_model(cuts,m);count=0
    for x,y in product((-3,3),(-4,0,4)):
        q=Q(y,x);A=0 if q==0 else 1 if q>0 else -1;angle=A if x>0 else A+4 if y>=0 else A-4
        args=list(map(c,(x,y,q,A,4,angle)));assert run('ejos',args,mm);count+=1
        for slot in range(6):
            bad=args[:];bad[slot]=c(cuts.read(bad[slot])+Q(1,2))
            # Along a horizontal ray, changing its nonzero length preserves angle.
            assert run('ejos',bad,mm)==(slot==0 and y==0);count+=1
        for wrong in (angle+8,angle-8):
            assert not run('ejos',list(map(c,(x,y,q,A,4,wrong))),mm);count+=1
        if x<0:assert not run('ejos',list(map(c,(x,y,q,A,4,A))),mm);count+=int(x<0)
    for y in (-4,0,4):
        assert not run('ejos',list(map(c,(0,y,0,0,4,0))),mm);count+=1
    # The half-open range chooses +pi, never -pi, for the negative axis.
    assert run('ejos',list(map(c,(-3,0,0,0,4,4))),mm);count+=1
    assert not run('ejos',list(map(c,(-3,0,0,0,4,-4))),mm);count+=1
    for a in (-2,2):
        assert not run('ejos',list(map(c,(3,4,Q(4,3),a,4,a))),mm|{'ejor':lambda *xs:True});count+=1
    for sign in (-1,1):
        args=list(map(c,(0,sign,0,0,4,sign*2)));assert run('ejot',args,mm);count+=1
        assert not run('ejos',args,mm);count+=1
        for slot in range(6):
            bad=args[:];bad[slot]=c(cuts.read(bad[slot])+Q(1,2));assert not run('ejot',bad,mm);count+=1
    assert not run('ejot',list(map(c,(0,0,0,0,4,0))),mm);count+=1
    unknowns(lambda mm:run('ejos',list(map(c,(-3,4,Q(-4,3),-1,4,3))),mm),mm,('ejor','sedi','sca','bg'))
    unknowns(lambda mm:run('ejot',list(map(c,(0,1,0,0,4,2))),mm),mm,('sedi',))
    return dict(cases=count,all_quadrants_signed_ratio_principal_and_range=True,all_six_argument_slots=True,positive_pi_endpoint_and_vertical_cases=True,zero_divisor_not_extended=True,rational_boundary_values_not_pi_or_atan=True)


@lru_cache(None)
def geometry_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));mm=branch_model(cuts,m);count=0
    vectors=((3,0,3),(0,3,3),(3,4,5),(-3,-4,5),(-3,4,5))
    for a,b in product(vectors,repeat=2):
        x,y,r=a;u,w,s=b;co=Q(x*u+y*w,r*s);si=Q(x*w-y*u,r*s);vals=(*a,*b,co,si)
        assert run('s2g',list(map(c,vals)),m);count+=1
        assert run('s2h',list(map(c,vals)),m)==(si>=0);count+=1
        q=si/co if co else Q(0);A=0 if not q else 1 if q>0 else -1
        angle=(2 if si>0 else -2) if not co else A if co>0 else A+4 if si>=0 else A-4
        args=list(map(c,(*vals,q,A,4,angle)));assert run('ejou',args,mm);count+=1
        assert not run('ejou',args,mm|{'sedi':lambda *xs:False});count+=1
    # Nondegenerate example distinguishes every geometric and measure slot.
    vals=(3,0,3,3,-4,5,Q(3,5),Q(-4,5),Q(-4,3),-1,4,-1);args=list(map(c,vals))
    for slot in range(12):
        bad=args[:];bad[slot]=c(cuts.read(bad[slot])+Q(1,2));assert not run('ejou',bad,mm);count+=1
    for vals in ((0,0,0,3,4,5,1,0),(3,4,5,0,0,0,1,0),(3,0,-3,3,4,5,Q(3,5),Q(4,5))):
        assert not run('s2g',list(map(c,vals)),m);count+=1
    for scale in (Q(1,2),Q(2)):
        vals=(3*scale,0,3*scale,3,-4,5,Q(3,5),Q(-4,5));assert run('s2g',list(map(c,vals)),m);count+=1
    unknowns(lambda mm:run('ejou',args,mm),mm,('ejor','sedi','shv','bf','sca','ba'))
    return dict(cases=count,native_inner_product_and_signed_area=True,all_twelve_slots_and_positive_scaling=True,unsigned_legacy_differs_for_negative_sine=True,zero_vectors_and_negative_magnitude_rejected=True)


@lru_cache(None)
def physical_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));norm=norm_factory(cuts,());count=0
    cosine,sine=Q(3,5),Q(-4,5);pair=FunctionValue(('truth',),RS,lambda b:c(cosine if b else sine))
    m|={'zb7':lambda:c(3),'zkc':lambda:c(3),'zkd':lambda:c(-4),'zkq':lambda:c(5),'zkt':lambda:pair}
    rows={'ejm2':{('K','k','context',Q(3),Q(0),Q(0))},'ejoj':{(Q(5),'context')},'ejou':{tuple(map(Q,(3,0,3,3,-4,5,cosine,sine,Q(-4,3),-1,4,-1)))},'ejos':{tuple(map(Q,(3,-4,Q(-4,3),-1,4,-1)))}}
    args=[c(-1),'context',c(Q(-4,3)),c(-1),c(4)];mm=relations(m,rows,norm)
    for name in ('ejov','ejow'):
        used={n:rs for n,rs in rows.items() if name=='ejow' or n!='ejos'}
        count+=perturb(lambda mm:run(name,args,mm,'instance'),mm,used,norm)
        for slot in range(5):
            bad=args[:];bad[slot]='other' if slot==1 else c(cuts.read(bad[slot])+1);assert not run(name,bad,mm,'instance');count+=1
        unknowns(lambda mm:run(name,args,mm,'instance'),mm,('zb7','zkc','zkd','zkq','zkt'))
        refused(lambda:run(name,args[:2],mm))
    # Geometry can have a vertical angle while the printed quotient stays absent.
    vertical=FunctionValue(('truth',),RS,lambda b:c(0 if b else 1))
    vm=m|{'zkc':lambda:c(0),'zkd':lambda:c(5),'zkt':lambda:vertical}
    vr=rows|{'ejou':{tuple(map(Q,(3,0,3,0,5,5,0,1,0,0,4,2)))},'ejos':set()};vm=relations(vm,vr,norm)
    va=[c(2),'context',c(0),c(0),c(4)]
    assert run('ejov',va,vm,'instance') and not run('ejow',va,vm,'instance');count+=2
    # The physical positive-v guard is native even when all boundaries say true.
    for speed in (0,-3):
        assert not run('ejow',args,m|{n:lambda *xs:True for n in rows}|{'zb7':lambda:c(speed)},'instance');count+=1
    return dict(cases=count,same_current_frames_context_components_and_magnitude=True,shared_ratio_principal_pi_and_angle_all_slots=True,geometry_and_printed_ratio_domains_distinguished=True,native_three_real_witnesses_refuse_enumeration=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=inv['units'][136:139];assert [u['id'] for u in units]==[f'einstein-1905:u{n:04d}' for n in (137,138,139)]
    assert units[0]['text']=='und' and units[1]['text']=='[M0253]'
    table={m['id']:m for m in inv['math']};segments=[]
    for u in units:
        end=u['text'].index('Nach einfacher') if u['id'].endswith('0139') else len(u['text']);text=u['text'][:end].rstrip();end=len(text)
        assert digest(u['text'].encode())==u['text_sha256'];math=[]
        for identifier in re.findall(r'\[(M\d+)\]',text):
            e=table[identifier];flat=re.sub(r'\s','',''.join(ET.fromstring(e['mathml']).itertext()));assert digest(e['mathml'].encode())==e['sha256']
            if identifier=='M0253':assert flat=='α=arctgwηwξ;'
            math.append(dict(id=identifier,sha256=e['sha256'],mathml_flat=flat))
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,end],text=text,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text)),math=math))
    old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256'])
    retrieval='artifacts/velocity-angle-reading-v1/retrieval.json';external=json.loads(read(retrieval))
    for e in external['sources']:assert digest((ROOT/e['path']).read_bytes())==e['sha256']
    paths={INVENTORY,DOC,READING,*old['source_sha256'],'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg',retrieval,*(e['path'] for e in external['sources'])}
    return dict(version='einstein-velocity-angle-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['905','906'],segments=segments,observations=['原刊のund、成分比の逆正接、αをvとwの間の角と見る一文を照合。後続M0257のcosαとsin²αも参照し、象限と符号を消さない読みを選ぶ。','向き付き代表(-π,π]は今回明示する解釈で、原文に枝の完全な指定があるとはしない。DLMFは積分表示の数学的参照に限定する。','旧s2mの向きなし角の部分主張は今回の読みと一般には一致しない。本文統合時に置換し、異なる内容のまま旧判断を引き継がない。','今回の依存定義だけでは著者の提示・原文全単位の判断は完了しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==356
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    legacy=parse(read(LEGACY));lb=json.loads(read(LEGACY_BASIS))
    assert next(d for d in new.document['declarations'] if d['name']=='s2g')==next(d for d in legacy['declarations'] if d['name']=='s2g')
    assert MEANINGS['s2g']==lb['definitions']['s2g']
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[355])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/velocity-magnitude-claim-identifiers-v1.json'))['entries']
    doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert {'sede','sedh','sedi','s2g','ejm2','ejoj','ejmx','ejmu','eiyw'}<=names('ejow')
    assert not {'zka','shd','zke','syu','s2h'}&names('ejow')
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive'] and not doc['statements']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=356,prior_judgments_preserved=True,legacy_oriented_body_and_meaning_preserved=True,legacy_unsigned_claim_requires_replacement_at_presentation=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('integral',integral_checks),('branch',branch_checks),('geometry',geometry_checks),('physical',physical_checks),('structure',structure_checks)]}
    helpers=('compose_velocity_magnitude_claim','compose_direction_angles','compose_solid_sphere_geometry','compose_material_relative_frame','compose_limits','check_clock_site_time','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','check_coordinate_correspondence','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,LEGACY,LEGACY_BASIS,*DEPENDENCIES,'scripts/compose_velocity_angle_measure.py','scripts/check_velocity_angle_measure.py','tests/test_velocity_angle_measure.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='real_oriented_angle_dependency_checked_not_author_presentation',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['旧s2k/s2mの二つの部分主張を置換し原文対応を更新する','undと角度定義を同じWir setzenへ接続し、αを二速度間の角と見る提示を結ぶ','u0135全体とu0137–u0138およびu0139前半の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
