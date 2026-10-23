"""Check third-frame naming, the same prior intention, quotation and source binding."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_four_coordinate_claim import model as previous_model
from scripts.compose_third_frame_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,NAMES,RULES,build

DOC='docs/third-frame-claim-v1.md';SOURCE='data/einstein-third-frame-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-phi-determination-intent-u0092-review-v1.json'
SOURCE_PARENT='data/einstein-third-frame-geometry-source-reading-v1.json'
DEPENDENCIES=('reports/third-frame-geometry-v1.json','reports/phi-determination-intent-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zgt':'unknown','zgn':'intent','zgo':'intro','zgp':'result','zgi':'third','yn':'x','yo':'y','yp':'z','eisnr':'Kname','eisns':'xname','eisnt':'yname','eisnu':'zname','eisnv':'tname','zgl':'stage','zb6':'context'}
DOMAIN=tuple(dict.fromkeys((*[x for n,x in CONSTANTS.items() if n not in ('ri','zgl','zb6')],'place','moment','other')))
POINTS=('context','stage','discourse','other')

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,{'eixu','eiyl','ejba'});doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtfc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtfcpoint',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jtfcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def run(name,args,m):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jtfcpoint':lambda:'discourse'}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=150000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def rule_checks():
    cuts,m,*_=previous_model();c=cuts.make;r=cuts.read;count=0
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    for _,rule,role in RULES:
        rows={'eixu':{('place','third',CONSTANTS[role],Q(7),'context')}}
        model=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
        count+=perturb(lambda mm:run(rule,['place',c(Q(7)),'context'],mm),model,rows,norm)
    rows={'eiyl':{('moment','third',Q(7),'context')}}
    model=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda mm:run('ejbg',['moment',c(Q(7)),'context'],mm),model,rows,norm)
    return dict(cases=count,all_three_spatial_roles_and_third_frame_time_rule=True,auxiliary_xprime_not_substituted=True)


@lru_cache(None)
def purpose_checks():
    rows={'eisd3':{('intro','third','paper','discourse')},'ug':{('intro','author','ejbb','section','discourse')},'eisd4':{('intro','author','Kname','third','paper','discourse')},'zgm':{('intent','author','spc','stage','section','discourse')},'eisnq':{('author','ejbh','intent','section','discourse')},'ue':{('intent','intro','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()}
    count=perturb(lambda mm:run('ejbi',[],mm),m,rows)
    assert run('ejbi',[],m|{n:forbidden for n in ('ejbb','eja2','eja3','spc','zeq','srh')});count+=1
    assert not run('ejbi',[],m|{'zgo':lambda:'intent'});count+=1
    return dict(cases=count,actual_introduction_and_same_prior_function_intention_required=True,purpose_not_intention_creation_or_goal_achievement=True,quoted_geometry_and_target_function_not_executed=True)


@lru_cache(None)
def presentation_checks():
    rows={'eislo':{(CONSTANTS[sign],rule,'paper','discourse') for sign,rule in [(s,r) for s,r,_ in RULES]+[('eisnv','ejbg')]},'eisnw':{('result','author',CONSTANTS[sign],rule,'paper','discourse') for sign,rule,_ in RULES},'zc':{('result','author','ejbc','ejbk','section','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('ejbl',[],mm),m,rows)
    assert run('ejbl',[],m|{n:forbidden for n in ('ejbc','ejbk','ei7c','ejba','eixu','eiyl')});count+=1
    # Naming all three positions is necessary; a time naming act is not required.
    assert len(rows['eisnw'])==3 and all(row[2]!='tname' for row in rows['eisnw'])
    for name,node,previous,message in (('ejbn','intro','unknown','ejbm'),('ejbp','result','intro','ejbo')):
        rows={'eir3':{(node,'author','paper',message,'discourse')},'ue':{(previous,node,'discourse')}}
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{'ejbi':forbidden,'ejbl':forbidden});count+=1
    assert run('ejbk',[],{'ejba':lambda ctx:ctx=='context'});count+=1
    assert not run('ejbk',[],{'ejba':lambda ctx:ctx=='other'});count+=1
    unknowns(lambda mm:run('ejbk',[],mm),{'ejba':lambda ctx:True},('ejba',))
    return dict(cases=count,three_current_namings_and_four_rule_references=True,same_premise_and_full_chain_result_author_scope_and_order=True,quoted_physical_claims_not_executed=True)


@lru_cache(None)
def source_record():
    previous=json.loads(read(SOURCE_PARENT));validate_hashes(ROOT,previous['source_sha256'])
    pins=dict(previous['source_sha256']);pins.update({p:digest((ROOT/p).read_bytes()) for p in (SOURCE_PARENT,DOC)})
    return dict(version='einstein-third-frame-claim-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['901'],segments=deepcopy(previous['segments']),observations=['原刊901頁を再視認し、Wir führen zu diesem Zweckeから第三系の並進、三原点と零時刻、Wir nennenと二回適用、四連鎖等式の句点まで通読した。','zu diesem Zweckeは直前の同じφを今から決定する意図を受ける。noch ein drittesは既出二系への追加で、K′は別の系として導入する。','原刊はΞを印字し、kの縦軸を指す。−vでその軸上を原点が動き、全体の平行並進を設定する。','t=0で三原点を一致させ、t=x=y=z=0の同じ基準出来事でK′のt′=0を置く。光の放出に限定した記述ではない。','Wir nennenはx′,y′,z′の三位置座標の命名。t′は第二文と式で用いられる第三系の時刻。以前の補助x′とは役割が異なる。','式の順序はt′,x′,y′,z′。時間式のv/V²とξ、位置式のvτ、正負のφの積、二つのβ(−v)、横二式にβがないこと、全八等号を確認した。'],source_sha256=pins)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==312
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[309])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    ann=load_annotations(ROOT,BASIS,ANNOTATIONS);entries={e['symbol']:e for e in ann.annotations['entries']}
    assert all(entries[n]['forms'][0]['text']==printed for n,printed in NAMES)
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert all(ds[n]['body']['force']=='assert' for n in ('ejbm','ejbo'))
    assert {'ejba','eja2','eja3','eja4','eja5','eja6','eja7','srf','srg','srh','ei7c','eiyx','zgm','spc'}<=set(ds)
    assert not set(ds)&{'shd','smk','sri','srj','srk','sro','srs','zgj'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),designation_primitives=len(NAMES),reusable_relation_primitives=2,preserved_statements=310,prior_whole_unit_judgment_preserved=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('rules',rule_checks),('purpose',purpose_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_third_frame_claim.py','scripts/check_third_frame_claim.py','tests/test_third_frame_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_clock_site_time.py','scripts/check_four_coordinate_claim.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES if i==0 else [INDICES[1]]),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='purposive_third_frame_and_double_application_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0093–u0094の全文通読判断と登録','u0095以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
