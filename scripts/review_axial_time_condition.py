"""Review the hypothetical axial trial and its displayed midpoint together."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_axial_time_condition import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_axial_time_condition import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/axial-time-condition-v1.json'
REVIEWS=('data/einstein-axial-time-condition-u0049-review-v1.json','data/einstein-axial-time-condition-u0050-review-v1.json')
CLAUSES=(
 (
  ('Vom Anfangspunkt des Systems [M0092] aus ',['ei2a','zbn','zbv','qc'],'出発地点を同じkの原点へ固定し、帰着でも同じ地点・時計を使う。'),
  ('werde ein Lichtstrahl zur Zeit [M0093]',['ei2a','eiz7','ei2e','ug'],'一光線の出発を同じ原点時計のτ₀へ結び、接続法を仮想設定の採用として保持する。'),
  ('längs der [M0094]-Achse nach [M0095] gesandt ',['ei2a','ei2b','zdw','eiz5','eiz6','sin'],'既出の共通縦方向に対応する同じk原点の軸上全経路を保持し、反射地点のx′を同じ出来事のK座標からx-vtとして作る。'),
  ('und von dort zur Zeit [M0096] nach dem Koordinatenursprung reflektiert, ',['da','sde','ei2a','eiz7'],'同じ光がその反射地点でτ₁に反射し、原点へ向かう復路を保持する。反射時計と原点時計の取り違えを許さない。'),
  ('wo er zur Zeit [M0097] anlange; ',['da','sde','ei2a','eiz7'],'同じ光の帰着を同じ原点時計のτ₂へ結び、出発とは別出来事であることを保持する。'),
  ('so muß dann sein:',['ei2c','ei2d','ei2h','ei2j','zc'],'その同じ仮想設定の下で後続の中点式が必要となるという結論提示を保持する。u0050の式と同じ主張を共有する。'),
 ),
 (
  ('[M0098]',['sit','ei2d','ei2h','ei2j'],'同じ試行のτ₀とτ₂を加えた半分がτ₁に等しいという実数値の式を、u0049末尾の必要性の結論として保持する。'),
 ),
)
REASONS=(
 (
  '固定原文u0049全245文字・167本文文字とM0092–M0097を原刊898頁へ照合した。出発からso muß dann seinまでを六つの連続範囲で保持し、直後の表示式を同じ結論として参照する。',
  '同じk原点・一光線・縦軸上全経路・補助座標の反射地点・出発と反射と帰着の三読み・原点への復帰・必要性を列挙し、非退化な往復と時刻順序も保持した。',
  '試行zdqとqc–qk、原点時計zdrと反射時計zdsを現在のeiyg/eiyi/eiyjへ結ぶ。先行する同じ測定と並進・平行軸の設定、全時計の同期、全出来事の座標対応を引き継ぎ、補助座標は現在の同じK出来事組から作る。',
  '接続法を仮想設定の導入、末尾をその設定に対する必要性の提示として読む。ugとzcへの引用を同じ著者・論説・第三節・前段の目的と本文順序へ帰属し、光の実際の発射済みや無条件の式へ替えない。',
  '帰着で別の時計や別の光を使うこと、片道だけの伝播、端点だけの軸上配置、同期範囲外の試行、tをτへ代入することを許さない。原点の零固定、x′=ξ、x′の符号固定、両原点や両正方向の一致、具体的なτ変換式を追加しない。',
  '大文字Xは既出の共通縦方向と読むことを明示する。その同じk原点から出る軸へ全経路を結び、eixtの初期配置・並進・全時点平行性を受ける。x′は距離そのものではなく補助座標値であり、零や負の値だけを理由に退化としない。新たな原始関係は追加していない。',
  '旧草案と数値核・同期・測定の証拠を保存し、現在の局所表示と結合した対照検査を分けて記録する。有限例の通過は物理的な全域導出や同義性の証明ではない。全試行同期と試行所属を別々に確認し、一つの中点式の成功を同期全体へ昇格させない。',
  '前段のτを同期時計から求める課題、同じ文の結論となるu0050、後続のt引数展開を含めて通読した。明示した軸・補助座標の読みの下で、同一性、局所時刻、経路、仮想設定、必要性と順序を欠落なく記述したと判断する。',
 ),
 (
  '固定u0050全7文字の置換要素M0098について、原刊の表示式とMathMLの分子1・分母2、τの添字の順序0,2,1を照合した。本文文字は零だが数式一つを単位全体として扱う。',
  '同じτ₀とτ₂の和、その半分、同じτ₁への実数値の等値を保持する。和の項・半分の係数・反射値のいずれも省略しない。',
  '三値は同じ試行zdqのqi,qj,qkへ固定し、u0049の原点時計／反射時計／原点時計の読取りに対応する。独立の数値例や別の光往復から集めた三数へ替えない。',
  'この式はu0049のso muß dann seinが導く必要条件の結論であり、両単位で同じ主張ei2jを共有する。式の転記だけ、無条件の事実、同期規約の新たな定義採用へ置き換えない。',
  '近似比較、切断関数の個体同一性、静止系tの中点、反射時刻だけの原点変更、式だけから三出来事の時間順序や実在を推論することを加えない。具体的なτの関数形も先取りしない。',
  '既存sitをそのまま使い、実数切断の妥当性・和・有理数1/2による尺度倍・数値の等値で合成する。同期規約の等しい二差との関係は旧数値核と同じ読みであり、この式全体を新規原始語としていない。',
  '固定数式の木、原刊、旧中点代数の証拠、正確な有理切断による局所対照を保持する。逆順・一致時刻でも式だけは成立する対照を使い、式の成立と非退化な物理設定を区別する。全実数上の物理的含意の自動証明は主張しない。',
  'u0049の仮想設定と必要性、後続の同式の引数展開を含めて表示式全体を再読した。指定された三つのk時計値についての同じ条件付き結論として、係数・項・等値・提示役割を欠落なく記述したと判断する。',
 ),
)

@lru_cache(None)
def records():
    source=source_record();catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_axial_time_condition.py','tests/test_axial_time_condition_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    results=[]
    for i,s in enumerate(source['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text
            assert all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text'])
        indices=[INDEX,INDEX+1] if i==0 else [INDEX+1]
        results.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['同じ文と表示式を明示した解釈の下で通読したアシスタントの判断。独立査読、全実数上の物理的導出、同義性の自動証明ではない。','u0051以降の引数展開と具体的なτ変換式、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return results

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,record in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(record,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for path,record in zip(REVIEWS,records()):
        assert json.loads(read(path))==record
        validate_review(ROOT,path,'einstein-1905',active,catalog,inv);merge_pins(pins,record['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='axial_trial_and_midpoint_both_whole_units_reviewed',document=FULL,source_units={'einstein-1905:u0049':167,'einstein-1905:u0050':0},reviewed_math_elements=7,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},general_physical_derivation_proved=False,concrete_tau_transformation_derived=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
