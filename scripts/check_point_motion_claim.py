"""Check motion-task, prior-section reference and rewrite attribution bindings."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_clock_site_time import relation,perturb,forbidden
from scripts.compose_point_motion_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build

DOC='docs/point-motion-claim-v1.md';SOURCE='data/einstein-point-motion-claim-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/einstein-point-motion-transform-source-reading-v1.json'
PRIORS=tuple(f'data/einstein-velocity-opening-u{n:04d}-review-v1.json' for n in range(129,133))
REFERENCES=('data/einstein-transformation-heading-review-v1.json','data/einstein-final-transform-u0106-review-v1.json')
DEPENDENCIES=('reports/point-motion-transform-v1.json','reports/point-motion-records-v1.json','reports/final-transform-claim-v1.json','reports/transformation-heading-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','ri':'discourse','eisoq':'fifth','eisms':'third','eisow':'question','zkg':'setting','zkh':'rewrite','eisne':'xname','eisnf':'yname','eisng':'zname','eism5':'tname'}
DOMAIN=tuple((*CONSTANTS.values(),'other'));POINTS=('discourse','context','other')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);assert not d['parameters']
    expr=dict(kind='call',symbol=name,arguments=[])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpmcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpmcpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc


def run(name,m):
    doc=fixture(name);mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jpmcpoint':lambda:'discourse'}|m
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=200000,memoize_definitions=True,memoize_expressions=True)[0]['value']


@lru_cache(None)
def presentation_checks():
    count=0
    tables=(('ejnq',{'eisou':{('question','author','ejnn','fifth','discourse')}}),('ejnt',{'zd3':{('rewrite','author','ejno','ejmy','ejnp','fifth','discourse')},'eisov':{('rewrite','author','third','ejeh','paper','discourse')},'eislo':{(label,rule,'paper','discourse') for label,rule in (('xname','eixv'),('yname','eixw'),('zname','eixx'),('tname','eiwt'))}}))
    for name,rows in tables:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,mm),mm,rows)
        # All quoted semantics remain unevaluated, including the unbounded question.
        assert run(name,mm|{n:forbidden for n in ('ejnn','ejno','ejmy','ejnp','ejeh','se','eismh','tc','zb7')});count+=1
        assert not run(name,mm|{'jpmcpoint':lambda:'other'});count+=1
    return dict(cases=count,question_task_and_rewrite_are_distinct_presentations=True,same_section_three_content_and_all_four_quantity_rules_bound=True,quoted_unbounded_question_and_physics_not_executed=True)


@lru_cache(None)
def attribution_checks():
    count=0
    for name,node,message,previous,previous_symbol in (('ejns','question','ejnr','setting','zkg'),('ejnv','rewrite','ejnu','question','eisow')):
        rows={'eir3':{(node,'author','paper',message,'discourse')},'ue':{(previous,node,'discourse')}};mm={n:relation(rs) for n,rs in rows.items()}
        count+=perturb(lambda mm:run(name,mm),mm,rows)
        assert not run(name,{n:lambda *xs:True for n in rows}|{previous_symbol:lambda node=node:node});count+=1
    return dict(cases=count,same_author_document_messages_and_two_sentence_order=True,task_setting_and_rewrite_nodes_not_collapsed=True)


@lru_cache(None)
def source_record():
    old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256']);rec=deepcopy(old)
    rec.update(version='einstein-point-motion-claim-source-reading-v1',observations=[old['observations'][0],'Gesucht istを同じ点のK運動を求める課題として提示する。Führt man ... ein, so erhält manは同じ前提・元の運動式・結果の三式による書換えの提示として読み、第三節で展開した最終変換への参照とKの四量の役割を保持する。第一文と第二文、コロンの後の三式を同じ文脈で通読する。',old['observations'][2]],source_sha256=old['source_sha256']|{p:digest((ROOT/p).read_bytes()) for p in (READING,DOC)})
    return rec


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==354
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for i,p in enumerate(PRIORS):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[350 if i==0 else 351])==prior['selection']
    for p in REFERENCES:
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);indices=[s['index'] for s in prior['selection']['statements']];assert selection_binding(new,indices)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/point-motion-transform-identifiers-v1.json'))['entries']
    doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert {'ejnn','ejnm','ejmu','eisou'}<=names('ejnq') and not {'ejnh','syt','sys'}&names('ejnq')
    assert {'ejno','ejmy','ejnp','ejng','ejnj','syt','ssn','ejeh','zd3','eisov','eislo'}<=names('ejnt')
    assert not {'zka','syu','syx','shd','zke'}&names('ejnt')
    assert len([d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive'])==3
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=352,prior_judgments_and_section_three_reference_contents_preserved=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('presentation',presentation_checks),('attribution',attribution_checks),('structure',structure_checks)]}
    helpers=('compose_point_motion_transform','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_clock_site_time','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*REFERENCES,*DEPENDENCIES,'scripts/compose_point_motion_claim.py','scripts/check_point_motion_claim.py','tests/test_point_motion_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES) if i==0 else [INDICES[1]],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='same_point_motion_task_and_section_three_substitution_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0133–u0134の全単位判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
