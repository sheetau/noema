"""Present the first-order consequence and define speeds from current trajectories."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_velocity_first_order import ROOT,read
from scripts.compose_origin_clock_question import tracks
from scripts.compose_rod_methods import interval
from scripts.compose_solid_sphere_geometry import bind
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-velocity-first-order.noema';PARENT_BASIS='data/velocity-first-order-basis-v1.json'
FULL='examples/v014/einstein-velocity-magnitude-claim.noema';CORE='examples/v014/velocity-magnitude-claim-core.noema'
BASIS='data/velocity-magnitude-claim-basis-v1.json';ANNOTATIONS='data/velocity-magnitude-claim-identifiers-v1.json';INDICES=(354,355)
PRIMITIVES={
 'eisox':([('item','a'),('content','i[e]'),('reference','d')],'命題項目itemが同じreferenceで持つ内容は、閉じたcontentの記述に与えられているという対応。項目の名称や真偽値だけで内容を代用せず、対象・量化・条件・留保・作用域を保持する。前提項目のeiscqとは異なり、帰結や主張も扱い、仮定として使うことを要求しない。どの理論に属するか、誰が述べるか、内容の現実の真理は別に結ぶ。'),
 'eisoy':([], 'u0135第一文の、平行四辺形則が我々の理論では第一近似でのみ成立するという帰結の提示箇所。'),
 'eisoz':([], 'u0135末のWir setzenからu0136の二つの速さの定義までの導入部分。後続のundと角度の定義は同じ導入に続く別部分として接続する。'),
 'eiso2':([], '同じ点のKに対する非負の速さを表すUという表記の個体。量そのものや速度成分の表記と区別し、役割はejopへ結ぶ。'),
 'eiso3':([], '同じ点のkに対する非負の速さを表すwという表記の個体。横成分wηと区別し、役割はejoqへ結ぶ。'),
}
MEANINGS={
 'ejod':'冒頭の同じ論説の構成課題eigjの到達先として指す体系に、第一近似と厳密一般則の不成立ejocという同じ内容の命題項目が属する。理論への帰属を明示し、内容の無条件の真理や別体系の主張へ替えない。',
 'ejoe':'著者が直前の同じ点の変換後三式ejnpから、同じ理論での第一近似の位置付けejodを帰結として提示する。alsoとnach unserer Theorieを同じ前提・結論・第五節へ結ぶ。',
 'ejof':'第一近似の帰結提示ejoeを述べるメッセージ。',
 'ejog':'同じ著者・論説へejofを帰属し、先行のK三式の提示zkhに続ける。',
 'ejoh':'同じ対象・系・全現在履歴の平面定速度ejmvについて、その系の全対象期間の中の同じ時刻で、実際の二座標関数の微分値が指定した二成分となり、非負の速さがそのノルムである。実際の座標関数・尺度・時刻を保ち、単なる成分名や有限差分へ替えない。',
 'ejoi':'現在の同じ点のK/kの物理的な合成成分ejnyを共有する二実数があり、Kの全対象実時刻でその同じ成分・同じ速さを用いるejohが成り立つ。都合のよい一時刻だけからUを一定としない。',
 'ejoj':'現在の同じK/kの設定ejmxとkでの同じ点の平面定速度について、二定数zkc/zkdの非負ノルムを速さとして得る。別の物体、速度成分の符号、kの時刻とKの時刻を混ぜない。',
 'ejok':'有効な実数量の候補がKの速さへの参照zkpに等しい。速さの物理的な取得規則はejoiに置き、定義導入の値側と分ける。',
 'ejol':'有効な実数量の候補がkの速さへの参照zkqに等しい。二成分からの取得規則はejojに置く。',
 'ejop':'同じ点zkbに対するejoiのKの速さである候補を、同じ値zkpへ結ぶUの表記役割。',
 'ejoq':'同じ点zkbに対するejojのkの速さである候補を、同じ値zkqへ結ぶwの表記役割。',
 'ejom':'著者が同じ第五節・提示文脈で、二微分の二乗和からの速さと二定数の二乗和からの速さをそれぞれU,wとして定義導入する。二つの式、両表記の役割、式の順序を同じWir setzenの速さ部分へ結ぶ。',
 'ejon':'二つの速さの定義導入ejomを述べるメッセージ。',
 'ejoo':'同じ著者・論説へejonを帰属し、第一近似の帰結の後に置く。後続の角度の定義とundは別途この導入へ続ける。',
}
LIMITS=[
 '原刊905頁のu0135第一文と、Wir setzenに続くu0136の二つの二乗式を対象とする。u0137–u0138のundと角度の指定も同じ導入に属するため、今回だけでu0135全体や導入全体の意味判断を完了しない。',
 '第一近似は前段の共通速度倍率による零での線形化の読みを保持する。nurは厳密な一般則としては不成立という限定で、全ての個別設定の不一致ではない。alsoは直前の三式からの帰結提示とする。',
 'nach unserer Theorieの第一人称複数は同じ著者の論説内の理論構成eigjを指すと読む。新たな共著者集団や現代の別理論を補わず、eisdjで同じ体系を指し、eiscrと項目内容eisoxで同じ結論をその体系へ帰属する。引用内容の物理的真理を無条件に実行しない。',
 'Uとwは非負の速さとして読む。二乗式だけでは負の枝も満たすので、この非負の読みを明示する。零の速さは許し、点の速度上限は加えない。後続の角度では零速度の扱いを別に整理する。',
 'Uの二乗は同じ点のKのx(t),y(t)を同じK時刻で微分した値の二乗和、wの二乗はkの同じ二定数wξ,wηの二乗和。全期間の実際の座標関数eismhと同じ局所時計・物差し・世界線へ接続する。K/kの時刻数値や二つの速さを等置しない。',
 '現在の点は平面内で等速であるためU,wを全対象期間で同じ値として扱う。既存の相対微分sjsをその系の正の全期間に用い、端点では同じ閉区間に対する片側の読みを許す。任意の加速運動にも同じ一つの定数Uがあると拡張しない。',
 '既存のsznとszqの数値・微分構造と、U/wの値zkp/zkq・式の箇所zkr/zksをその意味規約のまま再利用する。旧szr/szs/sztの部分的な履歴設定へ戻さず、ejny/ejmv/ejmxと全現在履歴へ接続し直す。新しい基本関係は命題項目と閉じた内容の対応だけで、他は表記・本文箇所の参照である。',
 '定義導入の帰属と、条件を具体的な履歴へ適用する評価を区別する。有限の数値・関数・引数検査は全実数の微分の一般定理を証明せず、文や単位の意味判断は別記録にする。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+(R if n in ('zkp','zkq') else 'c' if fs else 'a')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    point=v('point');theory=v('theory');item=v('item');author=k('rd');scope=k('eisoq')
    attribution=both(k('eisdj',theory,k('eirf'),quote('eigj'),point),k('eiscr',theory,item,point),k('eisox',item,quote('ejoc'),point))
    text+=content('ejod',bind(('theory','item'),'a','g',attribution))
    text+=content('ejoe',k('zc',k('eisoy'),author,quote('ejnp'),quote('ejod'),scope,point))
    obj=v('object');frame=v('frame');ctx=v('context');vx=v('vx');vy=v('vy');time=v('instant');mag=v('magnitude');zero=k('bb','n p a b')
    lo,hi=interval(frame,ctx);domain='i[time '+R+']['+k('lg',lo,hi,v('time'))+']';fx,fy,fz=tracks(obj,frame,ctx)
    text+=define('ejoh',[('object','a'),('frame','a'),('vx',R),('vy',R),('instant',R),('magnitude',R),('context','d')],both(k('ejmv',obj,frame,vx,vy,zero,ctx),k('lg',lo,hi,time),k('szq',domain,fx,fy,time,vx,vy,mag)))
    lo,hi=interval(k('ra'),ctx);value=v('value')
    every=q('f','instant',R,op('y',k('lg',lo,hi,time),k('ejoh',k('zkb'),k('ra'),vx,vy,time,value,ctx)))
    text+=define('ejoi',[('value',R),('context','d')],bind(('vx','vy'),R,'g',both(k('ejny',k('zkb'),ctx,vx,vy),every)))
    text+=define('ejoj',[('value',R),('context','d')],both(k('ejmx',ctx),k('szn',value,k('zkc'),k('zkd'))))
    for n,quantity in (('ejok','zkp'),('ejol','zkq')):text+=define(n,[('value',R),('context','d')],both(k('ba',value),k('ba',k(quantity)),k('sca',value,k(quantity))))
    for n,source,target in (('ejop','ejoi','ejok'),('ejoq','ejoj','ejol')):text+=define(n,[('object','a'),('value',R),('context','d')],both(op('e',obj,k('zkb')),k(source,value,ctx),k(target,value,ctx)))
    introductions=[k('zb',k(node),author,'r[p '+source+']','r[p '+target+']',scope,point) for node,source,target in (('zkr','ejoi','ejok'),('zks','ejoj','ejol'))]
    notation=[k('eislo',k(sign),'r[p '+rule+']',k('eirf'),point) for sign,rule in (('eiso2','ejop'),('eiso3','ejoq'))]
    text+=content('ejom',both(*introductions,*notation,k('ue',k('zkr'),k('zks'),point),op('u',op('e',k('zkr'),k('zks')))))
    for body,message,claim,node,previous in (('ejoe','ejof','ejog','eisoy','zkh'),('ejom','ejon','ejoo','eisoz','eisoy')):
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(claim,[],both(k('eir3',k(node),author,k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ejog','ejoo')];added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='first_order_consequence_and_current_speed_definitions_presented',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(INDICES)).document
    ann=json.loads(read('data/velocity-first-order-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    for symbol,form in (('eiso2','U'),('eiso3','w')):ann['entries'].append(dict(symbol=symbol,role='designation',forms=[dict(text=form,language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
