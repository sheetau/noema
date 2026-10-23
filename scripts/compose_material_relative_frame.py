"""Attach an oriented frame to a rigid material reference and compare motion."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_material_body_motion import ROOT,read,R,F,FAMILY,FIELDS,coord
from scripts.compose_limits import v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-material-body-motion.noema'
PARENT_BASIS='data/material-body-motion-basis-v1.json'
FULL='examples/v014/einstein-material-relative-frame.noema'
CORE='examples/v014/material-relative-frame-core.noema'
BASIS='data/material-relative-frame-basis-v1.json'
ANNOTATIONS='data/material-relative-frame-identifiers-v1.json'
AXES=('x','y','z')
ENAMES=tuple(a+b for a in ('u','v','w') for b in AXES)
MARKS=[(n,'a') for n in ('origin','guide','plane')]
FRAME=[(n,F) for n in ENAMES]
POINT=[('body','a'),('context','d'),('members','h[a] c')]+[(a,FAMILY) for a in AXES]+MARKS+[('time',R)]+FRAME
PROJECT=[('origin','a')]+[(s+a,FAMILY) for s in ('left','right') for a in AXES]+FRAME
HISTORY=FIELDS+MARKS+FRAME
PAIR=[('left','a'),('right','a'),('frame','a'),('context','d'),('lengthunit','a'),('timeunit','a'),
    ('lower',R),('upper',R),('leftmembers','h[a] c'),('rightmembers','h[a] c')]+[(s+a,FAMILY) for s in ('left','right') for a in AXES]+MARKS+FRAME

MEANINGS={
 'eiaj':'有効な九つの実成分が三本の単位直交ベクトルをなし、第三軸が第一軸と第二軸の外積に等しい。軸の倍率、斜交、鏡映による左手系を拒否する。数値条件だけでは物理的な物体へ軸を帰属させない。',
 'eiak':'二つの有効な変位u,vに対し、eiajの第一軸をuと同じ正方向へ、第二軸をu,vの平面内でv成分が正になる向きへ合わせる。第二変位の第三軸成分は零である。零の第一変位、同一直線上の二変位、反転した向きを許さない。',
 'eial':'同じ物体の完全な物質点範囲から互いに異なる原点・方向点・平面点を取り、同じ時刻の位置差からeiakの右手単位軸を決める。三点の名前だけで姿勢を決めず、同じ点の座標と向きを使う。全区間履歴の成立はeiaqが別に要求する。',
 'eiam':'点から原点を引いた三変位と指定単位軸の内積。軸が正規直交であり、両位置が同じ単位・時刻・系である場合の相対位置一成分。単独で有効性や物理的割当を保証しない。',
 'eian':'同じ左側原点と右側対象点の位置差を、時刻ごとの第一単位軸へ射影する関数族。軸・原点・対象点を同じ時刻で評価する。',
 'eiao':'同じ左側原点と右側対象点の位置差を、時刻ごとの第二単位軸へ射影する関数族。第一成分や異なる時刻の軸を代用しない。',
 'eiap':'同じ左側原点と右側対象点の位置差を、時刻ごとの第三単位軸へ射影する関数族。第三軸の向きは右手系で固定する。',
 'eiaq':'eiadの完全な物体履歴に、区間の全時刻でeialの同じ三物質点による右手単位軸を結び、その軸で表した全成員の位置が全時刻対で不変であることを要求する。参照物体全体の剛な配置を確認し、三標識点以外の変形を隠さない。参照側が変形する場合は本定義の適用外として残す。',
 'eiar':'互いに異なる二物体について、左側の剛な参照履歴eiaqと右側の完全な全物質点履歴eiadを同じ評価系・文脈・単位・閉区間で結ぶ。二物体の範囲と座標族を交換しない。右側の剛性は要求しない。',
 'eias':'eiarの下で、右側の同じ成員の位置が左側の物体に付随する軸で変わる、区間内の前後二時刻を指定する。絶対座標の差や中心間距離だけを相対運動の証人としない。',
 'eiat':'eiarが成立し、右側のいずれかの物質点と前後二時刻にeiasの証人が存在する、左側参照物体に対する区間の相対運動。瞬間の相対速度や異なる二実験の運動同一性をまだ定義しない。',
 'eiau':'eiarの成立の下で、右側の全物質点が左側の物体軸で区間内の全時刻対に同じ位置を持つ相対静止。履歴や基準軸が欠ける場合を静止へ分類しない。',
}
LIMITS=[
 '参照側の全物質点が同じ三点に付随する軸で不変な位置を持つ、剛な配置を扱う。非共線な三標識点を持てない点状・線状の理想化や、参照側の変形には別の記述が必要である。右側は変形してよく、全物質点の相対配置変化を検出する。',
 '同じ評価系の同じ時刻・長さ単位・時間単位を用いる運動学的記述である。動く側の時計との同時性、Lorentz変換下の同値、回転座標系が慣性系であること、電流の不変性をこの定義から導かない。',
 '共通並進や共通回転の位置・軸の変化を相対配置と混同しない。ただし共通回転による物理的効果がないという法則ではなく、ここで定めた物体相互の配置の性質に限る。',
 '原刊の磁石と導体に適用する物理的記述尺度、剛な参照配置の採用、同じ相対運動の二場合の比較、磁石・導体・電磁相互作用、原文全体の意味判断は未完。',
 '既存207主張と意味判断を保持した補助定義である。有限検査は明示した有理数埋込みと接続境界で行い、実数全域と全履歴を有限標本で代用しない。',
]


def params(fields):return ' '.join(n+' '+t for n,t in fields)
def args(fields):return [v(n) for n,_ in fields]
def define(name,fields,body,result='c'):return 'd '+name+'['+params(fields)+'] '+result+'['+body+'].\n'
def dot(a,b):return k('sexb',*a,*b)
def vec(prefix):return [v(prefix+a) for a in AXES]
def axis_at(prefix,t):return [app(v(prefix+a),t) for a in AXES]
def location(prefix,p,t):return [app(app(v(prefix+a),p),t) for a in AXES]
def subtract(a,b):return [k('bf',x,y) for x,y in zip(a,b)]
def history_args(side):return [v(side),v('frame'),v('context'),v('lengthunit'),v('timeunit'),v('lower'),v('upper'),v(side+'members'),*(v(side+a) for a in AXES)]
def project_args(left='left',right='right'):return [v('origin'),*(v(s+a) for s in (left,right) for a in AXES),*args(FRAME)]
def local_args():return [v('origin'),*(v(a) for _ in range(2) for a in AXES),*args(FRAME)]


def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b')
    u,wv,w=vec('u'),vec('v'),vec('w')
    cross=[k('bf',k('shv',u[i],wv[j]),k('shv',u[j],wv[i])) for i,j in ((1,2),(2,0),(0,1))]
    text=define('eiaj',[(n,R) for n in ENAMES],both(*(k('ba',v(n)) for n in ENAMES),
        *(k('sca',dot(a,a),one) for a in (u,wv,w)),
        *(k('sca',dot(a,b),zero) for a,b in ((u,wv),(u,w),(wv,w))),
        *(k('sca',a,b) for a,b in zip(cross,w))))
    displacement=[('d'+a,R) for a in AXES]+[('g'+a,R) for a in AXES]
    d,g=vec('d'),vec('g')
    text+=define('eiak',displacement+[(n,R) for n in ENAMES],both(
        *(k('ba',x) for x in d+g),k('eiaj',*(v(n) for n in ENAMES)),
        k('sexd',*d,*u),k('sca',dot(g,w),zero),k('sbg',dot(g,wv))))
    time=v('time');origin=v('origin');guide=v('guide');plane=v('plane')
    coord_at=lambda p:location('',p,time)
    text+=define('eial',POINT,both(k('eiac',v('body'),v('context'),v('members')),k('zzba',time),
        *(app(v('members'),p) for p in (origin,guide,plane)),
        *(op('u',op('e',a,b)) for a,b in ((origin,guide),(origin,plane),(guide,plane))),
        k('eiak',*subtract(coord_at(guide),coord_at(origin)),*subtract(coord_at(plane),coord_at(origin)),
            *(app(v(n),time) for n in ENAMES))))
    projfields=[(s+a,R) for s in ('p','o','e') for a in AXES]
    text+=define('eiam',projfields,dot(subtract(vec('p'),vec('o')),vec('e')),R)
    for name,prefix in zip(('eian','eiao','eiap'),('u','v','w')):
        expression=k('eiam',*location('right',v('point'),time),*location('left',origin,time),*axis_at(prefix,time))
        text+=define(name,PROJECT,'i[point a][i[time '+R+']['+expression+']]',FAMILY)
    atpoint=k('eial',v('body'),v('context'),v('members'),*(v(a) for a in AXES),*args(MARKS),time,*args(FRAME))
    difference=k('eiae',v('point'),v('first'),v('second'),*(k(n,*local_args()) for n in ('eian','eiao','eiap')))
    inside=lambda t:k('lg',v('lower'),v('upper'),t)
    text+=define('eiaq',HISTORY,both(k('eiad',*args(FIELDS)),
        q('f','time',R,op('y',inside(time),atpoint)),
        q('f','point','a',q('f','first',R,q('f','second',R,op('y',
            both(app(v('members'),v('point')),inside(v('first')),inside(v('second'))),op('u',difference)))))))
    text+=define('eiar',PAIR,both(op('u',op('e',v('left'),v('right'))),
        k('eiaq',*history_args('left'),*args(MARKS),*args(FRAME)),k('eiad',*history_args('right'))))
    difference=k('eiae',v('point'),v('first'),v('second'),*(k(n,*project_args()) for n in ('eian','eiao','eiap')))
    text+=define('eias',PAIR+[('point','a'),('first',R),('second',R)],both(k('eiar',*args(PAIR)),
        app(v('rightmembers'),v('point')),inside(v('first')),inside(v('second')),
        k('zzbg',v('first'),v('second')),difference))
    text+=define('eiat',PAIR,both(k('eiar',*args(PAIR)),q('g','point','a',q('g','first',R,q('g','second',R,
        k('eias',*args(PAIR),v('point'),v('first'),v('second')))))))
    text+=define('eiau',PAIR,both(k('eiar',*args(PAIR)),q('f','point','a',q('f','first',R,q('f','second',R,
        op('y',both(app(v('rightmembers'),v('point')),inside(v('first')),inside(v('second'))),op('u',difference)))))))
    return text


def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='rigid_material_reference_relative_motion_dependency',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,definitions=MEANINGS,primitives={},
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/material-body-motion-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Material reference frame and relative motion composed; no new primitive or assertion')
