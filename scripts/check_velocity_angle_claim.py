"""Check the shared definition introduction, angle interpretation and replacement."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.compose_velocity_angle_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build

DOC='docs/velocity-angle-claim-v1.md';SOURCE='data/einstein-velocity-angle-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
READINGS=('data/einstein-velocity-magnitude-source-reading-v1.json','data/einstein-velocity-angle-source-reading-v1.json')
PRIORS=tuple(f'data/einstein-point-motion-u{n:04d}-review-v1.json' for n in (133,134))+('data/einstein-velocity-magnitude-u0136-review-v1.json',)
DEPENDENCIES=('reports/velocity-angle-measure-v1.json','reports/velocity-magnitude-claim-v1.json','reports/velocity-first-order-v1.json')
CONSTANTS={'zkb':'point','rd':'author','eirf':'paper','ri':'discourse','eisoq':'fifth','eisoy':'consequence','eisoz':'speeds','eiso6':'introduction','zkr':'Ueq','zks':'weq','zku':'angleeq','zkv':'meaning','eiso2':'Uname','eiso3':'wname','eiso5':'aname'}
DOMAIN=tuple(CONSTANTS.values())+('other',);POINTS=('context','discourse','other')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|({'ejow'} if name=='ejoy' else set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvac'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jvacpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jvacpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots


def run(name,args,m):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jvacpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def reference_checks():
    cuts,m=numbers();c=lambda x:cuts.make(Q(x));norm=norm_factory(cuts,());count=0
    for angle in (-4,-1,0,1,4):
        mm=m|{'eiso4':lambda:c(angle)}
        assert run('ejox',[c(angle),'context'],mm);count+=1
        assert not run('ejox',[c(angle+1),'context'],mm);count+=1
        rows={'ejow':{(Q(angle),'context')}};mm|={'ejow':lambda *xs:norm(xs) in rows['ejow']}
        args=['point',c(angle),'context'];count+=perturb(lambda mm:run('ejoy',args,mm),mm,rows,norm)
        for bad in (['other',c(angle),'context'],['point',c(angle+1),'context'],['point',c(angle),'other']):
            assert not run('ejoy',bad,mm);count+=1
        assert not run('ejoy',args,mm|{'eiso4':lambda:c(angle+1)});count+=1
        unknowns(lambda mm:run('ejoy',args,mm),mm,('eiso4','ba','sca','ejow'))
    return dict(cases=count,distinct_real_measure_and_notation_same_point=True,same_candidate_value_and_context_to_angle_rule=True,unknowns_not_defaulted=True)


def introduction_rows():
    return {'zb':{('Ueq','author','ejoi','ejok','fifth','discourse'),('weq','author','ejoj','ejol','fifth','discourse'),('angleeq','author','ejow','ejox','fifth','discourse')},'eislo':{('Uname','ejop','paper','discourse'),('wname','ejoq','paper','discourse'),('aname','ejoy','paper','discourse')},'ue':{('Ueq','weq','discourse'),('weq','angleeq','discourse')}}


@lru_cache(None)
def presentation_checks():
    count=0;full=introduction_rows()
    angle={'zb':{('angleeq','author','ejow','ejox','fifth','discourse')},'eislo':{('aname','ejoy','paper','discourse')}}
    meaning={'eiso7':{('meaning','author','ejox','ejov','fifth','discourse')}}
    for name,rows in (('ejoz',angle),('ejo2',full),('ejo5',meaning)):
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert run(name,[],mm|{n:forbidden for n in ('ejoi','ejoj','ejow','ejov','ejox','ejoy','eiso4','zkt','eismh','sede','sedi')});count+=1
        assert not run(name,[],mm|{'jvacpoint':lambda:'other'});count+=1
    # One or two definitions cannot satisfy the composite, nor can reversed order.
    for row in full['zb']:
        mm={n:relation(rs) for n,rs in full.items()};mm['zb']=relation({row});assert not run('ejo2',[],mm);count+=1
    mm={n:relation(rs) for n,rs in full.items()};mm['ue']=relation({('Ueq','weq','discourse'),('angleeq','weq','discourse')})
    assert not run('ejo2',[],mm);count+=1
    assert not run('ejo2',[],{n:lambda *xs:True for n in full}|{'zku':lambda:'weq'});count+=1
    return dict(cases=count,all_three_definitions_shared_author_scope_and_context=True,und_conjunction_not_choice=True,all_method_target_notation_and_order_slots=True,quantity_to_geometric_role_not_new_naming=True,quoted_integrals_and_physics_not_executed=True)


@lru_cache(None)
def attribution_checks():
    count=0
    groups=(('ejo4',{'eir3':{('introduction','author','paper','ejo3','discourse')},'ue':{('consequence','introduction','discourse'),('speeds','angleeq','discourse')}}),('ejo7',{'eir3':{('meaning','author','paper','ejo6','discourse')},'ue':{('angleeq','meaning','discourse')}}))
    for name,rows in groups:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        assert run(name,[],mm|{'ejo2':forbidden,'ejo5':forbidden,'eiso7':forbidden,'zb':forbidden});count+=1
    for name,patch,relations in (('ejo4',{'eiso6':lambda:'consequence'},('eir3','ue')),('ejo4',{'zku':lambda:'speeds'},('eir3','ue')),('ejo7',{'zkv':lambda:'angleeq'},('eir3','ue'))):
        assert not run(name,[],{n:lambda *xs:True for n in relations}|patch);count+=1
    return dict(cases=count,same_author_document_message_and_discourse=True,definition_then_interpretation_order_and_distinct_nodes=True,no_evaluation_of_attributed_content=True)


@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][134];assert u['id']=='einstein-1905:u0135'
    assert u['text']=='Das Gesetz vom Parallelogramm der Geschwindigkeiten gilt also nach unserer Theorie nur in erster Annäherung. Wir setzen:'
    records=[json.loads(read(p)) for p in READINGS]
    for r in records:validate_hashes(ROOT,r['source_sha256'])
    first=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s','',u['text'])),math=[])
    segments=[first,*records[1]['segments']]
    assert [s['unit'] for s in segments]==[f'einstein-1905:u{n:04d}' for n in (135,137,138,139)]
    for s in segments:
        unit=next(u for u in inv['units'] if u['id']==s['unit']);assert unit['text'][slice(*s['range'])]==s['text'] and digest(unit['text'].encode())==s['unit_sha256']
    paths={INVENTORY,DOC,*READINGS,*(p for r in records for p in r['source_sha256'])}
    return dict(version='einstein-velocity-angle-claim-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['905','906'],segments=segments,observations=['原刊905頁の第一近似の帰結、Wir setzenのコロン、U/wの二式、und、αの逆正接とセミコロン、906頁の角と見る説明までを画像で再読した。','三量を一続きの定義導入とし、直後のdannは同じαを受ける説明の進行と読む。αの向き・測度・商の定義域は前段の明示した読みを保持する。','旧文131/132の部分的な読みは現行稿で置き換える。元と意味が一致したことにはせず、旧本文・旧証拠を保存する。','u0139後半の計算への移行とM0257は未接続のため、u0139全体を意味確認済みにしない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==len(old.document['statements'])==356
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==list(INDICES)
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([352,353],[353],[355])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries'][:-1]==json.loads(read('data/velocity-angle-measure-identifiers-v1.json'))['entries']
    doc=core();names={d['name'] for d in doc['declarations']}
    assert {'ejom','ejoi','ejoj','ejow','ejov','sede','sedi','s2g','eislo','zb','eiso7'}<=names
    assert not {'s2k','s2m','s2h','zka','shd','zke','syu'}&names
    active=extract_document(new.document,roots=[],statement_indices=list(range(356))).document
    assert not {'s2k','s2m'}&{d['name'] for d in active['declarations']}
    assert len([d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive'])==len(PRIMITIVES)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),replaced_partial_statements=list(INDICES),other_statements_preserved=354,prior_judgments_preserved=True,no_active_assertion_depends_on_old_partial_angles=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('reference',reference_checks),('presentation',presentation_checks),('attribution',attribution_checks),('structure',structure_checks)]}
    helpers=('compose_velocity_angle_measure','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_clock_site_time','check_moving_trip_geometry','check_material_relative_frame','check_coordinate_correspondence','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_velocity_angle_claim.py','scripts/check_velocity_angle_claim.py','tests/test_velocity_angle_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    selections=([131,354,355],[131],[131,132],[132])
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=selection,definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s,selection in zip(source_record()['segments'],selections)])
    return dict(status='combined_speed_angle_definition_and_geometric_reading_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0135・u0137・u0138の全単位意味判断','u0139後半の簡単な計算への移行とM0257'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
