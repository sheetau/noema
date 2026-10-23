"""Pin the whole-unit reading of the initial frame setting and its naming."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.check_einstein_principles_paragraph import calls
from scripts.compose_rest_frame_introduction import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS

INVENTORY='artifacts/written-units-v1/einstein-1905.json';SOURCE='data/einstein-rest-frame-source-reading-v1.json'
DOC='docs/rest-frame-introduction-v1.md';REPORT='reports/rest-frame-introduction-v1.json';REVIEW='data/einstein-rest-frame-review-v1.json'
REASONS=(
 '固定u0008全266文字・236非空白文字を原刊892頁と照合し、第一文[0,95)84文字と第二文[96,266)152文字を確認した。文間空白以外を全て覆う。数式・著者脚注はなく、Präzi-sierungの行末分割を転記のPräzisierungへ対応させる。',
 'Newtonの力学方程式が成り立つ座標系を置く設定、同じ系を静止系と呼ぶ命名、後で導入する座標系との言語上の区別、観念の明確化という二目的を保持する。単に存在又は名前だけを記述して条件・目的を落とさない。',
 '設定・仮定内容・命名対象・両目的・後続本文の参照を同じraへ結ぶ。dies Koordinatensystemを別の系へ交換せず、予定された他系の群を同じ論説の命名箇所より後の範囲へ固定する。呼称eisebのruhende Systemという原文表記も保持する。',
 '第一文を議論の設定を置く指示、第二文を現在の命名と目的を述べる著者の宣言として分ける。Wirを論述を進める著者の声と読み、人数や読者の同意を補わない。同じ著者・論説・提示点と、第一節見出しから二文への順序を保持する。',
 '仮定の採用からNewton方程式の現実的な真理・実証・信念を導かず、名称から絶対静止・全物体の停止を導かない。言語上の区別と明確化を達成済みの事実へ替えず、予定された他系の現在の実在や全読者の完全理解も要求しない。',
 '既存の座標系vaとNewton適格性eisbd、仮定採用ug、談話参照の導入、対象個体への命名、行為と目標の目的関係、本文上の将来範囲、言語上の区別と観念の明確化を再読した。原語の綴りや未説明の文単位の記号で内容を代用していない。',
 '原刊照合、仮定の非事実性、同じ対象の接続、両目的と達成の非含意、発話の力、識別表記、既存判断の保持の検査を固定した。有限の対照例を物理的な実証、読者の心理状態の確認、同義性の自動証明へ替えない。',
 '設定を置く第一文から、その同じ系を二目的のために名付ける第二文までを続けて通読した。明示した解釈の下で内容・範囲・参照・提示の未処理項目はないと判断する。次の位置指定の段落と第一節全体の完成はこの判断の範囲外である。',
)

@lru_cache(None)
def review_record():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));unit=inv['units'][7];source=json.loads(read(SOURCE))
    assert unit['id']=='einstein-1905:u0008' and source['source_unit']==unit['id'] and source['unit_sha256']==unit['text_sha256'] and source['text']==unit['text']
    assert len(unit['text'])==266 and sum(not c.isspace() for c in unit['text'])==236 and not unit['math_ids']
    assert [r['range'] for r in source['sentence_ranges']]==[[0,95],[96,266]]
    assert sum(r['nonblank_characters'] for r in source['sentence_ranges'])==236
    for r in source['sentence_ranges']:assert r['text']==unit['text'][slice(*r['range'])]
    ds={d['name']:d for d in catalog.document['declarations']}
    assert ds['eihv']['body']['force']=='direct' and ds['eih4']['body']['force']=='assert'
    def get(parent,callee):
        cs=[c for c in calls(ds[parent]['body']) if c['symbol']==callee];assert len(cs)==1;return cs[0]
    def constant(name):return dict(kind='call',symbol=name,arguments=[])
    def quoted(name):return dict(kind='quote',body=constant(name))
    assert get('eiht','eifb')['arguments'][0]==constant('ra')
    assert get('eihu','eisd3')['arguments'][1]==constant('ra')
    assert get('eihu','ug')['arguments'][2]==quoted('eiht')
    assert get('eih2','eisd4')['arguments'][2:5]==[constant(n) for n in ('eiseb','ra','eirf')]
    assert get('eihy','eisd6')['arguments'][0:2]==[constant(n) for n in ('eiseb','ra')]
    assert get('eihz','eisea')['arguments'][0:2]==[constant(n) for n in ('eiseb','ra')]
    purposes=[c for c in calls(ds['eih3']['body']) if c['symbol']=='eisd5']
    assert len(purposes)==2 and all(c['arguments'][1]==quoted('eih2') for c in purposes)
    assert [c['arguments'][2] for c in purposes]==[quoted(n) for n in ('eihy','eihz')]
    for parent,first,last in (('eihw','eisd2','eisec'),('eih5','eisec','eised')):
        assert [a['symbol'] for a in get(parent,'ue')['arguments']]==[first,last,'ri']
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).find('ruhende System','de')['matches'][0]['symbol']=='eiseb'
    evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC])
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,SOURCE,REPORT,DOC,'scripts/review_rest_frame_introduction.py','tests/test_rest_frame_introduction_review.py','scripts/check_einstein_principles_paragraph.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        record=json.loads(read(p));validate_hashes(ROOT,record['source_sha256']);merge_pins(pins,record['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=unit['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,
        source=dict(inventory=INVENTORY,unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,266],math=[]),selection=selection_binding(catalog,[221,222]),source_order_statements=[221,222],interpretation=LIMITS,
        limits=['明示した読みで原文の意味と提示の役割を照合したアシスタントの判断。独立査読、全ての歴史的解釈、同義性の自動証明、物理的な系や法則の実証を主張しない。','後続の位置指定の段落と第一節以降の全単位記述は未完で、二作品全体の目標は継続する。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=evidence,source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(review_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    assert json.loads(read(REVIEW))==review_record()
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    verified=validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='rest_frame_introduction_holistically_reviewed_under_explicit_reading',document=FULL,source_unit='einstein-1905:u0008',source_order_statements=[221,222],source_nonblank_characters=verified['source_nonblank_characters'],whole_unit_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=review_record()['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
