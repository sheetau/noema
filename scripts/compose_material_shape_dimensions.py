"""Connect arbitrary shapes and directional widths to complete body histories."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_moving_ellipsoid import ROOT,read
from scripts.compose_solid_sphere_geometry import SNAPSHOT,POSITION,args,bind
from scripts.compose_material_body_motion import FIELDS
from scripts.compose_shape_contraction import SHAPE
from scripts.compose_rod_methods import history,coords,interval
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-moving-ellipsoid.noema';PARENT_BASIS='data/moving-ellipsoid-basis-v1.json'
FULL='examples/v014/einstein-material-shape-dimensions.noema';CORE='examples/v014/material-shape-dimensions-core.noema'
BASIS='data/material-shape-dimensions-basis-v1.json';ANNOTATIONS='data/material-shape-dimensions-identifiers-v1.json'
SETTING=[('body','a'),('shape',SHAPE),('context','d')]
AT=[('body','a'),('frame','a'),('context','d'),('time',R)]
WIDTHS=[(n,R) for n in ('properx','propery','properz','observedx','observedy','observedz')]
MEANINGS={
 'ejgg':'同じ時刻と三座標族で同じ全物質点集合が占める三位置の条件をeje2から関数として取り出す。三成分を別の点から集めず、物体表面や外接球を占有領域と混同しない。',
 'ejgh':'同じ時刻の全成員の位置が指定形状を満たし、その形状を満たす全有効実数三位置に成員が存在するという完全な占有。空洞・非凸・非連結・開集合を形状側に許し、球や凸包への充填を要求しない。',
 'ejgi':'同じ全物質点の校正された剛性eigy・静止eiahと正の時間幅を保ち、全対象時刻に同じ任意形状をejghで占める。球の中心・半径や棒の二端を前提にしない。',
 'ejgj':'同じ物体のkにおける静止した任意形状・剛性、両系の全成員全時刻の現在記録、Kの全点の正X並進と同じ系間速度を結ぶ。特定球や閉球連続体に限らない一般の運動設定。',
 'ejgk':'指定物体・系・文脈・時刻について、完全な物質点対応と三座標族をejggへ渡して得る実際の占有形状。時間域・物理的履歴の有効性は利用側で要求する。',
 'ejgl':'指定系の対象時刻における同じ物体の実際の占有形状ejgkについて、指定軸の射影の上限と下限の差sukが指定の有限幅である。達成する端点や凸性を要求せず、空集合・無限幅に有限値を割り当てない。',
 'ejgm':'同じ物体がKの全対象時刻で、静止側の任意形状をβ(x−vt),y,zの代入で変換したstvの全領域を完全に占める。時間零だけ、表面の少数記録だけ、片方向包含だけへ縮めない。',
 'ejgn':'同じ物体の静止側の基準時刻とKの任意対象時刻で六つの有限軸幅が成立するなら、Kの縦幅は静止側縦幅の√(1−(v/V)²)倍、横二幅はそれぞれ同じとなる。無限幅や幅のない集合へ有限寸法を仮定しない。',
 'ejgo':'同じ現在の二系・尺度・速度の下で、全物体・全三位置形状条件についてejgjの運動設定からejgmの全時刻の形状とejgnの三軸幅の関係が従うという一般の内容。著者の提示への接続と通読判断は別途行う。',
}
LIMITS=[
 'u0116第一文の球から任意形状への拡張に必要な依存群。既存332主張と全118単位の意味判断を保持し、第一文の対照・帰結・速さによる縮小の比較、段落後半の極限・適用限界・予告を完成扱いにしない。',
 '物体の全物質点が占める集合と形状条件を双方向に一致させる。任意形状では先の閉球の内部充填を継承せず、空洞・非凸・非連結を許す。開集合にも定義できるが、物理的実在は別である。物質密度・質量・微視的な構成を追加しない。',
 '静止・剛性と現在測定記録、Kでの全点の並進は現在の履歴定義を再利用する。基準時刻はkの対象区間の下端とし、Kとkの時刻値や同時刻面を等置しない。静止により同じ形状を保つ期間についての幅を比較する。',
 '任意形状の変換は既存stvの数値構成を再利用し、現在の完全な占有へ接続する。旧sua/sub/sueのshd/zhu/x4や球専用eje5へ戻らない。基準系は既存の平行軸・共通単位・正X速度0<v<Vの比較設定。',
 '寸法は各座標軸への射影の有限幅として読む。上限と下限を使い、端点達成・連結性・凸性を仮定しない。零幅も許し、無限幅や空集合は有限寸法の関係を満たさない。幅の条件付き関係自体は、有限幅の存在を新たに保証する主張ではない。',
 '三位置・時刻・幅・形状関数の全域量化を保持する。有限評価は引数接続・区別例と範囲の検査であり、全実数域の占有・上限下限や物理的帰結の一般証明ではない。過去の数値・多項式・上限下限の検査証拠を再利用する。',
]

def snapshot(body,frame,ctx,time):
    return ['i[point a]['+k('eirh',body,v('point'),ctx)+']',*coords(body,frame,ctx),time]

def definitions():
    pos=args(POSITION);time=v('time');shape=v('shape');point=v('point')
    text=define('ejgg',SNAPSHOT,'i['+' '.join(n+' '+s for n,s in POSITION)+']['+k('eje2',*args(SNAPSHOT),*pos)+']',SHAPE)
    actual=[app(app(v(axis),point),time) for axis in ('x','y','z')]
    contained=q('f','point','a',op('y',app(v('members'),point),both(*(k('ba',x) for x in actual),app(shape,*actual))))
    covered=bind(('px','py','pz'),R,'f',op('y',both(*(k('ba',x) for x in pos),app(shape,*pos)),k('eje2',*args(SNAPSHOT),*pos)))
    text+=define('ejgh',SNAPSHOT+[('shape',SHAPE)],both(k('ba',time),contained,covered))
    every=q('f','time',R,op('y',k('lg',v('lower'),v('upper'),time),k('ejgh',*args(SNAPSHOT),shape)))
    text+=define('ejgi',FIELDS+[('shape',SHAPE)],both(k('bg',v('lower'),v('upper')),k('eigy',*args(FIELDS)),k('eiah',*args(FIELDS)),every))
    body=v('body');ctx=v('context');frame=v('frame');K=k('ra');moving=k('zbm');speed=k('zb7');zero=k('bb','n p a b')
    setting=[op('u',op('e',K,moving)),k('ejgi',*history(body,moving,ctx),shape),k('eje7',body,moving,ctx),k('eje7',body,K,ctx),k('eipf',*history(body,K,ctx),speed),k('eioj',K,moving,k('ta'),k('rb'),ctx)]
    setting.extend(k('sca',k('eislc',K,moving,k('ta'),k('rb'),k(axis),ctx),val) for axis,val in (('yn',speed),('yo',zero),('yp',zero)))
    text+=define('ejgj',SETTING,both(*setting))
    text+=define('ejgk',AT,k('ejgg',*snapshot(body,frame,ctx,time)),SHAPE)
    text+=define('ejgl',AT+[('axis','a'),('width',R)],both(k('lg',*interval(frame,ctx),time),k('suk',k('ejgk',*args(AT)),v('axis'),v('width'))))
    transformed=k('stv',shape,k('tc'),speed,time)
    every=q('f','time',R,op('y',k('lg',*interval(K,ctx),time),k('ejgh',*snapshot(body,K,ctx,time),transformed)))
    text+=define('ejgm',SETTING,every)
    widths=args(WIDTHS);conditions=[]
    for i,axis in enumerate(('yn','yo','yp')):
        conditions.extend([k('ejgl',body,moving,ctx,interval(moving,ctx)[0],k(axis),widths[i]),k('ejgl',body,K,ctx,time,k(axis),widths[i+3])])
    values=[k('shv',k('stw',k('tc'),speed),widths[0]),*widths[1:3]]
    consequent=both(*(k('sca',observed,expected) for observed,expected in zip(widths[3:],values)))
    relation=bind(tuple(n for n,_ in WIDTHS),R,'f',op('y',both(*conditions),consequent))
    text+=define('ejgn',[('body','a'),('context','d')],q('f','time',R,op('y',k('lg',*interval(K,ctx),time),relation)))
    general=q('f','body','a',q('f','shape',SHAPE,op('y',k('ejgj',body,shape,k('zb6')),both(k('ejgm',body,shape,k('zb6')),k('ejgn',body,k('zb6'))))))
    text+=content('ejgo',general)
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==332;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements'];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='arbitrary_material_shape_and_current_directional_widths_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/moving-ellipsoid-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
