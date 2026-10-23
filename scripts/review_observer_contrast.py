"""Review the length gloss and hypothetical contrast of observer responses."""
from functools import lru_cache
import json,re
from xml.etree import ElementTree as ET
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_observer_contrast import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

DOC='docs/observer-contrast-v1.md';SOURCE='data/einstein-observer-contrast-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
REPORT='reports/observer-contrast-v1.json';REVIEW='data/einstein-observer-contrast-review-v1.json'
PRIORS=('data/einstein-moving-trip-reading-u0036-review-v1.json','data/einstein-moving-trip-reading-u0280-review-v1.json')
DEPENDENCIES=('reports/moving-trip-reading-v1.json','reports/moving-trip-geometry-v1.json','reports/carried-clock-synchrony-v1.json','reports/rod-length-claims-v1.json')
REASONS=(
 '原刊897頁の二式直後のwobeiからerklären würdenまで、固定u0040全284文字・236本文文字とM0062のr_ABを照合した。長さの説明と二群の判断という二文を保持する。',
 '同じ棒の静止系測定長、共動観測者の中点条件に関する否定判断、静止観測者の局所時刻追従に関する肯定判断と宣言を結ぶ。非空の想定観測者範囲を保ち、判断と内容の真偽を分ける。',
 'r_AB=zavは同じ棒xiのeip6/eiqgへ結び、同じ二時計zaj/zakと二端xn/xo、三記録、共動する二人zay/zaz、静止系raを保つ。先行結果eitpと同じ想定範囲xyを理由と提示へ引き継ぐ。',
 'wobeiは二式の量への補足、würdenは想定範囲内の帰結、alsoは先行結果を理由とした説明、währendは二つの内容の対照として保持する。findenの判断とerklärenの発言を区別する。',
 '初期長や移動側の長さとの等値、同じ中点命題の肯定と否定の併存、動く時計の静止、現実の全人類の全知、実際に発言した事実、数式から心理過程が必然する法則を追加しない。',
 '代表位置の静止は同じ対象の完全な世界線と零速度の完全な世界線から構成する。判断はsdk/zba、発言はeisfd、現行の局所時刻追従はeiq4を用い、意味未説明の観測者名や数値のみで代用しない。',
 '原刊画像と固定原文・MathML、先行の時間・光往復・測定の証拠を保存する。全履歴の境界、同じ判断内容・肯否、量化範囲と引用の検査は全実数の証明や独立査読ではない。',
 '直前の二式と時間の著者注、直後の同時性への結論に照らして単位全体を通読した。理想化された同じ想定の下で異なる基準による判断を対照するという明示した読みで、全内容と論述上の役割を保持していると判断する。',
)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][39];assert u['id']=='einstein-1905:u0040' and len(u['text'])==284
    count=sum(not c.isspace() for c in re.sub(r'\[M\d+\]','',u['text']));assert count==236
    math=next(m for m in inv['math'] if m['id']=='M0062');sub=ET.fromstring(math['mathml']).find('.//{*}msub');assert sub is not None and [''.join(x.itertext()) for x in sub]==['r','AB']
    receipt='artifacts/einstein-moving-trip-v1/retrieval.json';paths={INVENTORY,DOC,'scripts/review_observer_contrast.py',receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-observer-contrast-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['897'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=count,math=[dict(id=math['id'],sha256=math['sha256'],reading='r_AB (A/B subscript)',binding='eismn designation; eit4 binds xi, eip6/eiqg and zav')])],observations=['r_ABの説明は静止系で測った動く棒の長さであり、ダッシュで測定系を補う。','共動観測者はnicht synchron ... finden、静止側はals synchron ... erklärenと異なる動詞を持つ。','würdenは先行の思考設定を引き継ぐ。alsoとwährendの理由・対照を保持する。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);segment=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,REPORT,*PRIORS,*DEPENDENCIES,'scripts/review_observer_contrast.py','tests/test_observer_contrast_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=segment['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=segment['unit_sha256'],text=segment['text'],range=segment['range'],math=[{k:m[k] for k in ('id','sha256')} for m in segment['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],interpretation=LIMITS,limits=['明示した解釈の下のアシスタントによる通読判断。独立査読や同義性の自動証明ではない。','u0041以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='rest_frame_length_and_observer_contrast_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0040':236},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
