"""Whole-unit judgment for the three rewritten equation chains, M0417."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-electron-mass-rewrite.noema';CORE='examples/v014/electron-mass-rewrite-core.noema'
BASIS='data/electron-mass-rewrite-basis-v1.json';ANNOTATIONS='data/electron-mass-rewrite-identifiers-v1.json'
SOURCE='data/einstein-electron-mass-rewrite-reading-v1.json';REPORT='reports/electron-mass-rewrite-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/electron-mass-rewrite-v1.md'
REVIEW='data/einstein-electron-mass-rewrite-u0253-review-v1.json'

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS));s=source['units'][1]
    assert s['unit']=='einstein-1905:u0253' and s['text']=='[M0417]' and s['range']==[0,7]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_electron_mass_rewrite.py','tests/test_electron_mass_rewrite_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        evidence=json.loads(read(path));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    symbols=['elq','elr','els','elt','elu','elv','elx','ek63','ek66','ek74','ek5i','elk','eisyo','zd3','eiswm','eisox']
    assert all(x in catalog.entries for x in symbols)
    reasons=(
     '固定u0253のM0417全体を、原刊919頁の前後、u0252第二文の(A)の書換え、u0254の力の説明とともに再読した。三行に各二等号があり、MathMLと原刊の軸・次数・符号・プライム・d²/dt²が一致する。u0252第一文を別の未完事項に残す。',
     'elqはμβ³ax=εX、μβ²ay=εβ(Y−vN/V)、μβ²az=εβ(Z+vM/V)を構成し、elrは中辺と同じkのεX′,εY′,εZ′を結ぶ。三行六等号、横の負号と正号、v/V、βの次数、同じμ・εを保持する。',
     '同じ電子eisxh・出来事eisxv・K=ra・k=eisxy・v=eisxt・V=tc・両系の単位尺度・低速慣性質量・電荷を先行PAIRから引き継ぐ。旧指定点は旧実場へ、新指定点ek5iは独立した実新電場へ渡す。ラベル(A)の指すelkと直前の式表示eisymへの照応を保持する。',
     '著者が既出変換ek7sの下で先行(A)のelkをeluへ同値な形として書き換えるというzd3、同じ先行表示へのeiswm、同じラベルeisch、次の三行の表示eisox、説明uf・順序ue・帰属eir3を接続する。数値条件を定義しただけにせず、引用内容の真理を提示の実行に含めない。',
     'eluは先行(A)と同じ全共動設定ek63にelsを適用する。実二階微分、同じ物理量の帰属、原点選択、0≤v<V、V>0、μ>0、正のβ、Kの右側初期変化を継承する。有限時間の一定加速度や場方程式全体を新条件に足さない。後続で述べる力の測定規約を数値一致から先取りしない。',
     '新規の基本記号二つは本文箇所への参照である。等式、実数演算、場評価、座標写像、二階微分、全称と同じ割当、条件付き書換えと著者帰属を既存概念で構成する。新電場を変換の帰結として定義せず、未知の入力を拒否する。',
     '各行の左・中・右を独立に変える対照、符号付き電荷、縦非零加速度、原点以外の座標と原点ずれ、同じ全42引数と38束縛、引用の非実行を検査する。保持した有理関数履歴の実二階微分は先行の固定証拠を再利用する。二値の束縛診断や数値例を全実数・全関数域の証明にしない。',
     '三行全体を先行の書換え導入と後続の力の説明の間に置いて再読し、各等号、対応する実物理量、参照、条件と表示の役割が揃ったと判断する。これは同じ初期運動と単位規約の読みでのu0253全体のアシスタント判断である。u0252第一文、力と質量の意味説明、二作品全体の完成を含めない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    record=dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[422]),source_order_statements=[422],clauses=[dict(range=[0,7],text='[M0417]',statements=[422],definitions=symbols,reason='三行の各二等号を、同じKの実二階微分と同じkの実電場へ結び、先行(A)の書換えとして提示する。')],interpretation=basis['limitations'],limits=['明示した初期運動の読みでのアシスタントによる全単位判断。独立査読、物理法則の真理、全域の同値性又は原文同義性の自動証明ではない。','u0252第一文と後続の力・加速度・質量の規約は未判断。書換え導入の第二文だけでu0252全体を完成扱いしない。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=0,source_sha256=pins)
    return [record]
def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(records()[0],ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);r=records()[0]
    assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='three_rewritten_chains_whole_unit_reviewed',document=FULL,source_units={r['unit']:0},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
