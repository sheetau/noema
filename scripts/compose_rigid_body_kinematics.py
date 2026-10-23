"""Compose rigidity by all material-point distances, including linear bodies."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_ether_dispensability import ROOT,read
from scripts.compose_material_body_motion import FIELDS,FAMILY
from scripts.compose_material_relative_frame import define,args
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-ether-dispensability.noema';PARENT_BASIS='data/ether-dispensability-basis-v1.json'
FULL='examples/v014/einstein-rigid-body-kinematics.noema';CORE='examples/v014/rigid-body-kinematics-core.noema'
BASIS='data/rigid-body-kinematics-basis-v1.json';ANNOTATIONS='data/rigid-body-kinematics-identifiers-v1.json'
COORDS=[(a,FAMILY) for a in ('x','y','z')]
PAIR=[('left','a'),('right','a'),('time',R)]+COORDS
COMPARE=[('left','a'),('right','a'),('first',R),('second',R)]+COORDS
PRIMITIVES={
 'eisdd':([('frame','a'),('lengthunit','a'),('timeunit','a'),('context','d')],'この物体履歴の座標が、同じframeの校正された直交Cartesian空間基底と共通のlengthunitで与えられ、同じtimeunitの時刻規約で同時刻の出来事を比べることを指定する計量規約。三成分の差の二乗和は、その規約で測る物質点間距離の二乗である。時間や場所ごとに尺度を伸縮させて変形を隠す座標選択を認めず、物差しと局所時計の校正に整合させる。個々の出来事・物質点・値の帰属と全区間履歴は既存eiadで別に要求する。任意の異なる系の同時性や長さを同一視せず、Lorentz変換での長さ不変や加速物体の実現可能性はこの規約から導かない。'),
}
MEANINGS={
 'eigw':'同じ二つの物質点の、同じ時刻における三座標差の二乗和。共通の直交空間基底・長さ単位という規約の下で距離の二乗になる。単独では履歴の妥当性や座標の物理的帰属を保証しない。',
 'eigx':'同じ二物質点と二時刻について、両時刻と全座標が有効な実数であり、eigwの距離の二乗が等しい。時間順序は課さず、成員と区間の範囲は上位で要求する。中心の位置、端点だけ、別物質点への交換では同じ対を代用しない。',
 'eigy':'既存eiadの非空の全物質点・全区間履歴と、同じ系・単位の物理的計量規約eisddの下で、全成員対・区間内の全時刻対にeigxを要求する。指定した同時性・尺度で全体の形状と大きさが不変な剛体の理想化。並進や回転を静止と同一視せず、三非共線標識点を必要としないため棒状の物体も扱える。',
}
LIMITS=[
 'u0005の剛体という語に必要な依存群を構成する。運動学への基礎依存、理論の全主張と座標系・時計・電磁過程の関係、理由、第二文の考慮不足と困難はまだ接続せず、本文の著者主張は追加しない。',
 '剛性は指定された評価系・時刻規約・物理的尺度での全物質点間距離の不変として読む。微視的な熱運動まで禁止せず、理想的な基準物体の巨視的な記述を扱う。',
 'この定義を全座標系で同じ同時性の下に成立する法則や、相対論的加速運動のBorn剛性へ替えない。任意の加速・回転の物体が物理的に実現できるという主張も加えない。後続の各物理設定に適用する系・範囲は別に指定する。',
 '位置の変化がないという静止eiahより弱く、同じ時刻での全点対の距離不変を要求する。非共線三点を使うeiaqは向きの付いた参照枠の構成として保持し、この一般の剛性へ無条件に置き換えない。',
 '点状・線状の幾何学的理想化を排除しない。単一物質点の場合の距離条件は自明になるが、物体・非空の全物質点・完全履歴・校正という条件は残る。',
 '全実数時刻の全称量化を有限標本に替えない。数値例は同じ対・同じ時刻の局所条件を検査するもので、有限回の一致から全区間の剛性を認定しない。',
]

def position(axis,point,time):return app(app(v(axis),point),time)

def definitions():
    text='r eisdd[a a a d] c.\n'
    delta=[k('bf',position(a,v('left'),v('time')),position(a,v('right'),v('time'))) for a in ('x','y','z')]
    squares=[k('shv',d,d) for d in delta]
    text+=define('eigw',PAIR,k('bd',squares[0],k('bd',squares[1],squares[2])),R)
    valid=[k('ba',v(t)) for t in ('first','second')]
    valid += [k('ba',position(a,v(p),v(t))) for t in ('first','second') for p in ('left','right') for a in ('x','y','z')]
    distance=lambda t:k('eigw',v('left'),v('right'),v(t),*args(COORDS))
    text+=define('eigx',COMPARE,both(*valid,k('sca',distance('first'),distance('second'))))
    member=lambda p:app(v('members'),v(p))
    inside=lambda t:k('lg',v('lower'),v('upper'),v(t))
    pair=op('y',both(member('left'),member('right'),inside('first'),inside('second')),k('eigx',v('left'),v('right'),v('first'),v('second'),*args(COORDS)))
    for n,t in reversed([('left','a'),('right','a'),('first',R),('second',R)]):pair=q('f',n,t,pair)
    text+=define('eigy',FIELDS,both(k('eiad',*args(FIELDS)),k('eisdd',v('frame'),v('lengthunit'),v('timeunit'),v('context')),pair))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==217;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='complete_material_pair_distance_rigidity',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=['eigy'],statement_indices=[]).document
    ann=json.loads(read('data/ether-dispensability-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
