"""Check current surface scope and the setting/equation/footnote attribution."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import model as body_model,DOMAIN as BODY_DOMAIN,refused,relations
from scripts.compose_sphere_setting import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,GROUPS,build

DOC='docs/sphere-setting-v1.md';SOURCE='data/einstein-sphere-setting-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-physical-meaning-heading-review-v1.json'
DEPENDENCIES=('reports/solid-sphere-geometry-v1.json','reports/physical-meaning-heading-v1.json','reports/final-transform-claim-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','zhw':'body','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zhy':'setting','zht':'heading','eisn6':'equation','eisn7':'note','eisoa':'anchor','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*BODY_DOMAIN,*CONSTANTS.values())))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'ejfd':{'eiyx','ejfa','ssz'},'ejfe':{'eje5'},'ejff':{'ejfc'},'ejfg':{'ejfe'},'ejfh':{'ejfd'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'exists'},only_sort=RS))==3
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jsst'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jsstpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jsstpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jsstpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=('context','discourse','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def surface_checks():
    cuts,m=numbers();c=cuts.make;domain=('a','b');pairs=tuple(product(domain,repeat=2));count=0
    # Keep the four distinct coordinate roles in the separate native ssz
    # check below. The two-individual scope test uses an explicit boundary.
    values={'a':{'a':Q(1),'b':Q(0)},'b':{'a':Q(0),'b':Q(0)}}
    base=m|{'ssz':lambda rec,radius:rec=='a' and cuts.read(radius)==1,'zc7':lambda:'b','rb':lambda:'a','eisls':lambda *xs:c(Q(-1)),'eislt':lambda *xs:c(Q(1)),'zc6':lambda rec,role:c(values[rec][role])}
    for selectedmask,surfacemask in product(range(16),repeat=2):
        selected={p for i,p in enumerate(pairs) if selectedmask>>i&1};surface={p for i,p in enumerate(pairs) if surfacemask>>i&1}
        model=base|{'eiyx':lambda e,r,f,s:(f,s)==('a','context') and (e,r) in selected,'ejfa':lambda b,e,r,f,s:(b,f,s)==('b','a','context') and (e,r) in surface}
        expected=bool(selected&surface) and all(((e,r) in surface)==(r=='a') for e,r in selected)
        assert run('ejfd',['b','a','context',c(Q(1))],model,domain=domain)==expected;count+=1
    selected={('a','a'),('b','b')};surface={('a','a')}
    model=base|{'eiyx':lambda e,r,f,s:(f,s)==('a','context') and (e,r) in selected,'ejfa':lambda b,e,r,f,s:(b,f,s)==('b','a','context') and (e,r) in surface}
    check=lambda mm:run('ejfd',['b','a','context',c(Q(1))],mm,domain=domain)
    assert check(model);count+=1
    for radius in (-1,0,2):assert not run('ejfd',['b','a','context',c(Q(radius))],model,domain=domain);count+=1
    assert not check(model|{'eisls':lambda *xs:c(Q(1))});count+=1
    unknowns(check,model,('eiyx','ejfa','ssz','zc6','eisls','eislt','bg','ba'))
    # Test the native numerical surface body with three independent axes.
    cuts,m=numbers();c=cuts.make;values={'x':Q(0),'y':Q(0),'z':Q(0),'time':Q(1)}
    m|={'zc5':lambda rec:rec=='record','zc6':lambda rec,role:c(values[role]) if rec=='record' and role in values else forbidden()}
    for axis in ('x','y','z'):
        for coord in (-2,-1,0,1,2):
            values.update(x=Q(0),y=Q(0),z=Q(0));values[axis]=Q(coord)
            assert run('ssz',['record',c(Q(1))],m)==(abs(coord)==1);count+=1
    return dict(cases=count,full_current_domain_not_preselected_surface=True,both_directions_and_nonempty_surface_required=True,each_native_coordinate_and_radius_checked=True,two_individual_event_record_quantifiers_native=True)

@lru_cache(None)
def content_checks():
    cuts,m,pos,members,fs,pop,fields,norm=body_model();c=cuts.make;count=0
    center=[c(Q(n)) for n in (3,-1,2)];radius=c(Q(4));rows={'eje5':{norm(fields+center+[radius])}}
    model=relations(m,rows,norm);args=['body','k','context',radius,*center]
    count+=perturb(lambda mm:run('ejfe',args,mm,'instance'),model,rows,norm)
    refused(lambda:run('ejfe',args[:4],model))
    for i in range(3):
        bad=args[:];bad[4+i]=c(Q(0));assert not run('ejfe',bad,model,'instance');count+=1
    for name,bound,row in (('ejff','ejfc',('body',Q(4),'context')),('ejfg','ejfe',('body','k','context',Q(4))),('ejfh','ejfd',('body','k','context',Q(4)))):
        rows={bound:{row}};model=relations(m,rows,norm)|{'zhx':lambda:radius}
        count+=perturb(lambda mm:run(name,[],mm),model,rows,norm)
    return dict(cases=count,same_body_radius_context_and_rest_frame=True,rest_shape_allows_nonzero_center=True,unbounded_center_witness_refused=True)

@lru_cache(None)
def presentation_checks():
    examples=[('ejfi',{'ug':{('setting','author','ejff','section','discourse')}}),('ejfj',{'uh':{('equation','author','ejfh','section','discourse')}}),('ejfk',{'eisme':{('note','author','ejff','ejfg','paper','discourse')}})]
    for _,msg,claim,node,previous in GROUPS:examples.append((claim,{'eir3':{(CONSTANTS[node],'author','paper',msg,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}))
    examples.append(('ejfq',{'eir3':{('note','author','paper','ejfn','discourse')},'eisfo':{('anchor','note','paper',Q(1),'discourse')},'eisa5':{('note','author','ejff','ejfg','discourse')}}))
    count=0
    for name,rows in examples:
        m={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run(name,[],mm)
        count+=perturb(check,m,rows)
        assert check(m|{n:forbidden for n in ('ejff','ejfg','ejfh','ejfc','ejfd','ejfe')});count+=1
    for name,patch in (('ejfo',{'zhy':lambda:'heading'}),('ejfp',{'eisn6':lambda:'setting'}),('ejfq',{'eisoa':lambda:'note'})):
        rows=next(rs for n,rs in examples if n==name)
        assert not run(name,[],{n:lambda *xs:True for n in rows}|patch);count+=1
    return dict(cases=count,considered_setting_not_actual_manufacture=True,surface_equation_and_rest_gloss_distinct=True,source_footnote_one_attached_to_same_setting=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    readings=dict(zip(('M0191','M0192','M0193','M0194','M0195','M0196'),('R','k','k','K','v','ξ²+η²+ζ²=R²')))
    for n,flat in zip(readings,('R','k','k','K','v','ξ2+η2+ζ2=R2')):assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==flat
    ns={'m':'http://www.w3.org/1998/Math/MathML'};eq=ET.fromstring(math['M0196']['mathml']);assert len(eq.findall('.//m:msup',ns))==4
    for number in (110,111,281):
        u=inv['units'][number-1];assert u['id']==f'einstein-1905:u{number:04d}'
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n],mathml_flat=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']]))
    retrieval='artifacts/einstein-sphere-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']})
    paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-sphere-setting-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['903'],segments=segments,observations=['原刊903頁のWir betrachtenから球面式までと、頁下部の著者注1)を同じ画像で再読した。Kugel直後の標識、同じR、二度のk、比較側K、v、式の三つのギリシャ座標と四つの二乗を確認した。','この一つの剛な球は内部を含む理想的な閉球連続体として読む。内部充填は明示したモデル選択であり、球形という語から全ての球形物体の材質・空洞を決めるものではない。','u0281のDas heißtは同じ本文の球を静止時の形状で明確化する著者脚注。原刊番号1とHTML参照A0016/cite_note-3、掲載頁903とinventory末尾のpage_at_end=921を区別する。','u0111はξ²+η²+ζ²=R²の式と句点。直後のK座標x,y,zでt=0の式は後続単位として分ける。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-3]==old.document['statements'] and len(new.document['statements'])==330
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[326])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'ejfc','eje4','eje3','eje7','eiyx','ssz','eisme','eisfo'}<=names
    assert not names&{'shd','stk','stl','zhu','zhv','eipc','eipe','stf'}
    assert all(next(d for d in doc['declarations'] if d['name']==n)['body']['force']=='assert' for n in ('ejfl','ejfm','ejfn'))
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=327,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('surface',surface_checks),('content',content_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_sphere_setting.py','scripts/check_sphere_setting.py','tests/test_sphere_setting.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py','scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py','scripts/check_rod_methods.py','scripts/compose_limits.py','scripts/compose_rod_methods.py','scripts/compose_solid_sphere_geometry.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py'}
    selections=([327,328],[328],[329]);alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=indices,definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s,indices in zip(source_record()['segments'],selections)])
    return dict(status='same_rest_sphere_surface_equation_and_author_note_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0110–u0111・u0281の全文判断と登録','u0112以降のKの時刻零断面'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
