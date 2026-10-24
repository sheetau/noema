"""Separate whole-unit semantic reading of the new force wording, u0175."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_comoving_wording import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_comoving_wording import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/comoving-wording-v1.json'
REVIEW='data/einstein-comoving-wording-u0175-review-v1.json'
CLAUSES=(
 (['ejyb','ejxm','ejxk','ejxl','ejx3','ejyw','eislk'],'同じ点状単位電気量が同じ電磁場で動く条件を、第一項と同じ量1の記録・出来事・位置・履歴の三微分へ結ぶ。光速未満の任意方向を許す。番号2と先行導入を保持する。'),
 (['ejyt','ejyu','ejwt','ejws','ejts','eispt','eispu'],'その対象に働く力を、新系の同じ場所・出来事での電気側の場に等しい力として記述する。同じ対象・単位電気量・力記録・場単位・換算1・静止試験応答へ接続し、電気側の場をその場所で評価する。第一項のKで測る力の三成分をコピーしない。'),
 (['ejyk','ejyl','ejym','ejyn','ejyo','ejyp','ejyq','ejyr','ejys','ejyv','ejm2','eisqt','ejwr','eispn'],'対象へ当該瞬間相対静止する共動系の存在を、その対象の三速度に合わせた全系の等速並進、全域の物理的な座標対応、同じ対象の瞬間静止へ結ぶ。両場を同じ逆四座標で評価して混合し、同じ電磁過程の新系の場へ帰属する。全期間の静止や加速度0を加えない。'),
 (['ejyx','ejyz','ejy2','eisqr','uh','eir3','ue'],'同じ第一項を旧来、第二項を新しい言い方とする対比を共有し、著者・論説と提示順を保持する。第一項の一次近似と第二項の共動系での力を、同じ系での厳密な同一式にはしない。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_comoving_wording.py','tests/test_comoving_wording_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[]
    for part,(symbols,reason) in zip(s['clauses'],CLAUSES,strict=True):
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=part['range'],text=part['text'],statements=[INDEX],definitions=symbols,reason=reason))
    assert ''.join(c['text'] for c in clauses)==s['text'] and s['source_nonblank_characters']==301 and s['math']==[]
    reasons=(
        '固定u0175の第二項全体301非空白本文文字を、原刊910頁の画像と固定転記で再読した。別の数式要素はない。先行段落の力の単位と当該瞬間の相対静止、および第一項の旧来の言い方との対比を文脈として保持する。原資料は変更しない。',
        '点状単位電気量が電磁場で動く条件、その対象に働く力と同じ対象の場所の電気側の場との等値、相対静止系への場の変換によってその場を得る関係、新しい言い方という提示をすべて合成する。任意方向の三速度・四座標・両場・領域を結び、位置だけでなく時刻も同じ逆写像で評価する。',
        '対象zol、評価出来事zpo、旧位置zpj、旧系ra、両場znl/znmと領域znk、同じ過程eisppを保持する。新系と速さ・量記録・力記録・場単位・静止応答は同じ存在証人として共有する。量単位zou・力単位Dyn=zot・長さta・時間rbと換算1を結ぶ。旧固定kの参照やKの力を任意方向へ流用しない。',
        'Ist ... soの条件をejywの任意方向の運動前件と共動系の存在という内容にし、uhで著者が第二項に述べたことへ帰属する。番号2、先行導入、旧来／新しいの対比、第一項の後という順序を同じメッセージへ結ぶ。物理法則の真理を検査結果で断定せず、内容を引用した提示として記述する。',
        '前段の少なくとも当該瞬間という静止を引き継ぐ。共動系自体は対象の瞬間速度に合わせた等速並進系とし、対象の加速度0や前後の静止を要求しない。軸を同じ向き・共通原点とする純粋boostの代表が存在する読みであり、全回転・全原点表示の数値同一性を足さない。先行変換の正の光速度・光速未満の適用域を保つ。Kの機械力と共動系の力の無条件な三成分等値を加えない。',
        '新基本関係eisqtは物理的な二つの座標記述と同一出来事の全域対応を結ぶ規約であり、特定の変換・相対速度・対象静止・場・力を内包しない。三速度と速さの関係、全系の並進、四座標の純粋boost、両場の混合と逆像、瞬間静止、同じ単位電気量の静止試験力を別の定義で合成する。一文を一基本記号へ隠さず、未占有点も含む座標域と物理的帰属の境界を明示する。',
        '旧来の言い方、物理的運動・静止力・系の並進・標準配置の場変換の固定証拠を照合する。新検査では任意方向・符号・零速度の退化例、逆変換、時空間隔、標準配置との一致、両場と領域の逆像、全物理引数と証人全位置を対照する。有限の有理数例と二値の証人診断に限定し、全実数・全関数域の拒否を維持する。数値確認を物理的帰属や意味同義性の証明とはしない。',
        '原刊の第二項全体を、前段の単位電気量・当該瞬間の静止と第一項との対比を含めて読み直した。同じ対象・作用・場所・単位、運動条件、共動系への場の変換、同系の力との等値、新しい言い方という提示を、明示した解釈の下で欠落なく記述したと判断する。後続の磁動力・補助概念・非対称性解消はこの単位に含めず、別途完成させる。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    record=dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[]),selection=selection_binding(catalog,[INDEX]),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる全単位通読判断。独立査読・同義性の自動証明ではない。','原著者の物理法則や全連続系での変換を証明した記録ではない。物理的な帰属は明示した意味規約へ接続している。','u0176以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=301,source_sha256=pins)
    return [record]

def prepare():
    from scripts.audit_opening_scope import write_exact
    write_exact(ROOT/REVIEW,json.dumps(records()[0],ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    r=records()[0];assert json.loads(read(REVIEW))==r
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY)
    validate_review(ROOT,REVIEW,'einstein-1905',active,load_catalog(ROOT,BASIS),json.loads(read(INVENTORY)))
    pins=dict(r['source_sha256']);pins[REVIEW]=digest((ROOT/REVIEW).read_bytes())
    return dict(status='new_comoving_force_wording_whole_unit_reviewed',document=FULL,source_units={r['unit']:301},reviewed_math_elements=0,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
