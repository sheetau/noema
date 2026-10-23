"""Compose material axis geometry at every time without imposing rest."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_frame_motion import ROOT,read
from scripts.compose_material_axes import LINE,PAIR,ROLES,at,sub,pair_geometry
from scripts.compose_material_relative_frame import define
from scripts.compose_rod_methods import history,interval,coords
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-frame-motion.noema';PARENT_BASIS='data/frame-motion-basis-v1.json'
FULL='examples/v014/einstein-moving-axes.noema';CORE='examples/v014/moving-axes-core.noema'
BASIS='data/moving-axes-basis-v1.json';ANNOTATIONS='data/moving-axes-identifiers-v1.json'
MEANINGS={
 'eiv2':'線状支持体の全物質点の剛な完全履歴を保ち、指定原点の軌道を、同じ物体側の座標関数と代表位置eismhの双方から同じseへ結ぶ。正の区間の全時刻でeiu7の直線性・原点の所在・非零方向標識を要求する。静止や特定速度は加えない。',
 'eiv3':'同じ物体・基準系・原点・方向標識の指定時刻の実際の位置差の一成分。初期時刻に固定せず、原点の平行移動を方向そのものへ混ぜない。',
 'eiv4':'同じ時刻の二物質線にeiu7の全成員の直線配置を要求し、その実方向をsexcの平行へ渡す。逆向き、異なる原点、離れた支持直線を許す。',
 'eiv5':'同じ時刻の二物質線の全成員の直線配置と非零の実方向をeiu6へ渡し、直交を要求する。ラベルだけや初期方向だけで判定しない。',
 'eiv6':'同じ時刻の一座標系を、唯一の原点、異なる三物質線、全軸役割、原点からの出発、全点剛性と実座標による直交へ結ぶ。参照はraだが、その基準に対する静止は要求しない。',
 'eiv7':'同じ系の三軸それぞれにeiv2の完全履歴を要求し、共通の正の時間区間の全時刻でeiv6の同じ三軸構成を保持する。原点の各候補関数を同じ原点の出来事へ結ぶ。',
 'eiwa':'異なる二系の同時刻のeiv6を保持し、同じ三役割の各組にeiv4の幾何学的平行を要求する。X軸も支持直線の一致に強めず、二原点や正方向の一致を追加しない。',
 'eiwb':'二系それぞれの完全な三軸履歴eiv7を保ち、同じ静止基準raの全区間でeiwaの三組の平行を要求する。時刻ごとに対象や役割を選び直さず、有限の時点標本で代用しない。運動候補の存在や採用の正当化は別に述べる。',
}
LIMITS=[
 'u0044の各静止系時刻の軸配置と全時刻の平行性を支える依存群である。配置を表す状態の存在・同値性、候補履歴の存在、対称性の理由、設定指示、段落全体の著者帰属と意味判断はまだ追加しない。',
 '物質線の同じ全成員、原点に位置する成員、原点から離れた同じ方向標識を全時刻で要求する。線状支持体の物理的な連続性は既存eismvの明示的理想化であり、有限点から認定しない。',
 '原点標識は各軸の物質点そのものに同一視しない。各軸側から取る原点の位置関数とeismhの代表位置関数を、同じ原点・系・単位・区間の完全なseへ渡す。異なる候補を単に同じ名前で呼んで済ませない。',
 '静止条件eivaやeivfを移動系へ流用しない。一般の時間依存する直線配置を記述し、u0044第一文の正X並進は現行eivzと別に接続する。加速中の剛性、初期長さ保存、時計内部静止を要求しない。',
 '対応三軸の平行には逆向きと横方向に離れた支持直線を許す。X支持直線の一致はu0043の初期条件であり、ここで全時刻へ追加しない。具体的な運動の選択を対称性だけから証明しない。',
 '有限評価は時刻ごとの数値幾何・全成員範囲・軌道と軸役割の引数結合を識別する。全実時刻の量化は保持し、そのままの有限評価を拒否する。検査で取り出す量化変数の各場合を全域証明とはしない。',
]

def every_time(frame,ctx,body):return q('f','time',R,op('y',k('lg',*interval(frame,ctx),v('time')),body))
def direction(body,origin,guide,frame,ctx,time):return [k('eiv3',body,origin,guide,frame,k(a),ctx,time) for a in ROLES]

def definitions():
    b=v('body');o=v('origin');g=v('guide');f=v('frame');c=v('context');t=v('time')
    bounds=interval(f,c);origintracks=[app(fn,o) for fn in coords(b,f,c)]
    representative=[k('eismh',o,f,k('ta'),k('rb'),k(a),c) for a in ROLES]
    line=both(k('eismv',b,c),k('bg',*bounds),k('eigy',*history(b,f,c)),*(k('se',o,f,c,k('ta'),k('rb'),*bounds,*traces) for traces in (origintracks,representative)),every_time(f,c,k('eiu7',*[v(n) for n,_ in LINE],t)))
    text=define('eiv2',LINE,line)
    component=lambda p:app(app(k('eislu',b,f,k('ta'),k('rb'),v('axis'),c),p),t)
    text+=define('eiv3',LINE[:-1]+[('axis','a'),('context','d'),('time',R)],k('bf',component(g),component(o)),R)
    first=[v(n) for n in ('first','firstorigin','firstguide')];second=[v(n) for n in ('second','secondorigin','secondguide')]
    common=both(k('eiu7',*first,f,c,t),k('eiu7',*second,f,c,t))
    for name,kernel in (('eiv4','sexc'),('eiv5','eiu6')):
        text+=define(name,PAIR+[('time',R)],both(common,k(kernel,*direction(*first,f,c,t),*direction(*second,f,c,t))))
    origin=k('zbn',f,c);axis=lambda role:k('zbo',f,k(role),c)
    material='i[line a]['+k('eiu7',v('line'),origin,k('eismu',v('line'),k('ra'),c),k('ra'),c,t)+']'
    rigid='i[line a context d]['+k('eigy',*history(v('line'),k('ra'),v('context')))+']'
    perpendicular='i[first a second a context d]['+k('eiv5',*pair_geometry(v('first'),origin,v('second'),origin,v('context')),t)+']'
    triad=k('sex',f,origin,*(axis(a) for a in ROLES),*(k(a) for a in ROLES),c,'p zbv','p zbw',material,rigid,'p zbr',perpendicular)
    choices=[both(op('e',v('role'),k(a)),op('e',v('line'),axis(a))) for a in ROLES]
    exact=q('f','line','a',q('f','role','a',op('z',k('zbw',f,v('line'),v('role'),c),op('x',choices[0],op('x',*choices[1:])))))
    unique=q('f','point','a',op('y',k('zbv',f,v('point'),c),op('e',v('point'),origin)))
    text+=define('eiv6',[('frame','a'),('context','d'),('time',R)],both(k('va',f),k('ba',t),triad,exact,unique))
    lines=[k('eiv2',axis(a),origin,k('eismu',axis(a),k('ra'),c),k('ra'),c) for a in ROLES]
    text+=define('eiv7',[('frame','a'),('context','d')],both(k('bg',*interval(k('ra'),c)),*lines,every_time(k('ra'),c,k('eiv6',f,c,t))))
    left=v('first');right=v('second');distinct=op('u',op('e',left,right))
    paired=[k('eiv4',*pair_geometry(k('zbo',left,k(a),c),k('zbn',left,c),k('zbo',right,k(a),c),k('zbn',right,c),c),t) for a in ROLES]
    text+=define('eiwa',[('first','a'),('second','a'),('context','d'),('time',R)],both(distinct,k('eiv6',left,c,t),k('eiv6',right,c,t),*paired))
    text+=define('eiwb',[('first','a'),('second','a'),('context','d')],both(distinct,k('eiv7',left,c),k('eiv7',right,c),every_time(k('ra'),c,k('eiwa',left,right,c,t))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==268;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='complete_time_dependent_material_axis_geometry',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/frame-motion-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
