"""Record an explicit whole-unit reading of the three optical-method claims."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-optical-problem-method.noema';CORE='examples/v014/optical-problem-method-core.noema'
BASIS='data/optical-problem-method-basis-v1.json';ANNOTATIONS='data/optical-problem-method-identifiers-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/optical-problem-method-v1.md'
READING='data/einstein-optical-problem-method-reading-v1.json';REPORT='reports/optical-problem-method-v1.json'
REVIEW='data/einstein-optical-problem-method-u0226-review-v1.json'

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));u=inv['units'][225];text=u['text'];reading=json.loads(read(READING));segment=reading['segments'][0]
    assert segment['unit']==u['id'] and segment['source']==text and segment['statements']==[406]
    paths={FULL,CORE,BASIS,ANNOTATIONS,INVENTORY,DOC,READING,REPORT,'scripts/review_optical_problem_method.py','tests/test_optical_problem_method_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (REPORT,READING):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=reading['clauses']
    contents=[
      'ここで用いた同じ方法を先行の反射後の二系比較の提示へ参照し、動く物体の光学の全問題について、その方法の正しい還元案と還元先の完全な解答列の存在による解決可能性を著者が述べる。解けることを問題分類の前提にせず、実行済み・既知・唯一・有限時間保証を追加しない。',
      '同じ方法の中心的で不可欠な操作として、同じ動く物体に作用される光の電場と磁場を、同じ物体に相対静止する座標系へ変換するという内容を著者へ帰属する。光・関係節・両場・物体の同一性・相対静止する系を保持し、単に二つの場の名前を列挙しただけにはしない。',
      'その同じ中心操作によって、動く物体の光学の各問題を静止物体の光学の問題の列へ正しく還元するという著者の帰結提示を、直前の説明へ結ぶ。Reiheを少なくとも二項の順序付き有限列と明示し、全項の主題・対象・新系と全解答列からの逆変換を含む再構成を保持する。',
    ]
    reasons=[
      '原刊915頁の段落末三文を画像で再読し、Nach der hier benutzten Methodeからzurückgeführt.までの全範囲を固定した。本文の句点、三文の順、両方の全称語alle/jedes、関係節、Dadurch、Reiheを確認した。数式要素はない。',
      '全問題の実際の質問族、正しい還元、完全解答列の存在、同じ光の両場の変換、動く物体とその相対静止系、方法の本質的役割、手段による還元を別々の合成へ結ぶ。場の問題は列内の下位問題であり、他の量や性質を求める全光学問題と同一視しない。',
      '第一文のhier benutzten Methodeは先行提示ekti/eisuuを参照する。第二文のwelchesは同じ光を、dem Körperは同じ作用する物体を指す。第三文のDadurchは同じ方法のekwq操作と直前のekww特徴付けへ結び、別の方法・問題・場・系へ対象を交換しない。',
      '三文の内容をuhで同じ著者へ帰属し、同じ論説と範囲、先行圧力近似表示との順序を保持する。第二文は方法を特徴付ける説明、第三文は同じ操作を手段とする一般的帰結の提示である。物理的な全称命題を真として実行しない。',
      '主題分類は仮定の現実成立や解決成功を要求しない。可能性は認められた案の正しい還元と解答存在、Reiheは二項以上の有限列、本質的は不可欠な中心操作と明示する。一様な変換で任意の加速・回転体に静止慣性系が存在すると補わず、適用できない問題を分類から除かない。過去の印刷式の不一致も保存する。',
      '全称・存在量化、列と各位置の質問合致、正しい再構成、両場の正逆変換、物体の運動と相対静止は既存定義で構成する。新一般関係7は主題・対象対応・実際の質問・手続き適格性・操作の役割・先行使用・手段による提示を担い、三文全体の内容を原始関係へ押し込めない。',
      '実際の両場の逆変換と全解答列、全還元先の同一対象対応、物理文脈と論述文脈の区別、33証人の各位置、非空の全問題範囲、三文の参照・提示を対照する。全列・全実数・全関数域の有限評価は拒否する。これらは構文・結合の証拠であり、全光学問題の物理的可解性や原文との同義性の自動証明ではない。',
      '先行の鏡の計算から一般的方法へ移る段落として三文を続けて読み直した。明示した主題範囲・解決可能性・複数の有限列・方法の中心操作という読みの下で、対象、関係節、量化、操作、可能性、照応、帰結、著者提示を欠落なく記述したと判断する。著者の一般的な物理主張が正しいと認定した判断ではない。',
    ]
    source=dict(inventory=INVENTORY,unit_sha256=u['text_sha256'],text=text,range=[0,len(text)],math=[])
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=u['id'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=source,selection=selection_binding(catalog,[406]),clauses=[c|dict(reason=r) for c,r in zip(clauses,contents)],interpretation=reading['interpretation_limits'],limits=['明示した読みの下でのアシスタント判断であり、独立査読又は同義性の自動証明ではない。','全問題の物理的可解性、任意の物体の静止系の存在、手続きの計算可能性をテストで証明したものではない。','第八節見出し、後続の第九節以降及び二作品全体は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[READING],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=segment['reviewed_prose_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='three_optical_method_sentences_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
