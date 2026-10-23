"""Record the complete third-section heading reading."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_transformation_heading import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS

DOC='docs/transformation-heading-v1.md';SOURCE='data/einstein-transformation-heading-source-reading-v1.json';INVENTORY='artifacts/written-units-v1/einstein-1905.json'
REPORT='reports/transformation-heading-v1.json';REVIEW='data/einstein-transformation-heading-review-v1.json'
PRIORS=('data/einstein-simultaneity-conclusion-review-v1.json',)
DEPENDENCIES=('reports/simultaneity-conclusion-v1.json','reports/kinematics-headings-v1.json','reports/first-principle-v1.json')
REASONS=(
 '原刊897頁の独立した太字見出しを固定u0042全155文字・136非空白文字と照合した。§3と本文全語句を保持し、直後のSeienで始まる段落は含めない。',
 '三座標と時刻の四組を同じ出来事へ結び、静止した比較基準側から、それに対し等速並進する側への対応を主題とする。変換の規則・条件・理論的な説明を扱うことを保持する。',
 '同じ出来事、各系の時刻規約、長さ・時間単位、第一系と第二系の向き、第一部の区分と直前の結論箇所zbkを接続した。節は固定u0042からu0108まで、次の見出しはu0109である。',
 '見出しを同じ区分の主題と構造の案内としてeihqへ結ぶ。表示番号3は階層深さ2と区別し、Theorieを特定公式の真理や導出済みの宣言へ替えない。',
 '空間又は時間の片方を落とさず、第一系の時刻を第二系へコピーしない。絶対静止、標準配置、速度上限、Lorentz公式、任意の実数四組の実現、逆変換や線形性を補わない。',
 '座標値の組の型、実際の割当てと一意性、局所時計表示への対応、等速並進は既存定義に接続する。新しい主題規約は表示系間の変換規則の研究一般を表し、見出し本文を未分解な名前として格納しない。',
 '固定原文、既取得の原刊画像、見出しと相対運動・時計の先行証拠、接続検査を保存する。有限例の通過は全実数や具体的変換理論の証明、意味同値の自動証明ではない。',
 '直前の同時性への結論と、直後の二系の具体設定を含む原刊の配置で見出し全体を再読した。静止基準側から等速並進する側への三座標・時刻の変換理論を後続節の主題として案内するという読みで、全内容と論述上の役割を保持したと判断する。',
)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][41]
    assert u['id']=='einstein-1905:u0042' and len(u['text'])==155
    assert u['text_sha256']=='1c95e4d74538ecaaf84e21df73afe8e1c3b640c17ae0f2998e843d98aad73633'
    count=sum(not c.isspace() for c in u['text']);assert count==136 and u['kind']=='heading'
    next_heading=next(v for v in inv['units'][42:] if v['kind']=='heading');assert next_heading['id']=='einstein-1905:u0109' and next_heading['text'].startswith('§ 4.')
    receipt='artifacts/einstein-moving-trip-v1/retrieval.json';paths={INVENTORY,DOC,'scripts/review_transformation_heading.py',receipt}
    for row in json.loads(read(receipt))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-transformation-heading-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['897'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],nonblank_characters=count,math=[])],division=dict(level=2,ordinal=3,parent='einstein-1905:u0006',scope_first=u['id'],scope_last='einstein-1905:u0108',next_boundary=next_heading['id']),observations=['§3は同時性の結論の後、Seienで始まる段落の前に独立した見出しとして置かれる。','Koordinaten- und Zeittransformationは空間と時間の両方を対象とし、von ... auf ...は静止基準側から相対運動する側への向きを示す。','太字と中央配置は見出しの識別根拠であり追加の物理命題ではない。'],semantic_completion=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);segment=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,SOURCE,REPORT,*PRIORS,*DEPENDENCIES,'scripts/review_transformation_heading.py','tests/test_transformation_heading_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=segment['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=segment['unit_sha256'],text=segment['text'],range=segment['range'],math=[]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],interpretation=LIMITS,limits=['明示した解釈の下のアシスタントによる通読判断。独立査読、変換公式の証明、同義性の自動証明ではない。','u0043以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

def build_report():
    rec=record();assert json.loads(read(REVIEW))==rec
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='transformation_heading_whole_unit_reviewed',document=FULL,source_units={'einstein-1905:u0042':136},whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=rec['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
