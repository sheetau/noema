"""Whole-unit reading of the literal infinity claim and its parenthesis."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_doppler_infinity import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_doppler_infinity import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/doppler-infinity-v1.json'
REVIEW='data/einstein-doppler-infinity-u0192-review-v1.json'

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_doppler_infinity.py','tests/test_doppler_infinity_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    s=source_record()['segments'][0];text=s['text'];a=text.index('—');b=text.index('—',a+1)+1
    clauses=[
     dict(range=[0,a],text=text[:a],statements=[374],definitions=['ekfr','ekfv','uh','zdg','zc'],reason='Man sieht, daßを、同じ内容を認められる帰結として提示し、先行式からの帰結とする著者の態度へ結ぶ。実際の読者の心理や導出成功を要求しない。'),
     dict(range=[a,b],text=text[a:b],statements=[374],definitions=['ekfs','ekft','ekfu','ekfw','eisah','eisai','eisnp','eisa5'],reason='通常理解とその閉じた内容を存在量化し、その同じ内容と主節の境界内容を、同じ波・相対速度・周期数の共通観点で対照する。対照を主節への挿入として保持し、原文にない古典式や厳密な論理否定を補わない。'),
     dict(range=[b,len(text)],text=text[b:],statements=[374],definitions=['ekff','ekfg','ekfh','ekfi','ekfj','ekfk','ekfl','ekfm','ekfn','ekfo','ekfp','ekfq','ekfr','ekfy'],reason='v=−∞,ν=∞の印字を保持し、入力speedが負に非有界な同じ関係で放射frequencyが任意の有限上限を超えるという内容へ合成する。ν′を背景に保つ採用読解を明示し、空の定義域の発散認定と無限実数の導入を避ける。同じ著者・論説へ帰属し直前の表示に続ける。'),
    ]
    assert all(n in catalog.entries for clause in clauses for n in clause['definitions'])
    reasons=[
     '固定在庫u0192全文84文字とM0336/M0337を保存済み原刊912頁へ照合した。v=−∞と無印ν=∞の印字を保持し、理論に都合のよい記号へ変更していない。版・本文・MathML・原刊画像をハッシュで固定する。',
     '負方向の非有界な入力域、上限ごとの十分小さい入力、全ての出力への上限超過、同じ関係・速度・周期数、認められる帰結としての提示、通常理解との対照、挿入の作用範囲を合成する。無限大を一つの有限実数にせず、空の関係による空虚な発散を排除する。',
     'vは先行の相対速度speed、νは放射frequency、ν′は受信newfrequencyと同定する。直前の同じφ=0のekey/ekezを関係の点に使い、同じ源・波・系・観測者・単位とVを背景に保つ。43補助役割は各点で存在量化し、条件と等式へ同じ証人を渡す。',
     'uhとzdgで同じekfrの主張と認められる帰結としての提示、zcで先行eke3からの帰結を記述する。eisah/eisai/eisnpで通常理解と同じ内容の対照、eisa5で主節への挿入、eir3とueで著者・論説・本文順序を保つ。引用内容の物理的真理を談話評価で実行しない。',
     '受信ν′を背景にした関係的境界読解を明示し、歴史的意図の一意な確定とはしない。通常理解の具体式、全員一致、現代の理解、厳密な否定は追加しない。先行域0<v<Vではcutoff=0の必要条件が失敗することを隠さず、適用域外の平方根、超光速への拡張、v=−Vやν′への訂正は加えない。',
     '新一般基本関係を導入せず、既存の実数の順序・量化・関数と、引用・主張・帰結・通常理解・対照・挿入の規約を再使用した。∞を未説明の対象名とせずekff–ekfmへ分解し、追加の二参照は本文箇所だけを指す。',
     '実数の局所点、厳密な大小、二値の関係表での量化順序と空虚性、43存在位置・11全称位置、全60設定引数、入力と出力の向き、通常理解・主張・挿入の各引数を対照検査する。全実数及び全記述域を有限列挙へ替えず、その評価を拒否する。これらは発散の真理や原文との同義性を自動証明しない。',
     '直前のφ=0の式から一文全体を再読し、Man sieht、ダッシュ内の通常理解との対照、fürに続く二つの印字、主節への挿入を確認した。明示した関係的境界読解の下で全文の内容と提示を記述したと判断する。印刷された主張が先行域と整合しないことは、翻訳の未処理箇所や成立済みの定理へ置き換えない。',
    ]
    assert len(reasons)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=text,range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,s['statements']),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる意味判断であり、独立査読や意味同義性の自動証明ではない。','印刷された主張を正しい物理法則とは認定せず、誤植の歴史的確定もしていない。','u0178及びu0193以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));r=record()
    assert json.loads(read(REVIEW))==r
    validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inv)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='literal_infinity_claim_and_usual_view_aside_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
