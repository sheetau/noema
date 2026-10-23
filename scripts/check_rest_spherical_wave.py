"""Check full wave-front scope, common emission and current measured arrivals."""
from functools import lru_cache
from fractions import Fraction as Q
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
from scripts.compose_rest_spherical_wave import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/rest-spherical-wave-v1.md';SOURCE='data/einstein-rest-spherical-wave-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-light-proof-task-u0086-review-v1.json'
DEPENDENCIES=('reports/spherical-wave-v1.json','reports/origin-light-ray-v1.json','reports/frame-light-law-v1.json','reports/event-coordinate-task-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'time','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zgc':'assumption','zgd':'equation','zfy':'previous','ra':'rest','zbm':'moving','zfu':'wave','zfv':'emission','zb6':'context'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'ray','segment','event','record','other','a','b')))
RECORDS=('x','y','z','time');POINTS=('context','discourse','other')

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document;bounds=NUM|{'eiyx'}
    if name=='ei73':bounds.add('ei44')
    if name in ('ei74','ei76'):bounds|={'ei73','ei46'}
    if name in ('ei75','ejaa'):bounds.add('ei74')
    if name=='ei77':bounds|={'ei76','ei75','ei43'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jrsw'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jrswpoint',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jrswpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(name,args,m,domain=DOMAIN,point='discourse'):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jrswpoint':lambda:point}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def coordinate_model():
    cuts,m=numbers();c=cuts.make;coords={'x':[0,0,0,0],'y':[6,0,8,2],'z':[0,6,8,2],'time':[1,0,0,1]}
    m|={'tc':lambda:c(Q(5)),'zc5':lambda record:record in coords,'zc6':lambda record,role:c(Q(coords[record][RECORDS.index(role)])) if record in coords and role in RECORDS else forbidden()}
    return cuts,m,coords

@lru_cache(None)
def numeric_checks():
    cuts,m,coords=coordinate_model();c=cuts.make;count=0
    for point,cone,future in (((6,0,8,2),True,True),((0,6,8,2),True,True),((-6,-8,0,2),True,True),((0,0,0,0),True,False),((6,0,8,-2),True,False),((1,0,0,1),False,False)):
        coords['y']=list(point)
        assert run('sqk',['y',c(Q(5))],m)==cone and run('sql',['y',c(Q(5))],m)==future;count+=2
        if cone:
            for slot in range(4):
                coords['y'][slot]+=1;assert not run('sqk',['y',c(Q(5))],m);coords['y'][slot]-=1;count+=1
    coords['y']=[6,0,8,2]
    for speed in (0,-5,4):assert not run('sqk',['y',c(Q(speed))],m);count+=1
    unknowns(lambda mm:run('sql',['y',c(Q(5))],mm),m,('zc5','zc6','ba','sca','bg','shv'))
    return dict(cases=count,three_positions_time_and_positive_V_bound=True,squared_equation_distinct_from_future_front=True,emission_zero_and_negative_time_separated=True)

@lru_cache(None)
def arrival_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    rows={'zft':{('wave','ray','other')},'cf':{('ray',)},'ei44':{('segment','ray','emission','event',Q(10),'rest',Q(5),'other')}}
    m|={'tc':lambda:c(Q(5)),'wq':lambda s:c(Q(10)) if s=='segment' else forbidden(),'wh':lambda s:'emission' if s=='segment' else forbidden()}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    args=['wave','ray','emission','event','segment','rest','other'];count=perturb(lambda mm:run('ei73',args,mm),m,rows,norm)
    assert not run('ei73',args,m|{'wh':lambda s:'other'});count+=1
    unknowns(lambda mm:run('ei73',args,mm),m,('wh','wq','tc'))
    row=('a','b','b','a','a','b','other');m={'ei73':relation({row})}
    count+=perturb(lambda mm:run('ei74',['a','b','a','b','other'],mm,domain=('a','b')),m,{'ei73':{row}})
    return dict(cases=count,same_wave_ray_emission_endpoint_segment_frame_context=True,native_two_witness_arrival_binding=True,current_measurement_body_is_separately_pinned_ei44=True)

@lru_cache(None)
def emission_checks():
    members={'a','b'};rows={'ei46':{('b','a','b','other')},'ei73':{('a','a','b','b','a','a','other'),('a','b','b','a','b','a','other')}}
    def coordinate(e,f,ctx):
        if e!='b' or f not in ('a','b') or ctx!='other':forbidden()
        return f
    m={'ra':lambda:'a','zbm':lambda:'b','zdz':coordinate,'zft':lambda w,r,ctx:w=='a' and r in members and ctx=='other'}|{n:relation(rs) for n,rs in rows.items()}
    count=perturb(lambda mm:run('ei76',['a','b','other'],mm,domain=('a','b')),m,rows)
    members.clear();assert not run('ei76',['a','b','other'],m,domain=('a','b'));count+=1
    members.add('a');assert run('ei76',['a','b','other'],m,domain=('a','b'));count+=1
    members.add('b');unknowns(lambda mm:run('ei76',['a','b','other'],mm,domain=('a','b')),m,('zdz','zft','ei46','ei73'))
    return dict(cases=count,nonempty_all_constituent_rays_share_emission=True,same_event_two_current_zero_origin_records=True,two_value_witness_domain_not_large_tuple_enumeration=True)

def front_model():
    cuts,m,coords=coordinate_model();scopes={'events':set(RECORDS),'arrivals':{'y','z'},'charts':{(a,a) for a in RECORDS}}
    m|={'ra':lambda:'x','zfu':lambda:'z','zfv':lambda:'x','zc4':lambda e:e in scopes['events'],
        'eiyx':lambda e,r,f,ctx:f=='x' and ctx=='context' and (e,r) in scopes['charts'],
        'ei74':lambda w,em,e,f,ctx:(w,em,f,ctx)==('z','x','x','context') and e in scopes['arrivals']}
    return cuts,m,coords,scopes

@lru_cache(None)
def front_checks():
    count=0
    for label in ('baseline','missing_direction','extra_interior_arrival','past_arrival','empty_scope','empty_arrivals','wrong_frame','same_value_alias','inconsistent_alias'):
        cuts,m,coords,s=front_model();args=['z','x','x','context']
        if label=='missing_direction':s['arrivals'].remove('z')
        if label=='extra_interior_arrival':s['arrivals'].add('time')
        if label=='past_arrival':coords['z'][3]=-2
        if label=='empty_scope':s['events']=set()
        if label=='empty_arrivals':s['arrivals']=set()
        if label=='wrong_frame':args[2]='y'
        if label in ('same_value_alias','inconsistent_alias'):
            coords['time']=coords['y'][:];s['charts'].remove(('time','time'));s['charts'].add(('y','time'))
            if label=='inconsistent_alias':coords['time'][0]+=1
        assert run('ei75',args,m,domain=RECORDS)==(label in ('baseline','same_value_alias')),label;count+=1
    cuts,m,coords,s=front_model()
    assert run('ejaa',[],m,domain=RECORDS);count+=1
    for e in ('y','z'):
        coords[e][0]+=1;assert not run('ejaa',[],m,domain=RECORDS);coords[e][0]-=1;count+=1
    s['arrivals'].add('time');assert not run('ejaa',[],m,domain=RECORDS);count+=1
    s['arrivals']=set();assert run('ejaa',[],m,domain=RECORDS);assert not run('ei75',['z','x','x','context'],m,domain=RECORDS);count+=2
    s['arrivals']={'y','z'}
    unknowns(lambda mm:run('ei75',['z','x','x','context'],mm,domain=RECORDS),m,('eiyx','ei74','zc4','zc6','tc','ba','sca'))
    return dict(cases=count,full_native_event_record_scope_and_both_directions=True,missing_and_extra_arrival_alias_and_future_side_checked=True,equation_covers_arbitrary_current_arrival_record=True,vacuous_conditional_does_not_supply_nonempty_wave=True)

@lru_cache(None)
def presentation_checks():
    cuts,m=numbers();norm=lambda xs:tuple(cuts.read(x) if isinstance(x,FunctionValue) else x for x in xs)
    rows={'ei76':{('wave','emission','context')},'ei43':{('rest',Q(5),'context')},'ei75':{('wave','emission','rest','context')}}
    m|={'tc':lambda:cuts.make(Q(5))}|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count=perturb(lambda mm:run('ei77',[],mm),m,rows,norm)
    for name,rows in (
        ('ejab',{'ug':{('assumption','author','ei77','section','discourse')},'zc':{('equation','author','ei77','ejaa','section','discourse')},'ue':{('assumption','equation','discourse')}}),
        ('ejad',{'eir3':{('assumption','author','paper','ejac','discourse')},'ue':{('previous','assumption','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{n:forbidden for n in ('ei77','ejaa','ei73','ei75','ei46')});count+=1
    return dict(cases=count,one_wave_emission_setting_and_V_joined=True,assumption_and_conditional_consequence_distinct=True,same_author_section_order_and_quotes_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    readings={'M0141':'t=τ=0','M0142':'K','M0143':'V','M0144':'x,y,z','M0145':'x²+y²+z²=V²t²'}
    for n,flat in zip(readings,('t=τ=0','K','V','x,y,z','x2+y2+z2=V2t2')):assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==flat
    assert len(ET.fromstring(math['M0145']['mathml']).findall('.//{*}msup'))==5
    hashes=('0f6ba2657250679177c450733a1f6b975bc01a188585f5492e6853fe6db16c78','a5285db7b7e0c75e976f1618a3037a1ed2ebedcce05a1fd44e4f8f38f5b3105d')
    for i,u in enumerate(inv['units'][86:88]):
        assert u['id']==f'einstein-1905:u{87+i:04d}' and u['text_sha256']==hashes[i]
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n]) for n in u['math_ids']]))
    retrieval='artifacts/einstein-light-proof-task-v1/retrieval.json';retrieved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']});paths={INVENTORY,DOC,retrieval,*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-rest-spherical-wave-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['901'],segments=segments,observations=['原刊901頁のZur Zeit t=τ=0からK球面波、Ist (x,y,z)の到来点、x²+y²+z²=V²t²と句点まで通読した。','共通の座標原点はzu dieser Zeitの放出時に限定され、波の放出はwerdeによる仮定として提示される。','KとVは既出の同じ系と光速度である。eben ... ergriffenerはその時に波が到来する点を指し、既に通過した内部全体としない。','式は三位置の平方和とV²t²の等号。単独の二乗式と未来側の波面を分け、時刻零の放出を別条件にする。','次のDiese Gleichung transformieren wirの計算は後続単位へ残す。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==306
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[304])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document();ds={d['name']:d for d in doc['declarations']};assert ds['ejac']['body']['force']=='assert'
    assert not set(ds)&{'shd','smk','sqn','sqo','sqp','sqq','sqy'}
    assert {'ei44','ei43','ei46','eiyx','sqj','sqk','sql'}<=set(ds)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,current_origin_and_measured_arrival_reused=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('arrival',arrival_checks),('emission',emission_checks),('front',front_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_rest_spherical_wave.py','scripts/check_rest_spherical_wave.py','tests/test_rest_spherical_wave.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='current_rest_spherical_wave_and_arbitrary_arrival_equation_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0087–u0088の全文通読判断登録','u0089以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
