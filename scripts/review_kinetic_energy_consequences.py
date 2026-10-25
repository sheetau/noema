"""Record complete readings of the energy boundary and material extension."""
from functools import lru_cache
from pathlib import Path
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
ROOT=Path(__file__).resolve().parents[1]
def read(path):return (ROOT/path).read_text(encoding='utf-8')
FULL='examples/v014/einstein-kinetic-energy-consequences.noema';CORE='examples/v014/kinetic-energy-consequences-core.noema'
BASIS='data/kinetic-energy-consequences-basis-v1.json';ANNOTATIONS='data/kinetic-energy-consequences-identifiers-v1.json'
SOURCE='data/einstein-kinetic-energy-consequences-reading-v1.json';REPORT='reports/kinetic-energy-consequences-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';DOC='docs/kinetic-energy-consequences-v1.md'
REVIEWS=['data/einstein-kinetic-energy-consequences-u0263-review-v1.json','data/einstein-kinetic-energy-consequences-u0264-review-v1.json']
CLAUSES=(
 (
  ('[M0428] wird also für [M0429] unendlich groß. ',['epq','epr','eps','ept','epu','epv','epw','epx','ep3','ep7','ekjt','serc','zc','uh'],'同じ電子・K・低速質量・光速度・仕事単位を背景にした有限の速度と運動エネルギーの関係の、光速への下側発散を述べる。全正近傍の非空性と、全ての有限上限に対する十分近い全出力の超過を保持する。alsoは先行の最右辺表現への帰結として提示する。'),
  ('Überlichtgeschwindigkeiten haben ',['epr','epy','epz','ep4','eisoe'],'考察中の同じ点状物体の、同じ理論が許す物理状況での実運動を対象にする。三方向の速さをノルムで扱い、運動の実現条件に光速未満や有限betaを入れない。'),
  ('— wie bei unseren früheren Resultaten — ',['ep2','eqg','ejht','eis3l','eiswm','eisa5'],'同じ著者の先行運動学の適用留保・上限の予告との同様性を、超光速の物理的排除という観点で主節へ挿入する。唯一の参照先、同義性、論理的導出又は予告の証明完了としない。'),
  ('keine Existenzmöglichkeit.', ['epy','epz','ep4','eqa','eqb','eqc','uh'],'全てのVを厳密に超える有限の速さについて、同じ理論が許すいずれの状況にも実現がないと述べる。許容状況と有限のエネルギー事例の非空性を保ち、発散そのものから自動推論する規則やv=Vの追加否定を置かない。同じ著者への全文帰属を閉じる。'),
 ),
 (
  ('Auch dieser Ausdruck für die kinetische Energie muß ',['ep5','ep6','ep7','eqd','eisij','eiswm','uh'],'先行の質量結果と同様に、直前の最右辺の運動エネルギー表現も適用すべきことを提示する。中間積分のμ欠落を修正せず、mußを推論上の必要性として読む。'),
  ('dem oben angeführten Argument zufolge ',['eoi','eoc','eoh','eqd','eiswm','zc'],'上のu0260の、同じ物質点に任意に小さい電荷を加えられるという可能性を理由として参照する。可能性からの数学的証明、実際の付加、付加後の質量の厳密不変へ替えない。'),
  ('ebenso für ponderable Massen gelten.', ['eoc','epr','eps','ep5','ep6','setf','eiszt','eiszw','eqd','eqe','eqf'],'同じ正の低速慣性質量を持つ点状物体の全適格な光速未満の事例へ、実速度ノルム・出来事・運動エネルギー・正の整合単位を結んで同じ式を適用する。帯電又は中性という制限を加えず、著者の主張・添加・理由・同じ論説への帰属を保つ。'),
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);source=json.loads(read(SOURCE));basis=json.loads(read(BASIS))
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,'scripts/review_kinetic_energy_consequences.py','tests/test_kinetic_energy_consequences_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for path in (SOURCE,REPORT):
        e=json.loads(read(path));validate_hashes(ROOT,e['source_sha256']);merge_pins(pins,e['source_sha256'])
    output=[]
    for i,s in enumerate(source['units']):
        selection=[430+i];offset=0;clauses=[]
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text,offset
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,statements=selection,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        reasons=(
         ('固定u0263の二文全体を原刊920頁と照合した。W、v=V、also、unendlich groß、Überlichtgeschwindigkeiten、二つのダッシュ、wie、同じ著者の先行結果、keine Existenzmöglichkeitを保持する。' if i==0 else '固定u0264全文を原刊920頁で、エネルギーの境界段落と後続の実験的性質の列挙の間に照合した。Auch、dieser Ausdruck、kinetische Energie、muß、上のArgument、zufolge、ebenso、ponderable Massen、geltenを保持する。'),
         ('発散は同じ関係の非空性・全正近傍の点の存在・上限ごとに選ぶ近傍・全出力の超過から合成する。可能性は同じ理論の全許容状況での校正実履歴と三速度の実現、否定は全超光速度についてのその不存在とする。二文を同一の推論規則へ潰さない。' if i==0 else '正の低速慣性質量を持つ点状物体の分類eoc、全適格な事例、同じ実速度ノルム・量の帰属・単位換算setfを結ぶ。先行表現への照応と、電荷付加の可能性からの著者の理由付け、質量結果への添加を分けて合成する。'),
         '対象・系・出来事・三速度・低速質量・光速度・仕事単位を共有する。発散では質量と全単位尺度を背景に固定し、履歴と代替状況は各点で一組として変えられる。可能性の対象を別物体又は別系へ交換しない。物質点への適用では各事例の同じ引数を前件と結論へ渡す。',
         ('uhで二つの著者主張を分け、zcでalsoの直前表現への理由を保持する。eiswmで直前の式と先行運動学へ照応し、eis3lで指定観点での同様性、eisa5でダッシュの挿入を保持する。著者・論説・本文順序をeir3/ueへ結び、引用内容を実行しない。' if i==0 else 'uhは表現の適用、eisijは先行の質量結果への添加、eiswmは同じ最右辺と上の電荷付加の議論への照応、zcはその理由から適用への推論である。mußを規範命令や処理系による証明へ替えず、同じ著者・論説と本文順序を保持する。'),
         'v=Vは有限点からの左境界と読む。超光速度の範囲は考察中の正の低速質量を持つ点状物体で、光・位相速度・現代の別種の対象へ拡張しない。前の運動学への照応は明示読解で、唯一の歴史的参照先とはしない。物質点には電荷又は中性を前提にせず、付加による質量の厳密不変を足さない。原刊中間積分のμ欠落は保持する。',
         '追加した基本関係は、二内容を指定した観点で同様の結果として提示する一般的な比較である。三次元ノルム、全称と存在、非空性、実数の境界、実軌道・物理的許容状況・エネルギーと仕事単位の対応は既存概念から合成する。未説明の速度ラベルや一文全体を原始記号へ埋め込む方法は採らない。',
         '数値検査は三方向・負の枝・正の単位尺度の変更を扱う。役割検査は同じ所有者・出来事・単位・代替状況・各履歴束縛と全称適用、光速ちょうどと超光速、有限beta又はエネルギーの先取りの不存在、引用の非実行を扱う。既存の非空発散・全出力条件・近傍証拠と単位換算を固定証拠として再利用し、全実数の量化は有限評価を拒否する。',
         ('u0263全文を直前のエネルギー表現と直後の物質点への適用の間へ戻して再読した。発散、そこへのalso、別に述べる物理的な存在不可能性、先行結果との挿入的比較、対象と量の同一性が揃い、明示した境界・物理範囲の読みで全文を記述できたと判断する。' if i==0 else 'u0264全文をu0260の物質点の議論・直前のエネルギー式・後続の実験的性質の導入と合わせて再読した。どの表現をどの範囲へ適用するか、同じ量と単位、先行理由、auch/ebenso/mußの提示が揃い、明示した読みで全文を記述できたと判断する。')+'これはアシスタントの意味判断であり、独立査読、物理的真理又は同義性の自動証明ではない。',
        )
        assert len(reasons)==len(REQUIREMENTS)
        output.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=basis['limitations'],limits=['明示した解釈の下でのアシスタントによる全文判断。独立査読、物理的真理又は原文同義性の自動証明ではない。','後続u0265以降の実験的関係は今回含めない。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,reasons)],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return output

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    rows=records();catalog=load_catalog(ROOT,BASIS);inventory=json.loads(read(INVENTORY));active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);pins=dict(rows[0]['source_sha256'])
    for path,r in zip(REVIEWS,rows):
        assert json.loads(read(path))==r;validate_review(ROOT,path,'einstein-1905',active,catalog,inventory);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='energy_boundary_and_material_extension_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in rows},reviewed_math_elements=2,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
