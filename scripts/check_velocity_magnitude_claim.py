"""Check theory attribution, actual coordinate derivatives and both speed definitions."""
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
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_rod_methods import value
from scripts.check_point_motion_records import moving_model
from scripts.check_point_motion_transform import model
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import refused
from scripts.compose_velocity_magnitude_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build

DOC='docs/velocity-magnitude-claim-v1.md';SOURCE='data/einstein-velocity-magnitude-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/einstein-velocity-first-order-source-reading-v1.json'
PRIORS=tuple(f'data/einstein-point-motion-u{n:04d}-review-v1.json' for n in (133,134))
DEPENDENCIES=('reports/velocity-first-order-v1.json','reports/point-motion-records-v1.json','reports/point-motion-transform-v1.json','reports/point-motion-claim-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','zkb':'clock','rd':'author','eirf':'paper','ri':'discourse','eisoq':'fifth','zkh':'equations','eisoy':'consequence','eisoz':'introduction','zkr':'first','zks':'second','eiso2':'Uname','eiso3':'wname'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b','other')));POINTS=('context','discourse','other')
BOUNDS={'szq':{'sjs'},'ejoh':{'ejmv','sjs'},'ejoi':{'ejny','ejoh'},'ejoj':{'ejmx'},'ejop':{'ejoi'},'ejoq':{'ejoj'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky','zzbb','zzbd'}
    if mode!='native':bounds|=BOUNDS.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert name=='ejoi' and len(expose(d,{'forall','exists'},only_sort=RS))==3
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvmc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jvmcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jvmcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots


def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jvmcpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def norm_with_domains(cuts,times=(-4,-3,0,2,7,8)):
    def one(x):
        if not isinstance(x,FunctionValue):return value(x)
        if x.parameters==('number',):return cuts.read(x)
        if x.parameters==(RS,):
            if x.result==RS:return tuple(cuts.read(x(cuts.make(Q(t)))) for t in times)
            if x.result=='truth':return tuple(x(cuts.make(Q(t))) for t in times)
        forbidden()
    return lambda xs:tuple(one(x) for x in xs)


def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}


@lru_cache(None)
def magnitude_checks():
    cuts,m,coords,norm,beta,den=model();c=lambda x:cuts.make(Q(x));count=0
    for x,y,speed in product((-4,-3,0,3,4),repeat=3):
        assert run('szn',list(map(c,(speed,x,y))),m)==(speed>=0 and speed*speed==x*x+y*y);count+=1
    for scale in (Q(1,2),Q(1),Q(2)):
        for sx,sy,sm in product((-1,1),repeat=3):
            assert run('szn',list(map(c,(sm*5*scale,sx*3*scale,sy*4*scale))),m)==(sm==1);count+=1
    unknowns(lambda mm:run('szn',list(map(c,(5,3,4))),mm),m,('ba','shv','bd','sca','bg'))
    # A second derivative and the common nonnegative norm both matter.
    cuts,m,fs,_=moving_model((2,-7,0),(3,4,0));c=lambda x:cuts.make(Q(x));norm=norm_with_domains(cuts)
    domain=FunctionValue((RS,),'truth',lambda t:-3<=cuts.read(t)<=7);t=c(2)
    rows={'sjs':{norm((domain,fs[i],t,c(v))) for i,v in enumerate((3,4))}}
    mm=relations(m,rows,norm);args=[domain,*fs[:2],t,c(3),c(4),c(5)]
    count+=perturb(lambda mm:run('szq',args,mm),mm,rows,norm)
    for slot in (3,4,5,6):
        bad=args[:];bad[slot]=c(cuts.read(bad[slot])+1);assert not run('szq',bad,mm);count+=1
    refused(lambda:run('szq',args,m,'native'))
    return dict(cases=count,nonnegative_two_component_norm_including_zero=True,signed_components_and_negative_magnitude_distinguished=True,both_actual_derivative_arguments_and_shared_time_required=True,native_real_derivatives_refuse_finite_enumeration=True)


@lru_cache(None)
def trajectory_checks():
    count=0
    for origin,velocity in product(((0,0,0),(2,-7,0)),((0,0,0),(3,4,0),(-3,4,0))):
        cuts,m,fs,_=moving_model(origin,velocity);c=lambda x:cuts.make(Q(x));norm=norm_with_domains(cuts);mag=0 if velocity==(0,0,0) else 5
        domain=FunctionValue((RS,),'truth',lambda t:-3<=cuts.read(t)<=7)
        for instant in (-3,0,2,7):
            rows={'ejmv':{('clock','K',Q(velocity[0]),Q(velocity[1]),Q(0),'context')},'sjs':{norm((domain,fs[i],c(instant),c(velocity[i]))) for i in (0,1)}}
            mm=relations(m,rows,norm);args=['clock','K',c(velocity[0]),c(velocity[1]),c(instant),c(mag),'context']
            count+=perturb(lambda mm:run('ejoh',args,mm),mm,rows,norm)
            for slot in (2,3,4,5):
                bad=args[:];bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ejoh',bad,mm);count+=1
            unknowns(lambda mm:run('ejoh',args,mm),mm,('eismh','eisls','eislt'))
        for instant in (-4,8):
            args=['clock','K',c(velocity[0]),c(velocity[1]),c(instant),c(mag),'context']
            assert not run('ejoh',args,m|{'ejmv':lambda *xs:True,'sjs':lambda *xs:True});count+=1
    # Distinct object, frame, length/time units and context must reach the tracks.
    cuts,m,fs,_=moving_model((2,-7,0),(3,4,0));c=lambda x:cuts.make(Q(x));norm=norm_with_domains(cuts)
    args=['clock','K',c(3),c(4),c(2),c(5),'context'];domain=FunctionValue((RS,),'truth',lambda t:-3<=cuts.read(t)<=7)
    rows={'ejmv':{('clock','K',Q(3),Q(4),Q(0),'context')},'sjs':{norm((domain,fs[i],c(2),c(v))) for i,v in enumerate((3,4))}}
    mm=relations(m,rows,norm)
    for symbol in ('ta','rb'):
        try:run('ejoh',args,mm|{symbol:lambda:'other'})
        except ValueError:pass
        else:raise AssertionError('Different coordinate unit silently accepted')
        count+=1
    return dict(cases=count,same_actual_two_coordinate_functions_frame_units_and_full_period=True,interior_and_both_endpoint_times_checked=True,constant_planar_velocity_and_derivative_norm_not_conflated=True)


@lru_cache(None)
def scope_checks():
    cuts,m,fs,_=moving_model((2,-7,0),(3,4,0));c=lambda x:cuts.make(Q(x));norm=norm_with_domains(cuts);count=0
    for instant in (-3,0,2,7):
        rows={'ejny':{('clock','context',Q(3),Q(4))},'ejoh':{('clock','K',Q(3),Q(4),Q(instant),Q(5),'context')}}
        mm=relations(m,rows,norm);args=[c(5),'context',c(3),c(4),c(instant)]
        count+=perturb(lambda mm:run('ejoi',args,mm,'instance'),mm,rows,norm)
    for instant in (-4,8):
        mm=relations(m,{'ejny':{('clock','context',Q(3),Q(4))}},norm)|{'ejoh':lambda *xs:False}
        assert run('ejoi',[c(5),'context',c(3),c(4),c(instant)],mm,'instance');count+=1
    refused(lambda:run('ejoi',[c(5),'context'],m|{'ejny':lambda *xs:True,'ejoh':lambda *xs:True}))
    cuts,m,coords,_,beta,den=model(3,3,4);c=lambda x:cuts.make(Q(x));norm=norm_with_domains(cuts)
    rows={'ejmx':{('context',)}};mm=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejoj',[c(5),'context'],mm),mm,rows,norm)
    assert not run('ejoj',[c(-5),'context'],mm);count+=1
    unknowns(lambda mm:run('ejoj',[c(5),'context'],mm),mm,('zkc','zkd'))
    for symbol,reference,source in (('ejop','zkp','ejoi'),('ejoq','zkq','ejoj')):
        rows={source:{(Q(5),'context')}};mm=relations(m,rows,norm)|{reference:lambda:c(5)}
        args=['clock',c(5),'context'];count+=perturb(lambda mm:run(symbol,args,mm),mm,rows,norm)
        assert not run(symbol,['other',c(5),'context'],mm);count+=1
        assert not run(symbol,args,mm|{reference:lambda:c(4)});count+=1
        unknowns(lambda mm:run(symbol,args,mm),mm,(reference,))
    return dict(cases=count,same_two_existential_components_at_every_real_time=True,own_speed_uses_current_planar_motion=True,notation_binds_same_point_and_distinct_magnitudes=True,native_real_time_and_component_quantifiers_refuse_enumeration=True)


@lru_cache(None)
def presentation_checks():
    count=0;domain=('a','b')
    for theory,item in product(domain,repeat=2):
        rows={'eisdj':{(theory,'a','eigj','discourse')},'eiscr':{(theory,item,'discourse')},'eisox':{(item,'ejoc','discourse')}}
        mm={n:relation(rs) for n,rs in rows.items()}|{'eirf':lambda:'a'}
        count+=perturb(lambda mm:run('ejod',[],mm,domain=domain),mm,rows)
        assert run('ejod',[],mm|{'ejoc':forbidden,'eismh':forbidden,'tc':forbidden},domain=domain);count+=1
    tables=(('ejoe',{'zc':{('consequence','author','ejnp','ejod','fifth','discourse')}}),('ejom',{'zb':{('first','author','ejoi','ejok','fifth','discourse'),('second','author','ejoj','ejol','fifth','discourse')},'eislo':{('Uname','ejop','paper','discourse'),('wname','ejoq','paper','discourse')},'ue':{('first','second','discourse')}}))
    for name,rows in tables:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert run(name,[],mm|{n:forbidden for n in ('ejnp','ejod','ejoi','ejoj','ejok','ejol','eismh','sjs','zkp','zkq')});count+=1
        assert not run(name,[],mm|{'jvmcpoint':lambda:'other'});count+=1
    assert not run('ejom',[],{'zb':lambda *xs:True,'eislo':lambda *xs:True,'ue':lambda *xs:True,'zks':lambda:'first'});count+=1
    for name,node,message,previous,previous_symbol in (('ejog','consequence','ejof','equations','zkh'),('ejoo','introduction','ejon','consequence','eisoy')):
        rows={'eir3':{(node,'author','paper',message,'discourse')},'ue':{(previous,node,'discourse')}};mm={n:relation(rs) for n,rs in rows.items()}
        count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert not run(name,[],{n:lambda *xs:True for n in rows}|{previous_symbol:lambda node=node:node});count+=1
    return dict(cases=count,same_theory_and_item_content_all_witness_slots=True,first_order_consequence_from_same_previous_equations=True,two_definition_methods_targets_names_and_order=True,quoted_derivatives_and_physics_not_executed_by_attribution=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u,w=inv['units'][134:136];assert (u['id'],w['id'])==('einstein-1905:u0135','einstein-1905:u0136')
    old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256']);first=old['segments'][0];assert u['text'][first['range'][1]:]==' Wir setzen:'
    table={m['id']:m for m in inv['math']};e=table['M0252'];root=ET.fromstring(e['mathml']);flat=re.sub(r'\s','',''.join(root.itertext()))
    assert flat=='U2=(dxdt)2+(dydt)2,w2=wξ2+wη2' and w['math_ids']==['M0252'];assert digest(e['mathml'].encode())==e['sha256']
    ns='{http://www.w3.org/1998/Math/MathML}';assert len(root.findall('.//'+ns+'mfrac'))==2
    segments=[]
    for unit,start,end,math in ((u,0,first['range'][1],[]),(u,first['range'][1]+1,len(u['text']),[]),(w,0,len(w['text']),[dict(id='M0252',sha256=e['sha256'],mathml_flat=flat)])):
        assert digest(unit['text'].encode())==unit['text_sha256'];text=unit['text'][start:end]
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],text=text,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text)),math=math))
    paths={INVENTORY,DOC,READING,*old['source_sha256']}
    return dict(version='einstein-velocity-magnitude-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['905'],segments=segments,observations=['原刊905頁のalso/nach unserer Theorie/nur、Wir setzenのコロン、二行の速さの二乗式を固定本文と照合した。Uは二つの時間微分、wはwξ/wηの二定数の二乗和であり、同じwを横成分と読まない。','第一近似の共通倍率の読みを保ち、同じ論説の理論構成への帰属と先行のK三式からの帰結を保持する。','U/wは非負の速さ、定速度の現在全期間における同じ二座標の微分と読む。二乗式だけが許す負の枝と明示的に区別する。','u0137のundとu0138の逆正接も同じ導入に続く。今回の二つの速さだけでu0135全体や角度を完成扱いしない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==356
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    legacy=parse(read('examples/v014/einstein-speed-magnitude.noema'));legacy_basis=json.loads(read('data/speed-magnitude-basis-v1.json'))
    for n in ('szn','szq'):
        assert next(d for d in new.document['declarations'] if d['name']==n)==next(d for d in legacy['declarations'] if d['name']==n)
        # The current corpus adds a namespace label without changing this meaning.
        assert new.entries[n]['meaning_ja'].removeprefix('[current の記号名] ')==legacy_basis['definitions'][n]
    for p,selection in zip(PRIORS,([352,353],[353])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries'][:-2]==json.loads(read('data/velocity-first-order-identifiers-v1.json'))['entries']
    doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert {'eisdj','eiscr','eisox','ejoc','ejnp','zc'}<=names('ejog')
    assert {'ejny','ejmu','ejmv','ejmx','eiyw','eismh','szn','szq','sjs','zb','eislo'}<=names('ejoo')
    assert not {'zka','shd','zke','syu','szr','szs','szt'}&names('ejoo')
    assert len([d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive'])==len(PRIMITIVES)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=354,prior_judgments_preserved=True,legacy_norm_and_derivative_bodies_and_meanings_unchanged=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('magnitude',magnitude_checks),('trajectory',trajectory_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_velocity_first_order','compose_origin_clock_question','compose_rod_methods','compose_speed_magnitude','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_point_motion_records','check_point_motion_transform','check_clock_site_time','check_rod_methods','check_coordinate_correspondence','check_moving_trip_geometry','check_material_relative_frame','check_translated_light_trial','check_transverse_segment','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'examples/v014/einstein-speed-magnitude.noema','data/speed-magnitude-basis-v1.json','scripts/compose_velocity_magnitude_claim.py','scripts/check_velocity_magnitude_claim.py','tests/test_velocity_magnitude_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDICES[0] if i==0 else INDICES[1]],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='first_order_consequence_and_current_speed_definitions_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0136の全単位意味判断','u0137–u0138の接続語と角度の導入、u0139前半の角の解釈','u0135全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
