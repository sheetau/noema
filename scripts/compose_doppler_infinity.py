"""Attribute the printed infinity claim without adding infinite real values."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_doppler_specialization import ROOT,read,EXTENDED
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,app,op,both,quant as q,lam

PARENT='examples/v014/einstein-doppler-specialization.noema';PARENT_BASIS='data/doppler-specialization-basis-v1.json'
FULL='examples/v014/einstein-doppler-infinity.noema';CORE='examples/v014/doppler-infinity-core.noema'
BASIS='data/doppler-infinity-basis-v1.json';ANNOTATIONS='data/doppler-infinity-identifiers-v1.json';INDEX=374
GRAPH='h['+R+' '+R+'] c'
BACKGROUND=[(n,t) for n,t in EXTENDED if t in ('a','d') or n in ('light','newfrequency')]
WITNESSES=[(n,t) for n,t in EXTENDED if (n,t) not in BACKGROUND and n not in ('speed','frequency')]
VARIABLES=[(n,t) for n,t in BACKGROUND if n not in ('frame','light','scope','context')]
assert (len(BACKGROUND),len(WITNESSES),len(VARIABLES))==(15,43,11)
PRIMITIVES={
 'eisst':([], 'u0192のMan siehtから始まる、印刷された無限大の帰結を提示する箇所。'),
 'eissu':([], 'u0192のダッシュ間で通常の理解との対照を挿入する箇所。通常の理解の具体的な公式を原文にない形で指定する参照ではない。'),
}
MEANINGS={
 'ekff':'二実数関係graphの有効な有限実数の点(input,output)。無限大を実切断へ追加しない。',
 'ekfg':'有効な有限cutoffよりinputが厳密に小さく、同じgraphの有効な点である条件。',
 'ekfh':'指定cutoffの下に同じgraphの点が一つ以上ある。inputとoutputを共に存在量化し、別の関係で証人を選ばない。',
 'ekfi':'全ての有限実数cutoffについてekfhが成立する負方向の非有界性。空又は下に有界な定義域を負の無限大への接近と認めない。',
 'ekfj':'同じgraphの点がcutoffの下にあるなら、そのoutputが同じ上限boundを厳密に超えるという一点の含意。切断の有効性はekfg及び呼出側ekfkが保持する。',
 'ekfk':'有効なboundとcutoffについて、全input/outputでekfjが成り立つ。多価関係の一つの大きい値だけを選んで他の小さい値を隠さない。',
 'ekfl':'指定された有限boundに対してekfkを満たす有限cutoffがある。cutoffはboundの後で選ぶ。',
 'ekfm':'負方向に非有界な同じgraphについて、任意の有限boundごとにekflを要求する。input→−∞でoutput→+∞という関係的発散であり、一つの無限実数の存在や一様な単一cutoffを述べない。',
 'ekfn':'先行と同じ60役割で、物理的なφ=0の条件ekeyと、放射frequency及び受信newfrequencyの平方根比の関係ekezを共に要求する。',
 'ekfo':'背景15役割と入力speed・出力frequencyを固定し、残る43役割を同じekfnの証人として存在量化した関係。各点で周期・位相率・軌道などを選び直せるが、条件と等式で別々の証人を取らない。',
 'ekfp':'背景15役割に対し、同じekfoを入力speedと出力frequencyの二変数関係として返す。印字の無印νを出力にし、ν′は背景側で保つ。',
 'ekfq':'同じ背景でekfoを満たす有限のspeedとfrequencyが少なくとも一組ある。物理設定が全くない背景への空虚な主張を避ける前件。',
 'ekfr':'K・V・第七節・評価状況を保ち、残る背景11役割の全割当について、ekfqなら同じgraphがekfmを満たすと述べる内容。原文のv=−∞,ν=∞を、同じ有限ν′を背景にした関係的境界主張と読む。内容の成立を著者への帰属時に要求しない。',
 'ekfs':'指定waveが先行の同じK・V・第七節で、φ=0の放射・受信周期数と相対速度の関係に入るという性質。対照の共通観点として引用し、単なる語順や箇所の名前を共通観点の代わりにしない。',
 'ekft':'指定viewが当該論説の通常の理解として取り上げられ、その下で指定の閉じたdescriptionが採られ、その内容から今回の境界主張ekfrへ同じ波・周期数・速度の観点で対照的に提示されること。通常理解の具体的公式やekfrの厳密な論理否定を補わない。',
 'ekfu':'通常理解とその内容を存在量化したekft。原文が特定しない通常理解の式を未指定のまま保ち、対応する同じ内容を対照に渡す。',
 'ekfv':'著者が同じekfrを述べ、それを認められる帰結として提示し、直前のφ=0の式eke3からの帰結とする談話内容。物理的な正しさ、実際の読者の心理又は証明成功を含意しない。',
 'ekfw':'主節の提示ekfv、通常理解との対照ekfu、同じ主節ekfrへの挿入的補足eisa5を連言した一文全体。',
 'ekfx':'u0192全文のekfwを述べるメッセージ。',
 'ekfy':'u0192全文を同じ著者・論説へ帰属し、直前のφ=0の表示の後に接続する。',
}
LIMITS=[
 '固定原文u0192と原刊912頁の印字をv=−∞,ν=∞と読んで保持する。v=−Vやν′=∞へ訂正しない。誤植の可能性や物理的に望ましい式の推測を原文そのものへ混ぜない。',
 '等号を含む無限大表記は、有限実数を入力・出力とする関係の境界挙動として読む。各有限上限より下へ進む入力と、任意の有限上限を超える出力を量化する。無限大を実数として存在させず、空の定義域を発散と認めない。',
 '印字のνは先行の放射周期数frequencyである。受信newfrequency=ν′、同じ物体・波・系・単位と状況を背景に保ち、入力をv、出力をνとする。これは曖昧な境界文の採用読解であり、著者の唯一の意図の確定ではない。νとν′の取り違えや暗黙の訂正で整合性を作らない。',
 '43個の補助量は関係の各点に存在量化し、周期や軌道を固定して発散を人工的に妨げない。15背景のうちK・V・節・状況を固定し、残る11役割を全称量化する。非空の設定の下で同じ関係の発散を述べる条件内容とする。',
 '先行の物理的な標準配置は0<v<Vであり、今回もその式からの帰結という参照を保つ。その関係はcutoff=0より下に点を持たず、印刷通りの負の無限大への接近を支持しない。この不整合を隠すための超光速拡張、未定義平方根の値、量記号の差替えを追加しない。',
 'Man siehtは著者が同じ内容を認められる帰結として提示することと読む。zdgとzcは引用を評価して証明する規則ではない。偽又は適用域外の主張も閉じた内容として帰属できることと、主張が真であることを分ける。',
 'im Gegensatz zu der üblichen Auffassungは、この論点で取り上げられる通常理解との対照を主節へ挿入したものと読む。原文は通常理解の具体式を示さないので見解と内容を存在量化し、古典式、全員一致、現代の理解、主節の厳密な論理否定は補わない。既存eisah/eisai/eisnp/eisa5を再使用する。',
 '有限評価は局所点・量化順序・結合・談話の接続を診断する。全実数や全記述域の評価は拒否し、有限モデルの通過を一般の発散証明、物理的真理又は意味同義性の自動証明とはしない。',
]

def quantified(marker,fields,body):
    for n,t in reversed(fields):body=q(marker,n,t,body)
    return body

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES)
    g=[('graph',GRAPH)];xy=[('input',R),('output',R)];G=v('graph');x=v('input');y=v('output');B=v('cutoff');M=v('bound')
    text+=define('ekff',g+xy,both(k('ba',x),k('ba',y),app(G,x,y)))
    text+=define('ekfg',g+[('cutoff',R)]+xy,both(k('ba',B),k('ekff',G,x,y),k('bg',x,B)))
    text+=define('ekfh',g+[('cutoff',R)],quantified('g',xy,k('ekfg',G,B,x,y)))
    text+=define('ekfi',g,q('f','cutoff',R,op('y',k('ba',B),k('ekfh',G,B))))
    text+=define('ekfj',g+[('bound',R),('cutoff',R)]+xy,op('y',k('ekfg',G,B,x,y),k('bg',M,y)))
    text+=define('ekfk',g+[('bound',R),('cutoff',R)],both(k('ba',M),k('ba',B),quantified('f',xy,k('ekfj',G,M,B,x,y))))
    text+=define('ekfl',g+[('bound',R)],both(k('ba',M),q('g','cutoff',R,k('ekfk',G,M,B))))
    text+=define('ekfm',g,both(k('ekfi',G),q('f','bound',R,op('y',k('ba',M),k('ekfl',G,M)))))
    text+=define('ekfn',EXTENDED,both(k('ekey',*args(EXTENDED)),k('ekez',*args(EXTENDED))))
    text+=define('ekfo',BACKGROUND+[('speed',R),('frequency',R)],quantified('g',WITNESSES,k('ekfn',*args(EXTENDED))))
    text+=define('ekfp',BACKGROUND,'i[speed '+R+' frequency '+R+']['+k('ekfo',*args(BACKGROUND),v('speed'),v('frequency'))+']',GRAPH)
    text+=define('ekfq',BACKGROUND,quantified('g',[('speed',R),('frequency',R)],k('ekfo',*args(BACKGROUND),v('speed'),v('frequency'))))
    fixed={'frame':k('ra'),'scope':k('eisrx'),'context':v('point'),'light':k('tc')};actual=[fixed.get(n,v(n)) for n,t in BACKGROUND]
    text+=content('ekfr',quantified('f',VARIABLES,op('y',k('ekfq',*actual),k('ekfm',k('ekfp',*actual)))))
    text+='d ekfs[wave a] e[b point['+quantified('g',[(n,t) for n,t in VARIABLES if n!='wave'],k('ekfq',*actual))+']].\n'
    p=v('context');node=k('eisst');aside=k('eissu');author=k('rd');scope=k('eisrx');description=v('description')
    text+=define('ekft',[('view','a'),('description','i[e]'),('context','d')],both(k('eisah',v('view'),k('eirf'),p),k('eisai',v('view'),description,p),k('eisnp',aside,author,aside,description,node,quote('ekfr'),'r[p ekfs]',p)))
    text+=content('ekfu',quantified('g',[('view','a'),('description','i[e]')],k('ekft',v('view'),description,v('point'))))
    p=v('point')
    text+=content('ekfv',both(k('uh',node,author,quote('ekfr'),scope,p),k('zdg',node,author,quote('ekfr'),scope,p),k('zc',node,author,quote('eke3'),quote('ekfr'),scope,p)))
    text+=content('ekfw',both(evaluate('ekfv'),evaluate('ekfu'),k('eisa5',aside,author,quote('ekfr'),quote('ekfu'),p)))
    text+='d ekfx[] f[j s[k ekfw[]]].\n'
    text+=define('ekfy',[],both(k('eir3',node,author,k('eirf'),quote('ekfx'),k('ri')),k('ue',k('eissr'),node,k('ri')),op('u',op('e',k('eissr'),node))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ekfy',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='printed_negative_infinity_claim_and_usual_view_contrast',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX]).document
    ann=json.loads(read('data/doppler-specialization-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
