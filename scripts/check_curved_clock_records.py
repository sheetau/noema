"""Check complete current curve bindings and the still-unattributed extension."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,SequenceValue,Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_clock_transfer_records import phase_model
from scripts.check_polygon_clock_claim import model as polygon_model,CONSTANTS,DOMAIN,POINTS
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.check_rod_methods import value
from scripts.compose_curved_clock_records import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,CURVE,COMPARE,POINT,OLD_CURVE,PATH,POLYGON_COMPARE,build

DOC='docs/curved-clock-records-v1.md';SOURCE='data/einstein-curved-clock-records-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-polygon-clock-u0127-review-v1.json'
DEPENDENCIES=('reports/polygon-clock-claim-v1.json','reports/clock-transfer-records-v1.json')
BOUNDS={'ejlm':{'ejj6'},'ejln':{'ejlm'},'ejlo':{'se','ejj5','ejlm','ejln'},'ejlp':{'sxv','ejlo','ejj7'},'ejlq':{'ejlp','ejk2'},'ejlr':{'ejlb'},'ejls':{'ejla'},'ejlt':{'svp'},'ejlu':{'ejlq','ejkb'},'ejlv':{'ejlq','ejls'},'ejlw':{'ejlq','ejlr','ejls'},'ejlx':{'ejlc','ejlv'},'ejly':{'ejlc','ejlv'},'sxv':{'sxu','sjs'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=BOUNDS.get(name,set()) if mode!='native' else set()
    abstract(doc,NUM|{'sje','sjd','sky','zzbb','zzbd'}|bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        added=expose(d,{'forall','exists'},only_sort=None if name in ('ejlv','ejlw') else RS)
        assert len(added)==(len(COMPARE) if name in ('ejlv','ejlw') else 1)
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jccr'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jccrpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jccrpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jccrpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def norm_factory(cuts,individuals=('e0','e1','e2','alias','s0','s1','initialreference')):
    def one(x):
        if not isinstance(x,FunctionValue):return value(x)
        if x.parameters==('number',):return cuts.read(x)
        if x.parameters==('individual',):return tuple(one(x(n)) for n in individuals)
        if x.parameters==(RS,):return tuple(one(x(cuts.make(Q(t)))) for t in (0,10,15,20,30))
        forbidden()
    return lambda xs:tuple(one(x) for x in xs)

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

def model():
    cuts,m,coords,p,_,tables=polygon_model(True);c=cuts.make;r=cuts.read;norm=norm_factory(cuts)
    def components(t):
        s=t-10
        return (Q(3,5)*s*(10-s),Q(1,25)*s*(10-s)*(s-5),Q(0),Q(3,5)*(10-2*s),Q(1,25)*(-3*s*s+30*s-50),Q(0))
    funcs=[FunctionValue((RS,),RS,lambda time,i=i:c(components(r(time))[i])) for i in range(6)]
    def track(cl,frame,lu,tu,axis,setting):
        if cl!='clock' or (frame,lu,tu)!=('K','length','duration') or axis not in ('x','y','z') or setting!='motion':forbidden()
        return funcs[('x','y','z').index(axis)]
    m['eismh']=track;a=p[3:11]+funcs
    # shh evaluates guarded non-axis candidates eagerly. Give these known, inactive
    # individuals explicit dummy coordinates; unknown records/individuals still fail.
    axes=('x','y','z','time')
    def coordinate(record,axis):
        if record not in coords or axis not in DOMAIN+('r1alias',):forbidden()
        return c(Q(coords[record][axes.index(axis)]) if axis in axes else Q(0))
    m['zc6']=coordinate
    return cuts,m,coords,a,a+p[11:],norm,tables

def adapted(a,items):
    fields=dict(zip((n for n,_ in COMPARE),a));empty=SequenceValue((),'"individual"')
    constants={'segments':empty,'start':FunctionValue(('individual',),'individual',lambda x:fields['first']),'end':FunctionValue(('individual',),'individual',lambda x:fields['last'])}
    return [constants[n] if n in constants else fields[n] for n,_ in items]

@lru_cache(None)
def point_checks():
    cuts,m,coords,a,compare,norm,t=model();c=cuts.make;count=0
    p=a+['e1','alias','r1','C'];row=['clock','e1','alias','r1','C',c(Q(11)),'motion'];rows={'ejj6':{norm(row)}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejlm',p,mm),mm,rows,norm)
    for axis in range(4):
        coords['r1'][axis]+=1;assert not run('ejlm',p,mm);coords['r1'][axis]-=1;count+=1
    t['records']['e1']='r0';assert not run('ejlm',p,mm);t['records']['e1']='r1';count+=1
    t['places']['e1']='B';assert not run('ejlm',p,mm);t['places']['e1']='C';count+=1
    # A changed dial is a possible observation before the extension law is assumed.
    t['readings']['e1']=Q(12);rows={'ejj6':{norm(row[:5]+[c(Q(12)),row[6]])}}
    assert run('ejlm',p,relations(m,rows,norm));assert not run('ejlm',p,mm);count+=2;t['readings']['e1']=Q(11)
    coords['r1alias']=coords['r1'][:];alias=p[:-2]+['r1alias','C']
    assert run('ejlm',alias,m|{'ejj6':lambda *xs:True},domain=DOMAIN+('r1alias',));count+=1
    for axis in range(4):
        coords['r1alias'][axis]+=1;assert not run('ejlm',alias,m|{'ejj6':lambda *xs:True},domain=DOMAIN+('r1alias',));coords['r1alias'][axis]-=1;count+=1
    original=coords['r1'][:]
    for at in (9,21):
        coords['r1']=[cuts.read(f(c(Q(at)))) for f in a[8:11]]+[at]
        assert not run('ejlm',p,mm);count+=1
    coords['r1']=original
    for record,axis in (('unknown','x'),('r1','unknown')):
        try:m['zc6'](record,axis)
        except ValueError as e:assert 'Unknown clock-site-time' in str(e)
        else:raise AssertionError('Unknown coordinate input accepted')
        count+=1
    unknowns(lambda mm:run('ejlm',p,mm),mm,('zc6',))
    return dict(cases=count,current_observed_record_candidate_curve_place_and_reading_shared=True,numerical_record_alias_allowed_but_inconsistent_chart_rejected=True,changed_reading_not_a_geometric_failure=True)

def small_model():
    cuts,m,coords,fs,_,domain,base=phase_model();c=cuts.make;norm=norm_factory(cuts,domain)
    record=FunctionValue(('individual',),'individual',lambda x:x)
    reading=FunctionValue(('individual',),RS,lambda x:c(Q(7+domain.index(x))))
    places=FunctionValue(('individual',),'individual',lambda x:'b')
    a=[record,reading,places,'a','a','b',c(Q(3)),'context',*([fs['x']]*6)]
    return cuts,m,a,norm,domain,base

@lru_cache(None)
def coverage_checks():
    cuts,m,a,norm,domain,base=small_model();c=cuts.make;count=0
    for witnesses in product(domain,repeat=4):
        rows={'ejlm':{norm(a+list(witnesses))}};mm=relations(m,rows,norm);time=c(Q(domain.index(witnesses[2])))
        count+=perturb(lambda mm:run('ejln',a+[time],mm,domain=domain),mm,rows,norm)
        assert not run('ejln',a+[c(Q(1-domain.index(witnesses[2])))],mm,domain=domain);count+=1
    local=('a','b','a','b','b','context');rows=base|{'ejj5':{local},'ejlm':{norm(a+list(local[1:5]))},'ejln':{norm(a+[c(Q(1))])}}
    mm=relations(m,rows,norm);check=lambda mm:run('ejlo',a+[c(Q(1))],mm,'instance',domain)
    # Recreate se rows under this norm; phase_model's original norm sampled different times.
    hist=['a','a','context','b','b',c(Q(0)),c(Q(1)),*([a[8]]*3)]
    rows['se']={norm(hist)};mm=relations(m,rows,norm)
    count+=perturb(check,mm,{n:rs for n,rs in rows.items() if n!='ejj5'},norm)
    extra=('a','a','b','a','a','context');assert not check(mm|{'ejj5':relation({local,extra})});count+=1
    # Removing the target-time witness cannot be repaired by correct sampled records.
    assert not check(mm|{'ejln':lambda *xs:False});count+=1
    refused(lambda:run('ejlo',a,mm,domain=domain))
    return dict(cases=count,four_shared_witnesses_every_slot=True,all_current_candidates_and_all_real_times_distinct=True,complete_phase_and_calibration_bound=True)

@lru_cache(None)
def kinematic_checks():
    cuts,m,coords,a,compare,norm,t=model();c=cuts.make;r=cuts.read;count=0
    velocities=(Q(9,5),Q(12,5),Q(0));origins=(Q(2),Q(3),Q(4))
    position=[FunctionValue((RS,),RS,lambda time,i=i:c(origins[i]+velocities[i]*(r(time)-10))) for i in range(3)]
    velocity=[FunctionValue((RS,),RS,lambda time,i=i:c(velocities[i])) for i in range(3)]
    linear=a[:8]+position+velocity;fields=dict(zip((n for n,_ in CURVE),linear));old=[fields[n] for n,_ in OLD_CURVE]
    domain=FunctionValue((RS,),'truth',lambda time:10<=r(time)<=20)
    for at in (Q(10),Q(15),Q(20)):
        rows={'sxu':{norm([domain,f]) for f in position+velocity},'sjs':{norm([domain,f,c(at),c(vv)]) for f,vv in zip(position,velocities)}}
        mm=relations(m,rows,norm);count+=perturb(lambda mm:run('sxv',old+[c(at)],mm,'instance'),mm,rows,norm)
        bad=old[:];bad[5]=c(Q(4));assert not run('sxv',bad+[c(at)],mm,'instance');count+=1
        refused(lambda:run('sxv',old,mm))
    for speed,components,expected in ((3,(3,0,0),True),(3,(-3,0,0),True),(3,(0,0,-3),True),(3,velocities,True),(3,(3,3,0),False),(0,(0,0,0),False),(-3,(3,0,0),False)):
        assert run('syh',[c(Q(x)) for x in (speed,*components)],m)==expected;count+=1
    # The closed test polynomial used for observations is deliberately not uniform-speed.
    for at in (10,15,20):assert not run('syh',[a[6],*(f(c(Q(at))) for f in a[11:14])],m);count+=1
    refused(lambda:run('sxu',[domain,position[0]],m));refused(lambda:run('sjs',[domain,position[0],c(Q(10)),c(velocities[0])],m))
    rows={'sxv':{norm([dict(zip((n for n,_ in CURVE),a))[n] for n,_ in OLD_CURVE])},'ejlo':{norm(a)},'ejj7':{norm(['clock',e,a[0](e),a[2](e),a[1](e),'motion']) for e in ('e0','e2')}}
    count+=perturb(lambda mm:run('ejlp',a,mm),relations(m,rows,norm),rows,norm)
    return dict(cases=count,all_six_continuities_three_derivatives_and_common_speed_bound=True,relative_endpoint_domain_and_native_infinite_rejection=True,closed_polynomial_fixture_not_certified_uniform_speed=True)

@lru_cache(None)
def adapter_checks():
    cuts,m,coords,a,compare,norm,t=model();c=cuts.make;count=0
    for name,key,items,arguments in (('ejlr','ejlb',PATH,a),('ejls','ejla',POLYGON_COMPARE,compare)):
        row=adapted(compare,items);rows={key:{norm(row)}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run(name,arguments,mm),mm,rows,norm)
        assert row[0].items==() and row[1]('e1')=='e0' and row[2]('e1')=='e2';count+=1
    rows={'ejlp':{norm(a)},'ejk2':{norm(adapted(compare,POLYGON_COMPARE))}}
    count+=perturb(lambda mm:run('ejlq',compare,mm),relations(m,rows,norm),rows,norm)
    for scale in (Q(1,5),Q(1),Q(2)):
        rows={'svp':{norm([c(scale),'motion'])}};mm=relations(m,rows,norm)
        count+=perturb(lambda mm:run('ejlt',a+[c(10*scale),c(scale)],mm,'instance'),mm,rows,norm)
        assert not run('ejlt',a+[c(10*scale+1),c(scale)],mm,'instance');count+=1
        refused(lambda:run('ejlt',a+[c(10*scale)],mm))
    rows={'ejlq':{norm(compare)},'ejkb':{norm(['clock',c(Q(10)),c(Q(20)),c(Q(7)),c(Q(4,5)),'motion']),norm(['reference',c(Q(10)),c(Q(20)),c(Q(7)),c(Q(1)),'motion'])}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejlu',compare,mm),mm,rows,norm)
    t['readings']['e2']+=1;assert not run('ejlu',compare,mm);t['readings']['e2']-=1;count+=1
    bad=compare[:];bad[-2]=c(Q(18));assert not run('ejlu',bad,mm|{'ejlq':lambda *xs:True});count+=1
    return dict(cases=count,unused_polygon_parameters_explicit_and_no_fake_path=True,initial_comparison_return_and_total_lag_reuse_current_rules=True,elapsed_seconds_and_additional_rate_laws_separate=True)

@lru_cache(None)
def scope_checks():
    cuts,m,coords,a,compare,norm,t=model();count=0
    for name in ('ejlv','ejlw'):
        for setting,closed,result in product((False,True),repeat=3):
            mm=m|{'ejlq':lambda *xs:setting,'ejlr':lambda *xs:closed,'ejls':lambda *xs:result}
            assert run(name,compare,mm,'instance')==(not(setting and (closed if name=='ejlw' else True)) or result);count+=1
        rows={'ejlq':{norm(compare)},'ejls':{norm(compare)}}
        if name=='ejlw':rows['ejlr']={norm(a)}
        mm=relations(m,rows,norm);count+=perturb(lambda mm:run(name,compare,mm,'instance'),mm,{'ejls':rows['ejls']},norm)
        for key in ('ejlq',)+(('ejlr',) if name=='ejlw' else ()):
            row=next(iter(rows[key]))
            for i in range(len(row)):
                bad=tuple('wrong' if i==j else x for j,x in enumerate(row))
                assert run(name,compare,mm|{key:lambda *xs,bad=bad:norm(xs)==bad,'ejls':lambda *xs:False},'instance');count+=1
        refused(lambda:run(name,[],mm))
    def cv(truth):return Content(POINTS,tuple(truth if p=='discourse' else not truth for p in POINTS))
    for polygon,curve in product((False,True),repeat=2):
        mm={'ejlc':lambda:cv(polygon),'ejlv':lambda:cv(curve)}
        assert run('ejlx',[],mm)==(not polygon or curve);assert run('ejly',[],mm)==(polygon and curve);count+=2
    return dict(cases=count,all_curve_function_real_and_situation_quantifiers_preserved=True,closed_case_only_adds_return=True,polygon_content_and_assumed_extension_not_conflated=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][127];assert u['id']=='einstein-1905:u0128' and digest(u['text'].encode())==u['text_sha256'];table={m['id']:m for m in inv['math']};math=[]
    for mid,flat in zip(u['math_ids'],('A','A','t','A','12t(v/V)2')):
        e=table[mid];assert re.sub(r'\s','',''.join(ET.fromstring(e['mathml']).itertext()))==flat;assert digest(e['mathml'].encode())==e['sha256'];math.append(dict(id=mid,sha256=e['sha256'],mathml_flat=flat))
    assert len(math)==len(u['math_ids'])==5
    paths={INVENTORY,DOC}
    for retrieval in ('artifacts/einstein-origin-clock-setting-v1/retrieval.json','artifacts/einstein-curved-clock-records-v1/retrieval.json'):
        rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths|={retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-curved-clock-records-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['904','905'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=math)],observations=['原刊904頁末のNimmt man anから905頁冒頭の赤道・極の時計比較まで通読した。改頁をまたぐun-bewegt gebliebenenと½t(v/V)²秒の式は同じ帰還比較に属する。A0018は頁境界であり著者の注ではない。','曲線への拡張を仮定することと、著者が折れ線結果を証明済みとして扱うことを区別する。閉曲線・一定の速さ・初期同期・同じAへの帰還・所要時間t・残る時計との到着比較を保持する。','後半はUnruhuhr、全く同じ構造、その他同条件、赤道と一方の極、ごく小さい歩度差とそこからの推論を含む。今回は前半の現在表示と曲線の依存群であり、発話・地球時計の接続と全単位判断は後続。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==347
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[345,346])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert {'sxv','sxu','sjs','syh','ejj5','ejj6','ejlo','ejk2','ejla','swy'}<=names('ejlv')
    assert not {'swl','swq','x4','sxl','sxp','sxq','ejlu'}&names('ejlv')
    assert {'ejlc','ejlv'}<=names('ejlx') and {'ejlc','ejlx'}<=names('ejly')
    # End comparison adapters genuinely do not inspect the three polygon-only parameters.
    for name in ('ejk2','ejlb','ejla','ejk7','sxn','sxo'):
        d=next(x for x in doc['declarations'] if x['name']==name)
        def variables(x):
            if isinstance(x,list):return set().union(*(variables(y) for y in x))
            if isinstance(x,dict):return ({x['name']} if x.get('kind')=='variable' else set())|set().union(*(variables(y) for y in x.values()))
            return set()
        # ejlb/ejla pass the unused parameters on to sxn/sxo; these leaf bodies are decisive.
        if name in ('ejk2','ejk7','sxn','sxo'):assert not {p['name'] for p in d['parameters'][:3]}&variables(d['body'])
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=347,prior_judgments_preserved=True,current_geometry_and_displays_do_not_assume_lag=True,author_attribution_and_earth_clocks_still_pending=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('point',point_checks),('coverage',coverage_checks),('kinematics',kinematic_checks),('adapters',adapter_checks),('scope',scope_checks),('structure',structure_checks)]}
    helpers=('compose_polygon_clock_claim','compose_curved_clock','compose_clock_transfer_records','compose_rod_methods','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_limits','check_polygon_clock_claim','check_clock_transfer_records','check_clock_site_time','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_curved_clock_records.py','scripts/check_curved_clock_records.py','tests/test_curved_clock_records.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='current_complete_curved_clock_records_and_extension_content_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0128の仮定・証明済みという位置付け・帰結の発話、所要時間tの説明、地球時計の機構/比較条件/歩度差、全文通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
