"""Connect the infinitesimal step to the same tau candidate and current trial."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_light_time_expansion import ROOT,read
from scripts.compose_comoving_labels import TAU
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both

PARENT='examples/v014/einstein-light-time-expansion.noema';PARENT_BASIS='data/light-time-expansion-basis-v1.json'
FULL='examples/v014/einstein-differential-step.noema';CORE='examples/v014/differential-step-core.noema'
BASIS='data/differential-step-basis-v1.json';ANNOTATIONS='data/differential-step-identifiers-v1.json';INDEX=280
MEANINGS={
 'ei2v':'同じ四引数関数、光速、速度、出発時刻について、ある指定された正の半径以内の全正変位での中点式skc、原点(0,0,0,t)での二変数全微分可能性sjvと同じ二偏微分sjwを合わせる。正速度と光速未満を保つ。単一の選択距離の式から近傍全体を推論せず、無限小を通常の実数の極限として読む前提を明示する。',
 'ei2w':'現在の同じ光往復・座標規約・局所時計・光速度原理・τ候補を結ぶei2pと、同じ候補zd4・V・v・出発時刻・近傍半径・二偏微分値によるei2vを合わせた微分への移行の前提。旧sjl依存を使わない。',
 'ei2x':'同じ中点式から正変位を零へ近づけるときの前提ei2wの内容。十分な局所正則性を明示した読みであり、原文がε–δ条件を逐語的に述べるという主張ではない。',
 'ei2y':'同じ第三節で、前の引数展開に続いて、同じ前提ei2xから逆数の和を含む偏微分式skfが従うと著者が提示する内容。Hieraus folgtの推論帰属を保持し、引用された前提・結論の真理を処理系で証明したとしない。',
 'ei2z':'正変位の極限による偏微分式の帰結ei2yを述べるメッセージ。',
 'ei22':'u0054の条件付き推論とu0055の表示式を同じ著者・論説へ帰属し、先行する引数展開からの本文順序を保持する。',
 'ei23':'同じ前提ei2xの下で、同じ二偏微分の最初の式skfを、v/(V²-v²)を含む整理後の式skgへ同値な形で書き換えるという著者の提示。u0056 oderとu0057を結ぶ。',
 'ei24':'二偏微分の式の整理ei23を述べるメッセージ。',
 'ei25':'u0056–u0057の書換えと表示式を同じ著者・論説へ帰属し、直前の微分による帰結からの本文順序を保持する。',
}
LIMITS=[
 'u0054全54文字・40本文文字、u0055 M0103、u0056 oderの4文字、u0057 M0104を一組として読む。原刊899頁の冒頭、x′の無限小への移行、二偏微分の関係、同じ式の整理を保持する。',
 '無限小は新たな非アルキメデス数ではなく、正の変位hを0へ近づける通常の実数の極限として読む。ある正の半径の内側の全ての0<h<radiusで同じ中点式を課す。固定された一回の反射距離だけや零変位の恒等式で済ませない。',
 '同じ候補τ、光速V、速度v、実際の出発K時刻tを先行ei2pへ接続する。微分点は(0,0,0,t)であり、tを零に固定せず、x′とt以外の二座標を固定する。原点以外への一般化はu0058で扱う。',
 '全微分可能性sjvのε–δ条件とsjwの二切片の差商極限を同じ係数に結ぶ。独立した偏微分の存在だけから全微分可能性を導かない。先行u0047の線形性の主張と整合する十分な正則性を明示した読みであり、同じ座標対応がアフィンであることから局所延長の性質を自動導出したとはしない。',
 'M0103は½(1/(V-v)+1/(V+v))*τt=τx′+τt/(V-v)、M0104はτx′+v/(V²-v²)*τt=0である。既存sjx/sjyとskf/skgを変更せず、両式で同じ候補偏微分zd6,zd7を使う。正速度とv<Vを保ち、分母を零にしない。',
 '原文のHieraus folgtは同じ中点式と極限の読みからの帰結の提示、oderはその式の同値な書換えとして記述する。著者・論説・第三節・順序を保持し、具体的なτ解の発見、無条件の物理事実、処理系の証明済み判断へ替えない。',
 '旧逆数・極限・有理代数の定義と証拠を保存する。有限の差分例は切片・引数・係数を区別する検査に限り、全実数の近傍、全微分可能性、連鎖律を有限標本で認定しない。新規原始語は追加しない。',
]


def definitions():
    zero=k('bb','n p a b');f=v('function');light=v('light');speed=v('speed');time=v('time')
    parameters=[('function',TAU)]+[(n,R) for n in ('light','speed','time','radius','spacepartial','timepartial')]
    point=(f,zero,zero,zero,time,v('spacepartial'),v('timepartial'))
    text=define('ei2v',parameters,both(k('sbg',speed),k('ba',light),k('bg',speed,light),k('skc',f,light,speed,time,v('radius')),k('sjv',*point),k('sjw',*point)))
    t=k('sjh',k('qe',k('zdq')),k('zb6'))
    text+=define('ei2w',[],both(k('ei2p'),k('ei2v',k('zd4'),k('tc'),k('zb7'),t,k('zd5'),k('zd6'),k('zd7'))))
    text+=content('ei2x',k('ei2w'))
    text+=content('ei2y',k('zc',k('zea'),k('rd'),quote('ei2x'),quote('skf'),k('eisms'),v('point')))
    text+='d ei2z[] f[j s[k ei2y[]]].\n'
    def author(name,node,message,prior):return define(name,[],both(k('eir3',k(node),k('rd'),k('eirf'),quote(message),k('ri')),k('ue',k(prior),k(node),k('ri')),op('u',op('e',k(prior),k(node)))))
    text+=author('ei22','zea','ei2z','zd2')
    text+=content('ei23',k('zd3',k('zeb'),k('rd'),quote('ei2x'),quote('skf'),quote('skg'),k('eisms'),v('point')))
    text+='d ei24[] f[j s[k ei23[]]].\n';text+=author('ei25','zeb','ei24','zea')
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not set(MEANINGS)&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ei22','ei25')]
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='same_tau_local_limit_and_differential_equations',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[INDEX,INDEX+1]).document
    ann=json.loads(read('data/light-time-expansion-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
