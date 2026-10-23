"""Separate the parallelogram law, its first-order limit and failure as an exact law."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_point_motion_claim import ROOT,read
from scripts.compose_solid_sphere_geometry import bind
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-point-motion-claim.noema';PARENT_BASIS='data/point-motion-claim-basis-v1.json'
FULL='examples/v014/einstein-velocity-first-order.noema';CORE='examples/v014/velocity-first-order-core.noema'
BASIS='data/velocity-first-order-basis-v1.json';ANNOTATIONS='data/velocity-first-order-identifiers-v1.json'
MEANINGS={
 'ejnw':'同じ三軸・尺度で表した二つの三成分量に対し、結果の各成分が対応する二成分の和となる平行四辺形の加法則。共通始点から二辺を取り、同じ和の頂点への対角成分を指定する。零・反対向き・平行の退化例も許す。物理的な速度への帰属は別に結ぶ。',
 'ejnx':'同じ光速V、系の速度v、点の二成分u,wから、Kでの縦横の速度成分X,Yを指定する関係。現行sytを形式上の時刻1に適用し、旧szoと同じ成分化を再利用する。正のβと非零の符号付き分母を保持し、実際の観測時刻1の存在としない。',
 'ejny':'同じ点と現在状況のK/k全履歴・K結果三式ejnl、既出の系の設定eivz、kの平面運動ejmw、Kの三定速度ejmvを、同じ二定数とejnxの成分へ接続する。数値三組だけで別々の運動を同じ速度と見なさない。',
 'ejnz':'固定した無次元の三係数a,b,cを同じ倍率λで縮小する族の、零を含む局所定義域。λ²a²<1かつ1+λ²ab>0を要求する。正の分母は零近傍を選ぶための条件で、元の合成式全域を正の分母へ変更しない。',
 'ejn2':'光速を1に規格化した縦成分λ(a+b)/(1+λ²ab)。同じ倍率を系の速度と点の縦速度へ用い、元の合成式の無次元表示とする。',
 'ejn3':'光速を1に規格化した横成分λc√(1−λ²a²)/(1+λ²ab)。点の横成分にも同じ倍率を用い、正の根を保つ。',
 'ejn4':'同じejnzの零近傍で、二つの厳密成分関数が零で値零を持ち、実切断の微分sjsにより零での導関数がa+bとcになる条件。線形項はλ(a+b),λcであり、有限差分・単一点の一致や特定誤差閾値で一次近似を代用しない。',
 'ejn5':'正の同じ光速Vでv,u,wを無次元化してejn4へ渡す。光速を固定したまま三速度成分を共通倍率で零へ近づける一次の読み。点の成分を固定したまま系の速度だけを変える展開とは区別する。',
 'ejn6':'正の許容された系の速度について、厳密なejnxの成分が平行四辺形則ejnwと一致しないこと。同じ成分を両側で比較し、違う速度の二例を比べない。',
 'ejoa':'同じ光速でejn6を満たす五つの実数が存在する。平行四辺形則が厳密な一般則ではないことを反例の存在として表す。全ての個別設定で必ず異なるという主張にはしない。',
 'ejob':'正の光速と、正で光速未満の全ての系速度・有効な任意の点の二成分についてejn5の一次の一致を要求し、同じ光速のejoaで厳密な一般的一致を排除する。有限の速度一覧を全範囲へ替えない。',
 'ejoc':'先行する同じ点のK結果内容ejnpと、現在の両系の物理的な二速度成分ejnyが存在すること、同じ光速での一次の一致と厳密一般則の不成立ejobを合わせた内容。著者の帰結・我々の理論という限定の提示は後続。',
}
LIMITS=[
 'u0135第一文の平行四辺形則と第一近似の意味依存群を扱う。原刊905頁では同じ三運動式の直後に、我々の理論では第一近似でのみ成立すると述べる。今回の内容だけで発話の提示やu0135全体の意味判断を済ませず、Wir setzen以下の速さ・角度導入も後続に残す。',
 '第一近似を、Vを固定してv,wξ,wηを同じ倍率λで零へ近づけたときの定数項と線形項の一致として読む。無次元係数a=v/V,b=wξ/V,c=wη/Vを固定し、厳密成分をVで割って比較する。原文がこの展開変数を逐語的に指定したとはしない。',
 '実際の微分sjsによる零での線形化を用いる。より強い三次誤差評価や解析級数全体、特定の実用誤差幅を著者の主張へ追加しない。第三成分は先行平面設定のまま零であり、零を一つの近似値として捨てない。',
 'nurは平行四辺形則が厳密な一般則としては成立しないという限定と読む。全ての速度の組で必ず不一致とはせず、零や特殊な組で厳密に一致することを許す。',
 '局所族は零近傍で正の分母を選ぶが、元の厳密な合成式は非零の負の分母も保つ。点の光速上限を追加しない。全対象係数に同じ一つの近傍半径があるという一様性も要求しない。',
 '平行四辺形則の三成分加法を、同じ点・系・尺度・全現在履歴と定速度へ接続する。ベクトルの加法という幾何規則と、物理的な速度合成の厳密則は区別する。',
 '全実数の微分、全速度係数と反例の存在を有限評価しない。有限対照例は式・共通倍率・引数・正の根・局所定義域を検査し、一般的な実数解析や物理法則の証明は主張しない。新規基本記号は追加しない。',
]


def definitions():
    zero=k('bb','n p a b');one=k('bb','n p b b');mul=lambda a,b:k('shv',a,b);add=lambda a,b:k('bd',a,b);sq=lambda a:mul(a,a);eq=lambda a,b:k('sca',a,b)
    names=[p+a for p in ('first','second','result') for a in ('x','y','z')]
    text=define('ejnw',[(n,R) for n in names],both(*(k('ba',v(n)) for n in names),*(eq(v('result'+a),add(v('first'+a),v('second'+a))) for a in ('x','y','z'))))
    ns=('light','speed','longitudinal','transverse','outx','outy');V,s,u,w,X,Y=map(v,ns)
    text+=define('ejnx',[(n,R) for n in ns],k('syt',V,s,k('soy',V,s),u,w,X,Y,zero,one))
    obj=v('object');ctx=v('context')
    text+=define('ejny',[('object','a'),('context','d'),('outx',R),('outy',R)],both(k('ejnl',obj,ctx),k('eivz',ctx),k('ejmw',obj,k('zbm'),k('zkc'),k('zkd'),ctx),k('ejmv',obj,k('ra'),X,Y,zero,ctx),k('ejnx',k('tc'),k('zb7'),k('zkc'),k('zkd'),X,Y)))
    a=v('a');b=v('b');c=v('c');lam=v('scale');den=add(one,mul(sq(lam),mul(a,b)));rad=k('bf',one,sq(mul(lam,a)));common=[('a',R),('b',R),('c',R)]
    text+=define('ejnz',common+[('scale',R)],both(*(k('ba',x) for x in (a,b,c,lam)),k('bg',sq(mul(lam,a)),one),k('sbg',den)))
    text+=define('ejn2',[('a',R),('b',R),('scale',R)],k('sje',mul(lam,add(a,b)),den),R)
    text+=define('ejn3',common+[('scale',R)],k('sje',mul(mul(lam,c),k('sky',rad)),den),R)
    domain='i[scale '+R+']['+k('ejnz',a,b,c,lam)+']';fx='i[scale '+R+']['+k('ejn2',a,b,lam)+']';fy='i[scale '+R+']['+k('ejn3',a,b,c,lam)+']'
    text+=define('ejn4',common,both(*(k('ba',x) for x in (a,b,c)),eq(k('ejn2',a,b,zero),zero),eq(k('ejn3',a,b,c,zero),zero),k('sjs',domain,fx,zero,add(a,b)),k('sjs',domain,fy,zero,c)))
    text+=define('ejn5',[(n,R) for n in ns[:4]],both(k('sbg',V),*(k('ba',x) for x in (s,u,w)),k('ejn4',*(k('sje',x,V) for x in (s,u,w)))))
    text+=define('ejn6',[(n,R) for n in ns],both(k('sbg',s),k('ejnx',V,s,u,w,X,Y),op('u',k('ejnw',s,zero,zero,u,w,zero,X,Y,zero))))
    text+=define('ejoa',[('light',R)],bind(ns[1:],R,'g',k('ejn6',V,s,u,w,X,Y)))
    guard=both(k('sbg',s),k('bg',s,V),k('ba',u),k('ba',w))
    text+=define('ejob',[('light',R)],both(k('sbg',V),bind(ns[1:4],R,'f',op('y',guard,k('ejn5',V,s,u,w))),k('ejoa',V)))
    text+=content('ejoc',both(op('t',k('ejnp'),v('point')),bind(('outx','outy'),R,'g',k('ejny',k('zkb'),k('zb6'),X,Y)),k('ejob',k('tc'))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==354;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements'];added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_velocity_parallelogram_first_order_and_not_exact_general_law_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/point-motion-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
