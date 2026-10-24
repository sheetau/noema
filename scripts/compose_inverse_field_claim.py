"""Connect the two inverse constructions, required identity and product one."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_two_postulates import quote
from scripts.compose_limits import v,call as k,app,op,both

PARENT='examples/v014/einstein-field-comparison-claim.noema';PARENT_BASIS='data/field-comparison-claim-basis-v1.json'
FULL='examples/v014/einstein-inverse-field-claim.noema';CORE='examples/v014/inverse-field-claim-core.noema'
BASIS='data/inverse-field-claim-basis-v1.json';ANNOTATIONS='data/inverse-field-claim-identifiers-v1.json'
INDICES=[156,162];SOURCE_ORDER=[162,156]
PRIMITIVES={'eisp5':([], 'u0166のM0311にある係数積1の表示箇所。直前u0165の二つの逆変換の方法と、その一致からの帰結に接続する。')}
MEANINGS={
 'ejur':'現在の物理的な両場・同じ過程・同じ座標域の比較設定ejubに、逆数を使う第一係数の非零性と両係数の実数としての有効性を加える。正値や積1を候補選定へ加えない。',
 'ejus':'同じ比較設定で、直前の共通係数付き六式を解いて元のKの二場を復元する第一法sbp2の内容。逆速度の共通線形変換へψ(v)の逆数を掛ける。',
 'ejut':'同じ比較設定で、同じ変換の規則をkからKへ速度-vで適用して元の二場を復元する第二法sbq2の内容。ψ(-v)を使い、第一法の逆数へ予め同一化しない。',
 'ejuu':'直前の現在の六式ejuhの同じ記述から、第一法ejusと第二法ejutの別の記述へ至る、順序付けられた二つの非空手順。許容変形は同じ文脈に属する。引用内容の真理や手順の実行済みを要求しない。',
 'ejuv':'現在の逆変換設定で、二方法の共通の逆速度変換を除いた係数写像が全ての有効な実数入力で一致する内容sbr2。零の場の一致だけへ縮めない。',
 'ejuw':'非空の全ての現在の逆変換設定ejurで、二方法の同一性ejuvを要求する必要性。原文のidentisch sein müssenを数学的方法の必要性として読む。',
 'ejux':'二つの逆変換の手順の記述と、それらの式の同一性が必要だという内容。手順が実行済みだという報告ではない。',
 'ejuy':'二方法の記述・必要性ejux、直前の六式ejuh、および今の逆変換設定ejurを採用する、係数積1への著者の推論の前提。',
 'ejuz':'同じ現在の逆変換設定で、同じ第六節の係数関数のvと-vでの値の積が1になるsaq2を結論とする。正値・偶性・係数自体の値1は含めない。',
 'ejva':'二つの逆変換の方法と同一性の必要性ejuxを述べるメッセージ。',
 'ejvb':'u0165の二方法と必要性の記述を同じ著者・論説へ帰属させ、soebenの参照先である直前の六式表示eisp4の後へ結ぶ。旧文162を置き換える。',
 'ejvc':'同じ著者が二方法と同一性の要求を考慮して係数積1が従うと提示する。二方法の箇所zoeから帰結zn3、数式表示eisp5への順序と説明関係を保持する。',
 'ejvd':'係数積1への理由付き帰結とその表示ejvcを述べるメッセージ。',
 'ejve':'係数積1への推論の提示を同じ著者・論説へ帰属させる。旧文156を置き換え、本文上はejvbの後に読む。',
}
LIMITS=[
 'u0165–u0166を原刊909頁の一文として読み、直前の六式を解く第一法と同じ規則をkからKへ速度-vで用いる第二法、その式の同一性の必要性、考慮した条件から積1への帰結を保持する。',
 '二方法は同じ逆速度の線形場変換・逆座標写像と同じ旧新の場・領域を使う。第一法の係数1/ψ(v)と第二法のψ(-v)を別々に構成する。|v|<Vで共通線形変換が可逆なので、式としての一致を残る係数写像の任意入力での一致へ正規化するという読みを明示する。特定の零の場での一致ではない。',
 '逆変換を作る操作はψ(v)が非零である範囲で読む。正値は補わず負の係数も許す。積1の帰結から偶性や値1を先取りしない。',
 '原刊909頁のφは直前908頁のψと同じ第六節の係数znzを指す。第三節の座標係数への参照には戻さず、原刊の字形差と固定MathMLを保存する。',
 '手順列の接続・許容関係は記述された操作の構成であり、計算の実行ログではない。著者が同一性を必要として採用し、そこから積1を提示することを記述する。許容変形一般の健全性や著者の物理的論証の妥当性を処理系が証明したとはしない。',
 '全実数・全関数域を有限検査で代用しない。局所の有理数例・有限状況の対照、既存の記号的な係数消去、原文の通読判断は別の証拠である。',
 '旧文156と162を置き換え、残る356主張、旧版・原資料・既存証拠・既判断を保存する。文番号を動かさず原文順を162→156として明示する。u0167以降の対称性の段落は別途扱う。',
]

def definitions():
    text='r eisp5[] a.\n';p=v('point');speed=k('zb7');zero=k('bb','n p a b')
    a=app(k('znz'),speed);b=app(k('znz'),k('bf',zero,speed))
    text+=content('ejur',both(evaluate('ejub'),k('sbi2',a,b)))
    text+=content('ejus',both(evaluate('ejur'),evaluate('sbp2')))
    text+=content('ejut',both(evaluate('ejur'),evaluate('sbq2')))
    text+=content('ejuu',k('sbs2',k('zoc'),k('zod'),quote('ejuh'),quote('ejus'),quote('ejut'),'i[before i[e] after i[e]][k zla[v before v after v point]]'))
    text+=content('ejuv',both(evaluate('ejur'),evaluate('sbr2')))
    text+=content('ejuw',k('ejrj',k('ejur'),k('ejuv'),p))
    text+=content('ejux',both(evaluate('ejuu'),evaluate('ejuw')))
    text+=content('ejuy',both(evaluate('ejux'),evaluate('ejuh'),evaluate('ejur')))
    text+=content('ejuz',both(evaluate('ejur'),evaluate('saq2')))
    author=k('rd');scope=k('zno');ctx=k('ri')
    text+='d ejva[] f[j s[k ejux[]]].\n'
    text+=define('ejvb',[],both(k('eir3',k('zoe'),author,k('eirf'),quote('ejva'),ctx),k('ue',k('eisp4'),k('zoe'),ctx),op('u',op('e',k('eisp4'),k('zoe')))))
    nodes=('zoe','zn3','eisp5')
    text+=content('ejvc',both(k('zc',k('zn3'),author,quote('ejuy'),quote('ejuz'),scope,p),k('eisox',k('eisp5'),quote('ejuz'),p),k('uf',author,k('zn3'),k('eisp5'),p),*(k('ue',k(x),k(y),p) for x,y in zip(nodes,nodes[1:])),*(op('u',op('e',k(x),k(y))) for i,x in enumerate(nodes) for y in nodes[i+1:])))
    text+='d ejvd[] f[j s[k ejvc[]]].\n'
    text+=define('ejve',[],k('eir3',k('zn3'),author,k('eirf'),quote('ejvd'),ctx))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==358
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=deepcopy(old['statements'])
    for i,n in ((162,'ejvb'),(156,'ejve')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='two_inverse_methods_required_identity_and_product_one',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/field-comparison-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
