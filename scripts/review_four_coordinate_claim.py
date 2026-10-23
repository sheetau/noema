"""Whole readings of the four-coordinate rewrite and its beta specification."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_four_coordinate_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_four_coordinate_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/four-coordinate-claim-v1.json'
REVIEWS=tuple(f'data/einstein-four-coordinate-u{n:04d}-review-v1.json' for n in range(81,85))
CLAUSES=(
 (
  ('Setzen wir für [M0134] seinen Wert ein, ',['ei7e','ei7f','zd3','sin','ei67'],'同じx′の値x−vtを先行する四成分の表示へ戻す著者の計算提示として読む。'),
  ('so erhalten wir:',['ei7f','ei7c','ei7h'],'その書換えによって後続の四座標式を得るという帰結を保持する。'),
 ),
 (('[M0135]',['ei7a','ei7c','spg','spb','spc','spd','spe','spf','ei7h'],'τ=φ(v)β(t−vx/V²)、ξ=φ(v)β(x−vt)、η=φ(v)y、ζ=φ(v)zの全四式を同じ現在対応へ結ぶ。'),),
 (('wobei',['ei7i','ei7k','spq'],'直前の四式で使ったβを次の表示で指定する補足の接続として読む。'),),
 (('[M0136]',['spq','spa','soy','soz','ei7i','ei7k'],'同じV,vについてβ=1/√(1−(v/V)²)を指定する。'),),
)
REASONS=(
 (
  '固定u0081全体とM0134のx′を原刊900頁へ照合した。前のη・ζの結果と、次の四式・βまでを続けて読んだ。',
  'x′にその値を入れるという代入、先行値への照応、そうすれば得られるという帰結と後続の四式へのコロンを保持する。',
  'x′は同じK四入力のx−v*tであり、先行するaの式と新しい四式で同じV,vと四座標を使う。ei7bとei7cは現在の全eiyz/eiy2範囲の対応を扱う。',
  'ei7fのzd3は同じ前提・先行表示・結果の書換え提示であり、ei7hは同じ著者・論説・第三節への帰属とζの結果からの順序を保持する。',
  '全空間への拡張を単独の光線から自動的に証明したとはしない。ei66の同じアフィン行・原点・三光線の追加十分条件はzflの解釈注記として著者発話の外側に置く。',
  '実切断の差sinと先行数式、型付きの四式列、既存zd3とzflを組み合わせる。代入を単なる自然言語ラベルにせず、未説明の新原始語も加えない。',
  '原刊画像・固定原文・現在の定義を通読し、光線外の数値例、現行全対応の対照検査、既存の有理再表示・較正補題を補助証拠とした。一般実数体や物理的導出・意味同値の自動証明ではない。',
  '先行の横二軸の結果から代入の文、四式、βまで再読した。明示した全測定域への拡張と計算提示の読みの下で、文全体の参照・操作・帰結を欠落なく保持したと判断する。',
 ),
 (
  '固定u0082のM0135全体を原刊900頁の四行へ照合した。順はτ,ξ,η,ζで、各行末のコンマは固定MathMLの内部に含まれる。',
  'τとξの右辺の共通因子φ(v)β、各括弧、ηとζの右辺のφ(v)だけの因子、等号、積、差、V²による商を全て保持する。',
  '四式は同じ出来事のK/k四記録、同じV,vと新φを共有する。新φ=spcは先のa=zeqと同じ値ではなく、同じ速度でφ=aβと結ぶ。',
  'ei7cは四式の現在の全範囲での過不足ない対応と前段の方程式課題への答えを記述し、ei7f/ei7hは先行表示から得る著者の書換え結果として帰属する。',
  'aと新φの再表示を明示し、φ=1やa=1を先取りしない。y,z式へβを重ねず、時間と位置の役割も交換しない。未測定の全実数四組が現実に存在するとは加えない。',
  '既存spb/spcの速度関数の再表示、spd/spe/spfの実切断の四式を再利用し、非空の式列ei7aと現在のeiy4/ei7lへ結ぶ。対応の片方向だけで済ませない。',
  '原刊の四行とMathMLの構造、光線外の入力と四出力・係数の対照、同値な別記録・余分な解・対応の欠落の検査、既存の有理再表示補題を用いた。有限切断の指紋と一般の切断同値は区別する。',
  '代入の一文から四行全体、βの定義と後続の未知関数の説明へのつながりを読んだ。明示したφの参照変更と全測定域の読みの下で四式全体を欠落なく記述したと判断する。',
 ),
 (
  '固定u0083のwobei全体を原刊900頁へ照合した。四式の直後、βの表示の直前に置かれている。',
  'この四式で用いるβを後続の式で補足する接続として保持する。単語だけを独立した物理主張にしない。',
  '同じ四式のβを指し、spq/spaのV,vは直前の四式と同じtc/zb7である。別の速度比や別の式へ接続しない。',
  'ei7i/ei7kが同じ著者によるβの指定を直前のzfjの四式に続ける。選択は四式とβの両主張を含み、補足の参照を保つ。',
  'βを仮定の追加や測定値の報告に変えず、この表示での記号規約として読む。後続u0085の未知関数・加法定数の内容をこの語に混ぜない。',
  '既存uhによる内容の提示、spqの同じβ条件、同じ著者帰属とueの順序を組み合わせる。',
  '原刊での配置と固定原文、同じ著者・前節点・引用内容の対照検査を用いた。検査の成功から接続語の同義性を自動証明したとはしない。',
  '四行からwobei、βの式までを一続きに再読した。記号規約の補足という採用解釈の下で、その参照と提示上の役割を保持したと判断する。',
 ),
 (
  '固定u0084のM0136全体を原刊900頁へ照合した。分子1、分母の平方根、内部の1−(v/V)²、βの等号を確認した。',
  'β=1/√(1−(v/V)²)の商・平方・差・平方根・逆数を保持する。同じ領域で正のV/√(V²−v²)にも一致させる。',
  'Vとvは同じ運動設定と光速であり、βは直前のτ/ξとφ=aβに使った同じ値。現代に使われるβ=v/Vという別慣習を代入しない。',
  'ei7i/ei7kにより、直前の四式の記号を指定する著者の補足として提示する。係数を新たに実測したという報告にしない。',
  '正の枝と0≤v<Vの定義域を保持し、零分母や負の平方根の枝を許さない。現在の物理設定の正のvは保ち、数値核のv=0比較例を本文の設定変更にしない。',
  '既存sozは原文の逆平方根表示、soyは正の横成分による表示、spa/spqは両表示の一致と定義域を実切断の算術で構成する。',
  '原刊とMathML、v/Vや負の値との対照、異なる有理速度と既存のβ二乗の代数補題を用いた。一般平方根や実数体の法則の自動証明とはしない。',
  '四式・wobei・β全体を再読し、次のφが当面未知という説明を後続単位へ残した。この段階の定義と参照を欠落なく保持したと判断する。',
 ),
)

@lru_cache(None)
def records():
    source=source_record();catalog=load_catalog(ROOT,BASIS)
    paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_four_coordinate_claim.py','tests/test_four_coordinate_claim_review.py'}
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
        indices=[INDEX] if i<2 else [INDEX,INDEX+1]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,indices),source_order_statements=indices,clauses=clauses,interpretation=LIMITS,limits=['同じアフィン式による全測定域への拡張とφ=aβの再表示を明示した読みの下でのアシスタントの通読判断。独立査読や一般物理的導出・同義性の自動証明ではない。','u0085以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='four_coordinate_rewrite_and_beta_whole_units_reviewed',document=FULL,source_units={s['unit']:s['source_nonblank_characters'] for s in source_record()['segments']},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
