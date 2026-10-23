"""Whole-unit reading of the same clock's seconds lost and approximation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_clock_seconds_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDICES,LIMITS
from scripts.check_clock_seconds_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/clock-seconds-claim-v1.json';REVIEW='data/einstein-clock-seconds-u0125-review-v1.json'
CLAUSES=(
 ('woraus folgt, daß ',['ejjw','ejjx','ejj3'],'直前の同じ時計の比例式・差の式から、共通の秒換算の下で遅れを得るという著者の帰結提示。'),
 ('die Angabe der Uhr ',['ejit','ejjq','ejiu','ejjt'],'同じ時計zieの実際の校正された指示を、局所表示と現在記録へ結ぶ。別時計や単なる座標記号の値へ替えない。'),
 ('(im ruhenden System betrachtet) ',['ejjq','ejjs','ejjt'],'Kの正の経過時間と同じ時計のτ指示差を比較する基準を保持する。時計自身のk時刻を観測経過の分母にしない。'),
 ('pro Sekunde um [M0217] Sek. ',['svp','ejjr','ejjs','ejju','svt'],'同じ共通尺度で秒へ換算した指示経過が、Kの経過一秒当たり1−√(1−(v/V)²)秒だけ不足する。全経過の遅れとの区別と、一秒への規格化を保持する。'),
 ('oder — ',['ejjv','ejjy','ejj4'],'同じ厳密な遅れについて、留保付きの近似表示へ言い換える。二つの別の時計の選択や排他的な選言にしない。'),
 ('bis auf Größen vierter und höherer Ordnung ',['svx','svy','swc','ejjv'],'速度比の零近傍で誤差がO((v/V)^4)という明示した読みで留保を保持する。共通定数・近傍幅と全近傍点の量化を有限標本に替えない。'),
 ('um [M0218] Sek. ',['svq','svu','svv','ejjv'],'同じ一秒当たりの遅れの二次近似を(v/V)²/2秒とする。厳密値と残差へ結び、厳密等号や全速度での小誤差保証へ替えない。'),
 ('zurückbleibt.',['ejjr','ejju','ejjv','ejj3','ejj4'],'同じ時計の指示経過がKの経過に不足する関係として、厳密表示と留保付き近似を述べる一文を閉じる。'),
)
REASONS=(
 '固定u0125を原刊904頁の比例式末尾に続くworaus folgtからzurückbleibt.まで通読した。同じ時計の指示、Kからの比較、一秒当たり、二つのSek.、oderとダッシュ、四次以上の留保、M0217とM0218の根号・二乗・半分を確認した。',
 '同じ時計の先後のK/k局所対ejjqを選び、正の観測経過と指示経過を共通尺度で秒へ換算するejjsを構成した。ejjrがE=T*fとL=T−E=T*(1−f)を結び、ejjtは全時間の率と全現在範囲を保持する。ejjvで同じ厳密な遅れ、二次近似、残差、全近傍の四次誤差条件を結ぶ。',
 '時計は前から同じzie、状況はzb6、比較基準はK、指示は同じ出来事のkのτである。光速V、速度v、正の率fと秒への換算尺度を全ての記録対で共通にする。二つの時間差へ別の尺度を与えず、同じ記録を逆順や零時間幅へ替えない。',
 'woraus folgtは前の同じ時計の比例式と共通換算を前提とするzcの帰結提示である。oder以下は同じ遅れの近似を留保と共に提示するuhとして保持し、前の厳密内容をその近似内容へ含める。同じ著者・論説と文順へ帰属し、処理系の証明済み認定にはしない。',
 'pro Sekundeは規格化した率の読みで、一秒ちょうどの実測区間の存在を要求しない。秒は原文の共通の基準単位として既存の正の線形換算へ接続し、歴史的な実現装置を付加しない。近似の四次以上を零近傍のBig-Oとして明示し、全速度の実用精度や無限の解析展開を主張せず、原文にない残差係数の具体的上下限を加えない。',
 '新しい基本記号を追加せず、現在の全局所対・全時刻・校正・代表軌跡、時間単位ciと秒zik、線形換算zil/svp、正の平方根と実切断演算、既存svq/svy/swc、帰結と引用を合成した。旧zac/zdz/svcの草案の記録選択を再利用せず、現在の同じ出来事対応と指示差に結ぶ。',
 '正の秒経過と厳密な不足、全経過と一秒係数の区別、単位と状況と正尺度、各記録スロット、両時間差の共通換算、全時間順の区間、実際の率の非零時間幅、近似と残差、集積点・正の共通定数・近傍幅・全関数の有効性を対照検査した。全実数量化の有限評価は拒否し、既存の誤差規約の証拠と原刊通読を別に保持する。',
 '文全体を前の比例式と次の運搬時計への段落とともに再読した。同じ時計の指示がKの経過一秒当たりに厳密値だけ遅れ、その二次近似を四次以上の留保の下で述べるという読みで、関係・単位・範囲・参照・提示を欠落なく保持したと判断する。u0126以降の運搬と到着時の比較は次の作業である。',
)

@lru_cache(None)
def record():
    catalog=load_catalog(ROOT,BASIS);s=source_record()['segments'][0]
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_clock_seconds_claim.py','tests/test_clock_seconds_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[];offset=0
    for text,symbols,reason in CLAUSES:
        assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
    assert offset==len(s['text']) and len(REASONS)==len(REQUIREMENTS)
    return dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,list(INDICES)),source_order_statements=list(INDICES),clauses=clauses,interpretation=LIMITS,limits=['共通の秒換算と全時間の指示差、速度比の零近傍のBig-O型の留保という明示した読みの下でのアシスタントの通読判断。独立査読、全可能解釈の包含、物理的真理や意味同値の自動証明ではない。','u0126以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins)

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=record();assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    return dict(status='clock_seconds_loss_and_qualified_approximation_whole_unit_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters']},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=r['source_sha256']|{REVIEW:digest((ROOT/REVIEW).read_bytes())})
