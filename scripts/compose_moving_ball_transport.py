"""Connect local surface transfer and interior advection on one moving ball."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_volume_denial import ROOT,read,TOTAL
from scripts.compose_light_region_slices import OLD,XYZ,LOCATION
from scripts.compose_radiative_density import DENSITY,SCALAR,DENSITY_MODEL
from scripts.compose_observed_intensity import MODEL,VECTOR
from scripts.compose_wave_display import COORDS
from scripts.compose_field_equations import FIELD,TAU,POINT
from scripts.compose_material_relative_frame import define,args
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,v,call as k,app,op,both

PARENT='examples/v014/einstein-volume-denial.noema';PARENT_BASIS='data/volume-denial-basis-v1.json'
FULL='examples/v014/einstein-moving-ball-transport.noema';CORE='examples/v014/moving-ball-transport-core.noema'
BASIS='data/moving-ball-transport-basis-v1.json';ANNOTATIONS='data/moving-ball-transport-identifiers-v1.json'
SURFACE=[('flux',FIELD),('densityfield',TAU)]+OLD
PLANE=DENSITY+[('sine','h[h[b] c] h[b] c')]+[(n,R) for n in ('rate','ax','ay','az','radius')]
TRACER=[(n,R) for n in ('ox','oy','oz','time')]
FRAME=[(n,t) for n,t in MODEL if n not in ('phase','region')]+[(n,R) for n in ('light','rate','ax','ay','az','radius')]+[('portion','a')]
MEANINGS={
 'eknc':'同じ移動球の中心V*n*tから各空間座標への差を半径で割り、三成分ベクトルとして返す。球面上で外向きの単位法線になる。波面法線nや球の並進速度V*nそのものとは区別し、正の半径と球面所属は呼出側で要求する。',
 'eknd':'同じ球面・座標時刻で、既存ekk6の相対流J−rho*V*nを外向き法線ekncへ射影した符号付き流。時刻を別々に取り直さず、静止面を横切るJだけに替えない。',
 'ekne':'同じ符号付き相対法線流ekndの正の部分。単一の連続体流モデルで外向きに通過する局所量を表す。面全体の積分や、別方向のモードごとの巨視的に相殺した流を復元する量ではない。',
 'eknf':'同じekndの負号を反転した値の正の部分。外向きと逆の、内向きの局所通過量。',
 'ekng':'同じ時刻の移動球面上で、有効で非負の密度、有効な流の三成分、外向き法線の単位長を要求し、局所の外向きekneと内向きeknfを共に零とする。球面の異なる箇所で流入出が相殺するだけの条件とは分ける。',
 'eknh':'有効な四座標が同じ移動球の表面にあるなら、その同じ点でekngが成立するという点条件。表面の外や内部の点へ球面法線の主張を課さず、全時刻での成立は別に量化する。',
 'ekni':'有効で正のVと半径・単位方向の同じ球について、全実数の四座標でeknhを要求する。球面の全表面要素・全時刻の局所無流出入であり、有限の時刻標本や球全体の正味流零へ縮めない。',
 'eknj':'有効な正の光速度・半径・位相率・換算係数と、同じ単位波面法線・六係数の横波seajを要求する数値的な平面波条件。流出入零や輸送される密度の不変性を前提へ入れない。共通波形を掛ける代数には正弦の周期平均や非零振幅は不要。',
 'eknk':'同じ平面波位相ekbfと共通波形から構成した瞬間流ekka・瞬間密度ekkyについて、同じV*nで動く球の全点全時刻の無流出入ekniを述べる。平均密度を瞬間流へ混ぜない。',
 'eknl':'同じ平面波設定について、初期位置からV*nで進むsegbの経路を取り、球の閉内部・表面への所属が初期時刻と同じであるsegfを保持する。その同じ経路で位相と非負の瞬間密度が初期値に等しい。表面の無流出入だけから内部での生成消滅の不存在を推論せず、内部輸送の条件を別に明示する。',
 'eknm':'同じ平面波設定で、初期時刻の閉内部にある全初期位置と全実時刻についてeknlを要求する。球内部の全経路に沿った位相と瞬間密度の持続であり、表面の軌跡だけ又は任意ラベル集合の不変へ替えない。',
 'eknn':'同じwave/process/frame/校正単位/範囲/状況/部分について、球の全時刻の閉内部eklwを領域として、同じ平面波の瞬間流ekkbと瞬間密度ekkz、部分の領域割当eistm及びeknjを結ぶ。先行する局所近似から全時刻への物理的外挿を証明するものではなく、この理想モデルを全領域履歴に採用する追加の明示条件である。',
 'ekno':'eknnの同じ物理的な設定、eknkの全表面・全時刻の局所無流出入、eknmの全内部経路での密度持続を連言する。領域割当だけの保存や、単なる正味流零と区別する。光子の同一性又は別モード間の交換を記述するものではない。',
 'eknp':'前二文と同じ70役割の平均総量設定ekmoを保ち、同じK側の波・過程・単位・部分・半径・六係数・位相率についてeknnの全時刻モデルを加える。範囲は同じ第八節eistk。先行の局所モデルを暗黙に無限領域へ拡張しない。',
 'eknq':'同じ70役割から、eknpと同じK側の設定をeknoへ渡す輸送の帰結候補。別の波・部分・半径を成功例として選び直さない。原文の著者帰属と同じ光の集合という記述の読みは次の統合へ残す。',
}
LIMITS=[
 'u0203[422,597)–u0204–u0205の球面・無流出入・同じ光の集合へ必要な依存群。旧388主張と通読判断を保持し、新しい文又は全単位の完成判断はまだ増やさない。',
 '球面は原文M0355の(x−Vat)²+(y−Vbt)²+(z−Vct)²=R²。波面法線n=(a,b,c)に沿って球全体が並進し、球の外向き法線は(x−Vat,y−Vbt,z−Vct)/Rである。二つの法線を同一視しない。',
 'keine Energie hindurchを単一の平面波連続体における局所的な相対流の不存在として準備する。各点の内向き・外向きの正の部分を共に零にし、球全体の正味積分だけの相殺は認めない。任意の複数モードの反対向き移転をPoyntingベクトルの正負だけから分解したとは主張しない。',
 '先行の仕事基準に校正された同じ瞬間流と瞬間密度を使う。正弦の節で密度零も許し、平均A²/(8pi)を瞬間的な通過量へ代入しない。光速度で動く幾何学的境界は観測者の静止系ではなく、v=VのLorentz変換は行わない。',
 '全実時刻の球内部を覆う流と密度の物理モデルをeknnで明示して採用する。先行の局所近似・有限の領域時間に対する妥当性から、この全時刻の採用は自動的には従わない。球を永久に追跡する理想的な平面波モデルとして後続の本文読解へ接続する必要がある。',
 '境界を通らないだけでは、内部での生成消滅や内容の同一性を保証しない。全内部初期位置について、経路x(t)=x0+V*n*tで位相と瞬間密度が保たれることを別に記述する。並進は体積を保存するというユークリッド幾何の読みであり、一般の輸送定理・連続の式又は三次元測度をここで自動証明しない。',
 '任意ラベル集合segiの所属一致ではなく、同じ物理的流・密度のモデルと同じ球へ輸送を結ぶ。それでも同じ光の集合をどの連続体の同一性として読むか、原文のwir können daher sagenという帰結提示、d.h.と新系エネルギーの問いは未統合である。',
 '有限の有理切断例では共通波形に非定数の有理関数を使い、正弦そのものの全域解析の代用にはしない。代数的な相対流零と位相の輸送は波形の値の同一性で成立する。全実数・関数域の有限評価は拒否し、束縛検査と実際の数値本体を分ける。',
]

def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b');mul=lambda a,b:k('shv',a,b)
    valid=lambda xs:both(*(k('ba',x) for x in xs));positive=lambda x:both(k('ba',x),k('bg',zero,x))
    coords=args(COORDS);V=v('light');direction=[v(n) for n in ('ax','ay','az')];radius=v('radius')
    normal=[mul(k('bf',v(x),mul(mul(V,n),v('time'))),k('sjd',radius)) for x,n in zip(('x','y','z'),direction)]
    text=define('eknc',OLD+COORDS,k('ekbe',*normal),POINT)
    normal=k('eknc',*args(OLD),*coords);rel=k('ekk6',v('flux'),v('densityfield'),k('ekk7',V,*direction))
    terms=[mul(app(normal,k(axis)),app(app(rel,k(axis)),*coords)) for axis in ('yn','yo','yp')]
    text+=define('eknd',SURFACE+COORDS,k('bd',terms[0],k('bd',terms[1],terms[2])),R)
    signed=k('eknd',*args(SURFACE),*coords)
    for name,value in [('ekne',signed),('eknf',k('be',signed))]:text+=define(name,SURFACE+COORDS,k('szi',k('bg',value,zero),zero,value),R)
    rho=app(v('densityfield'),*coords);flux=[app(app(v('flux'),k(axis)),*coords) for axis in ('yn','yo','yp')]
    surface=k('secb',*args(OLD),*coords)
    text+=define('ekng',SURFACE+COORDS,both(surface,valid([rho,*flux]),k('bc',zero,rho),k('sca',k('seag',*[app(normal,k(axis)) for axis in ('yn','yo','yp')]),one),*(k('sca',k(name,*args(SURFACE),*coords),zero) for name in ('ekne','eknf'))))
    text+=define('eknh',SURFACE+COORDS,op('y',both(valid(coords),surface),k('ekng',*args(SURFACE),*coords)))
    shape=k('sege',*args(OLD),zero,zero,zero)
    text+=define('ekni',SURFACE,both(shape,quantified('f',COORDS,k('eknh',*args(SURFACE),*coords))))
    text+=define('eknj',PLANE,both(shape,positive(v('coefficient')),positive(v('rate')),k('seaj',*direction,*[v(n) for n in ('ex','ey','ez','hx','hy','hz')])) )
    phase=k('ekbf',V,v('rate'),*direction);actual={n:v(n) for n,t in PLANE}|dict(phase=phase)
    density=k('ekky',*[actual[n] for n,t in SCALAR]);flux=k('ekka',*[actual[n] for n,t in VECTOR])
    text+=define('eknk',PLANE,k('ekni',flux,density,*args(OLD)))
    offsets=[v(n) for n in ('ox','oy','oz')];point=k('segb',V,*direction,*offsets,v('time'))
    trace=[app(point,k(axis)) for axis in ('yn','yo','yp')]+[v('time')];initial=offsets+[zero]
    at=app(density,*trace);before=app(density,*initial)
    text+=define('eknl',PLANE+TRACER,both(k('eknj',*args(PLANE)),k('segf',*args(OLD),*offsets,v('time')),k('sca',app(phase,*trace),app(phase,*initial)),valid([at,before]),k('bc',zero,at),k('sca',at,before)))
    inside=both(valid(args(TRACER)),k('secc',*args(OLD),*initial))
    text+=define('eknm',PLANE,both(k('eknj',*args(PLANE)),quantified('f',TRACER,op('y',inside,k('eknl',*args(PLANE),*args(TRACER))))))
    actual={n:v(n) for n,t in FRAME}|dict(phase=phase,region=k('eklw',*args(OLD)))
    text+=define('eknn',FRAME,both(k('eknj',*args(PLANE)),k('ekkb',*[actual[n] for n,t in MODEL]),k('ekkz',*[actual[n] for n,t in DENSITY_MODEL]),k('eistm',*[actual[n] for n,t in LOCATION])))
    text+=define('ekno',FRAME,both(k('eknn',*args(FRAME)),k('eknk',*args(PLANE)),k('eknm',*args(PLANE))))
    actual={n:v(n) for n,t in TOTAL}|dict(scope=k('eistk'))
    text+=define('eknp',TOTAL,both(k('ekmo',*args(TOTAL)),k('eknn',*[actual[n] for n,t in FRAME])))
    text+=define('eknq',TOTAL,k('ekno',*[actual[n] for n,t in FRAME]))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==388
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='moving_surface_local_transfer_and_interior_advection_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/volume-denial-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
