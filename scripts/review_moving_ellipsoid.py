"""Whole-unit reading of general moving spheres and their three semiaxes."""
from functools import lru_cache
import json
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import REQUIREMENTS,digest,selection_binding,validate_hashes,validate_review
from noema.review_registry import merge_pins
from scripts.compose_moving_ellipsoid import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,INDEX,LIMITS
from scripts.check_moving_ellipsoid import DOC,SOURCE,INVENTORY,PRIOR,DEPENDENCIES,source_record

REPORT='reports/moving-ellipsoid-v1.json'
REVIEWS=tuple(f'data/einstein-moving-ellipsoid-u{n:04d}-review-v1.json' for n in (114,115))
CLAUSES=(
 (
  ('Ein starrer Körper, ',['ejgb','ejf7','eje5','eigy'],'同じ設定の任意の剛体を量化する。先の特定物体だけに縮めない。'),
  ('welcher in ruhendem Zustande ausgemessen die Gestalt einer Kugel hat, ',['ejf7','eje5','eiah','eje4','eje7'],'静止系で測った球形という条件を同じ物体の全点の剛性・静止・閉球占有・現在記録に接続する。'),
  ('hat also in bewegtem Zustande ',['ejga','ejgb','ejgc','ejgd','eipf'],'同じ物体が運動中に持つ形状を全対象時刻に述べ、先行する球面式と変換からの著者の帰結として提示する。'),
  ('— vom ruhenden System aus betrachtet — ',['ejga','eiyx','ejfa'],'Kの同時刻座標での形状という観測系を保持する。光の到着による画像とはしない。'),
  ('die Gestalt eines Rotationsellipsoides mit den Achsen',['ejf3','ejf4','ejf5','ejf6','ejga','stg','ejgf'],'移動中心を持つ閉回転楕円体の完全占有と独立な境界、等しい横二半軸を構成し、次の三値の表示へ接続する。'),
 ),
 (('[M0200]',['stg','sth','ste','ejga','ejgf'],'縦半軸R√(1−(v/V)²)と横二半軸R,Rをこの順序で同じ回転楕円体へ結ぶ。表示値に従って半軸と読み、直径へ替えない。'),),
)
REASONS=(
 (
  '固定u0114全体を原刊903頁へ照合した。Ein starrer Körperから静止時に測った球形、also、運動状態、Kからの記述という挿入、回転楕円体と次の軸表示への接続まで通読した。',
  'ejf7は同じ全物質点の静止球形・剛性・現在記録・並進条件を持つ。ejgaはKの全対象時刻で閉回転楕円体の完全占有と全現在記録の独立境界との一致を要求し、ejgbは物体・半径・静止側中心へ量化する。',
  '二つの状態は同じ物体のkとKでの形状を指す。静止側中心を任意にし、Kでは(cx/β+vt,cy,cz)を用いる。同じv,Vと二系・尺度を継承し、先の特定球zhwだけへ限定しない。',
  'alsoを先行する球面式・現在の最終四式・零断面の式からの著者の帰結としてejgdで提示し、ejgfで論説へ帰属する。処理系が一つの例から一般的な物理法則を証明したという意味を加えない。',
  '閉球を占める理想的な連続体という明示した読みを継承する。Kugelgestaltの語から内部充填が必然とはせず、実際の過去の測定や加速過程を補わない。Kの同時刻座標による形状と光学像を区別し、零時刻だけに範囲を縮めない。',
  '既存の実切断、全物質点の静止・剛性・並進、現在測定記録と独立境界を再利用する。中心差の規格化二乗和と等しい横二半軸から形状を合成し、原文一文専用の原始意味記号を追加しない。',
  '中心の異なる数値例、表面・内部・外部、全点包含と全位置被覆、半軸の順序、異なる時刻の移動中心、一般条件の全物体範囲と帰属の引数を検査した。全実数量化は残し、有限例の通過と一般証明・意味判断を区別する。',
  '直前の零断面の式、本文全体と後続の三値を再読した。明示した連続体と座標形状の読みの下で、任意の静止球形剛体、運動状態、観測系、回転楕円体、半軸への接続、帰結の提示を欠落なく保持したと判断する。',
 ),
 (
  '固定u0115のM0200を原刊903頁の根号、分数v/V、その二乗、先頭R、二つのR、区切りと句点へ照合した。句点は固定MathMLの内側に保持される。',
  'stgが同じ半径について縦半軸a=R/β=R√(1−(v/V)²)、横二半軸R,Rを要求する。ejgaの全時刻の閉回転楕円体と全現在記録の表面条件に同じ値を渡す。',
  'Rは静止側の同じ球の半径、vは同じK/kの相対速度、Vは同じ光速である。先頭は運動方向の半軸、後の二つは横方向の半軸を指す。任意の正半径の範囲を保持する。',
  '直前のmit den Achsenに続く、著者が示す回転楕円体の三半軸の列として帰属する。独立した定理や新しい実験結果として提示しない。',
  'Achsenは表示値に合わせて半軸と明示して読み、直径2Rへ替えない。縮小係数を横二方向へ広げず、根号を落とさず、v/VとV/v、根号の内側と外側の二乗を取り違えない。後続の光速極限や任意形状をこの単位へ補わない。',
  '既存の正の平方根ste、半軸sth、三値の関係stgと新しい中心差の形状を合成する。MathMLの文字列を意味そのものにせず、既存の許容速度と正の半径という読みを継承する。',
  'V=5,v=3,R=5で半軸4,5,5を確認し、8,5,5という直径混同、4,4,4という全方向縮小、5,4,5という軸交換、負半軸を区別した。有限数値検査は全実数域の同値証明とはしない。',
  '前の本文と三値の表示を一緒に再読した。同じ動く回転楕円体の半軸という読みで、三値の順序・根号・比・二乗・半径・物体への接続と著者の提示を欠落なく保持したと判断する。',
 ),
)

@lru_cache(None)
def records():
    catalog=load_catalog(ROOT,BASIS);paths={FULL,CORE,BASIS,ANNOTATIONS,SOURCE,REPORT,INVENTORY,DOC,PRIOR,*DEPENDENCIES,'scripts/review_moving_ellipsoid.py','tests/test_moving_ellipsoid_review.py'}
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
        out.append(dict(schema_version='noema-semantic-review-1',work='einstein-1905',unit=s['unit'],reviewer='assistant_review',decision='equivalent_under_stated_reading',document=FULL,meaning_basis=BASIS,identifier_annotations=ANNOTATIONS,source=dict(inventory=INVENTORY,unit_sha256=s['unit_sha256'],text=s['text'],range=s['range'],math=[{k:m[k] for k in ('id','sha256')} for m in s['math']]),selection=selection_binding(catalog,[INDEX]),source_order_statements=[INDEX],clauses=clauses,interpretation=LIMITS,limits=['閉球連続体・同時刻座標での形状・表示値に従う半軸という明示した読みの下でのアシスタントによる通読判断。一般の物理的導出や意味同値の自動証明、独立査読ではない。','u0116以降と二作品全体の目標は未完。'],unresolved=[],requirements=[dict(id=k,decision='satisfied',reason=v) for k,v in zip(REQUIREMENTS,REASONS[i])],evidence=dict(source_reading=[SOURCE],formal_checks=[REPORT,*DEPENDENCIES],semantic_reading=[DOC]),reviewed_prose_characters=s['source_nonblank_characters'],source_sha256=pins))
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
    return dict(status='general_moving_ellipsoid_and_semiaxes_whole_units_reviewed',document=FULL,source_units={r['unit']:r['reviewed_prose_characters'] for r in records()},reviewed_math_elements=1,whole_units_semantically_verified=True,verified_full_units={'kant-1784':0,'einstein-1905':2},semantic_equivalence_automatically_proved=False,source_sha256=pins)
