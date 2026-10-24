"""Connect the named general aberration law and its right-angle display."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_aberration_presentation import ROOT,read,SETTING,VARIABLES,allq
from scripts.compose_material_relative_frame import define,args
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-aberration-presentation.noema';PARENT_BASIS='data/aberration-presentation-basis-v1.json'
FULL='examples/v014/einstein-aberration-specialization.noema';CORE='examples/v014/aberration-specialization-core.noema'
BASIS='data/aberration-specialization-basis-v1.json';ANNOTATIONS='data/aberration-specialization-identifiers-v1.json';INDICES=[377,378]
PRIMITIVES={
 'eissz':([], 'u0195の光行差則の一般形としての同定とφ=π/2での簡明な表示を述べる箇所。'),
 'eiss2':([], 'u0196=M0342のcosφ′=−v/Vを表示する箇所。'),
 'eiss3':([], 'u0195のAberrationsgesetzという法則名の呼称個体。内容はeischで同じ全許容設定の角の関係へ結ぶ。原語だけで意味を定義しない。'),
}
MEANINGS={
 'ekhm':'同じVとspeedから負の速度比−speed/Vを構成する。V又はspeedへ別の値を代入せず、先頭の負号を保つ。利用域は呼出し側の設定に従う。',
 'ekhn':'同じ65役割の物理的・光学的設定ekgyと、同じ旧実数角angleが同じpiの半分である条件を連言する。新角、余弦値、又は別の設定の角に置き換えない。',
 'ekho':'同じ設定のnewanglecosが同じVとspeedの負比ekhmに等しいという特殊印刷形。前件へこの等式を混ぜず、結線との実際の角が印刷式を満たすとは定義しない。',
 'ekhp':'同じ61役割の全称条件で、直角を加えた同じekhnの下に一般印刷形ekgoを述べる。特殊形と比較する際の条件を一致させる。',
 'ekhq':'同じ61役割の全称条件で、同じ直角設定ekhnの下に負の速度比ekhoを述べる特殊形。全称変数・対象・値をekhpと共有する。',
 'ekhr':'直前の表示eisswをekhcの内容へ結び、その全許容速度・方向の同じ内容を光行差則という呼称eiss3へ対応させ、著者の主張として帰属する。一般性はekgyに特定角や小速度条件を加えない61全称の域として表す。物理的真理やこの配置を越える理論の万能性を含意しない。',
 'ekhs':'同じ直角条件下の一般形ekhpを同じ特殊形ekhqとして明示するという提示、既出記号での簡明さeissp、コロンから同じ表示への説明ufと順序ueを保持する。',
 'ekht':'u0195の第一文の法則同定・全域の内容ekhrと第二文の直角条件下の提示ekhsを同じ点で連言する。',
 'ekhu':'u0195全文ekhtを述べるメッセージ。',
 'ekhv':'u0195全文を同じ著者・論説へ帰属し、直前の光行差表示に続ける。',
 'ekhw':'u0196の表示項目を同じ直角設定の条件内容ekhqへ結ぶ。負号、旧角条件、新角の余弦、同じV・speedを保持する。',
 'ekhx':'u0196の表示対応ekhwを述べるメッセージ。',
 'ekhy':'u0196の表示を同じ著者・論説へ帰属し、u0195のコロンに続ける。',
}
LIMITS=[
 'u0195–u0196を原刊912頁と固定在庫で照合し、Aberrationsgesetz、in seiner allgemeinsten Form、φ=π/2、einfache Gestaltとコロン、cosφ′=−v/Vを保持する。',
 '最も一般的な形は、先行の標準配置・近似・正速度0<v<Vと同じ光学的設定の許容する全速度・方向を扱うという適用域上の読みとする。ekhcの61全称とekgyの全条件をそのまま名前と著者帰属の対象へ結ぶ。方向を特定した特殊場合、小速度の一次近似、選んだ標本へ縮めず、全理論や全座標表示の中で唯一最大という外部比較は補わない。',
 'φは旧波面法線と正速度方向の0からpiの実数角であり、φ′は先行の同時刻の源→観測者結線と新法線の角である。特殊条件は同じangle=pi/2で、cosφ=0だけの独立した値の指定にしない。正のpiと角の測度は先行の積分規約を継承する。',
 'φ=π/2からcosφ=0となり、一般表示の右辺(0−v/V)/(1−0)は−v/Vに整理できる。この代数的な整理を、実際の結線との角の余弦がその値であるという物理的真理へ替えない。V5,v3,n=(0,1,0)では実際の余弦4/5と印刷式−3/5の不整合が残る。基準線や負号を都合よく変更しない。',
 'einfache Gestaltは同じ記号・演算規約で依存量と式構成を見渡しやすい形という提示上の評価と読む。既存eisspを再使用し、文字数・演算数の絶対的最小、導出の容易さ、全読者の心理、内容の真理は追加しない。',
 '全称の許容域を有限標本で置き換えない。局所検査は負比の代数、角の境界、65役割の接続、各61全称位置と帰属・表示を確かめる。意味同義性の自動証明や法則の実験的証明ではない。一般基本関係は追加しない。',
]

def definitions():
    text=''.join('r '+n+'[] a.\n' for n in PRIMITIVES)
    V=v('light');speed=v('speed');zero=k('bb','n p a b');half=k('bb','n p b c')
    text+=define('ekhm',[('light',R),('speed',R)],k('bf',zero,k('shv',speed,k('sjd',V))),R)
    text+=define('ekhn',SETTING,both(k('ekgy',*args(SETTING)),k('sca',v('angle'),k('shv',v('pi'),half))))
    text+=define('ekho',SETTING,k('sca',v('newanglecos'),k('ekhm',V,speed)))
    fixed={'frame':k('ra'),'light':k('tc'),'scope':k('eisrx'),'context':v('point')};actual=[fixed.get(n,v(n)) for n,t in SETTING]
    for name,conclusion in [('ekhp','ekgo'),('ekhq','ekho')]:
        text+=content(name,allq(VARIABLES,op('y',k('ekhn',*actual),k(conclusion,*actual))))
    node=k('eissz');display=k('eiss2');prior=k('eissw');author=k('rd');scope=k('eisrx');p=v('point')
    text+=content('ekhr',both(k('eisox',prior,quote('ekhc'),p),k('eisch',k('eiss3'),quote('ekhc'),scope,p),k('uh',node,author,quote('ekhc'),scope,p)))
    text+=content('ekhs',both(k('eissb',node,prior,author,quote('ekhp'),quote('ekhq'),scope,p),k('eissp',quote('ekhq'),scope,p),k('uf',author,node,display,p),k('ue',node,display,p)))
    text+=content('ekht',both(evaluate('ekhr'),evaluate('ekhs')))
    text+=content('ekhw',k('eisox',display,quote('ekhq'),p))
    for shown,msg,stmt,item,previous in [('ekht','ekhu','ekhv','eissz','eissw'),('ekhw','ekhx','ekhy','eiss2','eissz')]:
        text+='d '+msg+'[] f[j s[k '+shown+'[]]].\n'
        text+=define(stmt,[],both(k('eir3',k(item),author,k('eirf'),quote(msg),k('ri')),k('ue',k(previous),k(item),k('ri')),op('u',op('e',k(previous),k(item)))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==377
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ekhv','ekhy')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='named_general_aberration_law_and_right_angle_form',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/aberration-presentation-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eiss3',role='designation',forms=[dict(text='Aberrationsgesetz',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
