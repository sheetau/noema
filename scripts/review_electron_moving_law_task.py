"""Review both sentences of the second electron case and law-finding task."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-electron-moving-law-task.noema';CORE='examples/v014/electron-moving-law-task-core.noema'
BASIS='data/electron-moving-law-task-basis-v1.json';ANNOTATIONS='data/electron-moving-law-task-identifiers-v1.json'
SOURCE='data/einstein-electron-moving-law-reading-v1.json';REPORT='reports/electron-moving-law-task-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/electron-moving-law-task-v1.md'
REVIEW='data/einstein-electron-moving-law-u0244-review-v1.json'
CLAUSES=(
 ('Es besitze nun zweitens ',[415],['ek4q','ek4t','ek4u','eisxq','ug'],'前の静止条件の場合に続いて、第二の場合を今取り上げる仮定的な設定指示。論述の順序であり、時間が経って二個目の粒子ができるとはしない。'),
 ('das Elektron ',[415],['ek34','ek4p','eisxh','eisra'],'先に導入しElektronと呼んだ同じ点状荷電粒子を受け直す。現在の物理的設定も同じ対象を保持する。'),
 ('in einer gewissen Zeitepoche ',[415],['ek4o','ek4p','ek4q','ek3q'],'一つの設定の同じ出来事の座標時刻を指定する。全時間、現在の実世界の日時、先の静止時点と同一の物理時点に置き換えない。'),
 ('die Geschwindigkeit [M0398]. ',[415],['ek4n','ek4o','ek4r','ek4s','eisxt','eisxu','ek4v'],'その時点の三速度成分の非負ノルムをvとする。まだX方向を選ばず、全区間での定速度や既出の系間速度へ同一視しない。第一文の句点までを設定指示の著者帰属へ結ぶ。'),
 ('Wir suchen das Gesetz, ',[416],['ek4w','ek4x','ek4y','eisxp','vd','eisxn','eisbi'],'同じ著者が運動法則の答えを見いだすことを現在の課題として提示する。物理法則の範囲・同じ対象の運動への適用・一般的な成立を分け、三加速度の数値だけの質問や答えの発見済みへ狭めない。'),
 ('nach welchem sich das Elektron ',[416],['ek4w','eisxo','vi','ek4p'],'同じ電子の同じ物理的設定の記述がその法則に従うことを候補条件へ結ぶ。対応記述の存在とその全てへの適合を要求し、別粒子・別時点又は一個の都合のよい記述に替えない。'),
 ('im unmittelbar darauf folgenden Zeitteilchen bewegt.',[416],['ek32','ek3y','ek3z','ek4w','ek4y','ek4z','ek42'],'直前に指定した同じ時点から直後への初期運動として、基点を含む右側時間領域で三速度の微分を同じ加速度へ結ぶ。有限な時間粒・有限時間の一定加速・全局所区間の厳密解を補わず、二文目の課題を同じ著者の論説へ帰属する。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_electron_moving_law_task.py','tests/test_electron_moving_law_task_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,indices,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text,(offset,text)
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=indices,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and s['unit']=='einstein-1905:u0244'
    reasons=(
      '固定u0244の全文とM0398を原刊917頁の同じ二文へ照合した。先行の静止時の法則と記号説明、後続の一般性を保つ座標選択の間に置き、Es besitze、nun zweitens、同じ電子、指定時点、v、第一文の句点、Wir suchen、法則に従う同じ電子、直後の時間部分までを連続して扱う。',
      '既存の点粒子の全物理設定ek34と位置変化ek4mを保持し、同じ時点の三速度を三次元非負ノルムek4nへ結ぶ。第二の場合の存在はek4qの仮定内容へ置く。法則候補ek4wは同じ設定、右側初期変化、法則範囲、対象への運動法則の適用、一般的な成立、同じ局所運動の全対応記述への適合を結ぶ。ek4xの候補は法則個体であって三つの数値ではない。',
      'das Elektronは先に命名したeisxhを受け、ek34が同じ対象を固定する。vの表記eisxuは同じ物理設定の瞬間速さeisxtへ射影し、先の系間速度へ同名によって同一視しない。daraufは第二の場合の設定で選んだ同じ出来事の時刻を指し、質問の外側で全設定を固定する。候補ごとの別粒子・別場・別時点の存在選択を許さない。',
      '第一文は仮定的な設定を置く指示形式ek4u、第二文は現在の探究課題を提示していることを述べる形式ek4zとする。nunとzweitensは前の静止条件の場合からの検討順に結び、物理的な後時点や二個目の電子にはしない。Wirは同じ著者の論述の声であり、探索の実施・完了又は読者全員の行為を補わない。',
      'vを非負の速さと読むこと、零を退化例として許すこと、直後を通常実数での右側初期微分と読むことを明示する。既存の正の低速慣性質量・整合単位・完全な二階微分可能な局所履歴の規約を継承する。X軸方向、全時間の等速、光速上限、有限時間の一定加速、解の存在一意性、法則の特定の答えをこの二文へ足さない。',
      '法則の一般的な成立eisbiと個々の記述の適合viを区別する。未知の答えの許容条件はlawを引数とするviへ保持し、特定の式の意味を空の名称で定義済みにしたとはしない。新しい関係は運動法則の範囲、初期状態と変化を表す局所記述との対応、個体回答型の条件付き探究提示、検討順に限る。初期変化と速度の数値構成は別に合成する。後続の答えを述べる際には同じlawと実際の方程式の内容を接続する。',
      '局所検査は非負ノルムの全三軸、同じ時点の速度、設定の全束縛位置、候補を変えても固定される設定、対応記述の非空性と全てへの適合、一般的な法則の成立の独立性、二文の著者帰属と順序を対照する。既存の右側微分の解析的診断を証拠として固定する。有限検査から物理法則の真理、全連続体、原文同義性を自動認定せず、全文判断を別に行う。',
      '原刊917頁の二文を先行の静止条件と後続の座標選択とともに読み直した。第二の場合として、同じ電子が指定時点で速さvを持つと置き、その直後の初期運動に従う運動法則を探すという二つの役割とその照応を保持したと判断する。方向未指定の非負の速さ、通常実数の右側初期微分という読みを明示した上での判断であり、後続の具体式や見出しの緩い加速は今回完了扱いしない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    return [dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[415,416]),source_order_statements=[415,416],clauses=clauses,interpretation=basis['limitations'],limits=['明示した読みの下でのアシスタントによる全単位判断。独立査読、物理法則の真理、原文同義性の自動証明ではない。','未定の法則を求める課題の記述であり、後続の具体的な運動方程式の答え・導出は別に接続する必要がある。','第十節見出しと二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)]

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(records()[0],ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    r=records()[0];assert json.loads(read(REVIEW))==r;validate_review(ROOT,REVIEW,'einstein-1905',active,catalog,inventory)
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='electron_moving_law_task_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
