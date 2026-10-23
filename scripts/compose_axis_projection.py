"""Compose signed orthogonal projection on an actual oriented material axis."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_parallel_choice import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_material_axes import ROLES,dot,sub
from scripts.compose_moving_axes import direction,every_time
from scripts.compose_rod_methods import interval
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-parallel-choice.noema';PARENT_BASIS='data/parallel-choice-basis-v1.json'
FULL='examples/v014/einstein-axis-projection.noema';CORE='examples/v014/axis-projection-core.noema'
BASIS='data/axis-projection-basis-v1.json';ANNOTATIONS='data/axis-projection-identifiers-v1.json'
VECTORS=[(p+a,R) for p in ('p','q','d') for a in ('x','y','z')]
PHYSICAL=[(n,'a') for n in ('axis','origin','guide','place','projection','frame','role')]+[('context','d')]
MEANINGS={
 'eiw4':'原点からの点変位p、射影変位q、非零方向dの有効な九実成分について、qがdと共線でp−qがdと直交する。零のqと零の残差を許す正射影で、軸方向の倍率や正負に依存しない。',
 'eiw5':'有効な変位qと非零の正方向dに対し、qとdの共線性、valueの平方とqの平方長の一致、valueとq・dの正負・零の一致を要求する符号付き距離。単位方向を強制せず、単なる内積値を距離にしない。',
 'eiw6':'同じ非零方向についてeiw4の正射影とeiw5の符号付き距離を結ぶ。射影点を原点に限定せず、点が軸上の場合や原点への射影も含む。実際の測定操作の成立は別に必要。',
 'eiw7':'同じ系・役割に割り当てた物質軸と原点、同じ軸の非零方向標識、対象地点と射影地点を結ぶ。全物質履歴eiv2、系に対する軸の静止eipw、原点と両地点の完全な静止軌道eit2、同じ計量と区間を要求し、指定時刻の実座標差をeiw4へ渡す。',
 'eixa':'eiw7の物理的射影を保ち、同じ軸・系・単位・文脈の正方向記録zsaが存在し、その全記録が実際の非零軸方向と平行で、同じ射影に同じ符号付き距離eiw6を与える。方向標識eismuそのものを正方向とみなさず、食い違う正方向記録を選んで隠さない。',
 'eixb':'同じ軸・原点・方向標識・地点・射影点・系・役割と同じ値について、正の共通区間の全実時刻でeixaを要求する。端点だけや時刻ごとに別の点を選ぶ解釈にしない。',
}
LIMITS=[
 'u0045第一文の座標測定を支える幾何の依存群であり、270の本文主張は変更しない。旧zcw/zcxを自動的に置換した意味判断ではない。',
 '正射影と符号付き距離は既存の操作的読解を具体化する。原文が射影の計算式や測定手順を明記しているとは述べない。',
 '正方向記録zsa/zsbは既存の意味規約を保持する。記録の方向を実際の物質軸へ接続するが、記録自体の物理的取得を数値だけから認定しない。逆向きの物質方向標識、正方向記録の正の倍率、軸の延長上の射影を許す。',
 '各系に固有の計量で表した位置履歴を用いる。二系の座標値・正方向・時計時刻の一致、ローレンツ変換の導出は追加しない。幾何学的標識を物質点に同一視しない。',
 '同じ物差しによる校正済みの距離測定操作、三成分と全空間の存在・一意性、二系の同じ初期計器との接続、時計配置点の時刻設定と設定指示の全体統合は残る。幾何条件の成立だけを測定実行としない。',
 '有限検査は実数切断への有理数埋込みと境界結合を用いる。全実数・全時刻の証明ではなく、元の全実時刻量化は有限評価を拒否する。未知入力を零や偽に置き換えない。',
]

def tracks(point,frame,ctx):return [k('eismh',point,frame,k('ta'),k('rb'),k(a),ctx) for a in ROLES]
def position(point,frame,ctx,time):return [app(fn,time) for fn in tracks(point,frame,ctx)]
def args(fields):return [v(n) for n,_ in fields]

def definitions():
    p=[v('p'+a) for a in 'xyz'];z=[v('q'+a) for a in 'xyz'];d=[v('d'+a) for a in 'xyz']
    zero=k('bb','n p a b');s=v('value');projection=both(*(k('ba',x) for x in p+z+d),k('sbg',dot(d,d)),k('eiu5',*z,*d),k('sca',dot(sub(p,z),d),zero))
    text=define('eiw4',VECTORS,projection)
    signed=both(*(k('ba',x) for x in z+d+[s]),k('sbg',dot(d,d)),k('eiu5',*z,*d),k('sca',k('shv',s,s),dot(z,z)),op('z',k('bg',zero,s),k('bg',zero,dot(z,d))),op('z',k('bg',s,zero),k('bg',dot(z,d),zero)),op('z',k('sca',s,zero),k('sca',dot(z,d),zero)))
    text+=define('eiw5',VECTORS[3:]+[('value',R)],signed)
    text+=define('eiw6',VECTORS+[('value',R)],both(k('eiw4',*p,*z,*d),k('eiw5',*z,*d,s)))
    axis=v('axis');o=v('origin');g=v('guide');place=v('place');foot=v('projection');f=v('frame');c=v('context');t=v('time')
    origin=position(o,f,c,t);point=position(place,f,c,t);projected=position(foot,f,c,t)
    delta=direction(axis,o,g,f,c,t);pdelta=sub(point,origin);qdelta=sub(projected,origin)
    roles=op('x',op('e',v('role'),k('yn')),op('x',op('e',v('role'),k('yo')),op('e',v('role'),k('yp'))))
    core=both(k('va',f),k('ti',k('ta')),k('ci',k('rb')),roles,k('zbv',f,o,c),k('zbw',f,axis,v('role'),c),k('zcu',place,f,c),k('zcu',foot,f,c),k('eisdd',f,k('ta'),k('rb'),c),k('eiv2',axis,o,g,f,c),k('eipw',axis,f,c),*(k('eit2',mark,f,c,k('ta'),k('rb'),*interval(f,c),*tracks(mark,f,c)) for mark in (o,place,foot)),k('ba',t),k('lg',*interval(f,c),t),*(k('ba',x) for x in origin+point+projected),k('eiw4',*pdelta,*qdelta,*delta))
    text+=define('eiw7',PHYSICAL+[('time',R)],core)
    record=k('zsa',v('record'),axis,f,k('ta'),c);positive=[k('zsb',v('record'),k(a)) for a in ROLES]
    oriented=both(k('eiw7',*args(PHYSICAL),t),k('ba',s),q('g','record','a',record),q('f','record','a',op('y',record,both(k('sexc',*delta,*positive),k('eiw6',*pdelta,*qdelta,*positive,s)))))
    text+=define('eixa',PHYSICAL+[('time',R),('value',R)],oriented)
    text+=define('eixb',PHYSICAL+[('value',R)],both(k('bg',*interval(f,c)),every_time(f,c,k('eixa',*args(PHYSICAL),t,s))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==270;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='signed_physical_axis_projection_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/parallel-choice-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
