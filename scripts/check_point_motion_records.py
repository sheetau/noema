"""Check complete current point histories and constant planar components."""
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
from scripts.check_moving_trip_geometry import NUM,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_clock_transfer_records import physical,phase_model,DOMAIN as OLD_DOMAIN,POINTS
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_point_motion_records import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/point-motion-records-v1.md';SOURCE='data/einstein-point-motion-records-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-curve-earth-u0128-review-v1.json'
DEPENDENCIES=('reports/curve-earth-claim-v1.json','reports/frame-motion-v1.json','reports/event-coordinate-task-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','zkb':'clock'}
DOMAIN=tuple(dict.fromkeys((*OLD_DOMAIN,*CONSTANTS.values())))
BOUNDS={'ejms':{'eiyw','sb'},'ejmt':{'ejms'},'ejmu':{'se','eiyw','ejms','ejmt'},'ejmv':{'ejmu'},'ejmw':{'ejmv'},'ejmx':{'eivz','ejmw'},'ejmy':{'ejmx'},'ejmz':{'ejms'},'sb':{'sa'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'sje','sjd','sky','zzbb','zzbd'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=RS))==1
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpmr'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpmrpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpmrpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jpmrpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

@lru_cache(None)
def local_checks():
    cuts,m,coords,fs,norm=physical();c=cuts.make;count=0;a=['clock','event','record','A','K','context']
    path=['clock','event','K','context','length','duration',c(Q(1)),c(Q(2)),c(Q(3)),c(Q(4))]
    rows={'zzbv':{('clock','event','context')},'eiyw':{('event','record','A','K','context')},'sb':{norm(path)}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejms',a,mm),mm,rows,norm)
    for i in range(4):
        coords['record'][i]+=1;assert not run('ejms',a,mm);coords['record'][i]-=1;count+=1
    # A coordinate alias is allowed; a numerical conflict is not.
    coords['alias']=coords['record'][:];alias=a[:];alias[2]='alias';alt=relations(m,rows|{'eiyw':{('event','alias','A','K','context')}},norm)
    assert run('ejms',alias,alt,domain=DOMAIN+('alias',));count+=1
    for i in range(3):coords['alias'][i]+=1;assert not run('ejms',alias,alt,domain=DOMAIN+('alias',));coords['alias'][i]-=1;count+=1
    for at in (-1,21):
        coords['record'][3]=at;p=path[:];p[6]=c(Q(at));assert not run('ejms',a,relations(m,rows|{'sb':{norm(p)}},norm));count+=1
    coords['record'][3]=1
    unknowns(lambda mm:run('ejms',a,mm),mm,('zc6','eismh','eisls','eislt'))
    rows={'zzbv':{('clock','event','context')},'sa':{norm(path[1:])}}
    count+=perturb(lambda mm:run('sb',path,mm),relations(m,rows,norm),rows,norm)
    return dict(cases=count,same_object_event_record_place_frame_and_actual_position=True,worldline_membership_and_coordinate_assignment_distinct=True)

@lru_cache(None)
def binding_checks():
    cuts,m,coords,fs,norm,domain,base=phase_model();c=cuts.make;count=0
    for event,record,place in product(domain,repeat=3):
        local=['a',event,record,place,'a','context'];rows={'ejms':{tuple(local)}};mm=relations(m,rows,norm);a=['a','a',c(Q(domain.index(record))),'context']
        count+=perturb(lambda mm:run('ejmt',a,mm,domain=domain),mm,rows,norm)
        bad=a[:];bad[2]=c(Q(1-domain.index(record)));assert not run('ejmt',bad,mm,domain=domain);count+=1
    for record in domain:
        for event,place in product(domain,repeat=2):
            rows={'ejms':{('a',event,record,place,'a','context')}};mm=relations(m,rows,norm)
            count+=perturb(lambda mm:run('ejmz',['a',record,'a','context'],mm,domain=domain),mm,rows,norm)
    return dict(cases=count,every_slot_of_shared_three_and_two_witnesses_checked=True,time_and_record_not_taken_from_different_events=True)

@lru_cache(None)
def coverage_checks():
    cuts,m,coords,fs,norm,domain,base=phase_model();c=cuts.make;count=0
    for at in (Q(0),Q(1,2),Q(1)):
        rows={n:rs for n,rs in base.items() if n in ('se','eisdd')}|{'zzbv':{('a','b','context')},'eiyw':{('b','b','b','a','context')},'ejms':{('a','b','b','b','a','context')},'ejmt':{norm(['a','a',c(at),'context'])}}
        mm=relations(m,rows,norm);a=['a','a','context',c(at)];check=lambda mm:run('ejmu',a,mm,'instance',domain)
        count+=perturb(check,mm,{n:rs for n,rs in rows.items() if n not in ('zzbv','eiyw')},norm)
        assert not check(mm|{'eiyw':relation(rows['eiyw']|{('b','a','a','a','context')})});count+=1
        # Records of an unrelated object do not enter this point's candidate set.
        assert check(mm|{'eiyw':relation(rows['eiyw']|{('a','a','a','a','context')})});count+=1
        assert not check(mm|{'eiyw':relation(rows['eiyw']|{('a','a','a','a','context')}),'zzbv':relation(rows['zzbv']|{('a','a','context')})});count+=1
        for hi in (0,-1):assert not check(mm|{'eislt':lambda *xs:c(Q(hi))});count+=1
        refused(lambda:run('ejmu',a[:-1],mm,domain=domain))
    return dict(cases=count,complete_history_all_current_candidates_and_all_real_times=True,empty_reversed_phase_and_missing_record_not_accepted=True)

def moving_model(origin,velocity,lower=Q(-3),upper=Q(7),detour=None):
    cuts,m,coords,_,_=physical();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(-3,0,2,7))
    functions=[FunctionValue((RS,),RS,lambda t,i=i:c(Q(origin[i])+Q(velocity[i])*r(t)+(detour(r(t)) if detour and i==0 else 0))) for i in range(3)]
    def track(obj,frame,lu,tu,axis,ctx):
        if (obj,frame,lu,tu,ctx)!=('clock','K','length','duration','context') or axis not in ('x','y','z'):forbidden()
        return functions[('x','y','z').index(axis)]
    def endpoint(frame,tu,ctx,at):
        if (frame,tu,ctx)!=('K','duration','context'):forbidden()
        return c(Q(at))
    m|={'eismh':track,'eisls':lambda *xs:endpoint(*xs,lower),'eislt':lambda *xs:endpoint(*xs,upper)}
    return cuts,m,functions,norm

@lru_cache(None)
def velocity_checks():
    count=0
    for origin,velocity in product(((0,0,0),(3,-5,8)),((0,0,0),(2,-3,4),(-7,11,0),(100,0,-1))):
        cuts,m,fs,norm=moving_model(origin,velocity);c=cuts.make
        rows={'ejmu':{('clock','K','context')}};mm=relations(m,rows,norm);a=['clock','K',*[c(Q(x)) for x in velocity],'context']
        for at in (-4,-3,0,2,7,8):assert run('ejmv',a+[c(Q(at))],mm,'instance');count+=1
        count+=perturb(lambda mm:run('ejmv',a+[c(Q(2))],mm,'instance'),mm,rows,norm)
        for i in range(3):
            bad=a[:];bad[2+i]=c(Q(velocity[i])+1);assert not run('ejmv',bad+[c(Q(2))],mm,'instance');count+=1
        refused(lambda:run('ejmv',a,mm))
        unknowns(lambda mm:run('ejmv',a+[c(Q(2))],mm,'instance'),mm,('eismh','eisls','eislt'))
    # Matching endpoints cannot mask a nonlinear excursion in the interior.
    cuts,m,fs,norm=moving_model((0,0,0),(2,0,0),detour=lambda t:(t+3)*(7-t));c=cuts.make
    a=['clock','K',c(Q(2)),c(Q(0)),c(Q(0)),'context'];mm=m|{'ejmu':relation({('clock','K','context')})}
    for at,expected in ((-3,True),(7,True),(0,False),(2,False)):
        assert run('ejmv',a+[c(Q(at))],mm,'instance')==expected;count+=1
    return dict(cases=count,all_three_constant_components_share_actual_position_functions=True,arbitrary_origins_signs_zero_and_unbounded_speeds=True,endpoint_only_detours_rejected_by_interior_instance=True)

@lru_cache(None)
def planar_checks():
    count=0
    for u,w,lower in product((-9,0,3),(-2,0,17),(-3,2)):
        cuts,m,fs,norm=moving_model((0,0,0),(u,w,0),lower=Q(lower));c=cuts.make
        a=['clock','K',c(Q(u)),c(Q(w)),'context'];row=['clock','K',c(Q(u)),c(Q(w)),c(Q(0)),'context'];rows={'ejmv':{norm(row)}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejmw',a,mm),mm,rows,norm)
        # Native three equations use the same two coefficients for negative and zero times too.
        for at in (-3,0,2,7):
            vals=[c(Q(u)),c(Q(w)),c(Q(u*at)),c(Q(w*at)),c(Q(0)),c(Q(at))]
            assert run('syr',vals,m);count+=1
            for slot in (2,3,4):
                bad=vals[:];bad[slot]=c(cuts.read(bad[slot])+1);assert not run('syr',bad,m);count+=1
        for axis in range(3):
            original=m['eismh']
            shifted=FunctionValue((RS,),RS,lambda t,axis=axis:c(cuts.read(fs[axis](t))+1))
            changed=m|{'eismh':lambda *xs,axis=axis,shifted=shifted:shifted if xs[4]==('x','y','z')[axis] else original(*xs),'ejmv':lambda *xs:True}
            assert not run('ejmw',a,changed);count+=1
    return dict(cases=count,planar_zero_third_component_and_zero_intercepts_preserved=True,nonzero_phase_start_does_not_reset_coordinate_origin=True)

@lru_cache(None)
def setup_checks():
    cuts,m,coords,fs,norm=physical();c=cuts.make;count=0
    m|={'zkc':lambda:c(Q(9)),'zkd':lambda:c(Q(-2))}
    rows={'eivz':{('context',)},'ejmw':{norm(['clock','k',c(Q(9)),c(Q(-2)),'context'])}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejmx',['context'],mm),mm,rows,norm)
    for name in ('zkc','zkd'):
        assert not run('ejmx',['context'],mm|{name:lambda:c(Q(3))});count+=1
    rows={'ejmx':{('context',)}};mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejmy',[],mm),mm,rows,norm)
    assert run('ejmy',[],mm|{'jpmrpoint':lambda:'other','zke':forbidden});count+=1
    return dict(cases=count,existing_frames_and_same_point_two_constants_in_one_context=True,frame_speed_not_substituted_for_point_components=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));table={m['id']:m for m in inv['math']};segments=[]
    expected=((),('X','K','v','k'),('ξ=wξτ,η=wητ,ζ=0,',),('wξ','wη'))
    for index,flats in zip(range(128,132),expected):
        u=inv['units'][index];assert u['id']==f'einstein-1905:u{index+1:04d}' and digest(u['text'].encode())==u['text_sha256'];math=[]
        assert len(u['math_ids'])==len(flats)
        for mid,flat in zip(u['math_ids'],flats):
            e=table[mid];assert re.sub(r'\s','',''.join(ET.fromstring(e['mathml']).itertext()))==flat;assert digest(e['mathml'].encode())==e['sha256'];math.append(dict(id=mid,sha256=e['sha256'],mathml_flat=flat))
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=math))
    retrieval='artifacts/einstein-curved-clock-records-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-point-motion-records-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['905'],segments=segments,observations=['原刊905頁の第5節見出しと冒頭の設定、三式、二速度成分の定数性を再読した。X/K/v/kとξ/η/ζ/τを区別し、wの添字ξ/ηと三式の末尾のコンマも照合した。','bewegeは設定を置く仮定として読み、後続のGesucht istという運動を求める課題提示と区別する。今回は点の全時刻の現在記録と三成分の依存群であり、見出し・仮定発話・記号説明・全体判断は後続。','下端時刻は原文で零に固定されていない。原点を通る三式と二定数を全期間に保持し、点の速度を光速未満へ先回りして制限しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==350
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[347,348,349])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();names={d['name'] for d in doc['declarations']}
    assert {'eiyw','se','sb','syr','eivz','eioj','ejms','ejmu','ejmv'}<=names
    assert not {'zka','syu','syw','zgj','zke','syt','eir3'}&names and not doc['statements']
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=350,prior_judgments_preserved=True,current_point_motion_not_old_history_oracle=True,whole_unit_review_pending=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('local',local_checks),('binding',binding_checks),('coverage',coverage_checks),('velocity',velocity_checks),('planar',planar_checks),('setup',setup_checks),('structure',structure_checks)]}
    helpers=('compose_curve_earth_claim','compose_origin_clock_question','compose_clock_transfer_records','compose_rod_methods','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_limits','check_clock_transfer_records','check_clock_site_time','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_point_motion_records.py','scripts/check_point_motion_records.py','tests/test_point_motion_records.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='current_point_motion_complete_history_and_constant_components_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0129見出しの速度合成定理の主題、u0130–u0132の仮定提示と記号説明、各全単位判断','u0133以降の課題提示と変換への接続'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
