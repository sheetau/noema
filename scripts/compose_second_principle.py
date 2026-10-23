"""Connect the second principle, path/time speed and section-one time reference."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_first_principle import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-first-principle.noema';PARENT_BASIS='data/first-principle-basis-v1.json'
FULL='examples/v014/einstein-second-principle.noema';CORE='examples/v014/second-principle-core.noema'
BASIS='data/second-principle-basis-v1.json';ANNOTATIONS='data/second-principle-identifiers-v1.json';INDICES=(250,251)
PRIMITIVES={
 'eisll':([], 'u0026末尾のHierbei istから表示式u0027と第一節への参照u0028まで続く、第二原理で用いる速度と時間の規定を述べる箇所。第二原理の法則提示wtとは区別する。'),
 'eislm':([('node','a'),('author','a'),('numerical','i[h['+R+' '+R+' '+R+'] c]'),('applied','i[h[a '+R+' '+R+' d] c]'),('document','a'),('context','d')], 'authorがnodeで、documentの当該議論に用いる速度を、numericalの経路長・経過時間・速度値の関係で規定し、appliedの同じ区間・経過時間・速度値・状況への対応で物理量へ結ぶ。量の役割と順序はこの二つの閉じた型に固定する。等式の規定であり、ある実測値の報告、法則の実証、無関係な三数の式ではない。引用した規則をその場で実行することは要求しない。'),
 'eisln':([], 'u0028で引用符付きのZeitdauerとして参照する量の呼称。印字形は識別表記へ、当該量の適用規則は別の関係へ保持する。'),
 'eislo':([('designation','a'),('rule','i[h[a '+R+' d] c]'),('document','a'),('context','d')], '同じdocumentの当該議論でdesignationが指す量を、同じ対象・値・状況に対する閉じたruleの規約に従って解釈する。語形の類似だけで意味を決めず、別の時計・原点・基準系の量を代入しない。規則の引用から実際の測定や全対象への値の存在を導かない。'),
 'eislp':([('node','a'),('author','a'),('division','a'),('rule','i[h[a a a '+R+' d] c]'),('document','a'),('context','d')], 'authorがnodeで、同じdocumentの先行区分divisionにある、出来事・時計・場所・時刻値・状況を結ぶruleの定義を、現在用いる時間量の解釈基準として参照する。節番号だけの連想や新しい時間の定義ではなく、同じ既定の時計・同期・共通参照の規約を引き継ぐ。参照先の定義の実証や実際の読取りの完了は意味しない。'),
}
MEANINGS={
 'eior':'同じ区間の光・放出元・放出出来事をsazで結び、静止又は運動の排他的分類を保持する。両端出来事の時刻は第一節のeingで同じ系ra・単位rb・参照時計rcへ結ぶ。光源の運動を局所時計の運動へ替えない。',
 'eios':'同じ静止系raで、既存eifxの全真空光伝播区間が同じ速度値を持ち、参照時計zbhが同じrcであり、全適用区間でeiorの放出元分類と第一節の時刻付与が成立する。範囲を静止光源又は成功例だけへ縮めない。',
 'eiot':'第二原理を、同じ静止系の全区間に一つの既出V=tcを固定するeiosとして述べる内容。非慣性系まで同じ座標速度を要求せず、現代の速度値は補わない。',
 'eiou':'同じ区間の両端をeingで時刻付与し、その終時刻から始時刻を引いた正の差がdurationに等しいという時間間隔。遠隔光の受信時刻、光源固有時、別時計規約への交換を認めない。',
 'eiov':'正の経路長・時間間隔・速度について、既存saxの始時刻を零、終時刻をdurationとして、path=speed×durationを構成する。正の分母の下で速度＝光路／時間と同じ条件であり、往復係数2を加えない。',
 'eiow':'同じ真空光区間の経路長、同期した両端の局所読み、第一節の時刻表示、単位校正を結び、durationと速度値をeiovの数式に渡す。固定速度tcへの一致はこの一般的な速度の規定には追加しない。',
 'eiox':'速度の数式eiovと物理的対応eiowを著者が説明箇所で規定する内容。全光線で同じVとなる法則の実証と、速度をどう定義するかを分ける。',
 'eioy':'同じZeitdauerの呼称をeiouの両端時刻差として解釈し、その時刻付与の定義eingを第一節eisdyから引き継ぐという参照内容。',
 'eioz':'表示された速度式の規定eioxと、その時間量を第一節の定義によって読むeioyを結ぶ、Hierbeiからwobeiまでの説明。',
 'eio2':'著者がwtでeiotを後続範囲wvの第二原理として定義提示し、先に呼称で指した真空光速度の原理eifyの定式化へ結ぶ。全適格系への先行表現とこの系での定式化の論理同値を認定しない。',
 'eio3':'第二原理の定義提示eio2を述べるメッセージ。処理系が光速度の普遍性を実証したという発話へ替えない。',
 'eio4':'第二原理を同じ著者・論説へ帰属し、導入wuの第二項と第一原理vkからの順序を保持する。',
 'eio5':'速度式と時間量の規定eiozを述べるメッセージ。実際の測定結果や別の独立原理とはしない。',
 'eio6':'説明の著者帰属と第二原理への補足関係、法則提示wtからの順序を結ぶ。u0026末尾・u0027・u0028を一続きの説明として扱う。',
}
LIMITS=[
 'u0026〜u0028の305転記文字・253本文文字とM0041/M0042を対象とする。u0026の法則文と、Hierbei istからwobeiまで続く速度・時間の説明を区別して保持する。',
 '第二原理は導入した同じ静止系raに関して読む。引用符付きruhendenは既存呼称eisebの同じ対象であり、絶対静止ではない。Vは前節のtcに固定し、現代の数値を補わない。真空の適用範囲は前節と先行の光速度原理から引き継ぐ。',
 '全光線・全方向・全時刻・非零の全部分区間と全放出元状態を含む既存eiscd/eisceの範囲を用いる。各放出について静止又は運動の明示的な排他的分類をsazで保持し、情報不足を静止と補わない。静止・運動それぞれの実例の実在を別途要求するわけではない。',
 '速度＝光路／時間を、正の経路長・時間間隔の下でpath=speed×durationという既存saxへ接続する。光路は同じ系での幾何学的な弧長であり、端点間の直線距離・媒質の光学長・2ABへ代用しない。原文の語句から追加の往復係数を作らない。',
 '時間間隔は同じra・rb・共通参照rcのeingで与えた終時刻から始時刻を引いた値である。局所時計はこの系で静止し、対象と同時の表示を与える。光源の時計や移動側の時計の固有時、信号の受信に要した別の時間へ取り替えない。',
 '速度の定義は任意の正の値候補を扱い、全区間のVへの一致は第二原理の別条件である。原理の定義、数式による速度の規定、第一節への参照、著者への帰属を分ける。引用した一般規則を有限標本で実行したことにしない。',
 '全物理範囲の完全性・真空・放出と運動状態・幾何学的弧長は明示した物理入力である。有限検査は数量と参照・局所時刻・論述役割を調べ、全実数や全物理法則の真理、原文との意味同値を自動証明しない。u0029以降は残る。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    at=lambda name:k(name,v('segment'))
    times=[k('eing',*[at(n) for n in fields],v('context')) for fields in (('wi','wk','wm','wo'),('wj','wl','wn','wp'))]
    text+=define('eior',[('segment','a'),('context','d')],both(k('saz',at('wf'),at('wg'),at('wh'),k('ra'),v('context'),'p wb','p wc','p wd','p we'),*times))
    selected=lambda s,c:k('eiscd',s,k('ra'),k('ta'),k('rb'),c)
    text+=define('eios',[('speed',R),('context','d')],both(k('eifx',k('ra'),v('speed'),v('context')),op('e',k('zbh',k('ra'),v('context')),k('rc')),q('f','segment','a',op('y',selected(v('segment'),v('context')),k('eior',v('segment'),v('context'))))))
    text+=content('eiot',k('eios',k('tc'),v('point')))
    text+=define('eiou',[('segment','a'),('duration',R),('context','d')],both(*times,k('ba',v('duration')),k('bg',k('bb','n p a b'),v('duration')),k('sca',v('duration'),k('bf',at('wp'),at('wo')))))
    text+=define('eiov',[(n,R) for n in ('path','duration','speed')],k('sax',v('path'),k('bb','n p a b'),v('duration'),v('speed')))
    text+=define('eiow',[('segment','a'),('duration',R),('speed',R),('context','d')],both(k('eifw',v('segment'),k('ra'),k('rc'),v('speed'),v('context')),k('eiou',v('segment'),v('duration'),v('context')),k('eisb7',k('ra'),k('rc'),k('rb'),v('context')),k('eiscc',k('ra'),k('ta'),k('rb'),k('tb'),v('context')),k('eiov',at('wq'),v('duration'),v('speed'))))
    text+=content('eiox',k('eislm',k('eisll'),k('rd'),'r[p eiov]','r[p eiow]',k('eirf'),v('point')))
    text+=content('eioy',both(k('eislo',k('eisln'),'r[p eiou]',k('eirf'),v('point')),k('eislp',k('eisll'),k('rd'),k('eisdy'),'r[p eing]',k('eirf'),v('point'))))
    text+=content('eioz',both('t[k eiox[]][v point]','t[k eioy[]][v point]'))
    text+=content('eio2',both(k('vl',k('wt'),k('rd'),quote('eiot'),k('wv'),v('point')),k('eislh',k('wt'),k('rd'),k('eisk4'),quote('eify'),quote('eiot'),k('eirf'),v('point'))))
    text+='d eio3[] f[j s[k eio2[]]].\n'
    text+=define('eio4',[],both(k('eir3',k('wt'),k('rd'),k('eirf'),quote('eio3'),k('ri')),k('eislk',k('wt'),k('wu'),'n p c b',k('eirf'),k('ri')),k('ue',k('vk'),k('wt'),k('ri')),op('u',op('e',k('vk'),k('wt')))))
    text+='d eio5[] f[j s[k eioz[]]].\n'
    text+=define('eio6',[],both(k('eir3',k('eisll'),k('rd'),k('eirf'),quote('eio5'),k('ri')),k('eisa5',k('eisll'),k('rd'),quote('eiot'),quote('eioz'),k('ri')),k('ue',k('wt'),k('eisll'),k('ri')),op('u',op('e',k('wt'),k('eisll')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eio4','eio6')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='second_principle_with_one_way_rate_and_section_one_duration',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=list(INDICES)).document
    ann=json.loads(read('data/first-principle-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eisln',role='designation',forms=[dict(text='Zeitdauer',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
