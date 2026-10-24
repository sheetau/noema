"""Normalize a local trajectory and keep independent comoving origins free."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,R,v,call as k,app,op,both,lam
from scripts.compose_material_relative_frame import define
from scripts.compose_material_velocity import POINT,DOMAIN,CURVE,ROLES,coord,valid
from scripts.compose_material_acceleration import PROFILES,ACCEL
from scripts.compose_field_transform import point_expression,MAP
from scripts.compose_point_particle_dynamics import ZERO,ONE,args

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-electron-moving-law-task.noema';PARENT_BASIS='data/electron-moving-law-task-basis-v1.json'
FULL='examples/v014/einstein-electron-coordinate-normalization.noema';CORE='examples/v014/electron-coordinate-normalization-core.noema'
BASIS='data/electron-coordinate-normalization-basis-v1.json';ANNOTATIONS='data/electron-coordinate-normalization-identifiers-v1.json'
MATRIX=[(f'r{i}{j}',R) for i in ('x','y','z') for j in ('x','y','z')]
NORMAL=MATRIX+[('origin',POINT)]
ALIGN=MATRIX+[('velocity',POINT),('speed',R)]
CHART=[('first','a'),('second','a'),('lengthunit','a'),('timeunit','a'),('context','d')]+NORMAL
BOOST=[('light',R),('speed',R)]
TANGENT=BOOST+[('velocity',POINT)]
MEANINGS={
 'ek43':'有効な九実数の三行が正規直交し、第一行と第二行の外積が第三行となる、向きを保つ三次元直交回転。鏡映・尺度変更・ずりを許さず、恒等回転は許す。',
 'ek44':'二つの四座標についてpointからoriginを成分ごとに引く。空間三成分と同じ座標時刻の原点を同時に変更する数値構成。',
 'ek45':'同じ九成分行列で三空間成分を回転し、時刻成分をそのまま保つ四座標写像。適格な回転であることはek43で別に要求する。',
 'ek46':'同じ行列の転置を三空間成分へ適用し、時刻を保つ。ek43の下でek45の逆となり、行と列を取り違えない。',
 'ek47':'同じoriginを四座標から引いた後、同じ回転を空間へ適用する。指定出来事を零へ移し、時間と空間の原点を別の出来事から選び直さない。',
 'ek5a':'回転の転置で戻した四座標に同じoriginを加える、ek47の逆写像。元に戻す順序を保ち、原点を回転後の座標と取り違えない。',
 'ek5b':'同じ三速度の非負ノルムがspeedであり、回転後の三成分が(speed,0,0)となる。零速度なら向きの選択を追加しない。',
 'ek5c':'適格な正の向きの回転ek43、有効な四原点、同じ速度を正X方向へ置くek5bを結ぶ代表配置の数値条件。任意の物理設定でその配置を採れるという全体主張とはまだ区別する。',
 'ek5d':'同じ旧時間領域を、時刻原点origin(t)だけ引いた新時刻へ移す。新時刻sの所属は旧時刻s+origin(t)の所属であり、端点や近傍を勝手に延長しない。',
 'ek5e':'同じ旧曲線を旧時刻s+origin(t)で評価し、その四座標へek47を適用した新曲線。同じ原点を時間引数と座標変換へ共用する。',
 'ek5f':'同じ旧時刻s+origin(t)で三つの実速度関数を評価し、同じ回転で三成分を移す速度ベクトルの関数。時間原点を変えても経過時間の尺度は変わらない。第四成分は零の補助表示。',
 'ek5g':'三つの同じ座標加速度を同じ空間回転へ移す。原点位置・時刻原点の値を加速度へ足さず、第四成分は零とする。',
 'ek5h':'同じ長さ・時間単位と状況で両座標系をejslへ校正し、適格な回転と原点移動ek47を同一出来事の全域の再表現eisqtへ結ぶ。数値写像だけで物理的対応を認定せず、特定の点だけの一致へ縮めない。',
 'ek5i':'係数1の既存Lorentz写像s46の四出力に、新系の任意の四原点ずれoffsetを加える。原点・時刻の一致をこの段階で要求しない。',
 'ek5j':'新系の四原点ずれoffsetをまず引き、反対速度のs46を適用するek5iの逆構成。空間だけ又は時刻だけを戻して同じ出来事を失わない。',
 'ek5k':'同じVと並進速度speedに対し、元の局所三速度のX成分uxを使ってβ(1−speed*ux/V²)を作る。新旧の座標時刻の局所変化率であり、電子の固有時の率ではない。原点ずれに依存しない。',
 'ek5l':'同じ局所速度の三成分を、β(ux−speed)、uy、uzの各分子と同じ時刻変化率ek5kで変換する。三成分全てで同じ分母を使い、新系の時刻による速度とする。第四成分は零。',
 'ek5m':'正のV、非負でV未満の並進速度、三速度の有効性、正の時刻変化率を保つ局所速度変換の適用条件。電子の全期間の等速や加速度零を要求せず、既存s45の実数boost適格性を再利用する。',
}
LIMITS=[
 'u0245の原点・X方向への代表配置と瞬間静止系を統合する依存群。原刊917–918頁を視認し、Koordinaten-sprungを後続の零座標指定と合わせて座標原点と読むことを明示する。原文保存ファイルは変更しない。今回の新主張と全文判断はない。',
 '空間回転は正規直交で向きを保ち、単位尺度は変えない。指定出来事の空間・時刻原点を同時に移す。速度、加速度、局所領域、位置曲線、速度関数を同じ回転と時刻移動へ結び、位置だけの形式的な置換へ縮めない。',
 '九成分の回転を変数として扱い、有限個の軸置換だけへ許容範囲を限定しない。数値条件ek5cだけで、全物理設定の同値代表が存在するという一般性の提示を済ませない。場・法則・対象・出来事を同じ物理設定へ対応させる全文統合は続けて行う。',
 '瞬間静止系kの原点と時刻原点は後続で追加指定されるため、今回は任意の四原点ずれを持つboostと逆を用意する。電子がKの原点にいることからkの四座標も零とはしない。',
 'V>0かつ0≤v<Vの慣性共動系の局所的な適用域を使う。u0244の速さ一般へ遡及して上限を追加せず、零速度では恒等boostと任意の原点ずれを許す。時間変化率を正とする領域で新系の座標時刻を局所パラメーターとする。',
 '元の瞬間速度が(v,0,0)なら変換後三速度は零となるが、前後の静止、電子の全期間の等速、加速度零、無放射は補わない。変換式の局所的な数値構成と、実際の同じ電子の二つの完全な物理的履歴・ネイティブな時間微分への接続は別に検証する。',
 '有限の直交回転・軌道多項式・原点ずれ・速度を対照する。全実数の回転存在、連鎖律又は全物理設定の一般性を有限試験から証明したとはしない。全文では仮定の許容と採用、明白な帰結、t=0・K・k・X・vの表記と著者帰属が残る。',
]

def coordinates(point):return [coord(point,a) for a in ROLES]
def vector(values):return point_expression([*values,ZERO])
def definitions():
    rows=[[v(f'r{i}{j}') for j in ('x','y','z')] for i in ('x','y','z')]
    dot=lambda a,b:k('sexb',*a,*b)
    mul=lambda a,b:k('shv',a,b)
    cross=[k('bf',mul(rows[0][i],rows[1][j]),mul(rows[0][j],rows[1][i])) for i,j in ((1,2),(2,0),(0,1))]
    text=define('ek43',MATRIX,both(*(k('ba',v(n)) for n,t in MATRIX),*(k('sca',dot(rows[i],rows[j]),ONE if i==j else ZERO) for i in range(3) for j in range(i,3)),*(k('sca',a,b) for a,b in zip(cross,rows[2]))))
    point=v('point');origin=v('origin');coords=coordinates(point);base=coordinates(origin)
    text+=define('ek44',[('origin',POINT),('point',POINT)],point_expression([k('bf',a,b) for a,b in zip(coords,base)]),POINT)
    for name,matrix in [('ek45',rows),('ek46',list(zip(*rows)))]:text+=define(name,MATRIX+[('point',POINT)],point_expression([*(dot(row,coords[:3]) for row in matrix),coords[3]]),POINT)
    text+=define('ek47',NORMAL+[('point',POINT)],k('ek45',*args(MATRIX),k('ek44',origin,point)),POINT)
    inverse=k('ek46',*args(MATRIX),point)
    text+=define('ek5a',NORMAL+[('point',POINT)],point_expression([k('bd',a,b) for a,b in zip(coordinates(inverse),base)]),POINT)
    velocity=v('velocity');speed=v('speed');spatial=coordinates(velocity)[:3];rotated=k('ek45',*args(MATRIX),velocity)
    text+=define('ek5b',ALIGN,both(k('ek4n',speed,*spatial),*(k('sca',coord(rotated,a),want) for a,want in zip(ROLES[:3],(speed,ZERO,ZERO)))))
    text+=define('ek5c',NORMAL+[('velocity',POINT),('speed',R)],both(k('ek43',*args(MATRIX)),valid(origin),k('ek5b',*args(ALIGN))))
    s=v('newtime');t=k('bd',s,coord(origin,ROLES[3]))
    text+=define('ek5d',[('domain',DOMAIN),('origin',POINT)],lam('newtime',R,both(k('ba',s),app(v('domain'),t))),DOMAIN)
    text+=define('ek5e',NORMAL+[('curve',CURVE)],lam('newtime',R,k('ek47',*args(NORMAL),app(v('curve'),t))),CURVE)
    oldvelocity=vector([app(v(n),t) for n,typ in PROFILES])
    text+=define('ek5f',NORMAL+PROFILES,lam('newtime',R,k('ek45',*args(MATRIX),oldvelocity)),CURVE)
    text+=define('ek5g',MATRIX+ACCEL,k('ek45',*args(MATRIX),vector(args(ACCEL))),POINT)
    ctx=v('context');lu=v('lengthunit');tu=v('timeunit');mapping=lam('location',POINT,k('ek47',*args(NORMAL),v('location')))
    text+=define('ek5h',CHART,both(k('ek43',*args(MATRIX)),valid(origin),*(k('ejsl',v(n),lu,tu,ctx) for n in ('first','second')),k('eisqt',v('first'),v('second'),lu,tu,mapping,ctx)))
    offset=v('offset');boost=k('s46',*args(BOOST),point)
    text+=define('ek5i',BOOST+[('offset',POINT),('point',POINT)],point_expression([k('bd',a,b) for a,b in zip(coordinates(boost),coordinates(offset))]),POINT)
    text+=define('ek5j',BOOST+[('offset',POINT),('point',POINT)],k('s46',v('light'),k('be',speed),k('ek44',offset,point)),POINT)
    beta=k('soy',*args(BOOST));ratio=mul(speed,k('sjd',mul(v('light'),v('light'))))
    rate=mul(beta,k('bf',ONE,mul(ratio,spatial[0])))
    text+=define('ek5k',TANGENT,rate,R)
    inverse_rate=k('sjd',k('ek5k',*args(TANGENT)))
    text+=define('ek5l',TANGENT,vector([mul(mul(beta,k('bf',spatial[0],speed)),inverse_rate),mul(spatial[1],inverse_rate),mul(spatial[2],inverse_rate)]),POINT)
    text+=define('ek5m',TANGENT,both(k('s45',*args(BOOST)),k('bc',ZERO,speed),*(k('ba',x) for x in spatial),k('bg',ZERO,k('ek5k',*args(TANGENT)))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==417
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='electron_coordinate_representative_and_free_origin_boost_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/electron-moving-law-task-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
