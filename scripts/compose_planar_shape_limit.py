"""Connect the whole moving shape to its transverse image in the light-speed limit."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_directional_contraction_claim import ROOT,read
from scripts.compose_material_shape_dimensions import SETTING
from scripts.compose_solid_sphere_geometry import POSITION,args,bind
from scripts.compose_shape_contraction import SHAPE
from scripts.compose_rod_methods import interval
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-directional-contraction-claim.noema';PARENT_BASIS='data/directional-contraction-claim-basis-v1.json'
FULL='examples/v014/einstein-planar-shape-limit.noema';CORE='examples/v014/planar-shape-limit-core.noema'
BASIS='data/planar-shape-limit-basis-v1.json';ANNOTATIONS='data/planar-shape-limit-identifiers-v1.json';INDEX=333
BASE=[('shape',SHAPE),('light',R),('time',R)]
PRIMITIVES={'eisod':'u0116第二文のv=Vで面状になるという表記を、同じ有限形状の光速未満からの極限として読む解釈注記の箇所。著者の本文箇所zh7とは分ける。'}
MEANINGS={
 'ejg5':'指定された三位置の形状を横二座標へ射影する。ある有効な縦位置で同じ横二座標が元の形状に含まれることを要求し、横平面全体や横二方向の外接長方形へ置き換えない。',
 'ejg6':'指定縦位置の平面上に、同じ元の形状の横二座標射影ejg5を置いた像。横方向の穴や非連結部分を保持し、縦方向の異なる点は同じ横位置へ重なることを許す。',
 'ejg7':'同じ光速・速度・観測時刻・静止側縦位置について、√(1−(v/V)²)倍した静止縦位置にvtを足す前向きの縦位置の数値核。適用域は利用側で要求し、有限βの逆変換をこの関数に使わない。',
 'ejha':'光速未満の非負速度と同じ時刻で、元の形状のある縦位置をejg7へ写し、横二座標を保った位置が指定位置になるという前向きの全形状像。元の位置の存在と同じ横二座標を保持する。',
 'ejhb':'同じ元の形状に含まれる全有効三位置について、ejg7による縦位置が同じ平面位置Vtから指定正精度未満の距離にある。単一の中心や幅だけではなく、形状内の全点を共通の精度で扱う。',
 'ejhc':'同じ有限形状と固定時刻に対し、光速未満の速度がVへ集積し、任意の正精度ごとに正の近傍を選べば、その中の全速度で全元位置がejhbを満たすという一様な平面への接近。近傍は形状と時刻に依存し、全物体に共通とはしない。',
 'ejhd':'光速未満の全非負速度と全有効三位置について、前向き像ejhaと既存の逆代入による形状stvが双方向に一致する。極限を取る形状族を前の座標変換の形状と接続し、境界v=Vでβを評価しない。',
 'ejhe':'同じ物体の現在の全K時刻の完全な変換形状ejgmを保持し、その同じ静止側形状について各K対象時刻でejhcの全点の平面接近とejhdの光速未満での一致を述べる。速度を変えた比較を加速履歴へ替えない。',
 'ejhf':'有限な静止三幅を持つ全ての適格物体・全任意形状についてejheが成立するという面状化の内容。極限の平面上の横像はejg6で与え、一般の物体を原点中心の球へ縮めない。',
 'ejhg':'著者がu0116第二文で、光速での面状化をejhfの明示した極限の読みで提示する。光速ちょうどで有限な変換系が実現するという意味を加えない。',
 'ejhh':'同じ全運動対象の面状化ejhgを述べるメッセージ。',
 'ejhi':'第二文の面状化を同じ著者・論説へ帰属し、第一文の寸法変化に続ける。',
 'ejhj':'先の全時刻の寸法変化ejgtから、同じ元形状の光速未満からの面状化ejhfを読む追加解釈をzflで注記する。著者の発話メッセージの外に置く。',
}
LIMITS=[
 'u0116第二文[271,390)とM0206のv=Vを原刊903頁へ照合する。原文の等号は、同じ形状族の光速未満からの極限として読む追加解釈を明示する。第一文と第三文をこの文へ混ぜず、単位全体の判断は第三文の接続後に行う。',
 '面状とは同じ形状の横二座標射影が縦位置Vtの平面上に残ることと読む。横方向の穴・非凸・非連結を埋めず、平面全体を占める、物質点が消える、必ず二次元の内点を持つという条件を加えない。線や零幅の退化例も許す。',
 '前向き像はx=f(v)x0+vt,y=y0,z=z0。v<Vでは既存stvと一致する関係を要求し、同じ全物質点の実際の占有形状ejgmに接続する。極限像は独立にejg6で定義し、v=Vの有限βや正則なLorentz変換、光速で実在する物体を仮定しない。',
 '各固定の有限形状・観測時刻について、全元位置が同じ正精度で平面へ近づく条件を使う。有限三幅の読みを継承するが、近傍を全物体・全時刻に共通にすることや、無限に広い形状の一様収束は要求しない。',
 '横二座標は各点で保たれ、ejg5/ejg6により極限像の全ての横位置にも元位置が存在する。少数の端点、中心、縦幅だけの零極限を全形状の面状化と同一視しない。',
 '速度の比較は同じ静止側形状に対する数式の族であり、同じ物体を実際に加速させる履歴ではない。Kの同時刻座標で見た形状を扱い、光の到着による画像の見かけではない。',
 '全位置・速度・精度・近傍の量化を保つ。有限区別例は結合と境界を検査し、一般実数域の収束証明・物理的真理・原文との自動同値証明を兼ねない。第三文の適用限界と後続への予告は残る。',
]

def definitions():
    text='r eisod[] a.\n';shape=v('shape');light=v('light');time=v('time');speed=v('speed');epsilon=v('epsilon');pos=args(POSITION);zero=k('bb','n p a b')
    valid=lambda xs:both(*(k('ba',x) for x in xs))
    domain=both(k('ba',speed),k('bc',zero,speed),k('bg',speed,light))
    projection=q('g','originx',R,both(k('ba',v('originx')),app(shape,v('originx'),pos[1],pos[2])))
    text+=define('ejg5',[('shape',SHAPE)]+POSITION[1:],both(valid(pos[1:]),projection))
    text+=define('ejg6',[('shape',SHAPE),('plane',R)]+POSITION,both(valid([v('plane'),*pos]),k('sca',pos[0],v('plane')),k('ejg5',shape,*pos[1:])))
    forward=k('bd',k('shv',k('stw',light,speed),v('originx')),k('shv',speed,time))
    text+=define('ejg7',[(n,R) for n in ('light','speed','time','originx')],forward,R)
    witness=q('g','originx',R,both(k('ba',v('originx')),app(shape,v('originx'),pos[1],pos[2]),k('sca',pos[0],k('ejg7',light,speed,time,v('originx')))))
    text+=define('ejha',BASE+[('speed',R)]+POSITION,both(k('sbg',light),k('ba',time),domain,valid(pos),witness))
    plane=k('shv',light,time)
    point_condition=op('y',both(valid(pos),app(shape,*pos)),both(k('lb',k('ejg7',light,speed,time,pos[0]),plane,epsilon),k('ejg6',shape,plane,plane,*pos[1:])))
    text+=define('ejhb',BASE+[('epsilon',R),('speed',R)],both(k('sbg',light),k('ba',time),k('sbg',epsilon),domain,bind(('px','py','pz'),R,'f',point_condition)))
    accumulation=q('f','radius',R,op('y',k('sbg',v('radius')),k('suo',light,v('radius'))))
    near=both(domain,k('bg',k('bf',light,speed),v('delta')))
    uniform=q('f','epsilon',R,op('y',k('sbg',epsilon),q('g','delta',R,both(k('sbg',v('delta')),q('f','speed',R,op('y',near,k('ejhb',shape,light,time,epsilon,speed)))))))
    text+=define('ejhc',BASE,both(k('sbg',light),k('ba',time),accumulation,uniform))
    agree=bind(('px','py','pz'),R,'f',op('y',valid(pos),op('z',k('ejha',shape,light,time,speed,*pos),app(k('stv',shape,light,speed,time),*pos))))
    text+=define('ejhd',BASE,both(k('sbg',light),k('ba',time),q('f','speed',R,op('y',domain,agree))))
    body=v('body');ctx=v('context')
    every=q('f','time',R,op('y',k('lg',*interval(k('ra'),ctx),time),both(k('ejhc',shape,k('tc'),time),k('ejhd',shape,k('tc'),time))))
    text+=define('ejhe',SETTING,both(k('ejgm',*args(SETTING)),every))
    general=q('f','body','a',q('f','shape',SHAPE,op('y',k('ejgp',body,shape,k('zb6')),k('ejhe',body,shape,k('zb6')))))
    text+=content('ejhf',general)
    text+=content('ejhg',k('uh',k('zh7'),k('rd'),quote('ejhf'),k('eisn5'),v('point')))
    text+='d ejhh[] f[j s[k ejhg[]]].\n'
    text+=define('ejhi',[],both(k('eir3',k('zh7'),k('rd'),k('eirf'),quote('ejhh'),k('ri')),k('ue',k('zh6'),k('zh7'),k('ri')),op('u',op('e',k('zh6'),k('zh7')))))
    text+=define('ejhj',[],k('zfl',k('eisod'),k('rd'),quote('ejgt'),quote('ejhf'),k('eisn5'),k('ri')))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejhi','ejhj')];added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='whole_shape_planar_limit_with_transverse_projection',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX,INDEX+1]).document
    ann=json.loads(read('data/directional-contraction-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
