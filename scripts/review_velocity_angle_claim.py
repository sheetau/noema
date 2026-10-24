"""Record rereading of the first-order introduction, conjunction and angle formula."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_velocity_angle_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_velocity_angle_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/velocity-angle-claim-v1.json'
REVIEWS=tuple(f'data/einstein-velocity-angle-u{n:04d}-review-v1.json' for n in (135,137,138))
REASONS=(
 (
  'u0135全範囲の平行四辺形則の文とWir setzen:を原刊905頁で照合し、その先のU/w二式、und、αの式、906頁の角の説明まで続けて読んだ。第一文だけで切らず、後続を指すコロンの範囲を三量の定義に固定した。',
  '平行四辺形の成分加法則を、同じ三速度の共通倍率を零へ近づける一次近似として述べ、厳密な一般則の不成立をnurの限定として保持する。alsoは直前のKでの三式からの帰結、nach unserer Theorieは同じ論説の構成対象の理論への帰属である。続くWir setzenはU,w,αの三つの量の定義導入であり、帰結文や実験実行と混同しない。',
  '第一文の前提ejnp、一次化ejoc、理論項目ejod、帰結ejoe、著者帰属ejogは前段と同一。定義導入は同じ著者rd、論説eirf、第五節eisoq、点zkbとK/kを用い、U/wの方法ejoi/ejoj・値zkp/zkq、αの方法ejow・測度eiso4を共有する。Wirのために別の著者集団を追加しない。',
  '第一文は同じ理論に属する主張を著者が帰結として提示する役割である。Wir setzen:は後続の三式を同じ導入全体eiso6として提示する。ejo2は既存の二式ejomと角の式ejozを同じ状況で連言し、ejo4は同じ著者・論説へ帰属させる。',
  'nurを全ての個別速度設定での不一致とせず、特殊な厳密一致を許す。一次は共通速度倍率という明示した読みであり、原文が誤差次数を逐語指定したとはしない。U/wは非負速さで零も許す。αの非零・非零除数条件を速さの定義へ加えず、点の光速上限も加えない。',
  '実数の微分、二成分のノルム、共通一次化、理論への帰属、既存の命名規約と閉じた内容の連言を合成する。αは積分とπ・内積と有向面積から測度を構成し、記号の綴りだけで量を代用しない。新しい参照記号の役割は型付きの規則に結ぶ。',
  '前段の一次化・速さの固定報告を保持し、今回の三定義・表記・順序・著者帰属の引数検査を加えた。全実数の微分や積分は有限列挙しない。旧文131/132は異なる部分内容として置換し、旧判断の等価な更新とは扱わない。原文判断は検査成功と独立に行う。',
  '第一文からコロン、三定義とund、角の説明まで再読した。第一近似・理論の限定・帰結・著者による定義導入とその全参照先を、共通一次化、非負速さ、明示した角の枝の解釈の下で欠落なく記述したと判断する。u0139後半の計算移行はこの単位の判断へ含めない。',
 ),
 (
  'u0137の全3文字undを原刊905頁で照合した。w²の式とαの逆正接の式の間にあり、上のWir setzen:が三式を導入している。',
  'U/wの二定義とαの定義を同じ提示文脈で共に採る連言ejo2と、wの式からαの式への本文順序を保持する。二者択一、条件付き片方向、独立した別の定義導入へ替えない。',
  '左側はejomの同じ二式とU/wの規則、右側はejozのαの規則である。両側ともrd/eirf/eisoqと同じ提示状況を用い、順序はzksからzkuへ結ぶ。別のw成分や後続の合成速度式へ接続しない。',
  'undを一つの著者によるWir setzenの列挙の継続として、三定義を含むメッセージejo3と帰属ejo4へ保持する。数式内容だけの論理演算にせず、定義提示同士を連言する。',
  '三量の定義方法はそれぞれの条件を保つ。角が未定義の速度設定でも速さの二定義の意味を削らず、連言を全物理条件の無条件な実現の主張としない。接続語へ計算結果や新たな光速上限を足さない。',
  '既存の内容評価・連言・本文順序と著者帰属を合成し、und一語専用の新しい原始関係を置かない。引用された数量規則の同一性を型と参照で保持する。',
  '三つの定義のどれか一つ・一部だけでは導入全体を満たさず、方法・値・表記・範囲・順序の取り違えを拒否する対照を確認した。引数検査の成功を原文の全体判断へ自動変換せず、原刊での接続位置と範囲を通読した。',
  'Wir setzen:、二つの速さの式、und、αの式を続けて再読した。同じ著者の三量の定義を連ねるという役割を欠落なく保持したと判断する。',
 ),
 (
  'u0138の全範囲[M0253]を原刊905頁へ照合した。α、等号、arctg、分子wη・分母wξ、末尾セミコロンを確認し、次頁のαをvとwの間の角と見る説明まで読んだ。保存MathMLの式と画像の参照を固定する。',
  '符号付きの同じ二成分の比を非零の縦成分xとの積x*r=yで指定し、実直線積分による主値と成分の象限で枝を選ぶ角へ接続する。等号はその方法で得る測度を同じαの値として導入する規約である。単位円の対だけで実数測度を代用しない。',
  '分子と分母は同じ点のkでの横・縦定速度zkd/zkc。系の速度は同じK/kの実際の相対速度、wは同じ点の非負の大きさzkqである。zktの二成分、αの測度eiso4、αの表記eiso5は別の型としてejoy/ejowへ結ぶ。表記だけ似た別の角やUの値へ置換しない。',
  'この式はWir setzenに属する三番目の定義導入zbであり、前の二つの速さにundで続く。ejozで方法側ejowと値側ejox、αの表記規則を提示し、ejo4で同じ著者・論説へ帰属する。直後の幾何学的な説明ejo7も同じ測度を受ける。',
  '採用する角は正の系速度から点速度への向き付き代表(-π,π]。主値だけで負の縦成分を除かず、負の横成分も許す。原文が枝を逐語指定したとはせず、この明示した読みで判断する。零の速度には角なし、縦成分零では商なし。幾何学的直角の指定から商の値を補わず、点の光速上限も足さない。',
  'ejorは既存の全タグ付き分割積分sedeと1/(1+t²)のsedhを用い、負の上端では区間と値の符号を反転する。πはsedi、単位円の向きは内積と有向面積s2gで指定し、ejos/ejot/ejouが同じ実数測度へ結ぶ。角度専用の未説明の原始述語や浮動小数値を定義としない。',
  '前段の象限・端点・零・符号・内積と有向面積・共通証人・現在速度への接続の307対照例を固定報告として保持する。今回は同じ値・表記・定義方法・説明・帰属の引数を検査した。全実数積分の存在一意性、歴史的規約の一意な確定、意味同値の自動証明とは区別する。',
  'undからαの式、セミコロン、次頁の幾何学的意味の説明まで再読した。成分比、逆正接の枝、実数測度、同じ点と二速度、著者の定義提示を、向き付き角という明示した解釈の下で欠落なく保持したと判断する。u0139後半とM0257は未完であり、この判断から完成扱いしない。',
 ),
)


@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_velocity_angle_claim.py','tests/test_velocity_angle_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[];selections=([131,354,355],[131],[131,132]);orders=([354,355,131],[131],[131,132])
    symbols=(['ejoc','ejod','ejoe','ejog','ejom','ejoo','ejoz','ejo2','ejo4'],['ejom','ejoz','ejo2','ejo4','zb','ue'],['ejox','ejoy','ejoz','ejo4','ejo5','ejo7','ejow','ejov','ejor','ejos','ejot','ejou','sede','sedi','s2g'])
    for i,s in enumerate(source_record()['segments'][:3]):
        assert len(REASONS[i])==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols[i])
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selections[i]),source_order_statements=orders[i],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols[i],reason=REASONS[i][1])],interpretation=LIMITS,limits=['共通速度倍率の一次化、非負の速さ、象限を選ぶ向き付き実数角という明示した解釈の下でのアシスタントの通読判断。独立査読・全可能解釈の包含・意味同値の自動証明ではない。','u0139後半の計算への移行とM0257、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,r in zip(REVIEWS,records()):write_exact(ROOT/p,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for p,r in zip(REVIEWS,records()):
        assert json.loads(read(p))==r
        validate_review(ROOT,p,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[p]=digest((ROOT/p).read_bytes())
    return dict(status='first_order_definition_introduction_conjunction_and_angle_formula_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},semantic_equivalence_automatically_proved=False,source_sha256=pins)
