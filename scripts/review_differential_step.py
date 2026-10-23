"""Read the infinitesimal inference and its rearranged equation as four whole units."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_differential_step import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_differential_step import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

REPORT='reports/differential-step-v1.json'
REVIEWS=tuple(f'data/einstein-differential-step-u{n:04d}-review-v1.json' for n in (54,55,56,57))
CLAUSES=(
 (
  ('Hieraus folgt, ',['ei2w','ei2x','ei2y','zc'],'同じ中点式と微分への移行の条件から後続式が従うという著者の提示を保持する。'),
  ('wenn man [M0102] unendlich klein wählt:',['ei2v','skc','sjv','sjw'],'x′を正側から零へ近づける極限として読み、同じ候補・時刻の正近傍全体と同じ点の二偏微分へ結ぶ。'),
 ),
 (('[M0103]',['sjx','skf','ei2y'],'二逆数の和の半分に同じt偏微分を掛けた左辺と、同じx′偏微分とt偏微分の1/(V-v)倍を加えた右辺を等値にする。'),),
 (('oder',['ei23','zd3'],'同じ前提の下で最初の式を後続式へ同値な形で書き換える提示を保持する。'),),
 (('[M0104]',['sjy','skg','ei23'],'同じx′偏微分とv/(V²-v²)倍のt偏微分の和が零に等しい整理後の式を保持する。'),),
)
REASONS=(
 (
  '固定u0054全54文字・40本文文字とM0102を原刊899頁の冒頭へ照合した。Hieraus folgtとwenn以下の全条件を二つの連続範囲で保持し、直後の表示式へ結ぶ。',
  '同じ前の中点式から従うこと、x′を無限小に選ぶ条件、後続の二偏微分式という関係を保持する。正近傍全体の中点条件と同じ点での全微分可能性・二偏微分を明示する。',
  '現在のei2pから同じ候補zd4、V、v、実際の出発K時刻を引き継ぐ。二偏微分値を同じ評価点(0,0,0,t)のsjv/sjwへ結び、旧sjlの時計・座標条件へ戻さない。',
  '著者が同じ第三節でei2xの下にskfが従うと述べるzcを使う。本文順序を引数展開から結び、条件の採用と結論の帰属を無条件の実在や処理系の導出証明へ変えない。',
  '一回の試行距離の成功から全近傍を得ず、零変位の恒等式で済ませない。tを零へ固定せず、独立な偏微分だけから全微分可能とせず、任意の出発点への一般化を加えない。',
  '無限小は正の変位を零へ近づける通常の実数極限と読む。先行する線形性と整合する十分な正則性を明示した解釈であり、原文がε–δ条件をそのまま述べたとはしない。新たな無限小数や原始語を作らない。',
  '旧極限・逆数・有理代数の証拠を保存し、現在の接続と近傍範囲を局所対照する。全実数の極限・近傍の有限評価は拒否し、一般連鎖律や局所延長の自動証明を主張しない。',
  '前頁の同じ中点式、最初の偏微分式、oderによる整理と次の一般化の文を含め通読した。明示した正側極限と正則性の読みの下で、条件・参照・帰結・提示を欠落なく記述したと判断する。',
 ),
 (
  '固定u0055全7文字のM0103について、原刊899頁とMathMLの全分数を照合した。半分、V-vとV+v、二種類の偏微分、加号と等号を保持する。本文文字は零として数える。',
  '½(1/(V-v)+1/(V+v))*τt=τx′+τt/(V-v)の両辺を保持する。二逆数の和、半分の作用範囲、同じτtの両出現と同じτx′を省略しない。',
  'skfのzd6とzd7はei2vのsjv/sjwにより同じτ候補の同じ評価点の偏微分である。光速と速度も現在の光往復の同じ値であり、単なる任意の四数の式へ替えない。',
  'u0054のHieraus folgtが導く結論として同じ著者主張ei22を共有する。式だけを独立した無条件の法則やτの定義採用にしない。',
  '二偏微分の交換、二分母の符号交換、半分の省略を排除する。具体的τ解や全位置での偏微分条件を加えず、数値例の成功から微分可能性を推定しない。',
  '既存sjxとskfを変更せず、切断の妥当性、正逆数、和、積、尺度倍、数値等値を再利用する。0<v<Vを引き継ぎ、分母零への形式的な割算を認めない。',
  '保存した数式木、原刊、旧有理代数、現在の正確な有理切断と切片の対照が根拠である。関数指紋は引数を区別する検査に限り、極限や一般連鎖律の証明ではない。',
  '同じ条件付き推論の結論として式全体を再読した。明示した極限の読みの下で、全係数・二偏微分・同じ参照と帰結の役割を欠落なく記述したと判断する。',
 ),
 (
  '固定u0056の全4文字oderを原刊899頁で前後の二式の間へ照合した。単独の短語であっても原文単位全体として扱う。',
  '直前の式を直後の式へ同値な形で書き換えるという関係を保持する。排他的選択、いずれかの成立だけ、別の物理仮説の導入とは読まない。',
  'zd3へ同じ前提ei2x、書換え前skf、書換え後skgを順序通り渡す。両式は同じV,v,zd6,zd7を共有し、別の試行や別の偏微分値へ替えない。',
  '著者が同じ第三節で同値な式として提示する内容ei23を、同じ論説の主張ei25へ帰属する。直前の微分による結論からの本文順序を保持する。',
  '単なる論理和や無条件の意味同義性へ変えず、前提を省略しない。処理系が全実数上で整理を証明したという追加主張もしない。',
  '既存の条件付き書換えの帰属zd3を合成して使い、この語だけの新規原始関係は作らない。引用された前後内容を実行して真理値に置き換えない。',
  '書換え前後、前提、著者、第三節と文脈の各引数を対照検査し、旧代数の証拠を保存する。原文の読解と有限の帰属検査を区別する。',
  '最初の式と整理後の式を一緒に再読し、ここでのoderを同じ条件の下の書換えと判断した。その提示の向きと範囲を欠落なく記述したと判断する。',
 ),
 (
  '固定u0057全7文字のM0104を原刊899頁とMathMLへ照合した。分子v、分母V²-v²、二偏微分、加号、等号と零を保持する。本文文字は零である。',
  'τx′+v/(V²-v²)*τt=0の全項を保持する。係数vの省略、二乗の欠落、差を和へ変えること、符号の反転を許さない。',
  '同じzd6とzd7をsjwの同じ切片微分とsjvの一次近似係数へ結ぶ。Vとvも同じ光往復から引き継ぎ、二式で別の値を選ばない。',
  'u0056のoderによる書換えの結果として同じ著者主張ei25を共有する。最初の微分式と同じ前提ei2xを保持し、別の無条件の方程式にしない。',
  '具体的τ関数をこの式から得たとはせず、原点以外の全位置への拡張やy,z偏微分の零を先取りしない。v=Vで定義されない商を有効としない。',
  '既存sjyとskgの実数切断の算術を再利用する。偏微分という意味は同じ関数と評価点の差商極限で与え、記号名の説明だけに依存しない。',
  '原刊と固定数式、旧多項式の整理、現在の同じ偏微分への接続と有理切断対照を保存する。一般実数法則や意味同値の自動証明を主張しない。',
  '前の式からの書換えと次の任意の出発点への議論まで通読した。明示した局所的な極限の読みの下で、式全体と著者の提示を欠落なく記述したと判断する。',
 ),
)

@lru_cache(None)
def records():
    source=source_record();catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,*PRIORS,*DEPENDENCIES,'scripts/review_differential_step.py','tests/test_differential_step_review.py'}
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
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        indices=[INDEX+i//2]
        results.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['明示した局所正則性と正側極限の読みの下で通読したアシスタントの判断。独立査読、全実数上の連鎖律や同義性の自動証明ではない。','u0058以降の任意の出発点への一般化、具体的なτ変換式、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='infinitesimal_inference_and_rearrangement_four_whole_units_reviewed',document=FULL,source_units={'einstein-1905:u0054':40,'einstein-1905:u0055':0,'einstein-1905:u0056':4,'einstein-1905:u0057':0},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},general_real_chain_rule_proved=False,concrete_tau_transformation_derived=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
