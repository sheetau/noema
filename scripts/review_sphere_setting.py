"""Record the whole source reading of the sphere setting and attached gloss."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_sphere_setting import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,LIMITS
from scripts.check_sphere_setting import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/sphere-setting-v1.json'
REVIEWS=tuple(f'data/einstein-sphere-setting-u{n:04d}-review-v1.json' for n in (110,111,281))
CLAUSES=(
 (
  ('Wir betrachten eine starre Kugel vom Radius [M0191], ',['ejff','ejfi','ejfo','ejfc','eigy','eje4','eje7'],'同じ半径Rの剛な球を考察の対象設定として採る。全物質点の剛性と、閉球連続体という明示した読みの全形状を保持する。'),
  ('welche relativ zum bewegten System [M0192] ruht, ',['ejfc','ejfb','eje5','eiah'],'比較側Kに対して動く同じ系kに関して、この球が静止する。物体のKにおける静止や時計内部の運動停止へ替えない。'),
  ('und deren Mittelpunkt im Koordinatenursprung von [M0193] liegt. ',['ejfb','eje5','eixu','zbv'],'同じ球の中心三成分を、測定された同じkの座標原点の零へ合わせる。名称だけの中心の参照ではない。'),
  ('Die Gleichung der Oberfläche dieser relativ zum System [M0194] mit der Geschwindigkeit [M0195] bewegten Kugel ist:',['ejfc','eipf','eioj','ejfd','ejfh','ejfj','ejfp'],'Kに対して同じvで動くその球の表面式を次の表示として提示する。全現在記録の境界と同じkの球面数値式を双方向に結ぶ。'),
 ),
 (('[M0196].',['ssy','ssz','ejfd','ejfh','ejfp'],'ξ²+η²+ζ²=R²と句点を、同じkの全適格記録における境界の式として直前のコロンへ接続する。'),),
 (
  ('Das heißt einen Körper, ',['ejfk','eisme','ejfq','eisfo','ejff'],'先の同じ球を何という意味で扱うかという著者の説明。Kugel直後の注1)に接続し、別の物体を導入しない。'),
  ('welcher ruhend untersucht Kugelgestalt besitzt.',['ejfg','ejfe','eje5','eiah','eje4'],'同じ物体を静止側で調べたときに球形を持つという形状条件。実測の過去の実施や動く側での球形を追加しない。'),
 ),
)
REASONS=(
 (
  '固定u0110の二文全280文字とM0191–M0195、脚注参照A0016を原刊903頁に照合した。Wir betrachten、starre Kugel、R、二つのk、K、v、球面式を導入するコロンまで再読した。',
  'ejfcが同じ全物質点の剛性・静止・形状・k原点・Kでの速度を結び、ejfdが独立の物質境界と数値球面式を同じ現在記録全範囲で双方向に結ぶ。設定と式の提示をejfi/ejfjで分ける。',
  '半径はzhx、物体はzhw、kはzbm、Kはra、速度はzb7、設定はzb6で前の二系と同じである。derenとdieserは同じ物体へ接続し、中心の系もkを保つ。脚注はeisoaからeisn7へ結ぶ。',
  'Wir betrachtenは思考上の設定を採るug、Die Gleichung ... istとコロンは設定内の式を提示するuhとして同じ著者・第四節へ帰属する。原物体の実在・製作・測定実験の報告ではない。',
  '一つの球を内部を含む理想的な閉球連続体として扱うモデルを明示する。内部充填を語義上の必然性へ一般化せず、密度・質量や全ての殻を含む主張は加えない。全位置被覆と全物質点の現在記録を省かず、Kの時刻零断面は先取りしない。',
  '全履歴・一般の剛性と静止・開閉球・物質占有と独立境界・測定原点・現在記録を既存の定義から合成した。追加原始記号は式位置・注本文・注の付着位置を識別する三個体だけである。',
  '全現在記録を先に選ぶ検査、双方向不一致・空の表面の拒否、同じ物体・半径・系・引用の接続と原刊通読を記録した。例化検査を一般の実数領域・物理的境界定理や意味同値の自動証明に替えない。',
  '二文を原刊の脚注と後続の式とともに通読した。明示した閉球連続体の読みの下で、剛性、半径、静止する相手系、原点中心、比較側での同じ速度、表面と式提示の関係を欠落なく保持したと判断する。',
 ),
 (
  '固定u0111のM0196と句点を原刊903頁へ照合した。三つのギリシャ座標と半径R、四つの二乗、加算、等号を確認した。',
  'ssyは三つの座標の二乗和と正の同じ半径の二乗の等値、sszは同じ記録の三成分への適用である。ejfdはその式と同じ物体の独立な境界ejfaの同値を全現在記録で述べる。',
  'ξ,η,ζは同じkにおける三座標、Rは直前の同じzhxである。Kのx,y,zや時間τを三空間成分に混ぜず、後続のt=0の式と区別する。',
  '直前のコロンに続く式の提示ejfj/ejfpであり、全式を単なる引用文字列にしない。著者がこの設定内で述べる表面式という役割を保持する。',
  '表面条件の等号を内部を含む不等号にせず、時間成分を二乗和へ加えない。任意の実数四組が測定済みだという存在要求は加えないが、設定側の全物質点と記録の範囲を保持する。',
  '実切断の加算・乗算・値の同値、現在座標記録の各役割と占有領域の境界を合成して式を意味付ける。MathMLや原語の綴りは出典識別であり、記述内容の代用ではない。',
  '三軸それぞれの数値表面、正負半径、全イベント・記録の選択と境界の過不足を区別する有限例を検査した。境界と球面の一般定理の証明ではなく、その全範囲の主張を記述した証拠と原刊通読を分ける。',
  '直前二文、表示式、後続のK座標への移行を通読した。同じ静止側kの表面式という読みで、成分・二乗・等号・半径・提示の役割を欠落なく保持したと判断する。',
 ),
 (
  '固定u0281の全71文字を原刊903頁下部の著者注1)へ照合し、Kugel直後の付着位置も確認した。inventory末尾の掲載位置を原刊掲載頁としない。',
  'eismeが先の設定ejffを静止時の球形ejfgで説明する向きを保持し、ejfeは同じ全履歴・静止・球体形状を何らかの中心について表す。eisfoとeisa5が同じ注の構造と補足先を結ぶ。',
  'Körperは先の同じzhwで、静止する基準は同じk、同じ半径zhxと物理設定zb6を保つ。本文の設定位置・Kugel直後の注付着位置・注本文位置を別の個体として結ぶ。',
  'Das heißtはすなわちという説明の提示であり、別の代案や新しい実験の導入ではない。脚注の同じ著者へのメッセージ帰属を保持し、注本文を後世の編集注へ替えない。',
  'ruhend untersuchtは静止状態を形状判定の基準とする読みであり、誰かが過去に測定した事実を補わない。球の形状分類は中心位置を自由にし、原点条件は本文の同じ設定に置く。閉球連続体という明示したモデルの範囲を超えて空洞を持つ全物体の語義を決めない。',
  '同じ物体の全物質点・全履歴の静止と閉球形状を合成し、球形という未説明の原始名詞を追加しない。既存の説明・脚注参照・同じ内容への補足の規約を再利用する。',
  '中心三位置の存在、静止側・物体・半径の引数接続、脚注番号・付着位置・説明先の取り違え、引用内容の非実行を検査した。全実数の中心候補の有限評価は拒否し、検査と通読判断を分ける。',
  '脚注全体を本文のstarre Kugelとともに再読した。同じ球を静止側で調べた形状によって説明する読みの下で、説明の向き・同一物体・静止の基準・形状・注の構造を欠落なく保持したと判断する。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_sphere_setting.py','tests/test_sphere_setting_review.py'}
    pins={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};merge_pins(pins,catalog.source_sha256)
    for p in (SOURCE,REPORT,*DEPENDENCIES):
        evidence=json.loads(read(p));validate_hashes(ROOT,evidence['source_sha256']);merge_pins(pins,evidence['source_sha256'])
    out=[];selections=([327,328,329],[327,328],[329])
    for i,s in enumerate(source_record()['segments']):
        clauses=[];offset=0
        for text,symbols,reason in CLAUSES[i]:
            assert s['text'][offset:offset+len(text)]==text and all(n in catalog.entries for n in symbols)
            clauses.append(dict(range=[offset,offset+len(text)],text=text,definitions=symbols,reason=reason));offset+=len(text)
        assert offset==len(s['text']) and len(REASONS[i])==len(REQUIREMENTS)
        selection=selections[i]
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,selection),source_order_statements=selection,clauses=clauses,interpretation=LIMITS,limits=['内部と境界を含む一つの理想的な閉球連続体という明示した読みの下でのアシスタントの通読判断。空洞を持つ全ての球形物体を含む語義の自動判定、独立査読、物理的真理の証明ではない。','u0112以降の変換と時刻零断面、二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='sphere_setting_surface_equation_and_author_note_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=6,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':3},semantic_equivalence_automatically_proved=False,source_sha256=pins)
