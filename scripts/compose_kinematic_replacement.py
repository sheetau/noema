"""Connect tacit kinematic assumptions to complete material-coordinate snapshots."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_rod_methods import ROOT,read,history,coords,interval
from scripts.compose_material_body_motion import FAMILY
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-rod-length-claims.noema';PARENT_BASIS='data/rod-length-claims-basis-v1.json'
FULL='examples/v014/einstein-kinematic-replacement.noema';CORE='examples/v014/kinematic-replacement-core.noema'
BASIS='data/kinematic-replacement-basis-v1.json';ANNOTATIONS='data/kinematic-replacement-identifiers-v1.json';INDICES=(259,)
COORDS=[(s+a,FAMILY) for s in ('first','second') for a in ('x','y','z')]
MEANINGS={
 'eiqq':'同じ指定時刻で第一配置の物質点firstと第二配置の物質点secondが占める三座標を取り出し、全値の有効性と三成分すべての実数値の一致を要求する。二点の物質的同一性は要求しない。',
 'eiqr':'非空の二つの物質点範囲の、同じ時刻における全座標像が双方向に一致する。各第一点に同位置の第二点があり、各第二点にも同位置の第一点がある。点のラベル・重複度・密度ではなく占有位置を比較し、重心・端点・少数標本の一致で代用しない。',
 'eiqs':'同じ物体を同じ静止側ra・長さ単位ta・時間単位rbで比較する。movingは全物質点履歴で動く剛体、restingは同じ全物質点が静止する剛体で、別の許容配置zlである。指定時刻は両方の正の幅の区間内にあり、eiqrで全占有位置が一致する。',
 'eiqt':'同じ物体・運動設定・指定時刻についてeiqsを満たす静止配置が少なくとも一つあるという幾何学的置換可能性。配置の唯一性、現実に停止する過程、その過程での剛性維持は要求しない。',
 'eiqu':'原文の一般的な置換を、同じ考察設定ydで扱う全運動剛体znについて、任意に指定された時刻zpでeiqtが成立する内容として表す。対象範囲は非空で、棒一個や標本への制限ではない。',
 'eiqv':'現行の二操作eip2/eip6が各設定ye/yfでそれぞれ一意な正の長さを与え、その値が互いに厳密に一致するというsckの内容。初期静止長yaとの比較とは分ける。',
 'eiqw':'広く用いられる運動学zrについて、二操作の値の一致eiqvを使うが明示しないというscjの条件と、同じ扱いをする置換内容eiquを結ぶ。著者のoder mit anderen Wortenはzxによる言い換えとして帰属し、二内容の論理的同値を主張しない。',
 'eiqx':'通常の運動学の暗黙の仮定と幾何学的な言い換えeiqwを述べるメッセージ。アインシュタイン自身が二方法の等値や置換可能性を承認することではない。',
 'eiqy':'u0034全体を同じ著者・論説へ帰属し、方法bの値決定予告zhからの順序を保持する。',
}
LIMITS=[
 '原刊896頁のu0034全348文字・294本文文字とM0051のtを対象とする。比較時刻は既存zpという任意に指定された時刻であり、前の二端測定のxvや零時刻へ等置しない。',
 '剛体は同じ記述尺度の全物質点間距離が固定された系・尺度で全区間変わらないeigy、運動・静止はeiag/eiahとして読む。棒以外や非共線標識のない物体も含め、正方向等速並進だけへ狭めない。',
 '幾何学的に完全は、同じ固定計量・基準系・単位で、同じ指定時刻の全占有位置が一致するという読み。全物質点の座標像を双方向に比較する。個々の物質点の位置、密度、速度、時計表示、力の作用まで同一とは要求しない。',
 '両配置は同じbodyを保ち、eirhが指定する全物質点の範囲も一致する。比較する二点のラベルを同一にする必要はなく、対称な物体の点の入れ替わりを許す。異なる物体のコピーでは代用しない。',
 'zlは同じ物体に対し比較可能な静止配置を許容する物理的入力として再利用する。意味規約上、その物体を交換・加工・変形して別の静止形状を任意に作る許可ではなく、同じ物体の静止時の形状と寸法を保つ位置・姿勢の選択である。幾何が一致するという理由だけでzlを真にしない。加減速の動力学や物理的実現をこの入力から証明しない。',
 'znは考察設定ydで一般的な置換の対象となる全運動剛体の範囲として読む。都合のよい一例や、置換できる物体だけの選別ではない。非空性を要求し、選んだ全対象に完全履歴・剛性・指定時刻・置換を要求する。任意に指定されたtと運動設定の下の一般命題であり、数値を固定した一実験の結果に狭めない。',
 'zrは二原理に対して比較される既存の通常の運動学、zsはその文脈での広い使用という社会的関係として読む。頻度の数値や全員の使用は原文から補わず、実際の普及調査は翻訳の充足条件にしない。',
 '暗黙は同じ体系・仮定内容・範囲での使用ztと非明示not zuをともに要求する。記録が見つからないことから非明示を推論しない。著者によるこの帰属を保持するのであり、仮定内容を真として採用しない。',
 'oder mit anderen Wortenは同じ仮定の著者による言い換えzxとして保持する。長さの等値から任意物体の全形状一致を導いたという証明や、二内容の真偽同値を追加しない。',
 '全実数切断・全時刻・全物質点の条件を本文に保持する。有限検査は明示した履歴境界、座標像、引数結合、量化の論理骨格、引用の非実行を調べるもので、全履歴の実在や意味同値を自動証明しない。',
]


def members(body,c):return 'i[member a]['+k('eirh',body,v('member'),c)+']'
def definitions():
    at=lambda side,p,a:app(app(v(side+a),p),v('time'))
    left=[at('first',v('first'),a) for a in ('x','y','z')];right=[at('second',v('second'),a) for a in ('x','y','z')]
    text=define('eiqq',[('first','a'),('second','a'),('time',R)]+COORDS,both(k('ba',v('time')),*(k('ba',x) for x in left+right),*(k('sca',a,b) for a,b in zip(left,right))))
    match=k('eiqq',v('first'),v('second'),v('time'),*(v(n) for n,_ in COORDS))
    fm=lambda p:app(v('firstmembers'),p);sm=lambda p:app(v('secondmembers'),p)
    text+=define('eiqr',[('firstmembers','h[a] c'),('secondmembers','h[a] c'),('time',R)]+COORDS,both(k('ba',v('time')),q('g','first','a',fm(v('first'))),q('g','second','a',sm(v('second'))),q('f','first','a',op('y',fm(v('first')),q('g','second','a',both(sm(v('second')),match)))),q('f','second','a',op('y',sm(v('second')),q('g','first','a',both(fm(v('first')),match))))))
    body=v('body');moving=v('moving');resting=v('resting');time=v('time');frame=k('ra')
    mh=history(body,frame,moving);rh=history(body,frame,resting)
    text+=define('eiqs',[('body','a'),('moving','d'),('resting','d'),('time',R)],both(k('va',frame),k('ti',k('ta')),k('ci',k('rb')),op('u',op('e',k('ta'),k('rb'))),op('u',op('e',moving,resting)),k('zl',body,moving,resting),k('ba',time),*(k('bg',*interval(frame,c)) for c in (moving,resting)),*(k('lg',*interval(frame,c),time) for c in (moving,resting)),k('eiag',*mh),k('eigy',*mh),k('eiah',*rh),k('eigy',*rh),q('f','member','a',op('z',k('eirh',body,v('member'),moving),k('eirh',body,v('member'),resting))),k('eiqr',members(body,moving),members(body,resting),time,*coords(body,frame,moving),*coords(body,frame,resting))))
    text+=define('eiqt',[('body','a'),('moving','d'),('time',R)],q('g','resting','d',k('eiqs',body,moving,resting,time)))
    text+=content('eiqu',both(q('g','body','a',k('zn',body,k('yd'))),q('f','body','a',op('y',k('zn',body,k('yd')),k('eiqt',body,k('yd'),k('zp'))))))
    text+=content('eiqv',k('sck','i[value '+R+']['+k('eip2',v('value'),k('ye'))+']','i[value '+R+']['+k('eip6',v('value'),k('yf'))+']','p sbg','p sca'))
    clauses=[k('zs',k('zr'),v('point'))]
    for assumption in ('eiqv','eiqu'):clauses.append(k('scj',k('zr'),quote(assumption),k('xy'),v('point'),'p zt','p zu'))
    clauses.append(k('zx',k('zw'),k('rd'),k('zr'),quote('eiqv'),quote('eiqu'),k('xy'),v('point')))
    text+=content('eiqw',both(*clauses));text+='d eiqx[] f[j s[k eiqw[]]].\n'
    text+=define('eiqy',[],both(k('eir3',k('zv'),k('rd'),k('eirf'),quote('eiqx'),k('ri')),k('ue',k('zh'),k('zv'),k('ri')),op('u',op('e',k('zh'),k('zv')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eiqy',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='tacit_kinematic_equality_and_complete_geometric_replacement',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=list(INDICES)).document
    ann=json.loads(read('data/rod-length-claims-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
