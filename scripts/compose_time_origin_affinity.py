"""Separate coincident clock zeros from spatial gauge and affine extension."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_transverse_derivative_claim import ROOT,read
from scripts.compose_homogeneous_coordinates import MATRIX,VECTOR
from scripts.compose_comoving_labels import TAU
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-transverse-derivative-claim.noema';PARENT_BASIS='data/transverse-derivative-claim-basis-v1.json'
FULL='examples/v014/einstein-time-origin-affinity.noema';CORE='examples/v014/time-origin-affinity-core.noema'
BASIS='data/time-origin-affinity-basis-v1.json';ANNOTATIONS='data/time-origin-affinity-identifiers-v1.json';INDEX=286
PAIR=[('event','a'),('first','a'),('second','a'),('context','d')]
COEFFICIENTS=[(n,R) for n in ('space','ycoef','zcoef','timecoef','constant')]
MEANINGS={
 'ei4g':'kの同じ原点に位置する同じ対象出来事を、現在のKとkの四座標eiyxへ結ぶ。両系の局所時刻と測定への接続を保持し、この条件だけでは時刻値や空間値を零へ固定しない。',
 'ei4h':'同じk原点の出来事と現在の二座標組ei4gにおいて、k時刻成分τが零である条件。K時刻の零はまだ要求しない。',
 'ei4i':'同じei4hの出来事・座標組でK時刻tも零である。τ=0の出来事とt=0の出来事を別に選ばない。',
 'ei4j':'同じ設定の全対象出来事と全現在座標組について、k原点でτ=0ならt=0を要求し、その同時零点の出来事が少なくとも一つあると読む時刻原点規約。零点のない空虚な含意や全時刻でのt=τに替えない。',
 'ei4k':'同じ両時刻零の出来事ei4iにおいて、現在K組の補助三座標x-vt,y,zが零になる空間原点規約。時刻規約ei4jとは分け、k原点の空間ラベルを既出表示式に合わせる。',
 'ei4l':'同じ候補τの全対応と全k時計指示ei3c、全対象の時刻原点規約ei4j、同じ出来事の空間零点ei4k、およびτ(0,0,0,0)=0を結ぶ。零での関数値を偏微分条件だけから導いたとはしない。',
 'ei4m':'現在の四座標アフィン変換の同じ時間行からτの補助座標表示の五係数を取り出す。x=x′+v*tにより空間係数Aは変わらず、時間係数はD+v*Aとなる。y,z係数と加法定数は同じ行・定数ベクトルから取り、まだ零へ固定しない。',
 'ei4n':'先行する現在の座標対応の同じアフィン行列・定数ベクトルeizfと、同じτの全時計条件を保持する。ei4mで取り出した同じ五係数を全有効実数入力のsmdへ接続する。測定済み入力上の性質を無断で全実数へ証明済みとせず、同じアフィン式で延長する明示した読みとする。',
}
LIMITS=[
 'u0062–u0064の現在の本文接続に必要な原点とアフィン性の依存群。著者主張と全単位判断は増やさない。偏微分・未定速度係数・帰結と仮定の提示、全文判断は次の統合に残す。',
 '原文のk原点でτ=0のときt=0という条件を、現在の同じ出来事の二座標組に対する全称含意として保持する。選べる零点が一つある非空の時刻原点規約として読み、別々の出来事の零値を合わせない。全時刻でt=τとはしない。',
 '空間原点の選択は時刻条件と別にする。既出の原点往復の表示式と整合する補助三座標零を、両時刻零の同じ出来事へ接続する。原文の時刻条件だけが両系の全空間座標零を述べたとはしない。',
 '現在eiyxは同じ出来事の測定位置・局所時計・一意な時刻・系内時点へ結ぶ。旧shd/sioへ戻さない。smgの零値は同じ候補zd4について要求し、別の数式関数の零値で代用しない。',
 '先行のlinearの読みどおり加法定数を持つアフィン表示を使う。元のK座標での時間行を(A,B,C,D;E)とすると、補助座標では(A,B,C,D+v*A;E)。同じvと同じ行列を保持し、入力ごとに係数を選び直さない。',
 '全対象測定入力に対するeizfと、全有効実数四入力に対するsmdを区別する。同じ係数のアフィン式による延長を明示的な解釈条件とし、未測定の全入力が現実に出来事として存在することを要求しない。',
 '有限検査は原点の指示対象・量化範囲・零値の結合と、有理切断上の係数代入を調べる。全実数上のアフィン表示、偏微分の一意性や体の法則の自動証明とはしない。旧定義・判断・証拠を保存し、新規原始語は追加しない。',
]

def definitions():
    e=v('event');first=v('first');second=v('second');ctx=v('context');rest=k('ra');moving=k('zbm');origin=k('zbn',moving,ctx);zero=k('bb','n p a b')
    args=[v(n) for n,_ in PAIR];kt=k('zc6',first,k('zc7'));tau=k('zc6',second,k('zc7'))
    text=define('ei4g',PAIR,both(k('zc4',e),k('zbv',moving,origin,ctx),k('cb',e,origin,moving),k('eiyx',e,first,rest,ctx),k('eiyx',e,second,moving,ctx)))
    text+=define('ei4h',PAIR,both(k('ei4g',*args),k('sca',tau,zero)))
    text+=define('ei4i',PAIR,both(k('ei4h',*args),k('sca',kt,zero)))
    witness=k('ei4i',*args);allzeros=op('y',k('ei4h',*args),k('sca',kt,zero))
    for n in reversed(('event','first','second')):witness=q('g',n,'a',witness);allzeros=q('f',n,'a',allzeros)
    text+=define('ei4j',[('context','d')],both(witness,allzeros))
    text+=define('ei4k',PAIR,both(k('ei4i',*args),k('ei3h',e,first,zero,zero,zero,ctx)))
    anchor=k('ei4k',*args)
    for n in reversed(('event','first','second')):anchor=q('g',n,'a',anchor)
    text+=define('ei4l',[('context','d')],both(k('ei3c',k('zd4'),ctx),k('ei4j',ctx),anchor,k('smg',k('zd4'))))
    matrix=v('matrix');offset=v('offset');row=lambda a:app(matrix,k('zc7'),k(a));coeff=[v(n) for n,_ in COEFFICIENTS]
    values=[row('yn'),row('yo'),row('yp'),k('bd',row('zc7'),k('shv',k('zb7'),row('yn'))),app(offset,k('zc7'))]
    rows=[k('ba',k('zb7')),*[k('ba',x) for x in coeff],*[k('ba',row(a)) for a in ('yn','yo','yp','zc7')],k('ba',app(offset,k('zc7')))]
    rows += [k('sca',a,b) for a,b in zip(coeff,values)]
    fields=[('matrix',MATRIX),('offset',VECTOR)]+COEFFICIENTS
    text+=define('ei4m',fields,both(*rows))
    text+=define('ei4n',[('function',TAU)]+fields,both(k('eizf',matrix,offset),k('ei3c',v('function'),k('zb6')),k('ei4m',matrix,offset,*coeff),k('smd',v('function'),*coeff)))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='current_clock_origin_and_same_affine_extension_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/transverse-derivative-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
