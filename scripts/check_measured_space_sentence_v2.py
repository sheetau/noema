"""Verify the corrected naming location and supersede the first-sentence reading."""
from functools import lru_cache
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_measured_space_sentence import constants,relation,perturb,forbidden,DOMAIN,POINTS,notation_rows,CLAUSES
from scripts.compose_measured_space_sentence import LIMITS as FIRST_LIMITS
from scripts.compose_measured_space_sentence_v2 import ROOT,read,INDEX,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,LIMITS,build

DOC='docs/measured-space-sentence-v2.md';READING='data/einstein-measured-space-sentence-reading-v2.json'
OLD_READING='data/einstein-measured-space-sentence-reading-v1.json';OLD_REPORT='reports/measured-space-sentence-v1.json'
SOURCE='data/einstein-measured-space-source-reading-v1.json';PRIOR='data/einstein-parallel-choice-review-v1.json'

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);expr=dict(kind='call',symbol=name,arguments=[])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jmsv',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jmsv',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc

def run(name,m):
    doc=fixture(name);mm=constants()|m|{'jmsv':lambda:'discourse'}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def presentation_checks():
    rows=notation_rows();rows['eisd4']={('motionnode',)+row[1:] for row in rows['eisd4']}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiya',mm),m,rows)
    assert not run('eiya',m|{'eisd4':relation(notation_rows()['eisd4'])});count+=1
    assert run('eiya',m|{n:forbidden for n in ('eixu','eixq','zcy','eixt')});count+=1
    rows|={'eislz':{('node','author','eix3','section','discourse')},'ug':{('node','author','eix3','section','discourse')},'zao':{('motionnode','node','section','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiyb',mm),m,rows)
    assert run('eiyb',m|{n:forbidden for n in ('eixt','eix3','eiwn','eixs','eisnc','eism4')});count+=1
    rows={'eir3':{('node','author','paper','eiyc','discourse')},'ue':{('previousnode','node','discourse')}};m={n:relation(rs) for n,rs in rows.items()}
    count+=perturb(lambda mm:run('eiyd',mm),m,rows)
    assert run('eiyd',m|{n:forbidden for n in ('eisd4','eislz','ug','eixt','eix3','eiyb')});count+=1
    return dict(cases=count,previous_naming_location_required_current_renaming_rejected=True,thought_setting_and_nonexecuting_quotation_preserved=True)

@lru_cache(None)
def reading_record():
    old=json.loads(read(OLD_READING));validate_hashes(ROOT,old['source_sha256'])
    report=json.loads(read(OLD_REPORT));validate_hashes(ROOT,report['source_sha256'])
    new=deepcopy(old);catalog=load_catalog(ROOT,BASIS)
    new.update(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,selection=selection_binding(catalog,[INDEX]),supersedes=OLD_READING,decision='equivalent_under_stated_reading_for_measured_space_sentence_v2')
    replacements={'eix4':'eiya','eix5':'eiyb','eix6':'eiyc','eix7':'eiyd'}
    for clause in new['clauses']:clause['definitions']=[replacements.get(n,n) for n in clause['definitions']]
    new['clauses'][-1]['reason']+=' K/kの命名は先行zcgの対応を保持し、現在のzc2で新たに宣言したとはしない。'
    new['interpretation']=FIRST_LIMITS+LIMITS
    new['holistic_review']+=['K/kの命名行為eisd4の意味規約を再読し、原文の現在箇所は既出の名称の再使用であることを確認した。命名箇所を先行zcgへ戻し、現在箇所zc2では想定行為と座標規則を記述する。七範囲と文全体をこの修正後の選択で再確認し、明示した解釈の下で同じ第一文を記述できたと判断する。旧一文判断はこの記録により置き換え、176文字を重複加算しない。']
    paths=set(build())|set(catalog.source_sha256)|{DOC,SOURCE,OLD_READING,OLD_REPORT,PRIOR,'scripts/compose_measured_space_sentence_v2.py','scripts/check_measured_space_sentence_v2.py','tests/test_measured_space_sentence_v2.py'}
    new['source_sha256']={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};return new

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==271 and new.document['statements'][:INDEX]==old.document['statements'][:INDEX]
    assert new.document['statements'][INDEX]['body']['symbol']=='eiyd'
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[268,269])==prior['selection']
    oldreading=json.loads(read(OLD_READING));assert selection_binding(new,[INDEX])!=oldreading['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/measured-space-sentence-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert ds['eiyc']['body']['force']=='assert'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(READING))==reading_record()
    return dict(corrected_statement=INDEX,preserved_other_statements=270,new_definitions=4,new_primitives=0,prior_whole_unit_judgments_preserved=True,old_sentence_judgment_superseded_not_rebound=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(reading_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results=dict(presentation=presentation_checks(),structure=structure_checks());rec=reading_record();source=rec['source']
    paths=set(rec['source_sha256'])|{READING,'scripts/check_measured_space_sentence.py','scripts/compose_measured_space_sentence.py'}
    return dict(status='measured_space_sentence_with_prior_frame_names_reviewed',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},whole_sentence_semantically_verified=True,newly_reviewed_sentence_characters=176,supersedes=OLD_REPORT,semantic_equivalence_automatically_proved=False,remaining=['u0045第二文の時計配置点の時刻・§1同期手順・追加指示・表記','u0045全体の意味判断と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
