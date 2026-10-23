"""Apply one physical shape rule with exchanged frames and signed velocity."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_speed_boundary_forecast import ROOT,read
from scripts.compose_material_body_motion import FIELDS,coord
from scripts.compose_material_shape_dimensions import snapshot
from scripts.compose_solid_sphere_geometry import POSITION,args,bind
from scripts.compose_shape_contraction import SHAPE
from scripts.compose_rod_methods import history,interval
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-speed-boundary-forecast.noema';PARENT_BASIS='data/speed-boundary-forecast-basis-v1.json'
FULL='examples/v014/einstein-reciprocal-shape-results.noema';CORE='examples/v014/reciprocal-shape-results-core.noema'
BASIS='data/reciprocal-shape-results-basis-v1.json';ANNOTATIONS='data/reciprocal-shape-results-identifiers-v1.json';INDEX=336
SETTING=[('body','a'),('shape',SHAPE),('rest','a'),('observer','a'),('speed',R),('context','d')]
BODY=[f for f in SETTING if f[0]!='shape']
BASE=[('shape',SHAPE),('light',R),('time',R),('direction',R)]
REGIME=[('rest','a'),('observer','a'),('direction',R),('context','d')]
MEANINGS={
 'ejhw':'有効な符号付き速度、前後二時刻と同じ点の六座標について、縦変位が速度と時間差の積、横二変位が零である。正速度専用sbmを一般化し、負速度・静止も数値核に許す。',
 'ejhx':'指定系・尺度・文脈の同じ非空の全物質点履歴eiad、校正eisdd、正の時間幅の下で、全成員の全対象時刻対が同じ符号付き速度のejhwを満たす並進。中心や二端だけの速度へ縮めない。',
 'ejii':'同じ指定観測系と静止系の同じ出来事の現在記録が非空に対応し、その全対応四記録に同じ符号付き速度・光速・φ=1の四式sreが成り立つ。逆向きでは二記録の順と速度の符号を共に交換する。',
 'ejhy':'同じ物体の指定静止系での剛性・静止・任意形状の完全占有、両系の現在の全点記録、観測系での全点の符号付き非零並進、同じ系間速度三成分、同じ現在四式ejiiを結ぶ。',
 'ejhz':'同じ運動設定ejhyに、静止系の区間下端で三軸それぞれに有限な実際の幅が存在することを結ぶ。形状に凸性・球形・連結性を加えない。',
 'ejh2':'同じ物体が指定観測系の全対象時刻に、同じ静止形状へstvの符号付き速度を代入した全領域を完全に占める。観測系の時刻を使い、静止系の同時刻面へ交換しない。',
 'ejh3':'同じ静止系の基準時刻の実際の非負有限幅と、指定観測系の全対象時刻に存在する実際の幅を指定軸で比較する。横二幅は等しく、縦幅は符号付き速度の二乗から得る係数倍。正の元の幅・非零速度では厳密に縮む。',
 'ejh4':'同じ物体と任意静止形状についてejh2の完全な運動形状と、同じ二系での全三軸のejh3を合わせる。幅の条件付き等式だけで幅の存在を代用しない。',
 'ejh5':'指定方向係数が有効な実数で、その二乗が1であること。正負の二方向を数値的に指定し、新しい方向原始概念にしない。',
 'ejh6':'指定方向±1と光速未満の非負の速さについて、同じ元の形状をx=f(v)x0+direction*v*t,y=y0,z=z0へ写す前向き像。負方向を縦座標の鏡映や横軸交換と混同しない。',
 'ejh7':'同じ元形状の全有効位置について、指定方向の前向き像の縦位置がdirection*V*tの平面から正精度未満にあり、同じ横射影の平面像に対応する。',
 'ejia':'同じ有限形状・指定方向・固定観測時刻について、速さが光速未満からVへ近づくと、全元位置が共通の精度でdirection*V*tの平面へ近づく。近傍は形状・時刻に依存する。',
 'ejib':'同じ方向で速さが光速未満の全値を動くとき、全有効三位置でejh6の前向き像と符号付きstvが一致する。負方向でも同じ逆変換族へ極限を接続する。',
 'ejic':'同じ物体の全形状と三幅ejh4を、指定観測系の全対象時刻のejia/ejibへ接続する。指定方向と現在速度の符号が一致し、極限の比較族と現在の物体の形状が同じ静止形状を共有する。',
 'ejid':'静止系・観測系・方向を引数とする共通の帰結内容。既存の正の速さvと光速Vの下で、全物体・全任意形状の有限寸法の設定ejhzにejicを要求する。符号をdirection*vにし、同じ物体に二つの静止条件を同時に課さない。',
 'ejie':'同じ共通規則ejidを、k静止/K観測/+vとK静止/k観測/−vの双方に適用し、同じ元の幅の速さ比較ejgyを合わせる内容。同じ結果とは同じ形状・寸法・境界の規則の適用であり、両側の物体や寸法の数値の一致ではない。',
 'ejif':'著者が二系を交換した同じ形状結果ejieを述べ、その帰結を明らかだと提示する。明白さを処理系の証明認定や全物理法則の同値へ拡張しない。',
 'ejig':'u0117の同じ結果と明白さの提示ejifを述べるメッセージ。',
 'ejih':'同じ著者・論説へu0117を帰属し、先の適用限界・予告ziaの後に置く。',
}
LIMITS=[
 '固定u0117全体を原刊903頁に照合する。die gleichen Resultateは直前の物体の形状・三軸寸法・速さによる程度と光速への極限を指すと読む。未だ後続で示すと予告した内容を新たな実証済みの結果へ替えず、続く時計の結果も先取りしない。',
 '同じ二系・平行軸・共通尺度・共通原点と時刻零点という既存の比較設定を継承し、kに静止する物体をKから見る場合と、Kに静止する別の適格物体をkから見る場合に同じ規則を適用する。静止対象を同一個体に固定せず、同一物体が両系で同時に静止するとは要求しない。',
 '二系を交換すると観測する側での対象の速度は−vとなる。速度の符号は四記録の順序・全物質点の履歴・系間速度と共に交換する。縮小率は速度の二乗から得るため正負で同じだが、形状の中心の移動は逆向きになる。',
 '見た形状は各観測系の同時刻座標による完全な占有集合と読む。Kとkの同時性を等置せず、光の遅延による画像・同じ物体の加速履歴へ替えない。任意形状の有限射影幅の読みと零幅の扱いを継承する。',
 '前向き全形状像を負速度でも構成するので、球の場合の回転楕円体と横二半軸の保持も同じ規則に含まれる。負速度の符号を半軸の負値にせず、正の静止形状を鏡映しない。',
 '光速での面状化は先の発話外の解釈注記を継承した下側極限。負方向では−V*tの平面へ同じ全元位置が近づく。有限βを光速に割り当てず、横射影の穴・離れた部分を保持する。',
 '共通規則の両適用は、以前の式を観測系名だけ交換した表示ではない。静止側の全点履歴と有限幅、観測側の全点の符号付き並進と形状・幅、両系の現在四記録を実際に接続する。既存の正方向の定義と判断は変更しない。',
 'ist klarは既存zdgによる著者の明白さの提示。物理的主張の真理・数学的な一般証明・原文の通読判断・有限の対照検査を区別する。新しい原始記号は追加しない。',
]

def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b');speed=v('speed');first=v('first');second=v('second')
    nums=[(n,R) for n in ('speed','first','second','xfirst','xsecond','yfirst','ysecond','zfirst','zsecond')]
    conditions=[*(k('ba',v(n)) for n,_ in nums),k('bc',first,second),k('sca',k('bf',v('xsecond'),v('xfirst')),k('shv',speed,k('bf',second,first))),k('sca',v('yfirst'),v('ysecond')),k('sca',v('zfirst'),v('zsecond'))]
    text=define('ejhw',nums,both(*conditions))
    point=v('point');inside=both(app(v('members'),point),k('lg',v('lower'),v('upper'),first),k('lg',v('lower'),v('upper'),second),k('bc',first,second))
    motion=k('ejhw',speed,first,second,*(coord(a,point,t) for a in ('x','y','z') for t in (first,second)))
    allpoints=q('f','point','a',bind(('first','second'),R,'f',op('y',inside,motion)))
    text+=define('ejhx',FIELDS+[('speed',R)],both(k('eiad',*args(FIELDS)),k('eisdd',v('frame'),v('lengthunit'),v('timeunit'),v('context')),k('ba',speed),k('bg',v('lower'),v('upper')),allpoints))
    rest=v('rest');observer=v('observer');ctx=v('context');body=v('body');shape=v('shape');time=v('time');direction=v('direction')
    pair=both(k('eiyx',v('event'),v('firstrecord'),observer,ctx),k('eiyx',v('event'),v('secondrecord'),rest,ctx))
    ones='i[value '+R+']['+one+']'
    text+=define('ejii',[('rest','a'),('observer','a'),('speed',R),('context','d')],both(bind(('event','firstrecord','secondrecord'),'a','g',pair),bind(('event','firstrecord','secondrecord'),'a','f',op('y',pair,k('sre',v('firstrecord'),v('secondrecord'),k('tc'),speed,ones)))))
    setting=[op('u',op('e',rest,observer)),k('bg',zero,k('shv',speed,speed)),k('ejgi',*history(body,rest,ctx),shape),k('eje7',body,rest,ctx),k('eje7',body,observer,ctx),k('ejhx',*history(body,observer,ctx),speed),k('eioj',observer,rest,k('ta'),k('rb'),ctx),k('ejii',rest,observer,speed,ctx)]
    setting.extend(k('sca',k('eislc',observer,rest,k('ta'),k('rb'),k(a),ctx),n) for a,n in (('yn',speed),('yo',zero),('yp',zero)))
    text+=define('ejhy',SETTING,both(*setting))
    finite=bind(('wx','wy','wz'),R,'g',both(*(k('ejgl',body,rest,ctx,interval(rest,ctx)[0],k(a),v(w)) for a,w in zip(('yn','yo','yp'),('wx','wy','wz')))))
    text+=define('ejhz',SETTING,both(k('ejhy',*args(SETTING)),finite))
    every=lambda claim:q('f','time',R,op('y',k('lg',*interval(observer,ctx),time),claim))
    text+=define('ejh2',SETTING,every(k('ejgh',*snapshot(body,observer,ctx,time),k('stv',shape,k('tc'),speed,time))))
    axis=v('axis');proper=v('proper');observed=v('observed');axial=op('e',axis,k('yn'));transverse=op('x',op('e',axis,k('yo')),op('e',axis,k('yp')))
    smaller=op('y',both(k('sbg',proper),op('u',k('sca',speed,zero))),k('bg',observed,proper))
    longitudinal=both(k('sca',observed,k('shv',proper,k('stw',k('tc'),speed))),smaller)
    value=both(k('ba',observed),k('bc',zero,observed),k('ejgl',body,observer,ctx,time,axis,observed),op('y',axial,longitudinal),op('y',transverse,k('sca',observed,proper)))
    text+=define('ejh3',BODY+[('axis','a')],both(op('x',axial,transverse),q('g','proper',R,both(k('ba',proper),k('bc',zero,proper),k('ejgl',body,rest,ctx,interval(rest,ctx)[0],axis,proper),every(q('g','observed',R,value))))))
    text+=define('ejh4',SETTING,both(k('ejh2',*args(SETTING)),*(k('ejh3',*args(BODY),k(a)) for a in ('yn','yo','yp'))))
    text+=define('ejh5',[('direction',R)],both(k('ba',direction),k('sca',k('shv',direction,direction),one)))
    light=v('light');magnitude=v('magnitude');pos=args(POSITION);epsilon=v('epsilon');valid=lambda xs:both(*(k('ba',x) for x in xs))
    domain=both(k('ba',magnitude),k('bc',zero,magnitude),k('bg',magnitude,light));signed=k('shv',direction,magnitude);plane=k('shv',k('shv',direction,light),time)
    witness=q('g','originx',R,both(k('ba',v('originx')),app(shape,v('originx'),pos[1],pos[2]),k('sca',pos[0],k('ejg7',light,signed,time,v('originx')))))
    text+=define('ejh6',BASE+[('magnitude',R)]+POSITION,both(k('sbg',light),k('ba',time),k('ejh5',direction),domain,valid(pos),witness))
    pointwise=op('y',both(valid(pos),app(shape,*pos)),both(k('lb',k('ejg7',light,signed,time,pos[0]),plane,epsilon),k('ejg6',shape,plane,plane,*pos[1:])))
    text+=define('ejh7',BASE+[('epsilon',R),('magnitude',R)],both(k('sbg',light),k('ba',time),k('ejh5',direction),k('sbg',epsilon),domain,bind(('px','py','pz'),R,'f',pointwise)))
    accumulation=q('f','radius',R,op('y',k('sbg',v('radius')),k('suo',light,v('radius'))))
    near=both(domain,k('bg',k('bf',light,magnitude),v('delta')))
    uniform=q('f','epsilon',R,op('y',k('sbg',epsilon),q('g','delta',R,both(k('sbg',v('delta')),q('f','magnitude',R,op('y',near,k('ejh7',*args(BASE),epsilon,magnitude)))))))
    text+=define('ejia',BASE,both(k('sbg',light),k('ba',time),k('ejh5',direction),accumulation,uniform))
    agree=bind(('px','py','pz'),R,'f',op('y',valid(pos),op('z',k('ejh6',*args(BASE),magnitude,*pos),app(k('stv',shape,light,signed,time),*pos))))
    text+=define('ejib',BASE,both(k('sbg',light),k('ba',time),k('ejh5',direction),q('f','magnitude',R,op('y',domain,agree))))
    text+=define('ejic',SETTING+[('direction',R)],both(k('ejh5',direction),k('sbg',k('shv',direction,speed)),k('ejh4',*args(SETTING)),every(both(k('ejia',shape,k('tc'),time,direction),k('ejib',shape,k('tc'),time,direction)))))
    current=k('shv',direction,k('zb7'));setting_args=[body,shape,rest,observer,current,ctx]
    general=q('f','body','a',q('f','shape',SHAPE,op('y',k('ejhz',*setting_args),k('ejic',*setting_args,direction))))
    text+='d ejid['+' '.join(n+' '+s for n,s in REGIME)+'] e[b point['+both(k('ejh5',direction),k('sbg',k('zb7')),k('srd',k('tc'),k('zb7'),k('soy',k('tc'),k('zb7'))),general)+']].\n'
    forward=k('ejid',k('zbm'),k('ra'),one,k('zb6'));backward=k('ejid',k('ra'),k('zbm'),k('bf',zero,one),k('zb6'))
    text+=content('ejie',both(op('t',forward,v('point')),op('t',backward,v('point')),op('t',k('ejgy'),v('point'))))
    text+=content('ejif',both(*(k(n,k('zib'),k('rd'),quote('ejie'),k('eisn5'),v('point')) for n in ('uh','zdg'))))
    text+='d ejig[] f[j s[k ejif[]]].\n'
    text+=define('ejih',[],both(k('eir3',k('zib'),k('rd'),k('eirf'),quote('ejig'),k('ri')),k('ue',k('zia'),k('zib'),k('ri')),op('u',op('e',k('zia'),k('zib')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ejih',arguments=[]))];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='reciprocal_material_shapes_widths_and_planar_limits',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/speed-boundary-forecast-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
