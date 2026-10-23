"""Compose closed material balls, their boundaries and current point records."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_physical_meaning_heading import ROOT,read
from scripts.compose_material_body_motion import FIELDS,FAMILY
from scripts.compose_rod_methods import history,coords,interval
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-physical-meaning-heading.noema';PARENT_BASIS='data/physical-meaning-heading-basis-v1.json'
FULL='examples/v014/einstein-solid-sphere-geometry.noema';CORE='examples/v014/solid-sphere-geometry-core.noema'
BASIS='data/solid-sphere-geometry-basis-v1.json';ANNOTATIONS='data/solid-sphere-geometry-identifiers-v1.json'
POSITION=[(n,R) for n in ('px','py','pz')];CENTER=[(n,R) for n in ('cx','cy','cz')]
SNAPSHOT=[('members','h[a] c')]+[(n,FAMILY) for n in ('x','y','z')]+[('time',R)]
SPHERE=CENTER+[('radius',R)]
MEANINGS={
 'ejex':'二つの三位置値の各差の二乗和。共通の直交基底・尺度の下で距離の二乗となる数値核。有効性と物理的な帰属は利用側で要求する。',
 'ejey':'有効な三位置値が、指定した有効な中心から正の半径未満の距離にあるという開球の条件。境界を含めない。',
 'ejez':'有効な三位置値が、指定した有効な中心から正の半径以下の距離にあるという閉球の条件。内部と境界を含む。',
 'eje2':'同じ時刻・同じ三座標族において、指定三位置を占める同じmembers内の物質点が存在する。三成分を別々の物質点から集めず、範囲外の点で占有を代用しない。',
 'eje3':'同じ物質点集合の占有地点であり、任意の正の近傍半径に対し、その開近傍内に同じ集合が占めない位置が存在する。閉じた占有領域に対する物質境界の条件。球の半径や球面式をこの定義へ埋め込まない。',
 'eje4':'全成員の位置が同じ閉球に含まれ、その閉球内の全実数三位置に同じ集合の物質点が存在するという、閉じた球体の完全な占有。有限の表面点、包含だけ、内部の穴がある配置で代用しない。',
 'eje5':'同じ全物質点の完全な履歴・校正された剛性eigy・静止eiahを保持し、正の時間幅の全時刻に同じ中心と半径の閉球をeje4で占める。同じ静止系での球体の理想化。棒の長軸や二端標識は要求しない。',
 'eje6':'同じ物体の同じ物質点・出来事・四座標記録を、現在のeiyx、世界線のsb、同じ系の対象区間と座標族へ結ぶ。物質点所属eirhと三成分の一致を保ち、旧shdへ戻らない。',
 'eje7':'同じ物体の完全な全物質点履歴について、全成員・対象区間の全時刻にeje6の現在出来事記録が存在する。全称の前提が空のときだけ真となる記録条件を避け、各記録の時刻値も同じ指定時刻へ合わせる。',
 'ejfa':'現在の同じ出来事記録の時刻・三位置が、その時刻における同じ物体の閉じた占有領域の境界eje3上にある。対象出来事は必ずその物体自体の世界線上とは要求せず、光の交差など同所の出来事も扱える。全履歴・閉領域性は上位の設定で保つ。',
 'ejfb':'指定系の測定された原点を三成分零へ結び、同じ系・物体のeje5を中心零の同じ正の半径へ適用し、全成員・全時刻の現在記録eje7を保持する。中心という未接続な名詞で球体の位置を済ませない。',
 'ejfc':'同じ球体のkでの中心原点・静止・剛性・完全な形状と現在記録を保持し、Kの全物質点に同じ正X速度vの並進を課す。K/kの全系並進の同じ三成分へ結び、両系の時刻区間を等置しない。',
}
LIMITS=[
 'u0110–u0111と著者脚注u0281へ向けた依存群であり、著者の考察行為・球面式の提示・脚注の説明及び通読判断はまだ追加しない。327主張と全111単位の既存判断を保持する。',
 'eje4/eje5は内部を含めて閉球を占める連続体モデルである。密度の一様性や質量は要求しないが、殻だけ又は内部空洞を持つ物体の外形とは異なる。このモデルを原文へ採用する場合は明示した解釈として扱い、Kugelgestaltという語から物質の内部充填が無条件に従うとはしない。',
 'eje3は閉じた占有領域について、占有地点の任意に小さい開近傍に非占有地点があるという境界である。一般の非閉集合の閉包にある非占有点までを境界に含む定義ではない。球面条件ssyを境界の定義へ循環的に入れない。',
 '閉球の全実数三位置への被覆と、境界の全正近傍半径を保持する。局所の候補位置や近傍を例化する検査は一般の被覆・境界の証明ではなく、未例化の実数域は有限評価を拒否する。',
 'eje5は指定系の静止と全点対距離の剛性を使う。同じ物体の全物質点を追い、棒の長軸・二端標識・線状の配置を球体の条件にしない。幾何学的な中心は中心対称な閉球の中心として指定する。',
 '現在記録の全時刻での存在、同じ時刻の境界、同じ出来事の座標を区別して結ぶ。境界上で起きる出来事を、必ず同じ物質点の出来事へ狭めない。未知座標や未測定を零で補わない。',
 'Kとkの時刻はそれぞれの測定規約を保つ。ejfcは同じzb7の全物質点の正X並進と系全体のeiojを結ぶが、最終四式・球面の全記録への同値・著者の原文提示への接続は後続。',
]

def args(fields):return [v(n) for n,_ in fields]
def bind(names,sort,kind,body):
    for n in reversed(names):body=q(kind,n,sort,body)
    return body

def definitions():
    pos=args(POSITION);center=args(CENTER);radius=v('radius');time=v('time')
    ds=[k('bf',a,b) for a,b in zip(pos,center)];sq=[k('shv',d,d) for d in ds]
    text=define('ejex',POSITION+CENTER,k('bd',sq[0],k('bd',sq[1],sq[2])),R)
    for name,cmp in (('ejey','bg'),('ejez','bc')):
        text+=define(name,POSITION+SPHERE,both(*(k('ba',x) for x in pos+center),k('sbg',radius),k(cmp,k('ejex',*pos,*center),k('shv',radius,radius))))
    at=lambda a,p:app(app(v(a),p),time)
    occupied=q('g','point','a',both(app(v('members'),v('point')),*(k('ba',at(a,v('point'))) for a in ('x','y','z')),*(k('sca',at(a,v('point')),x) for a,x in zip(('x','y','z'),pos))))
    text+=define('eje2',SNAPSHOT+POSITION,both(k('ba',time),*(k('ba',x) for x in pos),occupied))
    outside=args([(n,R) for n in ('ox','oy','oz')]);epsilon=v('epsilon')
    close=k('ejey',*outside,*pos,epsilon)
    witness=bind(('ox','oy','oz'),R,'g',both(close,op('u',k('eje2',*args(SNAPSHOT),*outside))))
    boundary=q('f','epsilon',R,op('y',k('sbg',epsilon),witness))
    text+=define('eje3',SNAPSHOT+POSITION,both(k('eje2',*args(SNAPSHOT),*pos),boundary))
    contained=q('f','point','a',op('y',app(v('members'),v('point')),k('ejez',*(at(a,v('point')) for a in ('x','y','z')),*center,radius)))
    covered=bind(('px','py','pz'),R,'f',op('y',k('ejez',*pos,*center,radius),k('eje2',*args(SNAPSHOT),*pos)))
    text+=define('eje4',SNAPSHOT+SPHERE,both(k('ba',time),*(k('ba',x) for x in center),k('sbg',radius),contained,covered))
    alltimes=q('f','time',R,op('y',k('lg',v('lower'),v('upper'),time),k('eje4',*args(SNAPSHOT),*center,radius)))
    text+=define('eje5',FIELDS+SPHERE,both(k('bg',v('lower'),v('upper')),k('eigy',*args(FIELDS)),k('eiah',*args(FIELDS)),alltimes))
    body=v('body');point=v('point');event=v('event');record=v('record');frame=v('frame');ctx=v('context');stamp=k('zc6',record,k('zc7'))
    position=[k('zc6',record,k(a)) for a in ('yn','yo','yp')]
    member=lambda p:k('eirh',body,p,ctx)
    current=[('body','a'),('point','a'),('event','a'),('record','a'),('frame','a'),('context','d')]
    text+=define('eje6',current,both(member(point),k('eiyx',event,record,frame,ctx),k('lg',*interval(frame,ctx),stamp),k('sb',point,event,frame,ctx,k('ta'),k('rb'),stamp,*position),*(k('sca',actual,app(app(fn,point),stamp)) for actual,fn in zip(position,coords(body,frame,ctx)))))
    base=[('body','a'),('frame','a'),('context','d')]
    witness=bind(('event','record'),'a','g',both(k('eje6',*args(current)),k('sca',stamp,time)))
    every=q('f','point','a',q('f','time',R,op('y',both(member(point),k('lg',*interval(frame,ctx),time)),witness)))
    text+=define('eje7',base,both(k('bg',*interval(frame,ctx)),k('eiad',*history(body,frame,ctx)),every))
    snapshot=['i[point a]['+member(v('point'))+']',*coords(body,frame,ctx),stamp]
    text+=define('ejfa',[(n,s) for n,s in current if n!='point'],both(k('eiyx',event,record,frame,ctx),k('lg',*interval(frame,ctx),stamp),k('eje3',*snapshot,*position)))
    zero=k('bb','n p a b');origin=k('zbn',frame,ctx)
    text+=define('ejfb',base+[('radius',R)],both(k('zbv',frame,origin,ctx),*(k('eixu',origin,frame,k(a),zero,ctx) for a in ('yn','yo','yp')),k('eje5',*history(body,frame,ctx),zero,zero,zero,radius),k('eje7',body,frame,ctx)))
    K=k('ra');moving=k('zbm');speed=k('zb7')
    text+=define('ejfc',[('body','a'),('radius',R),('context','d')],both(op('u',op('e',K,moving)),k('ejfb',body,moving,ctx,radius),k('eje7',body,K,ctx),k('eipf',*history(body,K,ctx),speed),k('eioj',K,moving,k('ta'),k('rb'),ctx),*(k('sca',k('eislc',K,moving,k('ta'),k('rb'),k(a),ctx),value) for a,value in (('yn',speed),('yo',zero),('yp',zero)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==327;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements'];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='closed_material_ball_boundary_and_current_records',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/physical-meaning-heading-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
