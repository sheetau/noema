"""Whole-unit reading of phi=1, the final transformation and beta."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_final_transform_claim import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_final_transform_claim import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/final-transform-claim-v1.json'
REVIEWS=tuple(f'data/einstein-final-transform-u{n:04d}-review-v1.json' for n in (105,106,107,108))
CLAUSES=(
 (
  ('Aus dieser und der vorhin gefundenen Relation folgt, ',['ejea','ssk','sro','ejef'],'直前の正負値の一致と先に得た相反積1の二関係を、同じ著者の帰結の前提へ結ぶ。'),
  ('daß [M0188] sein muß, ',['ejeb','ejef','ejee','ejec'],'同じφ(v)=1でなければならないという推論を提示する。正の枝を選ぶ測定上の読みは著者の発話外に区別して記録する。'),
  ('so daß die gefundenen Transformationsgleichungen übergehen in:',['ejei','ejej','ei7c','ejeh','ejeg'],'そのφ=1によって同じ既出の変換式が次の四式へ書き換わるという帰結を、同じ全記録範囲で提示する。'),
 ),
 (('[M0189]',['ejeg','ssn','ejeh','ei7l','eiy4','ejej'],'τ,ξ,η,ζの四式を同じK/k二記録の全対応へ接続し、直前のコロンに続く書換え結果として帰属する。'),),
 (('wobei',['ejek','ejeq','ejeh','spq'],'直前の最終四式で用いた同じβを次の式で指定する補足。'),),
 (('[M0190]',['spq','spa','soy','ejek','ejeq'],'同じV,vについてβ=1/√(1−(v/V)²)の正の値を指定する。'),),
)
REASONS=(
 (
  '固定u0105の全137文字・非空白本文112文字とM0188を原刊902頁へ照合した。Aus dieserから最終四式を導入するコロンまで再読した。',
  '直前の二値の一致と先の積1をejeaへ合わせ、ejefがその二関係からejebのφ(v)=1が必要な帰結だと提示する。後半はejeiを前提とするejejで既出ei7cから最終ejehへの書換えを述べる。',
  'dieserはssk、vorhin gefundenen Relationはsroであり、どちらも同じspc・同じzb7とその符号反転を使う。gefundenen Transformationsgleichungenは同じ現在記録の既出四式ei7cを指し、新しいφ関数を導入しない。',
  'folgtとsein mußは前提からの必要な帰結という著者の推論帰属zc、so daßとübergehen inは同じ結果による式の書換えzd3として保持する。通読者や処理系が物理的正しさを保証するという発話に替えない。',
  '二関係だけでは−1も残るので、引用する前提へ正値を挿入しない。直前の正の測定長とl/φの一致から正の枝を選ぶ読みはejeeの解釈注記として発話外に置く。結論は原文通りφ(v)=1であり、φ(−v)=1を別の表示として加えない。',
  '既存の二内容ssk/sro・実切断の有効性と値同値・現在の全記録対応・引用と推論と書換えの規約を合成する。新しい原始記号は後続βの発話位置だけで、この文全体を隠す意味記号は追加しない。',
  '正負値の有限対照、−1の反例、正の枝との区別、測定長から符号への引数接続、引用の前提・結論の取り違え検査と原刊通読を記録した。有限検査は一般実数体や原論文の導出の自動証明ではない。',
  'この二関係からφ(v)=1でなければならず、したがって既出式が後続四式になるという一文を通読した。正の枝の文脈を明示し、著者の推論と解釈注記を区別する読みで、参照・必要性・書換えを欠落なく保持したと判断する。',
 ),
 (
  '固定u0106のM0189を原刊902頁の四行へ照合した。τ,ξ,η,ζの順序、縦二式のβ、時間式のV²、横二式のy,zと行末コンマを確認した。',
  'ejegは各行の左辺と右辺を同じ二記録へ適用する列であり、ssnは係数1の四等式を構成する。ejehは現在の全対象対で式条件と出来事対応が双方向に一致するei7lと、同じ四式列によるeiy4を保つ。',
  'x,y,z,tは同じK記録、ξ,η,ζ,τは同じ出来事のk記録の役割である。v,Vは先行式と同じ値、βは既存spqで指定する同じ正の係数であり、横二式へβを加えない。',
  'この表示は直前のso daßとコロンに続く、同じ著者が得た最終形である。ejej/ejeoが既出のφ付き四式からの書換え結果として帰属し、後続wobeiの指定へつなぐ。',
  '単一の光線や一組の測定例へ狭めず、現在の全対応を保持する。同値の別記録は許し、欠けた対応や余分な対応は拒否する。全実数四組が実在の記録であるという存在要求や、旧spiの対象範囲は追加しない。',
  '既存の実切断演算spd/spe、四式ssn、記録値の役割、現在の方程式課題を再利用する。列の各要素を左右両辺として合成し、式の画像や文字列を意味そのものにしない。',
  '全四成分の誤り、列の両辺・順序、四つの各欠落に対する区別例、同じ値の別記録と対応の過不足、未知入力の拒否を検査した。有限有理切断境界と原刊四式の通読は、全実数体の一般証明とは区別する。',
  '直前の式の書換えから四行と後続wobeiまで再読した。同じ二系の全座標対応における最終形という読みの下で、四等式・成分の役割・係数・提示順を欠落なく保持したと判断する。',
 ),
 (
  '固定u0107の全5文字wobeiを原刊902頁の四式とβの定義の間で照合した。',
  'ejekが同じβの内容spqを指定し、ejeqの発話順序がその指定を直前の最終四式zhpに続ける。独立な仮定文や別の変換を導入する接続にはしない。',
  '補足対象は直前四式でτとξの右辺に用いたβ、指定内容は後続M0190、著者と論説と節は直前から同一である。先のβ導入位置zfkと今回の位置eisn4は区別する。',
  '既に表示した式の記号を定義で補う役割として、同じ内容の採用uhと発話の進行ueで保持する。読者への質問や二式からの新しい推論を加えない。',
  'βの定義は同じV,vについての正の値であり、独立な速度記号を追加しない。wobei自体に測定の実施や証明済みという意味を混ぜない。',
  '既存の内容の指定と著者帰属を合成し、wobei専用の原始意味を作らない。eisn4は繰り返されるβの指定位置を識別するための個体に限る。',
  '指定内容、著者、節、直前の表示位置の取り違えと、引用内容を実行せず帰属できることを検査した。原刊上の接続位置は通読で別に確認した。',
  '最終四式の直後にwobeiがあり、そのβを次式で指定するというつながりを再読した。直前表示への補足という役割を欠落なく保持したと判断する。',
 ),
 (
  '固定u0108のM0190とMathMLの分数・根号・二乗を原刊902頁へ照合した。原刊末尾はコンマ、固定MathMLは句点であり、差を照合記録へ明記した。',
  'βは1を分子、√(1−(v/V)²)を分母とする正の値である。spq/spaは同じ正のV/√(V²−v²)との一致と有効な定義域を保持する。',
  'vは同じ対象速度zb7、Vは同じ光速tc、βは最終四式が使う同じsoyである。v/Vという別のβの慣習、負の根又は別速度の値へ替えない。',
  '直前wobeiに続く同じ記号の指定としてejek/ejeqで著者へ帰属する。前提から新しい物理定数を発見したという結論ではない。',
  '現在の動く系の設定は0<v<Vである。式の一般の許容範囲と対象速度の設定を区別し、光速点の分母零や光速超過を有効にしない。原刊と固定本文の句読点差は数式の意味を変えない。',
  '既存の正の根と商の実切断規約spa/soyを用い、入れ子の分数と平方根を実際の演算内容として保持する。平坦化文字列11−(vV)2を式として解釈しない。',
  '正のβでの四式、誤った負値・v/V・別値の拒否、既存βの定義の検査証拠と保存原刊の視認を記録する。有限例を全実数域の計算証明としない。',
  'wobeiからβの分数表示まで再読した。同じ最終四式の係数を正の逆平方根で指定する読みの下で、参照・分数構造・根号・二乗・提示の役割を欠落なく保持したと判断する。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_final_transform_claim.py','tests/test_final_transform_claim_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[];selections=([323,324],[324],[324,325],[325])
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        selection=selections[i]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=LIMITS,limits=['正の測定長による枝の解釈と著者の推論を区別し、現在の全座標記録と四式を結ぶ読みの下でのアシスタントの通読判断。独立査読、物理的導出や意味同値の自動証明ではない。','u0109以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='phi_one_final_transformation_and_beta_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':4},semantic_equivalence_automatically_proved=False,source_sha256=pins)
