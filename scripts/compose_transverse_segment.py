"""Compose a complete material axis segment and its current endpoint records."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_reciprocal_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_material_body_motion import FAMILY
from scripts.compose_rod_geometry import AXIS
from scripts.compose_rod_methods import history,coords,interval
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-reciprocal-claim.noema';PARENT_BASIS='data/reciprocal-claim-basis-v1.json'
FULL='examples/v014/einstein-transverse-segment.noema';CORE='examples/v014/transverse-segment-core.noema'
BASIS='data/transverse-segment-basis-v1.json';ANNOTATIONS='data/transverse-segment-identifiers-v1.json'
SNAPSHOT=[('members','h[a] c')]+[(a,FAMILY) for a in ('x','y','z')]+[('time',R),('extent',R)]
MEANINGS={
 'ejb7':'有効な三位置値が第一・第三成分零、第二成分が0から正のextentまでの閉区間にある。二端を含み、範囲外や軸からの横ずれを許さない。',
 'ejca':'同じ時刻の全成員の位置がejb7の区間内にあり、0からextentの全実数高さについて同じ成員集合のいずれかがその位置を占める。区間への包含だけでなく、穴のない全区間への被覆を保持する。物質点の同一性や履歴は利用側のeiad/eipeへ結ぶ。',
 'ejcb':'同じ物体の完全な全物質点履歴・剛性・静止・長軸端標識と正の軸長をeipeで要求し、正の時間幅の全時刻でejcaの閉区間全体を占める。両端標識をそれぞれ(0,0,0)と(0,extent,0)へ固定し、両端だけが正しい穴あきの配置では満たさない。',
 'ejcc':'同じ横棒と二端標識をkの全履歴へ渡し、現在の三軸構造と第二軸の割当て、ejcbの全区間占有へ結ぶ。幾何学的な第二軸の指定部分を理想化した線状棒として扱い、既存の軸材料を実際に切断したという操作は加えない。',
 'ejcd':'同じ棒・二端標識のKでの完全な全物質点と長軸の履歴を保持し、全成員の同じ正X方向・同じ正速度の等速並進eipfを課す。全区間の各時刻で、二端の実際の差ベクトルとその速度ベクトルがeiu6の非退化な直交を満たす。端点だけの移動や時点を混ぜた直交に替えない。',
 'ejce':'同じ棒の同じ端標識・出来事・系・文脈について、現在の四座標記録eiyxを端点の場所xg/cb、世界線と座標sb、同じ棒の履歴関数と区間に結ぶ。四成分は同じ一記録から取り、別時刻や別端点の関数を代用しない。',
 'ejcf':'同じzguの横棒、η=0側zgv、η=l側zgw、正のl=zgzを、kの全区間占有ejccとKの全点並進・自軸との直交ejcdへ結ぶ。速度は同じzb7で、前段の縦棒xiやその速度ybを混ぜない。',
}
LIMITS=[
 'u0097–u0100に必要な棒全体の軸区間占有、全点並進と自軸への直交、現在の端点記録への接続の依存群。意味への問い・取り上げる行為・二端座標の一般表示・本文帰属・全文判断はまだ追加しない。',
 '原文のη軸の指定部分を、同じ座標区間を全て占める理想化した線状の棒として読む。0≤η≤lを含む閉区間と正のlを採る。既存の軸の物質点を実際に切り離す操作や、任意の厚い棒が数学的な直線そのものであるという主張を加えない。',
 'ejcaの全高さへの存在条件を端点や有限の標本で代用しない。全成員の包含と全高さの被覆を同時に要求し、静止と全履歴はeipeへ保持する。実数・関数の全域量化は有限評価器の拒否を保ち、局所例化を一般的な被覆証明としない。',
 '各系の区間と時刻規約はその系のeisls/eisltと同じta/rbに従う。Kとkの同時刻値や区間端を無条件に等置しない。二端標識は長軸の幾何学的中心であり、個体として物質点と同一とは要求しない。',
 'Kでの正速度vは同じ既出のzb7。全成員のX方向並進eipfと全時刻の実際の端差の直交を使う。方向ラベルだけ、端点だけ、正しい一時刻だけで横棒の運動を代用しない。',
 '現在の端点記録をeiyxと同じ世界線・棒の座標族へ結ぶ。未知の座標は零に補わず、旧shd/zgj/ssaの未接続な物理条件をそのまま使わない。φの正値・対称性・φ=1、長さl/φの物理的解釈の結論はまだ加えない。',
]


def definitions():
    zero=k('bb','n p a b');extent=v('extent');time=v('time')
    text=define('ejb7',[(n,R) for n in ('x','y','z','extent')],both(*(k('ba',v(n)) for n in ('x','y','z')),k('sbg',extent),k('sca',v('x'),zero),k('sca',v('z'),zero),k('bc',zero,v('y')),k('bc',v('y'),extent)))
    at=lambda axis,point:app(app(v(axis),point),time)
    member=lambda p:app(v('members'),p)
    contained=q('f','point','a',op('y',member(v('point')),k('ejb7',*(at(a,v('point')) for a in ('x','y','z')),extent)))
    hit=q('g','point','a',both(member(v('point')),*(k('sca',at(a,v('point')),value) for a,value in (('x',zero),('y',v('height')),('z',zero)))))
    covered=q('f','height',R,op('y',both(k('ba',v('height')),k('bc',zero,v('height')),k('bc',v('height'),extent)),hit))
    text+=define('ejca',SNAPSHOT,both(k('ba',time),k('sbg',extent),contained,covered))
    point_on=lambda name,height:both(*(k('sca',at(a,v(name)),value) for a,value in (('x',zero),('y',height),('z',zero))))
    alltimes=q('f','time',R,op('y',k('lg',v('lower'),v('upper'),time),both(k('ejca',*[v(n) for n,_ in SNAPSHOT]),point_on('firstend',zero),point_on('lastend',extent))))
    text+=define('ejcb',AXIS+[('extent',R)],both(k('eipe',*[v(n) for n,_ in AXIS],extent),k('bg',v('lower'),v('upper')),alltimes))
    body=v('body');low=v('low');high=v('high');ctx=v('context');moving=k('zbm');rest=k('ra')
    fields=[('body','a'),('low','a'),('high','a'),('context','d')]
    text+=define('ejcc',fields+[('extent',R)],both(k('xa',body),k('sfb',moving,ctx),k('zbw',moving,k('zbo',moving,k('yo'),ctx),k('yo'),ctx),k('ejcb',*history(body,moving,ctx),low,high,extent)))
    family=coords(body,rest,ctx)
    delta=[k('bf',app(app(fn,high),time),app(app(fn,low),time)) for fn in family]
    perpendicular=q('f','time',R,op('y',k('lg',*interval(rest,ctx),time),k('eiu6',v('speed'),zero,zero,*delta)))
    text+=define('ejcd',fields+[('speed',R)],both(k('eipc',*history(body,rest,ctx),low,high),k('eipf',*history(body,rest,ctx),v('speed')),perpendicular))
    endpoint=v('endpoint');event=v('event');record=v('record');frame=v('frame');stamp=k('zc6',record,k('zc7'))
    position=[k('zc6',record,k(a)) for a in ('yn','yo','yp')]
    located=q('g','place','a',both(k('xg',endpoint,event,v('place'),frame,ctx),k('cb',event,v('place'),frame)))
    matches=[k('sca',actual,app(app(fn,endpoint),stamp)) for actual,fn in zip(position,coords(body,frame,ctx))]
    text+=define('ejce',[(n,'a') for n in ('body','endpoint','event','record','frame')]+[('context','d')],both(k('xf',endpoint,body,frame,ctx),k('eiyx',event,record,frame,ctx),located,k('lg',*interval(frame,ctx),stamp),k('sb',endpoint,event,frame,ctx,k('ta'),k('rb'),stamp,*position),*matches))
    text+=define('ejcf',[('context','d')],both(k('ejcc',k('zgu'),k('zgv'),k('zgw'),ctx,k('zgz')),k('ejcd',k('zgu'),k('zgv'),k('zgw'),ctx,k('zb7'))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==315;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='complete_transverse_material_segment_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/reciprocal-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
