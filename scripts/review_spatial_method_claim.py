"""Record complete readings of the spatial method and the two ray equations."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_spatial_method_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_spatial_method_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/spatial-method-claim-v1.json'
REVIEWS=tuple(f'data/einstein-spatial-method-u{n:04d}-review-v1.json' for n in (65,66,67,68))
CLAUSES=(
 (
  ('Mit Hilfe dieses Resultates ist es leicht, ',['smn','ei5g','ei5i','s2w','s2x','s2y'],'同じ先行τの結果を使う計算を、同じ有限手順列の非負負担と文脈基準による容易さとして著者へ帰属する。'),
  ('die Größen [M0118] zu ermitteln, ',['ei5b','ei5c','eiy4','ei5j'],'ξ,η,ζの三空間成分を求める目標を、既知の同じτを残した現在の四座標の方程式課題へ接続する。'),
  ('indem man durch Gleichungen ausdrückt, daß sich das Licht ',['ei5f','ei5h','ei5i','ei43','eifw','sax'],'同じ計算手順の途中で、現在の測定と時刻規約に結ぶ光の経路長=V×経過時間の等式を用いる。'),
  ('(wie das Prinzip der Konstanz der Lichtgeschwindigkeit in Verbindung mit dem Relativitätsprinzip verlangt) ',['ei5d','ei5k','eion','eios','zc'],'同じ二原理の結合による要請という挿入説明を、著者の帰結として保持する。'),
  ('auch im bewegten System gemessen mit der Geschwindigkeit [M0119] fortpflanzt. ',['ei5e','ei43','ei42'],'同じkで測っても同じVである全区間の法則を保持する。光源の運動への独立性と同系の局所時計を用いる。'),
  ('Für einen zur Zeit [M0120] in Richtung der wachsenden [M0121] ausgesandten Lichtstrahl gilt:',['ei5l','ei5m','ei5a','ei46','ei47','snr'],'τ=0に正のξ方向へ放出する同じ光線の条件と、次の式が成り立つという提示を保持する。原点放出は直前と式に合わせた明示的な読みとする。'),
 ),
 (('[M0122],',['snr','sng','ei5m','ei5t'],'同じ光線条件の下で同じkの到達出来事のξ=Vτを示し、コンマに続く別表示へつなぐ。'),),
 (('oder',['ei5n','zd3','snr','sns'],'同じ条件の下で後の式を同値な別表示として提示する。排他的な選択ではない。'),),
 (('[M0123].',['sns','snh','smh','snf','ei5n','ei5v'],'同じτの式をξ=Vτへ代入したξ=aV(t−v*x′/(V²−v²))を保持する。同じa=φ(v)、V,v,x′,tを用いる。'),),
)
REASONS=(
 (
  '固定u0065全体とM0118–M0121を原刊899頁へ照合した。先行τの式・原点規約、二つの後続表示式まで含めて読んだ。',
  '先行結果の利用、容易さ、三量を求めること、その手段として光を等式で表すこと、二原理の要請、kで測るV、τ=0・正のξ方向の放出、後続式への導入を保持した。',
  'Resultatはsmnの同じτ式。三成分は同じkのyn/yo/yp、課題は同じzdb/eiy4、方法と出力候補は同じ段階に結ぶ。光線の始終出来事・二系・全軌道・時計・Vとφ(v)も共通に保つ。',
  '容易さはei5jの著者評価、二原理による要請はei5kの帰結、光線の式はei5mの条件付き帰結である。三主張を同じ論説・第三節へ本文順に帰属する。',
  'leichtは文脈上低負担な計算、manはこの議論で方法を使う主体を著者に代表させる読みとする。全読者の能力や実行済みを補わない。原点放出は時刻条件だけの帰結でなく前後の表示を合わせた規約と明示する。',
  '容易を旧zf2だけで代用せず、既存s2w/s2x/s2yによる同じ有限手順列と非負負担へ接続した。目標は候補三成分と既知τが現在のeiy4を満たすこと。計算手順・規則・評価尺度は公開済みの文脈入力であり、方法名そのものを意味説明にしない。',
  '原刊画像・固定原文とMathML、四式の生成、手順接続・同じ負担・参照の対照検査、固定済みの全光区間と原点光線の証拠を用いた。著者の評価の真理、規則の健全性、一般物理的導出を有限検査が証明したとはしない。',
  '二文と括弧書き、導入コロンを前後とともに再読した。採用した計算の容易さ・主体・原点放出の読みの下で、関係・程度・範囲・参照・方法・帰属に未処理の欠落はないと判断する。',
 ),
 (
  '固定u0066の表示式M0122とコンマを原刊899頁へ照合した。式を除くコンマ一文字を本文集計に含める。',
  'ξとVτの等号と乗法を保つ。先行するτ=0の正方向光線を条件にし、次の式とoderに続ける。',
  'ξとτは同じ光線上の同じ到達出来事のk座標。Vは二原理で同じkへ適用した値であり、Kに対する原点の相対速度と混ぜない。',
  'ei5mは同じ光線条件ei5lから式snrへの著者の帰結を述べる。ei5tは同じ著者・論説へ帰属し、二原理の挿入説明に続ける。',
  '先行する零点規約と式に合わせた原点放出の読みを採る。光線外の全出来事への量化や、両系の時刻の同一性を加えない。',
  'sng/snrの実切断による値と積、現在の同じ二系記録ei5a、全軌道ei47を再利用する。数式の画像又は未説明の記号だけにしない。',
  '原刊と固定MathML、既存の同じ出来事の数値代入・全軌道結合の証拠、今回の条件と引用の対照検査を根拠にする。一般の光の伝播の実証とは区別する。',
  '先行する光線の設定から式とコンマ、oderと後続式まで再読した。同じ原点光線という読みの下で、式の全要素と提示の役割を保持したと判断する。',
 ),
 (
  '固定u0067全4文字oderを原刊899頁の前後の二式へ照合した。',
  '先のξ=Vτと、同じτ式を入れた次の表示の二項を保持する。ここでは同じ条件での別の書き方を導く接続として読む。',
  '両式は同じ光線・到達出来事・V・τへ結び、後の式だけ異なるφ(v)や原点を用いることを許さない。',
  'zd3は同じ著者が指定前提の下で二内容を等価な書換えとして提示する関係。ei5n/ei5vで同じ論説と順序へ帰属する。',
  '排他的な二択、一方だけの成立、無条件の同値にはしない。先行τの式を代入するという前後の文脈を保持する。',
  '既存の型付き内容引用とzd3で条件・第一式・第二式を別引数として保つ。接続語専用の未説明な新規演算子は追加しない。',
  '原刊での二式間の配置と前後の式、同じ前提・二内容の順序を取り違えた対照例を根拠にする。代数的導出の自動証明とはしない。',
  '前後の二式を含めて再読し、同じ条件の別表示という採用解釈の下で、接続の両項と提示の関係を欠落なく保持したと判断する。',
 ),
 (
  '固定u0068の表示式M0123と句点を原刊899頁へ照合した。固定MathMLの分数とV,vの二乗、x′を確認した。',
  'ξ=aV(t−v*x′/(V²−v²))の等号、aV、括弧、負号、分母の差と二乗、x′を保持する。',
  'aは先行する同じφ(v)、τは同じzd4、x′は同じKのx−vtであり、tとξを同じ出来事から取る。別の係数や別の座標記録へ交換しない。',
  'ei5nは同じ光線条件の下でsnrをsnsへ書き換える著者の提示。ei5vは同じ著者・論説・第三節で、先の式に続く本文順序を保持する。',
  'aを1や最終決定値へ固定せず、全空間の変換をこの一光線の式だけから決定しない。後続のV−vと時刻消去はまだこの式へ入れない。',
  'snh/smhは同じ実切断による積・差・商を用い、0≤v<Vの分母の条件を保つ。V*smhの積は同じaVと括弧に対応する。未説明の式名や画像引用にはしない。',
  '原刊と固定MathML、既存のτ・ξ・K座標を別々に変更する数値対照と今回の引用・条件の結合検査を用いた。全実数体や物理的導出の証明にはしない。',
  '先行時間式、光線の設定、ξ=Vτ、oder、この式と句点を再読した。明示した同じ原点光線と先行τの読みの下で式と文脈の欠落はないと判断する。',
 ),
)

@lru_cache(None)
def records():
    source=source_record();catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_spatial_method_claim.py','tests/test_spatial_method_claim_review.py'}
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
        indices=[INDEX,INDEX+1,INDEX+2] if i==0 else [INDEX+2] if i==1 else [INDEX+2,INDEX+3]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['明示した低負担計算・主体・原点放出の読みの下でのアシスタントの通読判断。独立査読、計算規則の健全性、一般の実数体・物理的導出や同義性の自動証明ではない。','u0069以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='spatial_method_and_two_ray_equations_whole_units_reviewed',document=FULL,source_units={s['unit']:s['source_nonblank_characters'] for s in source_record()['segments']},reviewed_math_elements=6,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
