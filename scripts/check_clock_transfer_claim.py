"""Check arrival lag, elapsed seconds, qualified approximation and faithful attribution."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_clock_transfer_records import setup_model,source_record as prior_source
from scripts.check_clock_seconds_claim import function_norm
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_clock_transfer_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,COMMON,CONSTANTS as ROLE_CONSTANTS,build

DOC='docs/clock-transfer-claim-v1.md';SOURCE='data/einstein-clock-transfer-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-clock-seconds-u0125-review-v1.json';SOURCE_PRIOR='data/einstein-clock-transfer-records-source-reading-v1.json'
DEPENDENCIES=('reports/clock-transfer-records-v1.json','reports/clock-seconds-claim-v1.json','reports/clock-transfer-v1.json')
CONSTANTS={'ra':'K','ta':'length','rb':'duration','zik':'second','yn':'x','yo':'y','yp':'z','zc7':'time','rd':'author','eirf':'paper','eisn5':'section','ri':'discourse','zim':'exact','zin':'approximation','eisoj':'intro','zi7':'result','zja':'interpretation','eisok':'durationname'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'clock','reference','A','B','departure','initialreference','arrival','first','initialrecord','last','a','b')))
POINTS=('initial','motion','context','discourse','other')
BOUNDS={'ejki':{'svp'},'ejkj':{'ejkf'},'ejkk':{'ejj7'},'ejkl':{'ejj7','sww'},'ejkm':{'ejkj','ejkk','ejkl'},'ejkn':{'ejkh','svp'},'ejkq':{'ejkj','ejkk'},'ejkr':{'ejkj','ejkl'},'swk':{'svp'},'sww':{'svp','swy'},'swy':{'svy'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document;bounds=NUM|{'sje','sjd','sky','zzbb','zzbd'}|BOUNDS.get(name,set())
    if name=='swy' and mode=='full':bounds.discard('svy')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=RS))==1
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jctc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jctcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jctcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jctcpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    cuts,m,coords,fs,norm,args,_=setup_model()
    m|={ROLE_CONSTANTS[n]:lambda x=x:x for (n,_),x in zip(COMMON,args)}
    return cuts,m,coords,norm,args

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
def content_value(truth):return Content(POINTS,tuple(truth if p=='discourse' else not truth for p in POINTS))

@lru_cache(None)
def seconds_checks():
    cuts,m,coords,norm,args=model();c=cuts.make;r=cuts.read;count=0
    for scale in (Q(1,5),Q(1),Q(2)):
        rows={'svp':{norm([c(scale),'motion'])}};mm=relations(m,rows,norm)
        a=['clock',c(10*scale),'motion',c(scale)];count+=perturb(lambda mm:run('ejki',a,mm,'instance'),mm,rows,norm)
        for bad in (['reference',a[1],a[2],a[3]],[a[0],a[1],'initial',a[3]],[a[0],c(10*scale+1),a[2],a[3]]):assert not run('ejki',bad,mm,'instance');count+=1
        # Same scale on elapsed coordinate time, actual arrival gap and approximation.
        numeric=[c(scale),c(10*scale),c(2*scale),c(Q(9,5)*scale),c(Q(1,5)*scale)]
        count+=perturb(lambda mm:run('swk',numeric,mm),mm,rows,norm)
        for i in range(1,5):bad=numeric[:];bad[i]=c(r(bad[i])+Q(1,7));assert not run('swk',bad,mm);count+=1
        for change in ('first','last'):
            coords[change][3]+=1;assert not run('swk',numeric,mm);coords[change][3]-=1;count+=1
        refused(lambda:run('ejki',a[:-1],mm))
    # Simultaneous shift of the K origin does not change elapsed seconds.
    for offset in (-100,100):
        coords['first'][3]+=offset;coords['last'][3]+=offset
        assert run('ejki',['clock',c(Q(10)),'motion',c(Q(1))],m|{'svp':lambda s,ctx:(r(s),ctx)==(1,'motion')},'instance');count+=1
        coords['first'][3]-=offset;coords['last'][3]-=offset
    for at in (10,9):
        coords['last'][3]=at;assert not run('ejki',['clock',c(Q(at-10)),'motion',c(Q(1))],m|{'svp':lambda *xs:True},'instance');count+=1
    coords['last'][3]=20
    return dict(cases=count,elapsed_duration_distinct_from_coordinate_time=True,same_positive_conversion_and_actual_gap_bound=True)

@lru_cache(None)
def arrival_checks():
    cuts,m,coords,norm,args=model();c=cuts.make;count=0
    rows={'ejj7':{norm([cl,'arrival','last','B',c(Q(val)),'motion']) for cl,val in (('clock',15),('reference',17))}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejkk',[],mm),mm,rows,norm)
    for val,expected in ((17,False),(18,True),(15,True)):
        assert run('ejkk',[],m|{'zi2':lambda:c(Q(val)),'ejj7':lambda *xs:True})==expected;count+=1
    for truth in (False,True):
        mm=relations(m,rows,norm)|{'sww':lambda:content_value(truth)}
        assert run('ejkl',[],mm)==truth;count+=1
    mm=relations(m,rows,norm)|{'sww':lambda:content_value(True)};count+=perturb(lambda mm:run('ejkl',[],mm),mm,rows,norm)
    # Native exact comparison: arrival readings, not the travel coordinate origin or initial dials.
    for offset,t0 in product((-100,0,100),(-20,10)):
        coords['first'][3]=t0;coords['last'][3]=t0+10
        mm=m|{'zi2':lambda:c(Q(15+offset)),'zi3':lambda:c(Q(17+offset))}
        assert run('swv',[],mm);count+=1
        for val in (17+offset,18+offset,16+offset):assert not run('swv',[],mm|{'zi2':lambda val=val:c(Q(val))});count+=1
    return dict(cases=count,same_clock_event_place_and_current_arrival_readings=True,non_synchrony_distinct_from_directional_lag=True,arrival_gap_invariant_under_common_dial_and_time_offsets=True)

@lru_cache(None)
def approximation_checks():
    cuts,m,coords,norm,args=model();c=cuts.make;r=cuts.read;count=0
    for scale in (Q(1,5),Q(1),Q(2)):
        rows={'svp':{norm([c(scale),'motion'])},'swy':{norm([c(10*scale)])}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('sww',[c(scale)],mm,'instance'),mm,rows,norm)
        # Replacing the exact gap by the displayed second-order number loses the residual.
        assert not run('sww',[c(scale)],mm|{'zi2':lambda:c(Q(17)-Q(9,5))},'instance');count+=1
        refused(lambda:run('sww',[],mm))
    for duration in (Q(1),Q(2),Q(10)):
        seen=[]
        def capture(*xs):seen.append(xs);return True
        assert run('swy',[c(duration)],m|{'svy':capture});count+=1
        domain,exact,estimate,fourth,point=seen[0];assert r(point)==0
        for u in (Q(-4,5),Q(-3,5),Q(0),Q(3,5),Q(4,5)):
            rate=Q(3,5) if abs(u)==Q(4,5) else Q(4,5) if abs(u)==Q(3,5) else Q(1)
            assert domain(c(u)) and r(exact(c(u)))==duration*(1-rate) and r(estimate(c(u)))==duration*u*u/2 and r(fourth(c(u)))==u**4;count+=1
        for u in (-2,-1,1,2):assert not domain(c(Q(u)));count+=1
        fn=function_norm(cuts);rows={'svy':{fn(seen[0])}};mm=relations(m,rows,fn)
        count+=perturb(lambda mm:run('swy',[c(duration)],mm),mm,rows,fn)
    for duration in (0,-1):assert not run('swy',[c(Q(duration))],m|{'svy':lambda *xs:True});count+=1
    refused(lambda:run('swy',[c(Q(10))],m,'full'))
    return dict(cases=count,observed_exact_gap_and_second_order_estimate_not_equated=True,fixed_duration_scales_actual_error_functions=True,real_neighborhood_quantifiers_retained=True)

@lru_cache(None)
def conditional_checks():
    cuts,m,coords,norm,args=model();count=0;c=cuts.make
    rows={'ejkf':{norm(args)}};mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejkj',[],mm),mm,rows,norm)
    assert run('ejkj',[],mm|{'ejkg':forbidden,'ejkh':forbidden,'svm':forbidden});count+=1
    for setting,nonsync,lag in product((False,True),repeat=3):
        mm={'ejkj':lambda:content_value(setting),'ejkk':lambda:content_value(nonsync),'ejkl':lambda:content_value(lag)}
        assert run('ejkm',[],mm)==(not setting or (nonsync and lag));count+=1
        assert run('ejkq',[],mm)==(not setting or nonsync);assert run('ejkr',[],mm)==(not setting or lag);count+=2
    rows={'ejkh':{norm(args)},'svp':{norm([c(Q(2)),'motion'])}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejkn',[c(Q(2))],mm,'instance'),mm,rows,norm)
    refused(lambda:run('ejkn',[],mm))
    rows={'zfl':{('interpretation','author','ejkn','ejkl','section','discourse')}};mm={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('ejko',[],mm),mm,rows)
    return dict(cases=count,original_setup_antecedent_not_strengthened_by_interval_laws=True,both_contrast_branches_keep_same_condition=True,additional_interpretation_is_separate=True)

@lru_cache(None)
def presentation_checks():
    count=0
    table=(
        ('ejkp',{'zc':{('intro','author','ejjv','ejkm','section','discourse')},'eisoi':{('intro','author','ejkm','ejkm',('exact','approximation'),'discourse')}}),
        ('ejks',{'uh':{('result','author','ejkm','section','discourse')},'zbc':{('result','author','ejkq','ejkr','section','discourse')},'eislo':{('durationname','ejki','paper','discourse')}}),
        ('ejku',{'eir3':{('intro','author','paper','ejkt','discourse')},'ue':{('approximation','intro','discourse')}}),
        ('ejkw',{'zfl':{('interpretation','author','ejkn','ejkl','section','discourse')},'eir3':{('result','author','paper','ejkv','discourse')},'ue':{('intro','result','discourse')}}))
    for name,rows in table:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert run(name,[],mm|{n:forbidden for n in ('ejkj','ejkk','ejkl','ejkm','ejkn','ejjv','ejki')});count+=1
    # The precise ordered discussion is retained, not just a collection of two nodes.
    rows=table[0][1];mm={n:relation(rs) for n,rs in rows.items()}
    for discussion in (('approximation','exact'),('exact',),('exact','approximation','result')):
        bad={('intro','author','ejkm','ejkm',discussion,'discourse')};assert not run('ejkp',[],mm|{'eisoi':relation(bad)});count+=1
    return dict(cases=count,prior_content_and_following_conditional_result_are_shared=True,peculiar_appraisal_is_nonfactive_and_discussion_scoped=True,negation_contrast_elapsed_time_gloss_and_source_order_bound=True)

@lru_cache(None)
def source_record():
    prior=json.loads(read(SOURCE_PRIOR));assert prior==prior_source();validate_hashes(ROOT,prior['source_sha256']);out=deepcopy(prior)
    out['version']='einstein-clock-transfer-claim-source-reading-v1';out['observations']=[
        '原刊904頁でu0126の二文全体を再読した。前の一秒当たりの遅れからの帰結、folgende/eigentümliche、Kでの初期静止と同期、AからBへ速度vで連結直線上を移送する条件、到着時の非同期と初めからBにある時計との比較を確認した。',
        'M0229は½tv²/V²秒、M0230はその同じ所要時間tを説明する。出発と到着の座標時刻差を共通尺度で秒へ換算する規則を結び、二次近似と四次以上の留保を同じ到着指示差へ接続した。',
        'eigentümlicheは特有で予期から外れる帰結としての著者評価、nicht mehr synchronは到着直後の同所指示の非一致と読む。初期同期と移送の原文前件を保ち、加速中の指示変化を無視する補足は発話の外の解釈注記にする。',
        '全体の意味判断は別のreview記録で行い、数値検査の通過から自動的に作らない。']
    out['source_sha256']|={SOURCE_PRIOR:digest((ROOT/SOURCE_PRIOR).read_bytes()),DOC:digest((ROOT/DOC).read_bytes())};return out

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==345
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[341,342])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    ann=load_annotations(ROOT,BASIS,ANNOTATIONS);assert ann.find('t')['matches']
    doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    claim=names('ejkm');assert {'ejkf','ejj7','ejkb','ejkd','sww','swk','swy','svy'}<=claim
    assert not {'ejkg','ejkh','ejkn','ejko','swm','swl','swq','svr','sxa','swz'}&claim
    assert 'ejko' not in names('ejkv') and 'ejkn' in names('ejkw')
    added=[d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive'];assert {d['name'] for d in added}==set(PRIMITIVES)
    from scripts.compose_reversal_focus import PRIMITIVES as KANT
    assert PRIMITIVES['eisoi'][1].startswith(KANT['h224r'][2])
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=3,general_appraisal_relations=1,new_designation_and_source_position=2,preserved_statements=343,prior_judgments_preserved=True,extra_interval_laws_outside_author_message=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('seconds',seconds_checks),('arrival',arrival_checks),('approximation',approximation_checks),('conditional',conditional_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_clock_transfer_records','compose_clock_transfer','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','compose_reversal_focus','check_clock_transfer_records','check_clock_seconds_claim','check_clock_site_time','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_clock_transfer_claim.py','scripts/check_clock_transfer_claim.py','tests/test_clock_transfer_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='current_clock_transfer_conditional_consequence_seconds_and_qualified_lag_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0126二文全体の通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
