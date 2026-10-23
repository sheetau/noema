"""Review all three sentences of the initial two-frame setting."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_frame_instruments import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

DOC='docs/frame-instruments-v1.md';SOURCE='data/einstein-frame-instruments-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
REPORT='reports/frame-instruments-v1.json';REVIEW='data/einstein-frame-instruments-review-v1.json'
PRIORS=('data/einstein-transformation-heading-review-v1.json',)
DEPENDENCIES=('reports/material-axes-v1.json','reports/second-local-clock-v1.json','reports/rod-methods-v1.json','reports/observer-contrast-v1.json')
REASONS=(
 '原刊897頁のSeien imからeinander genau gleichまでを固定u0043全441文字・361本文文字と照合した。M0063/M0064/M0065は大文字X/Y/Zであり、三文全体を対象とする。',
 '二系の三物質線・原点・直交・初期静止、対応X支持直線の一致とY/Z平行、各系の剛な物差しと非空の全時計、その構成・尺度仕様の厳密な一致を接続する。',
 '既出の静止基準raと後で動かす第二系zbmを同じ初期設定zb4へ結ぶ。各系の全軸・全時計、二物差し、共通尺度、原点・方向標識・全物質点の対応を維持する。',
 'Seien、mögen、sei、es seienを一つの設定採用の指示として保持する。d. h.は同じ二系の構成の説明的な言い直し、引用されたruhendenは既出基準の呼称への照応として扱う。',
 '絶対静止、二原点・二X物体の同一性、正方向又は右手性、具体的な時計数、すでに同期済み、同じ表示値、後続の運動付与・全系の長さ不変を追加しない。時計内部の運動を止めない。',
 '物質軸は全成員の静止・剛性と座標から構成し、物差しは全履歴と目盛尺度、時計は校正と代表配置の静止へ結ぶ。仕様比較は非空の完全な全特徴と全構成記述の両方向一致であり、単なる名前や近似で代用しない。',
 '原文と画像、先行の物質軸・時計構成・履歴の証拠、今回の全範囲と引用の検査を保存する。全仕様や全実数履歴の実証、原文との同義性の自動証明とは区別する。',
 '第三節見出しと次の運動付与の段落に照らして三文全体を再読した。同じ二系と同等な計器を初期静止配置として置く指示という明示した読みで、全条件と説明・照応・提示の役割を保持したと判断する。',
)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][42]
    assert u['id']=='einstein-1905:u0043' and len(u['text'])==441
    assert u['text_sha256']=='dc4d3477894bd39f1690f063aa87594a28c16a5076843ab57123bbdf9ad7f7ce'
    count=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']));assert count==361
    math={m['id']:m for m in inv['math'] if m['id'] in u['math_ids']};forms=dict(zip(('M0063','M0064','M0065'),('X','Y','Z')))
    for n,s in forms.items():assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==s
    receipt='artifacts/einstein-moving-trip-v1/retrieval.json';paths={INVENTORY,DOC,'scripts/review_frame_instruments.py',receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-frame-instruments-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['897'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=count,math=[dict(id=n,sha256=math[n]['sha256'],reading=s,binding=role) for (n,s),role in zip(forms.items(),('yn','yo','yp'))])],observations=['引用符付きruhendenは静止基準の呼称を保つ。d. h.は同じ二系の三物質線による説明である。','X軸のzusammenfallenとY/Z軸のbezüglich parallelを区別する。','各系にein starrer Maßstabとeine Anzahl Uhrenを与え、beide Maßstäbeとalle Uhren beider Systemeの全範囲にgenau gleichを要求する。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);segment=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,REPORT,*PRIORS,*DEPENDENCIES,'scripts/review_frame_instruments.py','tests/test_frame_instruments_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=segment['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=segment['unit_sha256'],text=segment['text'],range=segment['range'],math=[{k:m[k] for k in ('id','sha256')} for m in segment['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],interpretation=LIMITS,limits=['明示した解釈の下のアシスタントによる通読判断。独立査読、理想計器の実在や物理的真理の証明、同義性の自動証明ではない。','u0044以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='initial_frame_and_instrument_setting_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0043':361},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
