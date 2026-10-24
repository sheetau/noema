"""Whole-unit reading of symmetry appraisal and the positive axial case."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_velocity_axial_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_velocity_axial_claim import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/velocity-axial-claim-v1.json'
REVIEWS=tuple(f'data/einstein-velocity-axial-u{n:04d}-review-v1.json' for n in (141,142))
REASONS=(
 (
  'u0141全範囲を原刊906頁で照合した。第一文のvとw、対称な入り方へのbemerkenswertという評価、句点、Hat auchで始まる第二文、X軸と括弧内のΞ軸、so erhalten wirのコロンを読み、M0258–M0262の参照を固定した。',
  'ejplは同じ合成式の非負二入力を交換する一般的な関係不変性s3bを現在の量へ結ぶ。ejpmはその同じ内容を注目価値で評価する。第二文はejppの正方向条件からejpqの一次元式を得るというejpsであり、単に式や含意を定義するだけにしていない。',
  'vは同じK/kの正の相対速度、wは同じ点のkでの非負速さ、UはKでの微分から得る速さ、Vと角は直前の式と共有する。ejpaは現在の全履歴・微分・ノルム・角の取得を保持する。XとΞはその同じ両系の対応した縦軸で、auchはvとwがともに正方向であることへ結ぶ。',
  '対称性の主張と注目価値の評価を同じ著者・第五節・zkyへ帰属する。直前の表示式zkwからzky、その後の条件と表示式zlfへの順序を保持し、ejpuは帰結提示を同じ論説へ帰属する。評価や導出が述べられたことから、その真理や読者の反応を実行しない。',
  '対称性は同じV・角の下の数値入力の交換と読み、系や物理的役割の交換に拡張しない。bemerkenswertは注意価値と文脈基準による評価とし、固定閾値や驚きを加えない。Richtungは正の非零運動という既存の明示した読みを保ち、逆向きと停止を含めない。後続の点の光速上限は前提に加えない。',
  '対称性は実切断への全称量化と同じ結果に関する同値s3a、注目価値はs2zと既存の尺度・基準、方向は横成分零と正の非負ノルムへの等値s3iで構成する。現在の取得規則へ接続し、原文一文を表す説明のない基本記号は追加していない。',
  '対称性の三つの量化位置、固定V・角と交換される二入力、評価の対象・文脈、方向の本体、同じ四数値の式、帰属の各引数を対照した。全実数域の有限列挙は拒否する。既存の代数証拠と有限検査は一般の物理導出や意味同値の自動証明ではない。',
  '第一文の式への言及と注目評価、第二文のauch・条件・括弧内の軸名・得られるという提示、次の表示式まで通読した。現在の物理的な参照と明示した正方向・評価の読みの下で、両文全体を欠落なく記述したと判断する。歴史的に唯一の読みや著者の推論の無条件な正しさを認定するものではない。',
 ),
 (
  'u0142全範囲[M0263]を原刊906頁の直前のコロンから照合した。Uと等号、分子v+w、外側分母1+vw/V²、内側の分数とVの二乗、末尾の句点を確認した。電子MathMLの構造とも一致し、この式へ転記訂正を加えていない。',
  '同じU=(v+w)/(1+vw/V²)をs3g/s3jとして保持する。二つの加算、積vw、V²、二つの除算と符号付き商を区別する。交差乗算した多項式だけや分母の絶対値へ置き換えない。',
  'U、v、w、Vはejpqを通じて直前の式と同じ現在の量を参照する。U/wは同じ点のK/kでの非負ノルム、vは両系の実相対速度、Vは同じ光速である。ejpaを共有し、点・両系・対応軸・全期間・座標微分の既存の取得規則を外していない。',
  '表示式は独立した無条件の主張ではなく、直前のwも正の縦軸方向という条件から得る帰結としてejpsに含まれる。ejpuが著者・論説・第五節のその提示を帰属し、対称性の評価から条件とコロン、表示式への流れを保つ。',
  '式自体は有効な実数、正のV、非零分母を要求し、符号付き入力と結果を許す。正方向の物理的な適用条件ejppとは分ける。式の零入力での成立を零の方向へ転用せず、逆方向の速さを正方向成分に代入しない。点の光速未満はここへ加えない。',
  '既存s3g/s3jの実切断の加算・積・正のVによる二乗除算・符号付き逆数を保持する。現在の三量の取得と同方向条件を合成して接続し、数式全体に固有の原始述語は増やしていない。旧数式の本体と意味規約は変更していない。',
  '正方向、逆方向、負の結果、相殺、零入力、零分母、負分母、光速境界と範囲外の数値例を式単独で検査し、方向条件を別に対照した。同じ現在量の差し替えと、偽の前提からの含意と実際の帰結も区別した。代数的証拠の適用条件を保持し、普遍的な実数・物理導出の証明とはしない。',
  '直前の同方向条件とコロン、表示式全体と句点、次の光速未満の結果への移行まで通読した。明示した正方向の条件と符号付き式の読みの下で、数式と条件付きの提示を欠落なく記述したと判断する。後続の光速に関する論証は別の未完範囲として残す。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_velocity_axial_claim.py','tests/test_velocity_axial_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[];selections=([136,137,138],[138])
    symbols=(['ejpl','ejpm','ejpn','ejpo','ejpp','ejpq','ejps','ejpu','ejpa','s3a','s3b','s2z','s3i','s3g'],['ejpp','ejpq','ejps','ejpu','ejpa','s3g','s3j','s3i','ejoi','ejoj','ejow'])
    for i,s in enumerate(source_record()['segments']):
        assert len(REASONS[i])==len(REQUIREMENTS) and all(n in catalog.entries for n in symbols[i])
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selections[i]),source_order_statements=selections[i],clauses=[dict(range=s['range'],text=s['text'],definitions=symbols[i],reason=REASONS[i][1])],interpretation=LIMITS,limits=['非負二入力の数式上の対称性、同じ性質への注目価値、同じ正方向への非零運動という明示した読みの下でのアシスタントの通読判断。独立査読・全可能解釈の包含・意味同値の自動証明ではない。','式を得るという著者の帰結提示を記述し、その普遍的な物理的真理や導出の健全性を認定しない。','u0143以降、u0147に残る旧前提への接続、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='symmetry_appraisal_and_directed_axial_case_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=6,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},general_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
