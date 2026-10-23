"""Compose a straight rod's axis, rest length and full-point translation."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_second_principle import ROOT,read
from scripts.compose_material_body_motion import FIELDS
from scripts.compose_material_relative_frame import define,args
from scripts.compose_rigid_body_kinematics import position
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-second-principle.noema';PARENT_BASIS='data/second-principle-basis-v1.json'
FULL='examples/v014/einstein-rod-geometry.noema';CORE='examples/v014/rod-geometry-core.noema'
BASIS='data/rod-geometry-basis-v1.json';ANNOTATIONS='data/rod-geometry-identifiers-v1.json'
AXIS=FIELDS+[('firstend','a'),('lastend','a')]
COORDS=FIELDS[-3:]
AT=[('firstend','a'),('lastend','a'),('time',R)]+COORDS
SHAPE=FIELDS[:7]+[('firstend','a'),('lastend','a')]
PRIMITIVES={
 'eislq':(SHAPE,'指定したbodyの巨視的形状に、同じframe・context・単位と閉時間区間を通じて追跡する二つの縦方向端面の中心firstend/lastendを割り当てる。二中心を結ぶ直線を、その物体の直線状の長軸として採用し、軸方向の物体の全広がりがその二端面の間にある。断面の横方向の広がりは許し、全物質点を軸上へ制限しない。中心は幾何学的標識でもよく、空洞の中心を物質点とする必要はない。縦方向・端面・中心の形状上の同定を与える物理的入力であり、任意の二点や測定標本から推定しない。数値の非退化性、履歴の座標帰属、距離、剛性、静止、軸への配置、並進は別の合成条件で要求する。')
}
MEANINGS={
 'eio7':'有効な二端点の三座標について、両端のyとzが零であり、xが異なる。直線状の軸がX軸上にある条件で、平行なだけのずれた軸、零長、斜めの軸を除く。端点の順序と棒の向きは固定しない。',
 'eipa':'同じ二幾何学的端標識の同じ時刻における三座標と正の長さを結び、長さの二乗を既存eigwの距離二乗に一致させる。実装の同一性ではなく実数値の等値を用いる。',
 'eipb':'同じ三座標関数族から同じ時刻の二端標識を選び、eio7のX軸上配置を要求する。全物質点をこの条件へ代入せず、厚みを持つ棒を許す。',
 'eipc':'非空の全物質点履歴eiad、校正された同じ計量eisdd、長軸端面中心の物理的割当eislqを結ぶ。二標識の全区間履歴seを独立に要求し、全区間時刻で長軸の二乗長が正である。二中心が物質点であるとは要求しない。',
 'eipd':'eipcの同じ長軸について、区間内の全時刻にeipbのX軸上配置を要求する。区間端だけの一致や単なる方向の平行では代用しない。',
 'eipe':'eipcの物体と長軸に、全物質点の静止eiah、全点対距離不変eigy、全区間時刻での同じ正の軸長eipaを結ぶ。静止系の初期長を記述する依存条件。X軸への配置や実測の完了は加えない。',
 'eipf':'完全な全物質点履歴と校正された計量、正の一定速度、正の時間幅の下で、全成員・区間内の順方向の全時刻対に既存sbmを適用する。同じ速度でxのみが変位しy/zは不変。原点だけや端点だけの並進ではない。',
 'eipg':'同じ棒の全物質点の正のX方向等速並進eipf、全点対の剛性eigy、全時刻での長軸のX軸上配置eipdを結ぶ。移動後の区間の条件であり、初期長との一致や加速過程の実現を加えない。',
}
LIMITS=[
 'u0029に必要な剛性・静止長・長軸・全点等速並進をまとめる依存群。著者による設定・思考操作・二方法への問いはまだ新しい本文主張へ接続しない。',
 '直線状の長軸を持つ巨視的な棒という解釈を採る。横断面の寸法や長さとの比率は指定せず、零厚みや三非共線物質点を要求しない。曲がった棒を無説明に直線棒と扱わない。',
 '長軸の端面中心の同定は形状の物理的入力であり、全物質点の座標から対称軸を自動推定する算法ではない。幾何学的標識の座標にも同じseの全区間出来事対応を要求する。',
 '剛性は同じ系・同時性・尺度での全物質点対距離の不変。初期と運動後は別区間として評価し、両区間の長さの一致、Born剛性、任意の加速の可能性を含めない。',
 '有限検査では実数時刻の全域量化を標本に替えない。量化本体の明示した代入と引数接続を調べ、全域評価と未知入力は拒否する。',
]


def all_times(body):
    return q('f','time',R,op('y',k('lg',v('lower'),v('upper'),v('time')),body))


def definitions():
    text='r eislq['+' '.join(t for _,t in SHAPE)+'] c.\n'
    six=[(n,R) for n in ('ax','ay','az','bx','by','bz')]
    zero=k('bb','n p a b')
    text+=define('eio7',six,both(*(k('ba',v(n)) for n,_ in six),*(k('sca',v(n),zero) for n in ('ay','az','by','bz')),op('u',k('sca',v('ax'),v('bx')))))
    coords=[position(a,v(p),v('time')) for p in ('firstend','lastend') for a in ('x','y','z')]
    distance=k('eigw',v('firstend'),v('lastend'),v('time'),*args(COORDS))
    text+=define('eipa',AT+[('length',R)],both(k('ba',v('time')),*(k('ba',x) for x in coords),k('sbg',v('length')),k('sca',k('shv',v('length'),v('length')),distance)))
    text+=define('eipb',AT,both(k('ba',v('time')),k('eio7',*coords)))
    traces=[k('se',v(p),*[v(n) for n in ('frame','context','lengthunit','timeunit','lower','upper')],*(app(v(a),v(p)) for a in ('x','y','z'))) for p in ('firstend','lastend')]
    valid_axis=both(k('ba',v('time')),*(k('ba',x) for x in coords),k('sbg',distance))
    text+=define('eipc',AXIS,both(k('eiad',*args(FIELDS)),k('eisdd',v('frame'),v('lengthunit'),v('timeunit'),v('context')),k('eislq',*args(SHAPE)),op('u',op('e',v('firstend'),v('lastend'))),*traces,all_times(valid_axis)))
    text+=define('eipd',AXIS,both(k('eipc',*args(AXIS)),all_times(k('eipb',*args(AT)))))
    text+=define('eipe',AXIS+[('length',R)],both(k('eipc',*args(AXIS)),k('eiah',*args(FIELDS)),k('eigy',*args(FIELDS)),all_times(k('eipa',*args(AT),v('length')))))
    ordered=both(app(v('members'),v('point')),*(k('lg',v('lower'),v('upper'),v(t)) for t in ('first','second')),k('bc',v('first'),v('second')))
    pair=k('sbm',v('speed'),v('first'),v('second'),*(position(a,v('point'),v(t)) for a in ('x','y','z') for t in ('first','second')))
    for n,t in reversed([('point','a'),('first',R),('second',R)]):
        if n=='second':pair=op('y',ordered,pair)
        pair=q('f',n,t,pair)
    text+=define('eipf',FIELDS+[('speed',R)],both(k('eiad',*args(FIELDS)),k('eisdd',v('frame'),v('lengthunit'),v('timeunit'),v('context')),k('sbg',v('speed')),k('bg',v('lower'),v('upper')),pair))
    text+=define('eipg',AXIS+[('speed',R)],both(k('eipf',*args(FIELDS),v('speed')),k('eigy',*args(FIELDS)),k('eipd',*args(AXIS))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==252;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='rod_axis_rest_length_and_full_point_translation_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/second-principle-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
