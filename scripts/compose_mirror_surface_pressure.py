"""Bind a material plane, its two-frame records and mean normal-force inquiry."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_stationary_mirror_boundary import ROOT,read
from scripts.compose_solid_sphere_geometry import SNAPSHOT,POSITION
from scripts.compose_material_body_motion import FIELDS
from scripts.compose_rod_methods import history,coords,interval
from scripts.compose_field_transformation_application import coordinates
from scripts.compose_field_equations import POINT,REGION
from scripts.compose_material_relative_frame import define,args
from scripts.compose_doppler_infinity import quantified
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-stationary-mirror-boundary.noema';PARENT_BASIS='data/stationary-mirror-boundary-basis-v1.json'
FULL='examples/v014/einstein-mirror-surface-pressure.noema';CORE='examples/v014/mirror-surface-pressure-core.noema'
BASIS='data/mirror-surface-pressure-basis-v1.json';ANNOTATIONS='data/mirror-surface-pressure-identifiers-v1.json'
BODY=[('body','a'),('frame','a'),('context','d')]
RECORDS=[('body','a'),('point','a'),('event','a'),('lab','a'),('own','a'),('context','d')]
MAP=RECORDS+[('light',R),('speed',R)]
PLANE=[('body','a'),('light',R),('speed',R),('context','d')]
BOUNDS=[(n,R) for n in ('ylower','yupper','zlower','zupper')]
COORDS=[(n,R) for n in ('px','py','pz','stamp')]
PATCH=[('body','a'),('patch','a'),('frame','a'),('context','d')]+BOUNDS
FORCE='h['+R+'] '+POINT
FORCE_MODEL=[(n,'a') for n in ('process','body','patch','frame','lengthunit','timeunit','forceunit')]+[('lower',R),('upper',R),('force',FORCE),('scope','a'),('context','d')]
AVERAGE=[('force',FORCE),('lower',R),('upper',R)]+BOUNDS+[('pressure',R)]
SETTING=[(n,'a') for n in ('body','patch','process','frame','forceunit','scope')]+[('context','d'),('light',R),('speed',R),('lower',R),('upper',R)]+BOUNDS+[('force',FORCE)]
PRIMITIVES={
 'eisub':(FORCE_MODEL,'同じprocessがbodyの同じ物質的部分patchへ及ぼす機械的な力の寄与を、指定frame・長さ時間及び力単位、lowerからupperまでの各時刻で三成分force(time)のモデルとしてscopeに採用する物理的対応。力はその過程による運動量変化への寄与又はそれを釣り合わせる校正された機械的作用との比較で同定する。支持力や他過程の寄与を加えた合力と区別し、同じ対象から他へ及ぼす力へ反転しない。単位は当該系で校正された直交軸の有向成分に対応し、時間はtimeunitで読む。仮定上のモデルを許し、実測済みや無限精度の測定を要求しない。面の形状、法線、面積、圧力、平均、光・反射・損失の性質又は具体的な力の式はこの関係に含めず別に合成する。'),
}
MEANINGS={
 'ekqo':'同じ時刻・全物質点と三座標族のeje2による占有と、有効な位置のpx=0とを双方向に結ぶ一点条件。物質点は幾何学的位置そのものと同一視しない。',
 'ekqp':'同じ時刻に全成員がpx=0にあり、その平面の全有効三位置が同じ成員で占有される。有限標本の包含だけで全面を認定せず、余分な無効位置の成員も許さない。',
 'ekqq':'同じ完全な物質点履歴・計量・剛性・静止を保持し、正長区間の全時刻でekqpの完全な平面占有を要求する。固定された物質点を追う厚さ零の平面シートの理想化。',
 'ekqr':'bodyの指定系での同じ既定の長さ時間単位・区間・物質点履歴をekqqへ渡し、全成員・全時刻の現在出来事記録eje7を保持する。記録がないことを静止としない。',
 'ekqs':'同じbodyの同じ物質点point・同じeventについて、Kのlab記録とkのown記録をそれぞれ現在のeje6へ結ぶ。別の出来事や別の物質点の四組を組み合わせない。',
 'ekqt':'ekqsの同じ記録対へ、同じV/vの正逆Lorentz四座標対応ekce、kでξ=0、Kでx=v*tを同時に要求する。Kのx=0又は二系の同時刻値の同一視へ替えない。',
 'ekqu':'同じbodyのkでの完全な静止面、Kでの完全な記録と同じ速度の並進を保つ。両側の各物質点出来事記録に他側の同じ出来事記録を要求し、全記録対でekqtを課す。成功した一対だけへ範囲を絞らない。零速度も扱う一般構成であり、著者の正速度範囲は適用側で指定する。',
 'ekqv':'同じ二接線軸の幅(yupper−ylower)*(zupper−zlower)を返す矩形面積。単位は長さ単位の二乗で、同じ時刻の直交軸に対する値として上位で結ぶ。',
 'ekqw':'四端点が有効で、二接線軸の各上端が下端より厳密に大きいという非退化な有限矩形の条件。',
 'ekqx':'有効な時刻の平面px=0の点が、同じ二つの閉区間に入る条件。全四座標と二接線方向を保持する。',
 'ekqy':'同じ矩形端点を固定した四座標の領域関数ekqx。候補ごとに面部分を選び直さない。',
 'ekqz':'同じ静止平面bodyの全物質点・全時刻について、矩形内にあることとpatchの物質点であることを双方向に結ぶ。patch自身の完全な履歴も要求し、同じ成員の三座標をbodyと一致させる。名前だけの面部分や一つの点を面積の対象にしない。',
 'ekq2':'同じ力ベクトル履歴の指定軸成分を、同じ時刻へ適用する実数時間関数。法線の向きは適用側で明示する。',
 'ekq3':'正長の時間区間と正の矩形面積について、+x法線力のRiemann時間積分をpressure*area*durationへ結ぶ。圧力は同じ力単位/長さ単位²の符号付き平均法線力密度であり、仕事率や振幅を圧力と呼ばない。接線力を零に制限しない。',
 'ekq4':'同じbodyの二系の完全な平面、kで固定した同じ物質的矩形部分、K又はkの評価系、その系の対象区間内の正長時間区間に対するeisubの力履歴を結ぶ。横座標はekceで不変なので矩形の面積を同じ単位で使う。異なる系の時刻や力の値を同一視しない。',
 'ekq5':'同じ設定ekq4の下で、候補pressureを同じ力履歴・時間区間・面積のekq3へ結ぶ。候補値の外側に既知の圧力値を置かず、異なる部分や別の力への変更を許さない。',
 'ekq6':'同じ設定を固定し、ekq5を満たす実数値を求める圧力質問。答えの存在・一意性・既知性、著者がこの問いを提示したことは構成自体から要求しない。',
}
LIMITS=[
 'u0215へ必要な物理的面と圧力の依存群。394主張と全判断を保持し、新しい原文対応範囲や全単位判断は追加しない。入射・反射波とこの同じ面への相互作用の帰属、完全反射の損失の読み、仮定と前節照応及び四量の問い全体の著者提示はまだ未完。',
 '面は厚さ零で全座標平面を占める、固定物質点を持つ剛なシートの連続体理想化としてモデル化する。原文が物体の内部充填・厚さ・密度・質量を指定したという主張ではない。有限の物質点モデルを全無限平面の実在証明にしない。',
 'kでξ=0、Kでx=v*tと読む。正逆Lorentz写像は全同一物質点・同一出来事の全記録対へ要求する。両系の時間区間は各系に与えられ、値を等置しない。二側の記録存在も課し、片側しか記録のない範囲から対応を断定しない。',
 '正長の二接線区間から有限の面部分を選ぶ。閉辺の包含は面積に影響しない矩形の標準面積を使う。K/kの変換はx方向なので同じ物質部分のy,z端点と面積を保持する。面積単位を任意の独立単位へ換算する係数を省略したのではなく、ta²という派生単位を採る。',
 '力は同じprocessによるpatchへの機械的作用の寄与として物理的に同定する入力であり、支持力も含む合力としない。圧力はその+x法線力の時間平均/面積。過程が光の相互作用であること、正の押す力であること、法線力の具体的式は後の接続・導出の責務であり、原始関係へ文全体を格納しない。',
 '圧力の候補は符号付き実数で、負値を数学的に排除しない。接線力があっても法線圧力を問える。静止鏡でも正の力と圧力を扱い、速度で割った仕事から圧力を定義しない。時刻の瞬間値、区間平均、面積あたりの仕事率、全力を区別する。',
 '現在の平均は指定した有限区間に対するもの。Lichtdruckを周期平均として本文へ接続する際は、同じ波の周期をこの区間へ追加で結ぶ必要がある。力履歴の全時刻の成分妥当性は物理モデルと全域の積分定義に保持し、有限の積分診断を一般の積分存在の証明にしない。',
 '既存ekqb–ekqnの完全導体候補は保存するが、今回の幾何学的平面だけから鏡・反射・無吸収を認定しない。四量の探索に必要な圧力質問だけを構成し、残る三量や著者の問いの提示を省略した全文判断を作らない。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');pos=args(POSITION);time=v('time');point=v('point');ctx=v('context');body=v('body');frame=v('frame')
    positive=lambda x:both(k('ba',x),k('bg',zero,x))
    at=lambda p:[app(app(v(a),p),time) for a in ('x','y','z')]
    text+=define('ekqo',SNAPSHOT+POSITION,both(k('ba',time),*(k('ba',x) for x in pos),op('z',k('eje2',*args(SNAPSHOT),*pos),k('sejm',*pos,time))))
    contained=q('f','point','a',op('y',app(v('members'),point),k('sejm',*at(point),time)))
    covered=quantified('f',POSITION,op('y',both(*(k('ba',x) for x in pos)),k('ekqo',*args(SNAPSHOT),*pos)))
    text+=define('ekqp',SNAPSHOT,both(k('ba',time),contained,covered))
    text+=define('ekqq',FIELDS,both(k('bg',v('lower'),v('upper')),k('eigy',*args(FIELDS)),k('eiah',*args(FIELDS)),q('f','time',R,op('y',k('lg',v('lower'),v('upper'),time),k('ekqp',*args(SNAPSHOT))))))
    text+=define('ekqr',BODY,both(k('ekqq',*history(body,frame,ctx)),k('eje7',body,frame,ctx)))
    event=v('event');lab=v('lab');own=v('own');K=k('ra');moving=k('zbm')
    record=lambda rec,fr:k('eje6',body,point,event,rec,fr,ctx)
    text+=define('ekqs',RECORDS,both(record(lab,K),record(own,moving)))
    owncoords=[k('zc6',own,k(a)) for a in ('yn','yo','yp','zc7')];labcoords=[k('zc6',lab,k(a)) for a in ('yn','yo','yp','zc7')]
    text+=define('ekqt',MAP,both(k('ekqs',*args(RECORDS)),k('ekce',v('light'),v('speed'),coordinates(lab),coordinates(own)),k('sejm',*owncoords),k('sejn',v('light'),v('speed'),*labcoords)))
    pair=k('ekqs',*args(RECORDS));allpairs=quantified('f',[(n,'a') for n in ('point','event','lab','own')],op('y',pair,k('ekqt',*args(MAP))))
    coverage=[]
    for fr,rec,other in ((K,'lab','own'),(moving,'own','lab')):
        coverage.append(quantified('f',[(n,'a') for n in ('point','event',rec)],op('y',record(v(rec),fr),q('g',other,'a',pair))))
    text+=define('ekqu',PLANE,both(op('u',op('e',K,moving)),k('s45',v('light'),v('speed')),k('ekqr',body,moving,ctx),k('eje7',body,K,ctx),k('eipf',*history(body,K,ctx),v('speed')),*coverage,allpairs))
    text+=define('ekqv',BOUNDS,k('shv',k('bf',v('yupper'),v('ylower')),k('bf',v('zupper'),v('zlower'))),R)
    text+=define('ekqw',BOUNDS,both(*(k('ba',v(n)) for n,t in BOUNDS),k('bg',v('ylower'),v('yupper')),k('bg',v('zlower'),v('zupper'))))
    text+=define('ekqx',BOUNDS+COORDS,both(k('ekqw',*args(BOUNDS)),k('sejm',*args(COORDS)),k('lg',v('ylower'),v('yupper'),v('py')),k('lg',v('zlower'),v('zupper'),v('pz'))))
    text+=define('ekqy',BOUNDS,'i['+' '.join(n+' '+t for n,t in COORDS)+']['+k('ekqx',*args(BOUNDS),*args(COORDS))+']',REGION)
    patch=v('patch');bodypos=[app(app(fn,point),time) for fn in coords(body,frame,ctx)];patchpos=[app(app(fn,point),time) for fn in coords(patch,frame,ctx)]
    inside=k('lg',*interval(frame,ctx),time);member=k('eirh',patch,point,ctx)
    selection=op('z',member,both(k('eirh',body,point,ctx),k('ekqx',*args(BOUNDS),*bodypos,time)))
    shared=op('y',member,both(*(k('sca',a,b) for a,b in zip(patchpos,bodypos))))
    text+=define('ekqz',PATCH,both(op('u',op('e',body,patch)),k('ekqr',*args(BODY)),k('ekqw',*args(BOUNDS)),k('eiad',*history(patch,frame,ctx)),q('f','point','a',q('f','time',R,op('y',inside,both(selection,shared))))))
    text+=define('ekq2',[('force',FORCE),('axis','a')],'i[time '+R+']['+app(app(v('force'),time),v('axis'))+']',F)
    duration=k('bf',v('upper'),v('lower'));integral=k('shv',v('pressure'),k('shv',k('ekqv',*args(BOUNDS)),duration))
    text+=define('ekq3',AVERAGE,both(*(k('ba',v(n)) for n in ('lower','upper','pressure')),k('bg',v('lower'),v('upper')),k('ekqw',*args(BOUNDS)),k('sede',v('lower'),v('upper'),k('ekq2',v('force'),k('yn')),integral)))
    forces={n:v(n) for n,t in SETTING}|dict(lengthunit=k('ta'),timeunit=k('rb'))
    text+=define('ekq4',SETTING,both(k('ekqu',*args(PLANE)),k('ekqz',body,patch,moving,ctx,*args(BOUNDS)),op('x',op('e',frame,K),op('e',frame,moving)),k('bg',v('lower'),v('upper')),k('lg',*interval(frame,ctx),v('lower')),k('lg',*interval(frame,ctx),v('upper')),k('eisub',*[forces[n] for n,t in FORCE_MODEL])))
    text+=define('ekq5',SETTING+[('pressure',R)],both(k('ekq4',*args(SETTING)),k('ekq3',*args(AVERAGE))))
    text+=define('ekq6',SETTING,'j v[i[pressure '+R+']['+k('ekq5',*args(SETTING),v('pressure'))+']]','g['+R+']')
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==394
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='same_material_plane_patch_and_mean_normal_force_inquiry_dependencies',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    bodytext=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/stationary-mirror-boundary-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(bodytext.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:bodytext,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
