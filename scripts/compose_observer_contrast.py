"""Connect the measured length gloss and hypothetical observer judgments."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_moving_trip_geometry import ROOT,read,zero
from scripts.compose_rod_methods import interval
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,F,v,call as k,app,op,both,quant as q

PARENT='examples/v014/einstein-moving-trip-reading.noema';PARENT_BASIS='data/moving-trip-reading-basis-v1.json'
FULL='examples/v014/einstein-observer-contrast.noema';CORE='examples/v014/observer-contrast-core.noema'
BASIS='data/observer-contrast-basis-v1.json';ANNOTATIONS='data/observer-contrast-identifiers-v1.json';INDEX=264
FIELDS=[('object','a'),('frame','a'),('context','d'),('lengthunit','a'),('timeunit','a'),('lower',R),('upper',R)]+[(a,F) for a in ('x','y','z')]
TRUE=op('e','n p a b','n p a b');FALSE=op('u',TRUE)
PRIMITIVES={'eismn':([], 'u0040冒頭で説明するr_ABという量の識別表記。対象は同じ運動棒の静止系で測る長さであり、量の条件と値はeit4で別に結ぶ。')}
MEANINGS={
 'eit2':'同じ対象・基準系・単位・正の区間について、三つの代表位置関数の完全なseと、下端時刻の同じ位置から零速度で続くeitfの完全なseを要求する。同じ出来事への帰属・座標の一意な対応によって全区間の代表位置が一定となる。端点時刻の一致だけや内部の全物質点の停止ではない。',
 'eit3':'この設定の観測者xbが静止系raで静止するx4という役割を、eismhの代表位置と全区間のeit2へ結ぶ。静止系の座標で記述できるというだけでは静止としない。',
 'eit4':'rodが同じ棒xiであり、その静止系での数量条件eiqgと測定方法eip6を同じcontextで満たすvalueが、同じ運動状態ydから引き継いだr_ABの値zavに等しいことを要求する。',
 'eit5':'当該論説でr_ABの呼称を、同じ棒と静止系測定の値を結ぶeit4の規則に従って解釈するという説明。語の説明自体は測定を実行しない。',
 'eit6':'同じ二時計がそれぞれ自分の端点に付随し、各現在位置の静止系時刻を全区間で表示するeiq4の内容。静止系における同期という先行呼称の資格を保持する。',
 'eit7':'同じ静止系の観測者がeit6の内容を肯定と判断し、その内容を発言する。単なる判断の内面帰属と内容の発言を分け、どちらからも引用内容の真理を直接導かない。',
 'eiua':'同じ想定文脈の静止観測者eit3の範囲が非空で、その範囲の各観測者がeit7の肯定判断と宣言をする。現実の全人類へ範囲を広げない。',
 'eiub':'現行eitmの同じ共動観測者二人が、同じ三記録の中点条件sdoをともに否定と判断する。判定の適用、否定判断、実際の数値的不成立を区別する。',
 'eiuc':'同じ運動想定ydにおける共動観測者の否定判断eiubを対照の第一項とする内容。',
 'eiud':'同じ運動想定ydにおける静止系観測者の肯定判断と宣言eiuaを対照の第二項とする内容。',
 'eiue':'同じ想定内でeiucとeiudがともに成り立つという判断・宣言の結果内容。異なる基準に関する内容の対照であり、一つの無限定な命題とその否定を同時に真とする式ではない。',
 'eiuf':'r_ABの説明と二式への補足、想定範囲内の結果eiueの提示uh、先行の往復結果eitpを理由とするalso、eiuc/eiudを順序を保って対照するwährendを結ぶ。',
 'eiug':'長さの説明と、想定下の二群の判断・宣言の対照eiufを述べるメッセージ。実際の観測実験や全観測者の全知を報告しない。',
 'eiuh':'u0040全体を同じ著者・論説の箇所zbbへ帰属し、二式の提示za3からの本文順序を保持する。',
}
LIMITS=[
 '原刊897頁のu0040全284文字・236本文文字とM0062のr_ABを対象とする。wobeiの量の説明と、それに続く二群の観測者についての一文を共有された光往復設定の中で読む。',
 'r_ABは同じ動く棒を静止系で同時刻に測った長さ。現行eip6/eiqg、設定継承yxとzavの数値同一性を保つ。初期静止長・移動側の長さ・光路全長を代入しない。',
 '共動する観測者は直前の各時計のそばの二人を引き継ぐ。両者の否定判断は、同じ試行の三表示に第一節の中点条件biを適用する基準についての判断とする。無条件の非同期という別の命題へ替えない。',
 '静止系の観測者の肯定は、先行のsynchron im ruhenden Systemという限定付きの呼称、すなわち両時計が各場所の静止系時刻に追従するeiq4を基準とする。移動側の中点判定の肯定へ取り違えない。',
 'im ruhenden System befindliche Beobachterはこの思考設定の静止側観測者と読む。その巨視的代表位置の全区間の静止を構成する。身体内部や時計の機構の全運動を禁止せず、単に当該座標で記述できる任意の運動者を含めない。',
 '複数の観測者という表現は同じ想定に属する非空の静止観測者範囲として読む。量化はこの議論で条件に従って観測・判定をする理想化された対象範囲であり、任意の現実の人の知識・注意・能力の普遍性は追加しない。',
 'würden ... finden / erklären würdenは現在の思考設定の下での帰結の叙述とし、既存uhの仮定範囲内の主張として表す。数値関係から判断・発言するという心理法則を証明せず、現実に発言済み又は未来の予定とはしない。',
 'findenをzbaの否定判断、erklärenを肯定判断に加えた内容の発言eisfdとして区別する。発言には公的な聴衆・音声・文書媒体の指定を補わず、判断の真理や正当化をこの帰属から導かない。',
 'alsoは先行する光往復の結果eitpを理由とする説明eisdk、währendは否定判断と肯定宣言の対照zbcである。二つの異なる基準を、一つの命題の論理的矛盾や同じ時刻の発話順序へ替えない。',
 '有限検査は代表位置、全履歴への引数、判断の肯否と内容、観測者の範囲、引用の非実行を調べる。全実数時刻の列挙、観測者の認知一般の理論、物理法則や意味同値の自動証明ではない。u0041の同時性への結論は残る。',
]

def definitions():
    text='r eismn[] a.\n';args=[v(n) for n,_ in FIELDS]
    raw=k('se',*args);static=k('eitf',*args[:7],*(app(v(a),v('lower')) for a in ('x','y','z')),zero(),zero(),zero())
    text+=define('eit2',FIELDS,both(k('bg',v('lower'),v('upper')),k('eisdd',v('frame'),v('lengthunit'),v('timeunit'),v('context')),raw,static))
    who=v('who');c=v('context');frame=k('ra');ofns=[k('eismh',who,frame,k('ta'),k('rb'),k(axis),c) for axis in ('yn','yo','yp')]
    text+=define('eit3',[('who','a'),('context','d')],both(k('xb',who),k('x4',who,frame,c),k('eit2',who,frame,c,k('ta'),k('rb'),*interval(frame,c),*ofns)))
    text+=define('eit4',[('rod','a'),('value',R),('context','d')],both(op('e',v('rod'),k('xi')),k('yx',k('yd'),c),k('eiqg',v('value'),c),k('eip6',v('value'),c),k('sca',v('value'),k('zav'))))
    text+=content('eit5',k('eislo',k('eismn'),'r[p eit4]',k('eirf'),v('point')))
    text+=content('eit6',both(k('eiq4',k('zaj'),k('xn'),v('point')),k('eiq4',k('zak'),k('xo'),v('point'))))
    text+=define('eit7',[('who','a'),('context','d')],both(k('sdk',who,quote('eit6'),TRUE,c,'p zba'),k('eisfd',who,quote('eit6'),k('eirf'),c)))
    selected=k('eit3',who,c)
    text+=define('eiua',[('context','d')],both(q('g','who','a',selected),q('f','who','a',op('y',selected,k('eit7',who,c)))))
    text+=define('eiub',[('context','d')],both(k('eitm',c),*(k('sdk',k(observer),quote('sdo'),FALSE,c,'p zba') for observer in ('zay','zaz'))))
    for name,body in (('eiuc',k('eiub',k('yd'))),('eiud',k('eiua',k('yd'))),('eiue',both('t[k eiuc[]][v point]','t[k eiud[]][v point]'))):text+=content(name,body)
    text+=content('eiuf',both('t[k eit5[]][v point]',k('eisa5',k('zbb'),k('rd'),quote('eitp'),quote('eit5'),v('point')),k('uh',k('zbb'),k('rd'),quote('eiue'),k('xy'),v('point')),k('eisdk',k('eirf'),quote('eitp'),quote('eiue'),v('point')),k('zbc',k('zbb'),k('rd'),quote('eiuc'),quote('eiud'),k('xy'),v('point'))))
    text+='d eiug[] f[j s[k eiuf[]]].\n'
    text+=define('eiuh',[],both(k('eir3',k('zbb'),k('rd'),k('eirf'),quote('eiug'),k('ri')),k('ue',k('za3'),k('zbb'),k('ri')),op('u',op('e',k('za3'),k('zbb')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eiuh',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitive=next(d for d in added if d['kind']=='primitive')
    basis=dict(status='rest_frame_length_and_hypothetical_observer_contrast',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives={'eismn':dict(parameters=primitive['parameters'],result=primitive['result'],arguments=[],meaning_ja=PRIMITIVES['eismn'][1])},definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/moving-trip-reading-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eismn',role='designation',forms=[dict(text='r_AB',language='und',role='linearized_subscript_notation')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
