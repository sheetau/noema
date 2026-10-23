"""Whole reading of the sphere-equation rewrite and simple calculation."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_spherical_equation_rewrite import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_spherical_equation_rewrite import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/spherical-equation-rewrite-v1.json'
REVIEWS=tuple(f'data/einstein-spherical-equation-rewrite-u{n:04d}-review-v1.json' for n in (89,90))
CLAUSES=(
 (
  ('Diese Gleichung ',['ejaa','ejai'],'直前の同じ到来点のK球面方程式を指す。'),
  ('transformieren wir mit Hilfe unserer Transformationsgleichungen ',['ejag','ei7c','ei3a','ejai','zd3'],'同じ著者の既出四座標式を使い、同じ出来事の現在K/k記録により式を変形する提示。'),
  ('und erhalten nach einfacher Rechnung:',['ejaf','ejah','s2y','ejai','uh'],'その同じ計算によって後続の式を得る提示と、計算負担が低いという評価。'),
 ),
 (('[M0146].',['ejae','ejaf','sqj','sqk'],'同じ到来出来事のk記録のξ,η,ζ,τについてξ²+η²+ζ²=V²τ²を述べ、句点で計算提示を閉じる。'),),
)
REASONS=(
 (
  '固定u0089全117文字・非空白本文105文字を原刊901頁へ照合した。直前のK式から指示語Diese Gleichungを読み、後続u0090のk式と句点まで通読した。',
  '直前の式の指示、既出の同じ四座標変換を使うこと、著者による変形と結果取得の提示、同じ計算への簡単という評価、後続表示式へのコロンを保持する。前提ejagが同じK波面と式・四変換式・両系の記録を結ぶ。',
  'Diese Gleichungはejaa、unsere Transformationsgleichungenはei7cであり、別の旧草案を参照しない。波zfu・放出zfv・設定zb6を共有し、到来出来事のK記録とk記録を同じeiyxで結ぶ。V,v,φも既出の同じ規約を使う。',
  'wir ... transformieren und erhaltenを著者の論述上の書換えzd3として、前提・変形前・結果の三役割を分ける。同じ箇所zgeに計算評価uhを付し、同じ著者rd・第三節eisms・論説eirfと直前からの順序を保持する。実行済みの実験や読者への指示にしない。',
  '簡単さを数式の成立だけで省略せず、別計算の成功と低負担を混ぜない。原文にない手順数や閾値、φ=1、追加原点定数、kの未来側波面、両立性証明の完了を加えない。任意の到来点を一成功例へ固定せず、k記録の欠落を空の全称で隠さない。',
  '現在の同じ出来事の座標と既存の四変換式・球面式を合成する。簡単さは既存の利用可能な方法zlw、手順列zlx、許容変形zla、非負負担zlb、文脈基準zlcとs2yによる明示的な低負担の読みとし、文全体を説明のない新原始語で代用しない。',
  '原刊・固定本文・定義の通読を根拠とし、同じ出来事の結合、全到来範囲と記録存在、四式と球面残差、同じ有限計算列と負担、引用の非実行を区別して検査した。有理多項式の既存証拠と有限対照は一般物理的導出や意味同値の自動証明ではない。',
  'K球面式を受ける指示語から四式を使う変形、簡単な計算という評価、後続k式まで再読した。現在の全対象範囲と文脈上の低負担の読みの下で、全文の関係・参照・提示を欠落なく保持したと判断する。',
 ),
 (
  '固定u0090のM0146と句点を原刊901頁へ照合した。ξ,η,ζの三平方、Vとτの二平方、左辺の二加法、右辺の積と等号を確認した。',
  '同じk座標記録の三位置の平方和が同じV²τ²に等しいことをsqj/sqkで保持する。任意の現在K到来記録に同じ出来事のk記録が存在し、対応する全k記録にこの式を適用するejafを結果内容とした。',
  'ξ,η,ζ,τはejaeで同じ到来出来事に結ばれたk記録の四成分である。Kのx,y,z,tや別出来事の時刻を混ぜず、Vは同じtc。前提ejagの同じ四変換式と共通零原点の設定に接続する。',
  '前のtransformieren ... und erhaltenに続く結果式であり、ejaiのzd3がK式からk式への書換えとして提示する。同じ計算の評価ejahと同じ著者・論説へ帰属し、独立した無条件の実測値報告に変えない。',
  '二乗式は負時刻や零の座標でも成立し得るため、正時刻や非退化性を式に足さない。単にk記録がないため全称が真になる場合を除く一方、同じ値を持つ別記録は許す。後続のk球面波と両立性の結論はここで主張しない。',
  '既存の実切断の加法・乗法・差・同値と有効な四成分で式を構成する。現在の記録付与・同じ波の到来・既出四式を引き継ぎ、ギリシャ文字や原文数式を説明のないラベルとして埋め込まない。',
  '原刊とMathMLの五平方を確認し、現在の四式による数値変換、全成分の変更、負・零のφ、複数到来点、k記録欠落と別記録を対照した。保存済み残差の有理代数証拠を保持し、一般実切断上の物理的導出の証明とはしない。',
  'u0089の変形と計算評価から表示式と句点まで再読した。同じ到来出来事の両系の記録と二乗式という明示的な読みの下で、式全体と論述上の役割を欠落なく記述したと判断する。',
 ),
)


@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_spherical_equation_rewrite.py','tests/test_spherical_equation_rewrite_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[]
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['同じ到来出来事の現在両系記録と、文脈上の低負担計算という明示した読みの下でのアシスタントの通読判断。独立査読、一般物理的導出や意味同値の自動証明ではない。','u0091以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='sphere_equation_rewrite_and_simple_calculation_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,source_sha256=pins)
