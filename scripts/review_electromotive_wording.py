"""Record a separate whole-unit reading of the old force wording, u0174."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_electromotive_wording import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_electromotive_wording import DOC,SOURCE,INVENTORY,DEPENDENCIES,source_record

REPORT='reports/electromotive-wording-v1.json'
REVIEW='data/einstein-electromotive-wording-u0174-review-v1.json'
CLAUSES=(
 (['ejyb','ejxm','ejxk','ejxl','ejx3','eisqc','seoc','sbw2'],'第一項の同じ点状単位電気量が同じ電磁場で動く前件を、量1の記録・出来事・位置・座標単位・同じ履歴の三微分へ結ぶ。先行場変換の光速未満の適用域で任意方向を扱い、全期間の等速や加速度0を足さない。番号1は先行u0173の同じ第一項zpqへの列挙に接続している。'),
 (['ejx4','ejx7','ejye','ejyg','ejyh','eisqp','eisqq','ejwu','zpc'],'その電気量に働く同じ機械力応答を物理的に帰属し、零速度の電気基準との差を追加寄与へ結ぶ。全寄与・電気基準・追加寄与の系・対象・出来事・単位を共有し、電動力という引用用語をその同じ追加量の役割に結ぶ。電位差や独立した実体、非零の追加値を補わない。'),
 (['ejxy','ejx2','ejx5','ejx6','ejya','svy'],'M0318=v/Vの二次以上を省く留保を、固定した場と方向で速度を比例縮小した際のO((v/V)^2)の差として読む。三成分全ての一次部分を保ち、有限速度で厳密等値にせず、二次・三次等の差と零誤差を許す。場ごとの定数・近傍を保持する。'),
 (['ejx6','ejya','ejyc','ejyd','sci2','scg2','eispu','eirn'],'速度×磁気側の場の順序付き外積を同じ光速度で割る三成分式を構成し、その追加寄与への一次近似を条件付きの著者の主張にする。磁場の値は同じ電気量の場所で評価し、磁場単位と量単位の積を同じDynへ直す換算1を明示する。x方向だけへ制限しない。'),
 (['ejyh','ejyj','eisqr','uh','eir3','ue'],'第一項を既に使われてきた言い方、同じ後続第二項zprを今回提示する新しい言い方として対置する。同じ著者・論説と二表現の導入の後という順序を保ち、旧表現の禁止や歴史的初出を付け加えない。'),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);s=source_record()
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*DEPENDENCIES,'scripts/review_electromotive_wording.py','tests/test_electromotive_wording_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    clauses=[]
    for part,(symbols,reason) in zip(s['clauses'],CLAUSES,strict=True):
        assert all(n in catalog.entries for n in symbols)
        clauses.append(dict(range=part['range'],text=part['text'],statements=[INDEX],definitions=symbols,reason=reason))
    assert ''.join(c['text'] for c in clauses)==s['text'] and s['source_nonblank_characters']==386
    reasons=(
        '固定u0174の第一項全体386非空白本文文字とM0318を、原刊909末尾から910頁へまたがる文として連続して再読した。M0318はv/V、A0024は910頁への頁境界で脚注ではない。原資料・保存画像・転記を固定し、原文自体は変更しない。',
        '点状の単位電気量が同じ電磁場で動く条件、その対象に電気力に加えて働く寄与、引用用語、二次以上の留保、速度と磁気側の場の外積の順序、光速度による除算、旧来の言い方という位置付けをすべて構成する。速度方向は三成分で保持し、追加値が0になる場合も除外しない。',
        '単位電気量は直前からのzol、Kはra、力の評価出来事はzpo、場所はzpj、両場はznl/znm、量単位はzou、力単位はDyn=zotである。実際の速度は同じ履歴の三つの座標時刻微分、電気基準はzplとzpe、追加と全寄与は同じ物理応答と別々の記録に結ぶ。第一項zpq・第二項zprと先行導入eisqnを保つ。',
        '第一項のIst ... soをejydの任意方向の条件文として著者へuhで帰属し、引用用語の解釈と旧来／新しいの対比を同じ第一項のメッセージejyiへまとめる。eir3とueで同じ著者・論説・順序を保持する。用語の役割に近似の真理を組み込まず、引用された規則を実行したり物理法則を自動認定したりしない。',
        '両項を先行する最終場変換の言い表しとして正のV・光速未満の速さで読む。x方向限定、全期間の等速、加速度0、全場一様な誤差、解析性、有限速度の厳密等値、誤差の非零、力の非零を加えない。仮想的な速度比較を同じ出来事への相反する実速度や実験実施にせず、Kの機械的寄与とkの力の成分を等置しない。',
        '点状電気量、座標履歴、単位、電場の静止試験規約を既存の意味規約へ結ぶ。新しい物理応答eisqpは同じ場への機械的な寄与の帰属であり、公式を含めない。追加量を同じ応答と電気基準との差で合成し、速度比二乗・外積・誤差・全方向の条件は別に記述する。引用用語eisqqと二言い方の対置eisqrも一般的な意味規約を持ち、一文全体を一原始記号で代用しない。',
        '既存の物理的な運動・静止電気力・場の定義・外積の証拠を固定ハッシュで照合した。新たに実際の型の三成分計算、物理応答の全引数、記録と単位、任意方向と符号、定数・一次誤差の拒否、二次・三次差の許容、証人全位置、著者・用語・対比を対照する。漸近診断は明示した低次数多項式の族に限り、全実数・全関数の量化拒否を保つ。これらを通読判断の自動証明とはしない。',
        '原刊の第一項全体を前段の単位電気量と場の解釈、および後続する新しい言い方への対比とともに再読した。同じ対象・作用・場所・単位、条件、任意方向の式、二次以上の留保、引用語の物理的役割、旧来という提示を明示した解釈の下で欠落なく記述したと判断する。第二項の任意方向の共動系変換と全文の判断は、この第一項の判断に含めない。',
    )
    assert len(reasons)==len(REQUIREMENTS)
    record=dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:s['math'][k] for k in ('id','sha256')}]),selection=selection_binding(catalog,[INDEX]),clauses=clauses,interpretation=LIMITS,limits=['明示した解釈の下でのアシスタントによる全単位の通読判断。独立査読・同義性の自動証明ではない。','原著者の物理法則を真と証明した記録ではない。理想応答の物理的帰属は明示した意味規約である。','第二項u0175の全体、u0176以降、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=386,source_sha256=pins)
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
    return dict(status='old_electromotive_wording_whole_unit_reviewed',document=FULL,source_units={r['unit']:386},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':1},semantic_equivalence_automatically_proved=False,source_sha256=pins)
