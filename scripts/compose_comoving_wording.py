"""Compose an arbitrary-direction boost and the new comoving-force wording."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_field_equations import POINT,FIELD,REGION,ROLES
from scripts.compose_field_transform import MAP,point_expression
from scripts.compose_force_wordings import vector,at
from scripts.compose_rest_force import AXES
from scripts.compose_resting_charge_force import LOCAL
from scripts.compose_moving_field_definition import RESPONSE
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-electromotive-wording.noema';PARENT_BASIS='data/electromotive-wording-basis-v1.json'
FULL='examples/v014/einstein-comoving-wording.noema';CORE='examples/v014/comoving-wording-core.noema'
BASIS='data/comoving-wording-basis-v1.json';ANNOTATIONS='data/comoving-wording-identifiers-v1.json';INDEX=168
BOOST=[('light',R),('speed',R),('velocity',POINT)]
FIELDS=BOOST+[('electric',FIELD),('magnetic',FIELD)]
PAIR=[('velocity',POINT),('speed',R),('frame','a'),('context','d')]
CURRENT=PAIR[:3]+[(n,'a') for n in ('chargerecord','forcerecord','fieldunit')]+[('response',RESPONSE),('context','d')]
PRIMITIVES={
 'eisqt':([('first','a'),('second','a'),('lengthunit','a'),('timeunit','a'),('mapping',MAP),('context','d')], '同じcontextで、firstとsecondという二つの物理的な座標系の記述を、同じ出来事の座標を再表現するmappingへ結ぶ対応規約。両系の原点・軸の向きと尺度、局所時計の校正・同期・時刻原点を固定し、第一系の四座標を入力、第二系の四座標を出力とする。測定記録のある点だけでなく、当該座標記述の全域で同じ規約を適用し、未占有の場所の座標も含む。lengthunit/timeunitで値を表すが、異なる系での同時性や数値時刻の一致は含意しない。どの数値関数がこの対応を実現するかを物理的な軸・時計の設定へ帰属する関係であり、任意の数値写像だけで認定しない。特定の変換公式、相対速度、対象の静止、場・力の法則は含めず、別に合成する。実験実施や全実数点に物体があることは要求しない。'),
}
MEANINGS={
 'ejyk':'正の光速度と光速未満の有効な三速度ejx3を保ち、非負の速さspeedの二乗を三速度の二乗和へ結ぶ。向きや符号は三速度に保持し、βへ渡す速さだけを非負とする。零速度も退化した数式として許す。',
 'ejyl':'同じ正のβ=soy(light,speed)についてβ²/((β+1)*light²)を構成する。速度が0でも速度の二乗による除算を必要としない。',
 'ejym':'任意方向の三速度による係数1の四座標変換。x′=x+κ(u·x)u−βut、t′=β(t−u·x/V²)、κ=β²/((β+1)V²)を同じ全四成分へ構成する。両系の軸を同じ向きで対応させる純粋boostの代表を選び、別の空間回転や原点ずれは加えない。物理的な座標対応はejysで別に要求する。',
 'ejyn':'同じ旧地点の二場について電気側の三成分β(E+u×H/V)−κu(u·E)を構成する。速度と磁気側の外積の順序を保ち、物理的な場の帰属と座標引数の逆変換は別に行う。',
 'ejyo':'同じ旧地点の二場について磁気側の三成分β(H−u×E/V)−κu(u·H)を構成する。電気側と外積の符号を区別する。',
 'ejyp':'ejynの混合場へ、同じ速さ・反対向きの三速度のejymを合成して新四座標の関数として構成する。新地点をそのまま旧地点として評価しない。',
 'ejyq':'ejyoの混合場へejypと同じ逆四座標写像を合成する。電気・磁気側で違う出来事や速度を使わない。',
 'ejyr':'元の場領域znkの一般化した引数領域を、同じ逆四座標写像の逆像として構成する。新領域の点と対応する旧領域の点の所属を一致させる。',
 'ejys':'現在のKと指定frameについて、同じ三速度と速さの許容条件、ejm2の全固定配置・全比較時点の等速並進、両系の座標単位・時計規約と、ejymを全域の同一出来事対応にするeisqtを結ぶ。対象の一地点の対応だけや軸名の一致では済ませない。',
 'ejyt':'現在のKの同じ対象の位置zpjを、同じtc・速さ・三速度のejymで新系の位置時刻へ写す。時刻成分も変換する。',
 'ejyu':'同じ三速度に相対並進するframeで、同じzol・zpoがejytの地点に瞬間静止ejwrすることを要求する。現在の同じ電磁過程をKの二場と変換後の二場へ結び、その新地点の電気側ベクトルを、ejwtの同じ単位電気量・物理的静止試験応答・機械力記録へ接続する。Kの力zplや特定の旧kの力zpmをコピーしない。',
 'ejyv':'指定された同じ三速度について、その非負の速さ・共動系・同じ出来事で量1を持つ記録・力記録・場単位・静止試験応答が存在し、ejysとejyuを共に満たす。同じ証人を座標・場・力の全構成に共有する。',
 'ejyw':'同じ理論の適用域で点状単位電気量が任意方向に動くejybなら、その対象へ当該瞬間相対静止する系への場の変換と、その地点の電気側の場に等しい同系の力ejyvがあるという第二項の内容。前後の対象の静止や加速度0は要求しない。',
 'ejyx':'著者が第二項の内容ejywを述べ、同じ第一項を旧来、第二項を新しい言い方として対置し、先行導入の番号2へ接続する。旧来の一次式と新しい同系の力の関係を、有限速度での無条件な同一成分にしない。',
 'ejyz':'第二項全体の条件・変換・同系の力・新しい言い方ejyxを述べるメッセージ。',
 'ejy2':'第二項を同じ著者・論説へ帰属し、第一項の後へ接続する。文168を更新し、既判断の第一項と他358主張は保持する。',
}
LIMITS=[
 'u0175の第二項全体を原刊910頁で読む。点状の単位電気量が同じ電磁場で動く条件、その対象に働く力、同じ対象の場所での電気側の場、対象に相対静止する座標系への場の変換、新しい言い方という位置付けを保持する。',
 '先行u0173のwenigstens in dem betreffenden Augenblickを共有し、相対静止を当該瞬間の三速度0として読む。選ぶ系はその瞬間の対象速度に合わせて等速並進する慣性系の代表であり、対象が加速する場合もその前後の静止や回転・加速追従系を要求しない。',
 '任意方向の光速未満の三速度に対して、軸を同じ向きで対応させ、同じ原点出来事・時刻原点を取る純粋boostの代表を選ぶ。数式は標準配置の縦成分と横成分を三ベクトルへ展開した形であり、x方向だけへ制限しない。任意の回転・原点ずれを持つ全ての共動座標表示で同じ数値になるとは主張しない。',
 '全系の相対速度はejm2/eioj、軸・原点・時計を含む同一出来事の全域対応はeisqt、同じ対象の当該出来事での瞬間静止はejwrへ結ぶ。数値写像だけから物理的な系、単に一致する一点から全座標域の対応を認定しない。',
 'electric/magneticを同じ逆座標で評価し、両者を混合する操作を、同じ電磁過程の新系での場と同じ地点の力へ接続する。全回転方程式や場の実験検証を本文の余計な前提へ加えない。第一項のKでの力と共動系での力の三成分を無条件に等置しない。',
 '新系の電気量記録は同じzol・zpo・zouの値1であり、先行する単位量の解釈を保つ。力単位Dynと場単位との換算1をejwtの静止試験応答へ接続し、校正出来事zooとの同一性や一般の時間的電荷保存を足さない。',
 '本文の不定のKoordinatensystemを各速度に対する共動系の存在として読む。先行のkはその標準x配置の例であり、任意方向でも固定zbm・zb7・zpkを流用して制限しない。新しいという対比は第一項で導入した同じeisqrを共有する。',
 '新規基本関係は物理的な二つの座標記述と同一出来事の全域写像の対応一つである。相対速度、四式、場の混合・逆像、瞬間静止、単位、力、著者の提示は別に合成する。原文一文の真偽を一原始記号へ隠さない。全連続域の真理や独立査読・同義性の自動証明を有限検査の成功から認定しない。',
]

def bind(fields,body):
    for n,t in reversed(fields):body=q('g',n,t,body)
    return body

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    zero=k('bb','n p a b');one=k('bb','n p b b');V=v('light');speed=v('speed');u=v('velocity');p=v('point');ctx=v('context');frame=v('frame')
    b=k('soy',V,speed);coefficient=k('ejyl',V,speed);comps=lambda x:[app(x,k(a)) for a in ROLES[:3]]
    dot=lambda x,y:k('sexb',*comps(x),*comps(y))
    text+=define('ejyk',BOOST,both(k('ejx3',V,u),k('ba',speed),k('bc',zero,speed),k('sca',k('shv',speed,speed),k('ejx2',u))))
    text+=define('ejyl',[('light',R),('speed',R)],k('shv',k('shv',b,b),k('sjd',k('shv',k('bd',b,one),k('shv',V,V)))),R)
    spatial=[k('bf',k('bd',x,k('shv',coefficient,k('shv',dot(u,p),vcomp))),k('shv',b,k('shv',vcomp,app(p,k('zc7'))))) for x,vcomp in zip(comps(p),comps(u))]
    time=k('shv',b,k('bf',app(p,k('zc7')),k('shv',dot(u,p),k('sjd',k('shv',V,V)))))
    text+=define('ejym',BOOST+[('point',POINT)],point_expression(spatial+[time]),POINT)
    mix=BOOST+[('electric',POINT),('magnetic',POINT)]
    for name,own,cross,sign in [('ejyn','electric','magnetic','bd'),('ejyo','magnetic','electric','bf')]:
        ownv=v(own);extra=k('sci2',V,u,v(cross));parallel=dot(u,ownv)
        result=[k('bf',k('shv',b,k(sign,x,y)),k('shv',coefficient,k('shv',vcomp,parallel))) for x,y,vcomp in zip(comps(ownv),comps(extra),comps(u))]
        text+=define(name,mix,vector(result),POINT)
    coords=[(n,R) for n in ('x','y','z','time')];oldpoint=point_expression([v(n) for n,_ in coords])
    inverse='i[point '+POINT+']['+k('ejym',V,speed,k('ejxy',u,k('bf',zero,one)),p)+']'
    for name,mixer in [('ejyp','ejyn'),('ejyq','ejyo')]:
        value=k(mixer,V,speed,u,at(v('electric'),oldpoint),at(v('magnetic'),oldpoint))
        field='i[component a][i['+' '.join(n+' '+t for n,t in coords)+']['+app(value,v('component'))+']]'
        text+=define(name,FIELDS,k('s6h',field,inverse),FIELD)
    text+=define('ejyr',BOOST+[('region',REGION)],k('s6g',v('region'),inverse),REGION)
    V=k('tc');mapping='i[point '+POINT+']['+k('ejym',V,speed,u,p)+']'
    text+=define('ejys',PAIR,both(k('ejyk',V,speed,u),k('ejm2',k('ra'),frame,ctx,*comps(u)),*(k('ejsl',f,k('ta'),k('rb'),ctx) for f in (k('ra'),frame)),k('eisqt',k('ra'),frame,k('ta'),k('rb'),mapping,ctx)))
    text+=define('ejyt',[('velocity',POINT),('speed',R)],k('ejym',V,speed,u,k('zpj')),POINT)
    newpoint=k('ejyt',u,speed);E=k('ejyp',V,speed,u,k('znl'),k('znm'));H=k('ejyq',V,speed,u,k('znl'),k('znm'));region=k('ejyr',V,speed,u,k('znk'));force=at(E,newpoint)
    values=dict(carrier=k('zol'),frame=frame,event=k('zpo'),chargerecord=v('chargerecord'),forcerecord=v('forcerecord'),chargeunit=k('zou'),fieldunit=v('fieldunit'),forceunit=k('zot'),lengthunit=k('ta'),timeunit=k('rb'),point=newpoint,electricfield=E,magneticfield=H,region=region,force=force,context=ctx,response=v('response'))
    text+=define('ejyu',CURRENT,both(k('ejwr',k('zol'),frame,k('zpo'),newpoint,ctx),k('eispn',k('eispp'),k('ra'),k('znl'),k('znm'),k('znk'),ctx),k('eispn',k('eispp'),frame,E,H,region,ctx),k('ejwt',*[values[n] for n,_ in LOCAL+[('response',RESPONSE)]])))
    text+=define('ejyv',[('velocity',POINT),('context','d')],bind(CURRENT[1:-1],both(k('ejys',*[v(n) for n,_ in PAIR]),k('ejyu',*[v(n) for n,_ in CURRENT]))))
    text+=content('ejyw',q('f','velocity',POINT,op('y',k('ejyb',u,p),k('ejyv',u,p))))
    text+=content('ejyx',both(k('uh',k('zpr'),k('rd'),quote('ejyw'),k('zno'),p),k('eisqr',k('zpq'),k('zpr'),k('zno'),p),k('eislk',k('zpr'),k('eisqn'),'n p c b',k('eirf'),p)))
    text+='d ejyz[] f[j s[k ejyx[]]].\n'
    text+=define('ejy2',[],both(k('eir3',k('zpr'),k('rd'),k('eirf'),quote('ejyz'),k('ri')),k('ue',k('zpq'),k('zpr'),k('ri')),op('u',op('e',k('zpq'),k('zpr')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==360
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements']);doc['statements'][INDEX]=dict(kind='assert',body=dict(kind='call',symbol='ejy2',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='any_direction_comoving_frame_transformed_field_and_local_force',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/electromotive-wording-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
