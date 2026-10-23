"""Read the transverse analogy sentence and both displayed zero derivatives."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_transverse_derivative_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_transverse_derivative_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/transverse-derivative-claim-v1.json'
REVIEWS=tuple(f'data/einstein-transverse-derivative-u{n:04d}-review-v1.json' for n in (59,60,61))
CLAUSES=(
 (
  ('Eine analoge Überlegung — auf die [M0106]- und [M0107]-Achse angewandt — liefert, ',['ei4d','zep','skw','skx'],'同じ縦方向の先行推論を二横軸へ適用した類似議論から二式を得るという提示を保持する。H/Zは運動系のη/ζ方向の軸表記として読み、y/zへの既出の平行関係を使う。'),
  ('wenn man beachtet, daß sich das Licht längs dieser Achsen ',['ei4a','zei','ei34','ei35'],'横軸に沿う光の伝播条件に注意して推論することを保持する。同じ光・三出来事・全軌道と現在の時計への接続を条件に含める。'),
  ('vom ruhenden System aus betrachtet stets mit der Geschwindigkeit [M0108] fortpflanzt:',['ei35','ei36','skz','ei3z'],'Kから見た横成分√(V²−v²)を全試行範囲へ課す。全光速Vと成分速度を区別し、二標本だけへ狭めず、後続の二式へ結ぶ。'),
 ),
 (('[M0109]',['slv','slm','slk','sli','sjs','skw'],'同じτのy切片の差商極限が零である式を、同じ類似推論の第一の結論として保持する。'),),
 (('[M0110]',['slv','slm','slk','sli','sjs','skx'],'同じτのz切片の差商極限が零である式を、同じ類似推論の第二の結論として保持する。'),),
)
REASONS=(
 (
  '固定u0059全225文字・172本文文字とM0106–M0108を原刊899頁へ照合した。文全体を隙間なく三範囲で保持し、直前の全空間一般化と後続の二つの表示式を合わせて読んだ。',
  '二横軸へ適用する類似議論、伝播条件への注意、静止系からの視点、常に同じ横成分速度で進むことと後続二式への帰結を保持する。ei34/ei35は同じ出発出来事・距離・成分を現在の完全試行へ結ぶ。',
  'H/Zは同じ運動系のη/ζ方向の軸表記として読む。既出の平行性からy/zの式へ対応させ、別の第四軸を導入しない。τ・V・v・二基準系と単位を保ち、先行論法zea、同じ出発K時刻と全空間範囲を引き継ぐ。',
  'ei4aは条件への注意と内容の提示、ei4dは同じ条件と局所正則性の前提からの帰結および先行推論との類似を表す。二つの主張を同じ著者・論説・第三節へ帰属し、前文と文内の順序を保つ。',
  'Kの全光速Vを横成分wへ交換せず、光のK経路を横軸上としない。常にを成功した二標本へ限定せず、全範囲の非空な両横軸を保つ。全時刻の追加量化、具体的τ解や新しい係数をここで加えない。',
  '平方根とv²+w²=V²、軸引数交換、全空間の局所中点条件と同じ点の微分を既存定義で記述する。十分な局所正則性と正側極限を明示した先行の読みを引き継ぎ、原文がε–δ条件を逐語的に述べたとはしない。',
  '原刊と固定数式、現在の完全光軌道・時計の証拠、全試行範囲と関数切片の対照検査を用いる。平方根の一般実数法則、全経路の実現、一般連鎖律と物理的導出の自動証明は主張しない。',
  '前の全空間への一般化から二つの横偏微分の零、続く線形性の文まで通読した。明示した軸表記・成分速度・局所正則性の解釈の下で、文の全関係・参照・範囲・提示を欠落なく記述したと判断する。',
 ),
 (
  '固定u0060全7文字のM0109について、原刊899頁の第一の横偏微分式とMathMLを照合した。分子∂τ、分母∂y、等号と零を保持する。本文文字は零として数える。',
  '同じτについてx′,z,tを固定したy切片の偏微分が零であることを、sli/sjsの差商極限で保持する。単なる名前だけの微分値や局所で関数が定数という別条件に置き換えない。',
  'skwは同じ四引数τの第一・第二空間引数を交換し、指定したy評価点を第一変数の解析へ渡す。全空間値と同じ出発時刻をslmで保持し、zの式と別のτ候補を選ばない。',
  'u0059の同じ前提ei37の下で類似議論から得られる結論slvの第一成分である。二式をまとめる著者主張ei4fを共有し、独立の無条件な定義採用へ変えない。',
  'yとzやx′の偏微分を交換せず、零を原点での一つの係数だけに制限しない。二式の共有主張に第二成分があることは原文の連続した結論構造であり、第一式へ別の未出仮定を加えるものではない。',
  '既存slv/slm/slk/sli/sjsとskwを変更せず再利用する。偏微分の意味は同じ関数・評価点・固定した他の引数の差商極限で与え、固有記号の説明だけに依存しない。',
  '固定MathML・原刊・関数引数の対照を根拠とし、二次関数の中央差分が正確な検査例と一般微分を区別する。全実数の近傍と空間量化は有限評価を拒否し、標本の通過を一般証明にしない。',
  'u0059の条件付き類似推論と二式を連続して再読した。明示した前提の読みの下で、第一の式の全記号と同じτへの参照、全空間範囲、結論の役割を欠落なく記述したと判断する。',
 ),
 (
  '固定u0061全7文字のM0110を原刊899頁の第二の横偏微分式とMathMLへ照合した。分子∂τ、分母∂z、等号と零、文末の点を保持する。本文文字は零である。',
  '同じτについてx′,y,tを固定したz切片の偏微分が零であることを保持する。二つの式を論理和とせず、同じ関数と評価点で両方の偏微分が零である結論として結ぶ。',
  'skxで同じτの第一・第三空間引数を交換し、zを第一変数、yを第二、x′を第三へ正しく渡す。同じ全空間値と時刻パラメータを保持し、前のy式と値や関数を取り違えない。',
  '同じ類似推論の結論slvの第二成分としてu0059と同じ著者主張ei4fを共有する。第一式との並置と文末を保持し、後続の線形性からの具体的解をこの式へ混ぜない。',
  '横方向の二式が同時に成立する範囲を保ち、原点だけの式や有限点の一致に縮めない。τの全変数での定数性、t偏微分の零、具体的な係数aやφ(v)を加えない。',
  '既存の軸交換と偏微分・全空間量化を合成して使用する。二つの偏微分はそれぞれ同じτの異なる切片であり、未知の関数を既定の零や定数へ補わない。',
  '原刊・固定数式と同じτの切片を区別する対照例を保持する。有限の例で一般物理的導出や全実数の微分法則を証明せず、原文の意味判断と検査の範囲を分ける。',
  '類似議論を述べる一文と二つの式を再読し、後続の具体的τ式とは切り分けた。明示した解釈の下で、第二式全体と参照・範囲・結論の役割を欠落なく記述したと判断する。',
 ),
)

@lru_cache(None)
def records():
    source=source_record();catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_transverse_derivative_claim.py','tests/test_transverse_derivative_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        indices=[INDEX,INDEX+1] if i==0 else [INDEX+1]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['明示した軸表記・横成分速度・十分な局所正則性の読みの下でのアシスタントの通読判断。独立査読、全実数上の物理的導出や同義性の自動証明ではない。','u0062以降の具体的τ変換式と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
    return out

def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,r in zip(REVIEWS,records()):write_exact(ROOT/path,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    active=dict(document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source_inventory=INVENTORY);catalog=load_catalog(ROOT,BASIS);inv=json.loads(read(INVENTORY));pins={}
    for path,r in zip(REVIEWS,records()):
        assert json.loads(read(path))==r
        validate_review(ROOT,path,'einstein-1905',active,catalog,inv);merge_pins(pins,r['source_sha256']);pins[path]=digest((ROOT/path).read_bytes())
    return dict(status='transverse_analogy_sentence_and_two_zero_partials_whole_units_reviewed',document=FULL,source_units={'einstein-1905:u0059':172,'einstein-1905:u0060':0,'einstein-1905:u0061':0},reviewed_math_elements=5,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},general_real_physical_derivation_proved=False,concrete_tau_transformation_derived=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
