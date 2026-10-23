"""Ground definite axis configurations in complete coordinate histories."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_moving_axes import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_material_axes import ROLES,at
from scripts.compose_rod_methods import interval
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-moving-axes.noema';PARENT_BASIS='data/moving-axes-basis-v1.json'
FULL='examples/v014/einstein-axis-states.noema';CORE='examples/v014/axis-states-core.noema'
BASIS='data/axis-states-basis-v1.json';ANNOTATIONS='data/axis-states-identifiers-v1.json'
MEANINGS={
 'eiwc':'同じ点・時点について、二つの記述文脈の静止系raの時刻と三位置座標が存在し有効で値が一致する。文脈や記述個体の同一性を要求せず、方向だけの一致へ弱めない。',
 'eiwd':'軸配置の記述状態が、指定履歴文脈と同じ移動系の原点と三軸を同じ全役割で記述する。断面側の原点を唯一とし、補助的な物体の存在は排除しない。配置断面に期間全体の運動や静止を要求しない。',
 'eiwe':'指定物体側の同じ点の位置関数を、同じ静止系・単位・時点のymへ結ぶ。時刻ylが全履歴の区間内にあり、全三成分の実位置と記録の値が有効で一致する。原点標識は全軸で同じ出来事に結ぶ先行eiv2を使う。',
 'eiwf':'同じ候補履歴・静止系時刻に配置状態を対応させるsfuと、同じ原点・三軸のeiwdを保持する。全軸の全成員と原点について、履歴の実座標をeiweへ、配置断面との値一致をeiwcへ渡す。見えている標識だけで配置対応としない。',
 'eiwg':'二配置状態が同じ原点と三軸を記述し、同じ時点の全軸成員と原点の三座標・静止系時刻が一致する。状態識別子の一致や平行方向だけの一致とは異なる配置同値である。',
 'eiwh':'同じ候補履歴の指定時点にeiwfの対応状態が存在し、その全対応状態がeiwgで同じ配置を表す。都合のよい一状態だけを選ばず、記述の重複も許す。',
 'eiwi':'同じ区間内の指定実時刻に、静止系の有効な時刻記録を持つ全時点範囲ysの時点が存在する。区間の実時刻を記録標本から取り残さないための被覆条件である。',
 'eiwj':'同じ候補履歴に現行の共通並進eivzと移動三軸の完全幾何eiv7を要求する。共通範囲・当該履歴・eiojの全時点範囲を一致させ、全実時刻の被覆と、全選択時点での配置の存在・一意性eiwhを保持する。平行な運動候補の存在や対称性の正当化は別条件である。',
}
LIMITS=[
 'u0044の各静止系時刻に一定の軸配置が対応するという内容の依存群。候補運動を一つ選ぶ存在、対応三軸の全時刻の平行、対称性による仮定採用、設定指示と著者帰属、段落全体の意味判断は後で接続する。',
 '配置状態は同じ物理的な軸の記述として読む。状態識別子や文脈が異なっても、同じ原点・軸役割・全物質点の同時刻位置が一致すれば同じ配置を表す。内部時計や物差しの配置を軸配置の比較範囲へ追加しない。',
 'zclの断面文脈は同じ時刻に評価する記述であり、履歴全体を静止させる代用ではない。断面側にeiv7の全期間の履歴は課さず、全点の座標記録と履歴側の実座標への一致を要求する。',
 '元のzcmは位置・方向・役割の同値性を物理的入力としていた。今回の判断ではeiwgの全点座標の一致を使い、旧原始関係の意味を書き換えない。軸の物理的な直線性・剛性・原点の世界線は現行eiv7/eiv2に保持する。',
 '同じ履歴の全時点を共通のysとeislaへ両方向に一致させ、さらに区間内の全実時刻をeiwiで覆う。別の時点記録が同じ時刻値を持つことは許す。有限例はこの全域条件の証明ではない。',
 '第一文の既出速度zb7と同じ対象を維持する。加速機構、時計内部静止、初期長の保存、二系の時計指示の一致、正方向一致を加えない。全実数の量化は有限評価を拒否し、未知の座標を既定値で補わない。',
]

def time(moment,ctx):return k('yl',moment,k('ra'),k('rb'),ctx)
def coordinate(point,moment,axis,ctx):return k('ym',point,moment,k('ra'),k('ta'),k(axis),ctx)
def selected(body,point,ctx):return op('x',k('eirh',body,point,ctx),op('e',point,k('zbn',k('zbm'),ctx)))
def over_axes(ctx,make):
    return both(*(q('f','point','a',op('y',selected(k('zbo',k('zbm'),k(a),ctx),v('point'),ctx),make(k('zbo',k('zbm'),k(a),ctx),v('point')))) for a in ROLES))

def definitions():
    p=v('point');m=v('moment');c=v('context');left=v('first');right=v('second')
    fields=[('point','a'),('moment','a'),('first','d'),('second','d')]
    clauses=[]
    for ctx in (left,right):
        clauses.extend((k('zce',p,m,k('ra'),k('ta'),ctx),k('zcf',m,k('ra'),k('rb'),ctx),k('ba',time(m,ctx))))
        clauses.extend(k('ba',coordinate(p,m,a,ctx)) for a in ROLES)
    clauses.extend((k('sca',time(m,left),time(m,right)),*(k('sca',coordinate(p,m,a,left),coordinate(p,m,a,right)) for a in ROLES)))
    text=define('eiwc',fields,both(*clauses))
    pose=v('pose');scene=k('zcl',pose);moving=k('zbm');origin=k('zbn',moving,c);line=lambda a:k('zbo',moving,k(a),c)
    choices=[both(op('e',v('role'),k(a)),op('e',v('line'),line(a))) for a in ROLES]
    exact=q('f','line','a',q('f','role','a',op('z',k('zbw',moving,v('line'),v('role'),scene),op('x',choices[0],op('x',*choices[1:])))))
    unique=q('f','point','a',op('y',k('zbv',moving,p,scene),op('e',p,origin)))
    clauses=[k('zcn',pose),op('e',k('zbn',moving,scene),origin),k('zbv',moving,origin,scene),exact,unique]
    clauses.extend(op('e',k('zbo',moving,k(a),scene),line(a)) for a in ROLES)
    text+=define('eiwd',[('pose','a'),('context','d')],both(*clauses))
    actual=at(v('body'),p,k('ra'),c,time(m,c));records=[coordinate(p,m,a,c) for a in ROLES]
    text+=define('eiwe',[('body','a'),('point','a'),('moment','a'),('context','d')],both(k('zce',p,m,k('ra'),k('ta'),c),k('zcf',m,k('ra'),k('rb'),c),k('ba',time(m,c)),k('lg',*interval(k('ra'),c),time(m,c)),*(k('ba',x) for x in actual+records),*(k('sca',a,b) for a,b in zip(actual,records))))
    hist=v('history');ctx=k('zci',hist)
    matches=over_axes(ctx,lambda body,point:both(k('eiwe',body,point,m,ctx),k('eiwc',point,m,ctx,scene)))
    text+=define('eiwf',[('history','a'),('moment','a'),('pose','a')],both(k('sfu',hist,m,pose,'p ba','p sca'),k('eiwd',pose,ctx),matches))
    comparisons=over_axes(c,lambda body,point:k('eiwc',point,m,k('zcl',left),k('zcl',right)))
    text+=define('eiwg',[('first','a'),('second','a'),('moment','a'),('context','d')],both(k('eiwd',left,c),k('eiwd',right,c),comparisons))
    assigned=lambda pose:k('eiwf',hist,m,pose)
    unique=q('f','first','a',q('f','second','a',op('y',both(assigned(left),assigned(right)),k('eiwg',left,right,m,ctx))))
    text+=define('eiwh',[('history','a'),('moment','a')],both(q('g','pose','a',assigned(pose)),unique))
    t=v('time')
    witness=q('g','moment','a',both(k('ys',m,c),k('zcf',m,k('ra'),k('rb'),c),k('ba',time(m,c)),k('sca',time(m,c),t)))
    text+=define('eiwi',[('time',R),('context','d')],both(k('ba',t),k('lg',*interval(k('ra'),c),t),witness))
    scope=k('ys',m,k('zb6'));local=k('ys',m,ctx)
    moments=q('f','moment','a',both(op('z',scope,local),op('z',local,k('eisla',k('ra'),moving,m,ctx)),op('y',scope,k('eiwh',hist,m))))
    coverage=q('f','time',R,op('y',k('lg',*interval(k('ra'),ctx),t),k('eiwi',t,ctx)))
    text+=define('eiwj',[('history','a')],both(k('zch',hist,k('zb6')),k('eivz',ctx),k('eiv7',moving,ctx),q('g','moment','a',scope),moments,coverage))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==268;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='definite_axis_states_from_complete_coordinate_histories',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/moving-axes-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
