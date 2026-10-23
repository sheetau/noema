"""Connect a low-burden spatial method, two principles and the longitudinal ray."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_origin_light_ray import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_coordinate_correspondence import SIDE,SYSTEM,TRUE
from scripts.compose_calculation_discourse import STEPS,STEP,LEFT,RIGHT,FALSE
from scripts.compose_limits import R,v,call as k,app,op,both

PARENT='examples/v014/einstein-origin-light-ray.noema';PARENT_BASIS='data/origin-light-ray-basis-v1.json'
FULL='examples/v014/einstein-spatial-method-claim.noema';CORE='examples/v014/spatial-method-claim-core.noema'
BASIS='data/spatial-method-claim-basis-v1.json';ANNOTATIONS='data/spatial-method-claim-identifiers-v1.json';INDEX=289
SPATIAL='h[a a] '+R
PRIMITIVES={
 'eisnn':([], 'この箇所で利用できると著者が提示する空間座標の計算方法への参照。実際に実行した行為や原文に明記された特定の手順数を意味しない。'),
 'eisno':([('method','a'),('stage','d')], '同じ方法を同じ段階で用いる計算が答えとして提示する、入力記録と成分役割から実数値を与える候補写像。入力と役割の範囲、値の有効性、対応の正しさは別の条件で要求する。実際の実行済み、解の存在、正答をこの割当だけから導かない。'),
}
MEANINGS={
 'ei5b':'候補空間写像の三成分と既出の同じτから四式の有限列を構成する。各式の左辺はk側の当該成分、右辺はK側四座標からの候補空間成分又は同じzd4のτ(x−vt,y,z,t)。役割順はξ,η,ζ,τである。',
 'ei5c':'同じ方法・現在の談話段階に割り当てた候補写像の四式ei5bが、現在の方程式課題eiy4を満たすという到達目標内容。τを既知の式に固定して残る三空間成分を求める。候補を原文にない具体的な答えへ固定しない。',
 'ei5d':'同じ現在設定のK/kの等速並進、相対性原理eion、Kの第二原理eiosと現在のτ対応ei3cを合わせた、kでも同じVという著者の推論の前提内容。',
 'ei5e':'同じkで同じVを測る全光区間の現在法則ei43。Kの参照時計やKの時刻をkへ流用しない。',
 'ei5f':'先行する同じτの式smnと、kの現在の全区間光速度法則ei5eを合わせた内容。後者の経路長・経過時間の等式を空間成分を求める手順で使う。',
 'ei5g':'先行する同じτの結果smnと二原理の適用前提ei5dを合わせた、空間座標を求める計算の出発内容。',
 'ei5h':'有限手順列のいずれかの前又は後の記述が、指定した閉じた内容記述と同一である。空列なら偽。意味が似た別記述や列外の記述を流用しない。',
 'ei5i':'同じ著者が現在利用できる一方法の有限手順が、先行τと二原理の前提ei5gから空間三成分の解候補条件ei5cへつながり、途中にτとkの光速度等式ei5fを含む。その同じ列の非負負担合計が文脈の低負担基準に入る。実行済みや全読者の能力を要求しない。',
 'ei5j':'先行τの結果・三空間成分・同じ方程式課題zdbを参照する提示zf2に、利用可能な同じ低負担計算方法ei5iの著者評価を結ぶ。容易という語をzf2だけで説明済みとは扱わない。',
 'ei5k':'同じ著者が二原理と現在の運動設定ei5dから、kで測っても同じVであるei5eを要請する帰結として提示する。物理的導出の自動証明ではない。',
 'ei5l':'同じ選択記録zez/zeyに、原点放出・正の縦方向・全二軌道・現在の時計と座標・先行τ式ei5aを結んだ条件内容。',
 'ei5m':'その同じ光線条件ei5lの下でξ=Vτというsnrを同じ著者の帰結として提示する。',
 'ei5n':'その同じ光線条件の下で、ξ=Vτと同じτ式への代入snsを同値な別表示として提示する。oderを排他的な二択にしない。',
}
GROUPS=(('ei5j','ei5o','ei5p','ze7','zev'),('ei5k','ei5q','ei5r','ze2','ze7'),('ei5m','ei5s','ei5t','ze3','ze2'),('ei5n','ei5u','ei5v','ze4','ze3'))
for body,message,author,node,previous in GROUPS:
    MEANINGS[message]=body+'の著者による提示を述べるメッセージ。引用した物理的内容の真理を処理系自身が宣言しない。'
    MEANINGS[author]=body+'の提示を同じ著者rd・論説eirfへ帰属し、先行箇所'+previous+'から'+node+'への本文順序を保持する。'
LIMITS=[
 'u0065–u0068を先行τの利用、空間三座標の計算方法、二原理の挿入説明、原点から正のξ方向への光線、二つの式とoderの書換えとして読む。',
 'leichtは、この論説で利用できると提示された同じ計算方法の必要な手順が文脈上低負担であるという評価として読む。既存s2w/s2x/s2yの連続した有限手順・非負負担・合計基準を使い、本人の能力上限や実際の計算時間は補わない。',
 'manは同じ議論でこの方法を用いる主体として著者に代表させる。全人類・全読者が低負担で計算できるという全称にはしない。数値負担・閾値・手順数は原文にないため固定しない。',
 '計算の手順と許容変形は既存zlx/zlaの文脈入力である。計算が提示する候補写像の目標を現在のeiy4へ結ぶが、実行履歴・原文に省略された機械証明・規則の健全性を捏造しない。容易という著者の評価は偽でも記述できる。',
 'durch Gleichungenを、同じkの全区間に経路長=V×経過時間を要求するei43の式を手順中で使うこととして読む。先行τを保持し、任意の低負担の別計算で代用しない。',
 '二原理からkの法則を要請することはzcによる著者の帰結として保持する。測定規約の接続、全区間、同じV、光源の運動への独立性を保持し、引用から現実の法則の証明へ変えない。',
 '正のξ光線は直前の零点規約とξ=Vτに合わせた原点放出の読みを継承する。各系の全直線一定速度軌道ei47を用い、τ=0だけから全空間原点を導かない。',
 '表示式のξは同じ光線上の到達出来事の値である。τの代入には同じV,v,φ(v),x′,tを用いる。光線外の全変換をこの二式だけで決定せず、V−vと後続のtの消去はu0069以降に分ける。',
 '候補空間写像を代入する四式の構成は目標条件であり、その候補が現在の測定対応に一致することの自動証明ではない。有限検査・著者の提示・全文読解判断を区別する。',
]

def definitions():
    text='r eisnn[] a.r eisno[a d] '+SPATIAL+'.\n'
    first=v('first');second=v('second');coord=lambda tup,role:k('zc6',tup,k(role))
    time=app(k('zd4'),k('sin',k('zb7'),coord(first,'yn'),coord(first,'zc7')),coord(first,'yo'),coord(first,'yp'),coord(first,'zc7'))
    equations=[]
    for role in ('yn','yo','yp','zc7'):
        rhs=time if role=='zc7' else app(v('spatial'),first,k(role))
        choice=op('x',both(v('left'),app(coord(second,role),v('number'))),both(op('u',v('left')),app(rhs,v('number'))))
        equations.append('i[first a second a left c][i[number b]['+choice+']]')
    text+=define('ei5b',[('spatial',SPATIAL)],'l['+SIDE+']['+' '.join(equations)+']',SYSTEM)
    text+=content('ei5c',k('eiy4',k('ei5b',k('eisno',k('eisnn'),v('point')))))
    ctx=k('zb6')
    text+=content('ei5d',both(op('t',k('eion'),ctx),k('eios',k('tc'),ctx),k('eiok',k('ra'),k('zbm'),ctx),k('ei3c',k('zd4'),ctx)))
    text+=content('ei5e',k('ei43',k('zbm'),k('tc'),ctx))
    text+=content('ei5f',both(op('t',k('smn'),v('point')),op('t',k('ei5e'),v('point'))))
    text+=content('ei5g',both(op('t',k('smn'),v('point')),op('t',k('ei5d'),v('point'))))
    found=op('x',v('found'),op('x',op('e',app(v('step'),LEFT),v('target')),op('e',app(v('step'),RIGHT),v('target'))))
    text+=define('ei5h',[('steps',STEPS),('target','i[e]')],'q[v steps]['+FALSE+'][i[found c step '+STEP+']['+found+']]')
    steps=k('zlx',k('eisnn'),v('point'))
    text+=content('ei5i',both(k('zlw',k('rd'),k('eisnn'),v('point')),k('s2y',steps,quote('ei5g'),quote('ei5c'),'i[before i[e] after i[e]]['+k('zla',v('before'),v('after'),v('point'))+']','i[step '+STEP+']['+k('zlb',v('step'),v('point'))+']','i[burden b]['+k('zlc',v('burden'),v('point'))+']'),k('ei5h',steps,quote('ei5f'))))
    text+=content('ei5j',both(k('zf2',k('ze7'),k('rd'),quote('smn'),'l[a][k yn[] k yo[] k yp[]]',k('zdb'),k('eisms'),v('point')),k('uh',k('ze7'),k('rd'),quote('ei5i'),k('eisms'),v('point'))))
    text+=content('ei5k',k('zc',k('ze2'),k('rd'),quote('ei5d'),quote('ei5e'),k('eisms'),v('point')))
    text+=content('ei5l',k('ei5a',k('zez'),k('zey'),ctx))
    text+=content('ei5m',k('zc',k('ze3'),k('rd'),quote('ei5l'),quote('snr'),k('eisms'),v('point')))
    text+=content('ei5n',k('zd3',k('ze4'),k('rd'),quote('ei5l'),quote('snr'),quote('sns'),k('eisms'),v('point')))
    for body,message,author,node,previous in GROUPS:
        text+='d '+message+'[] f[j s[k '+body+'[]]].\n'
        text+=define(author,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(previous),k(node),k('ri')),op('u',op('e',k(previous),k(node)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=g[2],arguments=[])) for g in GROUPS]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='spatial_method_and_two_longitudinal_equations_connected',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=list(range(INDEX,INDEX+4))).document
    ann=json.loads(read('data/origin-light-ray-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
