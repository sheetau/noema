"""Whole-unit reading of the sublight result and strict-deficit explanation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_velocity_deficit_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_velocity_deficit_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/velocity-deficit-claim-v1.json'
REVIEWS=tuple(f'data/einstein-velocity-deficit-u{n:04d}-review-v1.json' for n in (143,144))
REASONS=(
 (
  'u0143の二文全範囲を原刊906頁と固定転記で照合した。Aus dieser Gleichung folgt、二つの速度がV未満という条件、stets、結果のV未満、Setzt man nämlich、vとwの二つの置き換え、双方の不足量の正性と厳密上限、末尾のコロンを確認した。M0264–M0270の七要素を固定した。',
  'ejpvは前の一次元式を同じ光速で一般の非負・光速未満の二入力へ適用する形、ejpwはその式から構成した結果が同じ合成関係と厳密上限を満たす全称内容である。ejpxは二つの置き換えと0<κ,λ<Vを合わせる。ejpyからejpzを得るという説明と、その表示式をejpwの論証として提示する役割も保持する。',
  'この式は直前のM0263のs3g/s3jを指す。ejpaを共有し、同じ点・K/k・光速・現在全履歴・座標微分・非負ノルムを保持する。量化する入力は実際の一組とは別だが、同じVと同じ合成式を用いる。κはV−v、λはV−wとしてそれぞれ別の実際の量へ結び、数値が偶然一致するだけでは対応を認めない。',
  'ejp2は前の式からの帰結、ejp3は局所範囲zlkに置く仮定、ejp4はその条件下の表示式への帰結、ejp5は先の一般主張を説明する論証の提示である。同じ著者・論説・第五節と局所範囲を保持し、zlfからzli、zlj、zllへの本文順序を記述する。nämlichを単なる数式の隣接に置き換えない。',
  '一般主張を同方向の式の0≤v,w<Vという既存の読みで保持し、任意方向や負速度へ拡張しない。原文の0<κ,λ<Vは零入力を含まないため、一般主張に含む境界を同じ不足の論証へ追加しない。前の正方向条件と同じ式を局所前提に保持し、新たな物理仮説や実測値・計算履歴を加えない。',
  '不足関係s3oは実数の正性・厳密上限・減算の等値、一般主張s3vは実切断への全称と構成した合成値の関係・上限で構成する。仮定・帰結・論証の提示は既存ug/zc/zfrを再利用し、原文一文を丸ごと表す未説明の基本記号を作らない。',
  '双方の量化位置、結果を実際に構成して関係と上限の双方を課すこと、厳密不足と零境界、二つの不足量の取り違え、前の同方向条件と物理的参照、帰属の全引数を対照した。全実数の有限列挙は拒否する。保存された有理多項式証拠と有限検査を全実数・全物理状況の証明や意味同値の自動判定とはしない。',
  '前の式から一般主張を得る第一文、仮定を置いて説明する第二文、次の表示式の等号と厳密上限まで続けて通読した。量化・二つの条件・参照・局所範囲・nämlichの論証提示を、明示した非負同方向の読みの下で欠落なく記述したと判断する。零境界を元の説明が直接扱っていないことも保持する。',
 ),
 (
  'u0144全範囲[M0271]を原刊906頁のコロンから照合した。U=V*(2V−κ−λ)/(2V−κ−λ+κλ/V)<Vという等号・厳密不等号の連続、外側と内側の分数、係数2、各符号、句点を確認した。固定MathMLのϰと原刊の不足量への参照を保ち、訂正を加えていない。',
  'ejpzはs3yを通じて同じUの商への等値とU<Vを連言で保持する。s3q/s3rは分子2V−κ−λ、分母へのκλ/Vの加算、外側のVの因子と符号付き除算を表す。単なる上限不等式や交差乗算した多項式だけに縮めない。',
  'Uは前の一次元式と同じ点のKでの非負速さ、Vは同じ光速である。κとλは直前の仮定ejpxによりそれぞれvとwへ結ばれる。ejpyは同じ現在の取得、正方向条件ejpp、一次元式ejpqと仮定を共有し、旧s3lの別の物理参照へ戻らない。',
  '表示式は直前の仮定とコロンに対する帰結としてejp4で提示され、同じ式箇所zllがejp5で先の一般主張の論証として提示される。両者を同じ著者・論説と局所範囲へ帰属する。等式の無条件な真理や著者の論証の健全性を帰属から認定しない。',
  '双方の不足量の厳密条件と正のV、商の非零分母、結果の有効性を保持する。一般主張の零入力は不足量がVとなるため、この式をその境界にも同じ条件で適用したことにはしない。反対向きの速度や任意方向へ適用範囲を拡張せず、前の式の正方向の読みを継承する。',
  '式の演算は既存の実切断の加算・減算・積、正のVによる逆数、外側の符号付き逆数と等値で構成する。厳密上限は同じUとVの順序関係で別に要求する。数値核の本体と意味規約を変更せず、現在の量と説明の提示へ接続した。',
  '正の不足量、交換、光速に近い値、誤った値だがV未満の場合、零不足、Vに等しい不足、負不足、無効なVを検査した。分母が域外のときの補助値を二通りに変えても条件を迂回できない。κ・λを交換して商が不変でも前提の参照は拒否される。これは全実切断の一般的な順序体の証明ではない。',
  '直前の仮定導入と論証の役割、表示式全項と等号・厳密不等号・句点、次の光速不変性への移行まで通読した。現在の同じ量、厳密不足条件、正方向、符号付き商という明示した読みの下で、式と提示を欠落なく記述したと判断する。後続の光速不変性は別の未完範囲として残す。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_velocity_deficit_claim.py','tests/test_velocity_deficit_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[];selections=([139,140,141,142],[140,141,142])
    symbols=(['ejpv','ejpw','ejpx','ejpy','ejpz','ejp2','ejp3','ejp4','ejp5','ejqc','ejqd','ejqe','ejqf','s3o','s3v','s3w','s4a'],['ejpx','ejpy','ejpz','ejp4','ejp5','ejqe','ejqf','s3o','s3q','s3r','s3y','ejpa','ejpp','ejpq'])
    for i,s in enumerate(source_record()['segments']):
        assert len(REASONS[i])==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols[i])
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selections[i]),source_order_statements=selections[i],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols[i],reason=REASONS[i][1])],interpretation=LIMITS,limits=['同方向の非負入力の一般主張、厳密不足による局所仮定、帰結と論証の提示という明示した読みの下でのアシスタントの通読判断。独立査読・全可能解釈の包含・意味同値の自動証明ではない。','一般主張に含む零境界と、原文の不足量による説明の厳密条件の違いを残す。著者の論証の提示を記述し、その全境界での妥当性や普遍的な物理的真理は認定しない。','u0145以降、u0147に残る旧前提への接続、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='universal_sublight_claim_and_strict_deficit_explanation_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=8,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},general_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
