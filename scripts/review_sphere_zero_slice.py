"""Whole-unit reading of the same surface expressed at K time zero."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_sphere_zero_slice import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_sphere_zero_slice import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/sphere-zero-slice-v1.json'
REVIEWS=tuple(f'data/einstein-sphere-zero-slice-u{n:04d}-review-v1.json' for n in (112,113))
CLAUSES=(
 (
  ('Die Gleichung dieser Oberfläche ',['ejfv','ejff','ejfh','ejfa'],'直前の同じ物体の表面とそのkの球面式を参照する。別の球・波面・物質内部へ替えない。'),
  ('ist in [M0197] ausgedrückt ',['ejfw','ejfx','ejfy','ejeh','zd3'],'現在の最終四式の下で、同じ表面をKのx,y,zによる式へ書き換えて提示する。'),
  ('zur Zeit [M0198]:',['ejfr','ejfs','ejft','ejfu','ejf2'],'Kの時刻t=0に対象断面を選び、次の表示へ続ける。比較元も同じ出来事の範囲へそろえ、kのτ=0を追加しない。'),
 ),
 (('[M0199]',['stf','ste','sje','sky','ejfu','ejfx','ejf2'],'同じK零断面の全適格記録についてx²/(√(1−(v/V)²))²+y²+z²=R²を物質境界へ結び、直前のコロンに続く表示として帰属する。'),),
)
REASONS=(
 (
  '固定u0112全体とM0197のx,y,z、M0198のt=0を原刊903頁へ照合した。直前のkの球面式から、dieser Oberfläche、ausgedrückt、zur Zeitとコロンまで通読した。',
  'ejfrが現在のK記録の時刻零とその系の期間を選び、ejfsが全候補で独立境界と式の同値・非空表面を要求する。ejftとejfuは同じ断面をそれぞれ同じ出来事のk記録とK記録で表す。',
  'dieserは同じzhwの境界、半径はzhx、x,y,z,tは同じKの役割、比較元ξ,η,ζ,τは同じ出来事のk記録を指す。速度v・光速Vと最終四式も前段から同じである。',
  'ausgedrücktは同じ球設定・元の表面式・既出の最終四式を前提とする書換えzd3である。著者の記述への帰属を保持し、新しい実験結果や新しい変換法則の発見として提示しない。',
  '比較元を全k時刻の表面、比較先をKの一断面として無条件に同値化せず、両方を同じK零時刻の出来事へそろえる。対応k記録が同じ表面に属する対象期間の選択を明示し、両系の時刻値・区間端・同時刻面は等置しない。',
  '現在記録eiyx、占有領域の独立境界ejfa、全物質点の設定、最終四式ejehと既存の表面数値式を合成する。新しい原始意味記号を追加せず、未構成の旧zhuや旧shdへ戻らない。',
  '全記録の選択と表面の過不足、同じ出来事のk記録の欠落、物体・半径・系の取り違えを検査した。Kで同時の両端がkでは異なる非零時刻になる数値例を確認し、有限例と一般実数域・物理的導出の証明を区別する。',
  '直前球面式、本文一文、後続の表示を通読した。同じ表面をKの時刻零でK座標により表すという読みの下で、参照・書換え・時刻条件・全候補範囲・提示の役割を欠落なく保持したと判断する。',
 ),
 (
  '固定u0113のM0199を原刊903頁の分数・根号・二乗・横二項・等号・R²・句点へ照合した。句点は固定MathML内に含まれるため、単位本文へ重ねて追加しない。',
  'stfは同じK記録について時刻t=0、正の半径、同じ許容速度とβ、表示された二乗和の等値を要求する。ejfuはこの条件と同じ物体の境界を、全ての適格K零時刻記録で双方向に結ぶ。',
  'x,y,z,tは同じK記録の役割、Rは同じ球の静止側半径zhx、vとVは既出のzb7とtcである。k側の空間値や時刻を代入する別の式へ替えない。',
  '直前のコロンに続く、同じ表面をK座標で表した書換え先ejfxとして著者へ帰属する。後続の回転楕円体・半軸の結論をこの表示の一部として補わない。',
  '分母の平方根の外の二乗を保持する。1−(v/V)²をさらに二乗した分母に替えず、横二成分へ係数を掛けず、半径と直径を入れ替えない。表面を内部を含む不等式にせず、後の時刻の表面もt=0の断面に混ぜない。',
  '既存の実切断の正の根・商・積・和・数値同値stf/ste/sje/skyを再利用し、現在の物質境界と記録へ接続する。MathML画像や文字列を式の意味そのものにしない。',
  'V=5,v=3,R=5でKの縦端点±4と横端点±5、内側、誤った二重二乗の分母なら通る16/5、後の時刻の表面を区別した。最終四式との同じ二記録の一致を実評価し、一般実数体の証明や物理的真理の認定とは分ける。',
  '元の球面式から時刻零の表示式と次の形状の説明まで再読した。同じK零断面の式という読みで、分数構造・根号・二乗・横成分・半径・全記録の表面条件・提示の役割を欠落なく保持したと判断する。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_sphere_zero_slice.py','tests/test_sphere_zero_slice_review.py'}
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
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['同じ閉球連続体の表面記録を含む各系の対象期間の下で、同じK零断面を二つの座標表現で述べるという読みのアシスタントによる通読判断。一般の実数域・物質境界の定理や原著者の物理的主張の自動証明、独立査読ではない。','u0114以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='K_zero_time_surface_equation_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=3,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
