"""Connect material axes and their support-line geometry to complete histories."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_transformation_heading import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_rod_methods import history,coords,interval
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-transformation-heading.noema';PARENT_BASIS='data/transformation-heading-basis-v1.json'
FULL='examples/v014/einstein-material-axes.noema';CORE='examples/v014/material-axes-core.noema'
BASIS='data/material-axes-basis-v1.json';ANNOTATIONS='data/material-axes-identifiers-v1.json'
LINE=[('body','a'),('origin','a'),('guide','a'),('frame','a'),('context','d')]
PAIR=[('first','a'),('firstorigin','a'),('firstguide','a'),('second','a'),('secondorigin','a'),('secondguide','a'),('frame','a'),('context','d')]
ROLES=('yn','yo','yp')
PRIMITIVES={
 'eismu':([('line','a'),('frame','a'),('context','d')], '同じlineの方向を座標で表すために選ぶ物質点の候補。frameとcontextに固定し、同じ物体の成員であること、原点との非零の距離、実際の全区間座標は合成側で要求する。候補という名前だけから方向や剛性を認定しない。'),
 'eismv':([('body','a'),('context','d')], 'bodyを、巨視的な形状の記述において一つの連続した線状の物質支持体として理想化するという物理的な形状分類。物質は同じbodyの全成員eirhとして追跡し、物質点を空間位置又は測定標本と同一視しない。横断面の厚みをこの軸の記述では捨象するが、原子が数学的な無厚みの直線であるという物性の主張ではない。有限の線状支持体から幾何学的な支持直線を延長して使うことを許す。線状支持体の連続性は形状の物理的入力であり、有限点から推定しない。直線性、非退化性、共通原点の所在、剛性、静止、向きと他軸との配置は別に合成する。'),
}
MEANINGS={
 'eiu5':'有効な二つの実三成分について、外積の三成分が零であるという共線条件。零変位も許す。方向が非零であることは呼び出し側で要求し、支持直線上の原点自身を排除しない。',
 'eiu6':'有効で零でない二つの実三成分の内積が零であるという直交条件。単位長・正方向・右手系を要求しない。',
 'eiu7':'同じ物体の全成員の同時刻座標が、指定原点と同じ物体内の方向標識を通る一つの直線上にある。原点位置に物質点が存在し、方向標識は原点から非零に離れる。原点という幾何学的標識を各物体で同一の物質点にする必要はない。',
 'eiva':'線状支持体の理想化、同じ物体の全物質点の完全な静止履歴eipwと剛性eigy、計量規約、原点標識の完全な静止軌道eit2、初期時刻での全成員の直線性eiu7を結ぶ。同じ区間で全位置が不変なので、初期断面の直線配置が区間を通じて保たれる。有限の時点標本の静止とは異なる。',
 'eivb':'同じ物体・原点・方向標識・系・文脈について、共通区間の初期時刻での標識から原点を引いた位置差の一成分。正規化した単位ベクトルではなく、物理的な座標履歴へ結ぶ非零方向の構成要素。',
 'eivc':'同じ静止基準でeivaを満たす二物質線の実際の方向をeiu6へ渡し、幾何学的な直交を要求する。ラベルや未接続の数値ベクトルだけで直交としない。',
 'eivd':'同じ静止基準の二物質線の非零方向を既存sexcへ結ぶ幾何学的平行。逆向きも許し、支持直線の位置又は物体の同一性は要求しない。',
 'eive':'eivdの二支持直線の平行に加え、二原点の位置差が第一方向と共線であることを要求する。同じ支持直線を占める条件で、原点が同じ場合と軸方向にずれる場合の両方を許す。物体として同一の線にしない。',
 'eivf':'指定した一つの系を、同じ初期静止基準raに対する三本の剛な物質線、同じ幾何学的原点、互いの直交、三役割の割当てへsexで結ぶ。全軸割当てがこの三役割・三線を尽くし、原点割当ても同じ一点を指す。補助物体の存在は排除しない。',
 'eivg':'異なる二系それぞれのeivfを保持し、seyへ実際の支持直線一致eiveと平行eivdを渡す。対応するX軸は同じ支持直線、Y軸とZ軸はそれぞれ平行。二原点の一致と軸の正方向の一致を加えない。',
}
LIMITS=[
 'u0043前半の二座標系・各三物質線・直交と対応軸配置を支える依存群である。267の既存本文主張は維持する。計器の仕様、設定指示、d. h.の説明提示、段落全体の帰属と意味判断はまだ接続しない。',
 '物質線は巨視的な連続線状支持体として理想化する。形状分類の物理的入力eismvと、全成員の実際の座標・直線性を分ける。有限の物質線の支持直線を幾何学的に延長でき、全空間を物質で満たす無限棒を要求しない。',
 '原点の場所には各線の物質点が存在するが、それらを同じ物質点個体に同一視しない。方向標識は同じ物体内の非零方向を選ぶ。原点からの正負の側や物質線の長さを限定せず、単位長の軸や右手三軸もこの原文へ加えない。',
 '全物質点・区間全体の静止と剛性を現在のeipw/eigyへ結び、原点の軌道にも同じ座標帰属を求める。静止区間の初期断面を幾何学的比較に使えるのは、この完全な静止条件を要求するためであり、端点標本だけで配置不変を推定しない。',
 '全軸割当ての限定は座標系を構成する三軸に関するもの。周囲の補助的な線、目盛り、別物体を世界から排除しない。支持直線の一致は二つの物質物体の同一性ではない。',
 '初期静止配置だけを扱い、後続u0044の運動付与・加速中の剛性・運動後の同時性・全系での長さ不変を追加しない。時計内部の機構を全物質点の静止へ渡す定義として使わない。',
 '有限検査は有理数埋込みの幾何学、全成員と軌道の境界結合、軸の全範囲、向きと原点差を検査する。全実数・全時刻の成立を有限標本から認定せず、未知の座標を零にしない。u0043全体と二作品の目標は未完。',
]

def args(fs):return [v(n) for n,_ in fs]
def dot(a,b):return k('sexb',*a,*b)
def sub(a,b):return [k('bf',x,y) for x,y in zip(a,b)]
def at(body,point,frame,ctx,time):return [app(app(f,point),time) for f in coords(body,frame,ctx)]
def direction(body,origin,guide,frame,ctx):return [k('eivb',body,origin,guide,frame,k(a),ctx) for a in ROLES]
def pair_geometry(first,fo,second,so,ctx):return [first,fo,k('eismu',first,k('ra'),ctx),second,so,k('eismu',second,k('ra'),ctx),k('ra'),ctx]

def definitions():
    text='r eismu[a a d] a.\nr eismv[a d] c.\n';six=[(s+a,R) for s in ('u','v') for a in ('x','y','z')]
    u=[v('u'+a) for a in ('x','y','z')];w=[v('v'+a) for a in ('x','y','z')];zero=k('bb','n p a b')
    cross=[k('bf',k('shv',u[i],w[j]),k('shv',u[j],w[i])) for i,j in ((1,2),(2,0),(0,1))]
    text+=define('eiu5',six,both(*(k('ba',x) for x in u+w),*(k('sca',x,zero) for x in cross)))
    text+=define('eiu6',six,both(*(k('ba',x) for x in u+w),k('sbg',dot(u,u)),k('sbg',dot(w,w)),k('sca',dot(u,w),zero)))
    b=v('body');o=v('origin');g=v('guide');f=v('frame');c=v('context');t=v('time');p=v('point')
    origin=at(b,o,f,c,t);guide=at(b,g,f,c,t);point=at(b,p,f,c,t);delta=sub(guide,origin)
    allpoints=q('f','point','a',op('y',k('eirh',b,p,c),k('eiu5',*sub(point,origin),*delta)))
    occupied=q('g','point','a',both(k('eirh',b,p,c),*(k('sca',x,y) for x,y in zip(point,origin))))
    text+=define('eiu7',LINE+[('time',R)],both(k('ba',t),*(k('ba',x) for x in origin+guide),k('eirh',b,g,c),k('sbg',dot(delta,delta)),allpoints,occupied))
    bounds=interval(f,c);origintracks=[app(fn,o) for fn in coords(b,f,c)]
    text+=define('eiva',LINE,both(k('eismv',b,c),k('eipw',b,f,c),k('eigy',*history(b,f,c)),k('eisdd',f,k('ta'),k('rb'),c),k('eit2',o,f,c,k('ta'),k('rb'),*bounds,*origintracks),k('eiu7',*args(LINE),bounds[0])))
    component=lambda p:app(app(k('eislu',b,f,k('ta'),k('rb'),v('axis'),c),p),bounds[0])
    text+=define('eivb',LINE[:-1]+[('axis','a'),('context','d')],k('bf',component(g),component(o)),R)
    first=[v(n) for n in ('first','firstorigin','firstguide')];second=[v(n) for n in ('second','secondorigin','secondguide')]
    common=both(k('eiva',*first,f,c),k('eiva',*second,f,c))
    for name,kernel in (('eivc','eiu6'),('eivd','sexc')):
        text+=define(name,PAIR,both(common,k(kernel,*direction(*first,f,c),*direction(*second,f,c))))
    origins=sub(at(second[0],second[1],f,c,bounds[0]),at(first[0],first[1],f,c,bounds[0]))
    text+=define('eive',PAIR,both(k('eivd',*args(PAIR)),k('eiu5',*origins,*direction(*first,f,c))))
    actualorigin=k('zbn',f,c);line=lambda role:k('zbo',f,k(role),c)
    material='i[line a]['+k('eiva',v('line'),actualorigin,k('eismu',v('line'),k('ra'),c),k('ra'),c)+']'
    rigid='i[line a context d]['+k('eigy',*history(v('line'),k('ra'),v('context')))+']'
    perpendicular='i[first a second a context d]['+k('eivc',*pair_geometry(v('first'),actualorigin,v('second'),actualorigin,v('context')))+']'
    triad=k('sex',f,actualorigin,*(line(a) for a in ROLES),*(k(a) for a in ROLES),c,'p zbv','p zbw',material,rigid,'p zbr',perpendicular)
    selected=[both(op('e',v('role'),k(a)),op('e',v('line'),line(a))) for a in ROLES]
    exact=q('f','line','a',q('f','role','a',op('z',k('zbw',f,v('line'),v('role'),c),op('x',selected[0],op('x',*selected[1:])))))
    origin_unique=q('f','point','a',op('y',k('zbv',f,p,c),op('e',p,actualorigin)))
    text+=define('eivf',[('frame','a'),('context','d')],both(k('va',f),triad,exact,origin_unique))
    a=v('first');z=v('second');fo=k('zbn',a,c);so=k('zbn',z,c)
    related=lambda name:'i[left a right a context d]['+k(name,*pair_geometry(v('left'),fo,v('right'),so,v('context')))+']'
    alignment=k('sey',*(k('zbo',frame,k(role),c) for frame in (a,z) for role in ROLES),c,related('eive'),related('eivd'))
    text+=define('eivg',[('first','a'),('second','a'),('context','d')],both(op('u',op('e',a,z)),k('eivf',a,c),k('eivf',z,c),alignment))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==267;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='material_axis_geometry_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/transformation-heading-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
