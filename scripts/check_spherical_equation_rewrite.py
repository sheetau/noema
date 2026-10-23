"""Check same-event sphere equations and one connected low-burden calculation."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_calculation_discourse import sequence,pair,symbol
from scripts.check_four_coordinate_claim import model as coordinate_model
from scripts.compose_spherical_equation_rewrite import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,STEPS,build

DOC='docs/spherical-equation-rewrite-v1.md';SOURCE='data/einstein-spherical-equation-rewrite-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-rest-spherical-wave-u0088-review-v1.json'
DEPENDENCIES=('reports/spherical-wave-v1.json','reports/rest-spherical-wave-v1.json','reports/four-coordinate-claim-v1.json','reports/event-coordinate-task-v1.json','reports/calculation-discourse-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'time','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zgd':'previous','zge':'rewrite','ra':'rest','zbm':'moving','zfu':'wave','zfv':'emission','zb6':'context'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'method','other','a','b','event','first','second')))
RECORDS=('x','y','z','time');POINTS=('context','discourse','other')

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky','eiyx','ei74'}
    if name=='ejag':bounds|={'ei77','ejaa','ei7c','ei3a'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if name=='ejah':
        pairs=json.loads(mode)
        helper=parse('n:r jserprogram[a d '+STEPS+'] '+STEPS+'.')['declarations'][0]
        replacement=parse('n:r ejag[] e.r ejaf[] e.r ejaa[] e.r ei7c[] e.r jserprogram[a d '+STEPS+'] '+STEPS+'.d zlx[method a stage d] '+STEPS+'[k jserprogram[v method v stage '+sequence(pairs)+']].')['declarations'][-1]
        doc['declarations']=[d for d in doc['declarations'] if d['name']!='zlx']
        missing={n for p in pairs for n in p}-{d['name'] for d in doc['declarations']}
        at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='ejah')
        doc['declarations'][at:at]=[dict(kind='primitive',name=n,parameters=[],result='content') for n in sorted(missing)]+[helper,replacement]
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jser'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jserpoint',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jserpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def run(name,args,m,domain=DOMAIN,point='discourse',mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jserpoint':lambda:point}
    mm.setdefault('jserprogram',lambda method,stage,seq:seq if (method,stage)==('method','discourse') else SequenceValue((),seq.element_type))
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def binding_checks():
    rows={'zc4':{('event',)},'eiyx':{('event','first','rest','other'),('event','second','moving','other')},'ei74':{('wave','emission','event','rest','other')}}
    m={n:relation(rs) for n,rs in rows.items()}
    count=perturb(lambda mm:run('ejae',['event','first','second','other'],mm),m,rows)
    return dict(cases=count,same_event_two_current_records_wave_emission_frames_context=True)


@lru_cache(None)
def numeric_checks():
    count=0
    # Use the current four-coordinate definitions, then the same record in sqk.
    for speed,scale,point in ((3,2,(6,0,8,2)),(4,Q(3,2),(0,6,8,2)),(0,2,(-6,8,0,2)),(3,-2,(6,0,8,2)),(3,0,(6,0,8,2)),(3,2,(6,0,8,-2))):
        cuts,m,coords,scopes,result,seen=coordinate_model(speed,scale,point);c=cuts.make
        assert run('spg',['x','y'],m) and run('sqk',['x',c(Q(5))],m) and run('sqk',['y',c(Q(5))],m);count+=3
        for slot in range(4):
            coords['y'][slot]+=1
            assert not run('spg',['x','y'],m) and not run('sqk',['y',c(Q(5))],m),(speed,scale,slot)
            coords['y'][slot]-=1;count+=2
        if scale<=0:
            assert not run('sql',['y',c(Q(5))],m);count+=1
        assert set(seen)=={Q(speed)}
    cuts,m,coords,scopes,result,seen=coordinate_model(3,2,(1,2,3,4));c=cuts.make
    assert run('spg',['x','y'],m) and not run('sqk',['x',c(Q(5))],m) and not run('sqk',['y',c(Q(5))],m);count+=3
    unknowns(lambda mm:run('spg',['x','y'],mm),m,('zc5','zc6','tc','zb7','zeq','sje','sjd','sky'))
    return dict(cases=count,same_current_four_equations_and_both_sphere_records=True,all_four_outputs_distinguished=True,negative_and_zero_phi_not_removed_from_squared_equation=True,non_light_inputs_not_promoted_to_wave=True,existing_polynomial_residual_evidence_preserved=True)


def target_model():
    cuts,m=numbers();c=cuts.make
    coords={'x':[6,0,8,2],'y':[0,6,8,2],'z':[12,0,16,4],'time':[0,12,16,4]}
    scopes={'events':{'x','y'},'arrivals':{'x','y'},'charts':{('x','x','x'),('y','y','x'),('x','z','y'),('y','time','y')}}
    m|={'ra':lambda:'x','zbm':lambda:'y','zfu':lambda:'z','zfv':lambda:'time',
        'tc':lambda:c(Q(5)),'zc5':lambda record:record in coords,'zc6':lambda record,role:c(Q(coords[record][RECORDS.index(role)])) if record in coords and role in RECORDS else forbidden(),
        'zc4':lambda e:e in scopes['events'],'eiyx':lambda e,r,f,ctx:ctx=='context' and (e,r,f) in scopes['charts'],
        'ei74':lambda w,em,e,f,ctx:(w,em,f,ctx)==('z','time','x','context') and e in scopes['arrivals']}
    return cuts,m,coords,scopes


@lru_cache(None)
def target_checks():
    count=0
    for label in ('baseline','first_bad','second_bad','missing_first','missing_second','wrong_event','wrong_frame','wrong_context','equal_alias','bad_alias','past_squared','zero_squared'):
        cuts,m,coords,s=target_model()
        if label=='first_bad':coords['z'][0]+=1
        if label=='second_bad':coords['time'][1]+=1
        if label=='missing_first':s['charts'].remove(('x','z','y'))
        if label=='missing_second':s['charts'].remove(('y','time','y'))
        if label=='wrong_event':s['charts'].remove(('x','z','y'));s['charts'].add(('y','z','y'))
        if label=='wrong_frame':m['zbm']=lambda:'z'
        if label=='wrong_context':m['zb6']=lambda:'other';m['eiyx']=lambda e,r,f,ctx:(e,r,f) in s['charts'] and ((f=='x' and ctx=='other') or (f=='y' and ctx=='context'));m['ei74']=lambda w,em,e,f,ctx:(w,em,f,ctx)==('z','time','x','other') and e in s['arrivals']
        if label in ('equal_alias','bad_alias'):
            coords['y']=coords['z'][:];s['charts'].remove(('y','y','x'));s['arrivals'].remove('y');s['charts'].add(('x','y','y'))
            if label=='bad_alias':coords['y'][0]+=1
        if label=='past_squared':coords['z'][3]*=-1
        if label=='zero_squared':coords['z']=[0,0,0,0]
        assert run('ejaf',[],m,domain=RECORDS)==(label in ('baseline','equal_alias','past_squared','zero_squared')),label;count+=1
    cuts,m,coords,s=target_model()
    unknowns(lambda mm:run('ejaf',[],mm,domain=RECORDS),m,('eiyx','ei74','zc4','zc6','zc5','tc'))
    s['arrivals'].clear();assert run('ejaf',[],m,domain=RECORDS);count+=1
    return dict(cases=count,native_full_arrival_event_and_record_scope=True,missing_k_record_rejected_for_each_K_arrival=True,bad_second_arrival_and_inconsistent_alias_rejected=True,target_alone_does_not_assert_nonempty_wave_or_future_front=True)


@lru_cache(None)
def premise_checks():
    names=('ei77','ejaa','ei7c');m={n:lambda:Content(POINTS,(True,True,True)) for n in names}|{'ei3a':lambda c:c=='context'}
    assert run('ejag',[],m);count=1
    for n in names:
        assert not run('ejag',[],m|{n:lambda:Content(POINTS,(True,False,True))});count+=1
    assert not run('ejag',[],m|{'ei3a':lambda c:False});count+=1
    assert not run('ejag',[],m|{'zb6':lambda:'other'});count+=1
    unknowns(lambda mm:run('ejag',[],mm),m,(*names,'ei3a'))
    return dict(cases=count,same_current_nonempty_wave_K_equation_four_equations_and_record_coverage=True)


@lru_cache(None)
def chain_checks():
    good=[('ejag','ejaa'),('ejaa','ejaf')];rows={}
    cases={
      'baseline':(good,2,{},True),
      'direct_allowed_rewrite':([('ejag','ejaf')],1,{},True),
      'empty':([],2,{},False),
      'reversed':(list(reversed(good)),2,{},False),
      'missing_four_equation_premise':([('ejaa','ejaf')],2,{},False),
      'wrong_result':([('ejag','ejaa')],2,{},False),
      'broken':([good[0],('ei7c','ejaf')],2,{},False),
      'expensive':(good,1,{},False),
      'negative_cost':(good,2,{good[0]:-1},False),
      'repeat_counted':([good[0],('ejaa','ejaa'),good[1]],2,{},False),
      'longer_valid':([good[0],('ejaa','ejaa'),good[1]],3,{},True),
      'cheap_other_chain':(good,0,{('ei7c','ejaf'):0},False),
    }
    for label,(pairs,budget,changed,expected) in cases.items():
        m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','discourse'),'zla':lambda a,b,s:s=='discourse','zlb':lambda step,s:Q(changed.get(pair(step),1)),'zlc':lambda n,s:s=='discourse' and n<=budget}
        actual=run('ejah',[],m,mode=json.dumps(pairs));assert actual==expected,(label,actual);rows[label]=actual
    m={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'zlw':lambda a,p,s:(a,p,s)==('author','method','discourse'),'zla':lambda a,b,s:s=='discourse' and (symbol(a),symbol(b)) in good,'zlb':lambda step,s:Q(1 if s=='discourse' else 10),'zlc':lambda n,s:s=='discourse' and n<=2}
    mode=json.dumps(good)
    for label,extra in (
        ('unavailable',{'zlw':lambda *xs:False}),('wrong_author',{'rd':lambda:'other'}),
        ('different_method',{'zlw':lambda a,p,s:(a,p,s)==('author','other','discourse')}),
        ('different_stage',{'zlw':lambda a,p,s:(a,p,s)==('author','method','other')}),
        ('forbidden_transition',{'zla':lambda a,b,s:(symbol(a),symbol(b))==good[0]}),
        ('cost_context',{'zlb':lambda step,s:Q(1 if s=='other' else 10)}),
        ('criterion_context',{'zlc':lambda n,s:s=='other' and n<=2}),
        ('program_other_method',{'jserprogram':lambda p,s,seq:seq if (p,s)==('other','discourse') else SequenceValue((),seq.element_type)})):
        assert not run('ejah',[],m|extra,mode=mode);rows[label]=False
    unknowns(lambda mm:run('ejah',[],mm,mode=mode),m,('zlw','zla','zlb','zlc'))
    assert run('ejah',[],m|{n:forbidden for n in ('ejag','ejaf','ejaa','ei7c','eiyx')},mode=mode)
    return dict(cases=rows,native_chain_and_nonnegative_total_same_existential_method=True,whole_current_premise_and_same_result_required=True,no_fixed_step_count_or_budget=True,quoted_contents_not_executed=True)


@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
        ('ejai',{'zd3':{('rewrite','author','ejag','ejaa','ejaf','section','discourse')},'uh':{('rewrite','author','ejah','section','discourse')}}),
        ('ejak',{'eir3':{('rewrite','author','paper','ejaj','discourse')},'ue':{('previous','rewrite','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ejag','ejaf','ejah','ei77','ei7c')});count+=1
    return dict(cases=count,rewrite_and_evaluation_share_node_author_section=True,prior_equation_current_premise_result_roles_preserved=True,same_paper_and_source_order_quotes_not_executed=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    root=ET.fromstring(math['M0146']['mathml']);assert ''.join(root.itertext())=='ξ2+η2+ζ2=V2τ2'
    assert [''.join(e.itertext()) for e in root.findall('.//{*}msup')]==['ξ2','η2','ζ2','V2','τ2']
    hashes=('5ffadc919ae1147b6ca607a646a894f803114a487a6773f53596f693f9976b10','b6b93209f26003f1a6ac6322e21a456a1c4203f625f57319b42613ce91af963b')
    for i,u in enumerate(inv['units'][88:90]):
        assert u['id']==f'einstein-1905:u{89+i:04d}' and u['text_sha256']==hashes[i]
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading='ξ²+η²+ζ²=V²τ²') for n in u['math_ids']]))
    retrieval='artifacts/einstein-light-proof-task-v1/retrieval.json';retrieved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']});paths={INVENTORY,DOC,retrieval,*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-spherical-equation-rewrite-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['901'],segments=segments,observations=['原刊901頁を共通零原点のK球面波からDiese Gleichung transformieren wir、簡単な計算、ξ²+η²+ζ²=V²τ²と句点まで視認・通読した。','Diese Gleichungは直前のK球面式。unsere Transformationsgleichungenは同じ著者が既に示した四座標式であり、別出来事や別の未知係数を使う変換ではない。','nach einfacher Rechnungはその同じ計算への容易さの評価である。具体的な手順数・時間・閾値は印刷されていない。','M0146はξ,η,ζの三平方和とV²τ²の等号。五平方、二つの加法と右辺の積を保持する。','次のkでの球面波の結論と二原理の両立性の証明完了はu0091へ分ける。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==307
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[305])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document();ds={d['name']:d for d in doc['declarations']};assert ds['ejaj']['body']['force']=='assert'
    assert not set(ds)&{'shd','smk','sqr','sqs','sqt','spk','sqn','sqz','zkz'}
    assert {'ei77','ejaa','ei7c','ei3a','eiyx','sqj','sqk','s2w','s2x','s2y'}<=set(ds)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,current_coordinate_wave_and_calculation_dependencies=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('binding',binding_checks),('numeric',numeric_checks),('target',target_checks),('premise',premise_checks),('chain',chain_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_spherical_equation_rewrite.py','scripts/check_spherical_equation_rewrite.py','tests/test_spherical_equation_rewrite.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_four_coordinate_claim.py','scripts/check_calculation_discourse.py','scripts/compose_calculation_discourse.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='current_sphere_equation_rewrite_and_easy_calculation_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0089–u0090の全文通読判断登録','u0091以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
