"""Compose hypothetical frame introduction and purposive naming of the same referent."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_kinematics_headings import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_limits import v,call as k,op,both

PARENT='examples/v014/einstein-kinematics-headings.noema';PARENT_BASIS='data/kinematics-headings-basis-v1.json'
FULL='examples/v014/einstein-rest-frame-introduction.noema';CORE='examples/v014/rest-frame-introduction-core.noema'
BASIS='data/rest-frame-introduction-basis-v1.json';ANNOTATIONS='data/rest-frame-introduction-identifiers-v1.json';INDICES=(221,222)
PRIMITIVES={
 'eisd3':([('node','a'),('referent','a'),('document','a'),('reference','d')],'nodeで、documentの以後の議論に使う一つの対象をreferentとして設定し、後続の指示が同じ対象を保てるよう導入する操作。対象は仮定的な設定の中で選べ、物理的な実在や測定での同定の証明とは区別する。与える条件は別の仮定内容へ保持し、条件を満たす世界唯一の対象だとはしない。名称を付ける操作とも区別する。'),
 'eisd4':([('node','a'),('author','a'),('designation','a'),('target','a'),('document','a'),('reference','d')],'authorがnodeでdesignationを、同じdocumentの議論における同じtargetの呼称として採用する命名行為。対象個体を指す名前の規約であり、閉じた命題内容の略称とは区別する。現在の命名の宣言として行われ、対象の新たな物理的性質や名称の字面の性質を付与しない。文中の引用された呼称の同一性を保持し、以後同じ対象を言い分けるために使える。原文にない改名歴、社会全体の承認や他者による実際の使用は要求しない。'),
 'eisd5':([('agent','a'),('action','i[e]'),('goal','i[e]'),('scope','a'),('reference','d')],'agentがscopeの活動で同じactionを行う目的として、goalに記述される事柄を目指すという目的関係。行為と目標の対象・向きを保ち、結果が先に生じたという時間順序や、目的が既に達成された事実とは区別する。同じ行為が複数の目的を持つことを許し、目標だけから行為の成功や正当性を推論しない。'),
 'eisd6':([('designation','a'),('target','a'),('alternatives','i[h[a d] c]'),('document','a'),('reference','d')],'同じdocumentの言語上の指示において、designationを用いることでtargetをalternativesの型が指定する別の対象群と取り違えずに言い分けられるという状態。共通の対象分類と本文上の参照を保つ。物理的な相違を新たに作ることや、違う名前を与えれば絶対運動を検出できることとは異なる。alternativesが今後導入予定の対象群の場合も、区別の目標を記述でき、現在それらが導入済み又は現実に存在することは要求しない。'),
 'eisd7':([('referent','a'),('document','a'),('after','a'),('reference','d')],'referentが同じdocumentでafterより後に導入されるものとして見越された対象群に属する。これは本文の展開における将来の指示範囲であり、物理的な未来時刻での生成や、現在導入済みの対象の一覧ではない。該当する全予定範囲を扱い、都合のよい比較相手だけを後から選ばない。予定された仮定的対象も含み、現実での存在を断言しない。'),
 'eisea':([('designation','a'),('target','a'),('document','a'),('reference','d')],'designationをtargetに固定して用いることで、同じdocumentでどの対象を考え、その関係や規約をどう捉えるかという観念が明確に定まるという状態。指示の曖昧さや対象の混同を減らし、後の記述を一つの同じ対象の下で把握するという意味の明確化である。座標値の測定精度、実験の実施、全読者の心理状態や完全理解を要求しない。'),
 'eiseb':([], 'この論説で同じ導入した基準系raを呼ぶために採用する呼称個体。原文の印字形ruhende Systemは識別表記へ記録する。名称だけから絶対静止、全物体の停止、系の唯一性を意味させない。'),
 'eisec':([], '固定原文einstein-1905:u0008[0,95)の第一文。Newtonの力学方程式が成立する座標系を議論の設定として置く箇所。'),
 'eised':([], '固定原文einstein-1905:u0008[96,266)の第二文。同じ座標系を静止系と呼び、言語的区別と観念の明確化の二目的を示す箇所。'),
}
MEANINGS={
 'eiht':'同じ後続参照raが物理的な座標系であり、Newtonの力学方程式が成り立つという既存eifbの条件内容。現実での成立をここで断言せず、設定として引用する。',
 'eihu':'同じ論説でraという対象参照を導入し、その同じraについてeihtを著者の議論の仮定として採用する設定操作。内容の真理や観測を要求しない。',
 'eihv':'eihuの設定操作を行うものとして議論を進める指示のメッセージ。物理法則を現実に成立させよという命令ではない。',
 'eihw':'第一文の設定指示eihvを同じ著者・論説へ帰属し、第一節見出しの後の別箇所として順序を保持する。',
 'eihx':'同じ論説の命名箇所より後に導入されるものとして見越された、raとは異なる座標系の全範囲。型として目的の内部で参照し、今ここで別系が実在するという存在主張を追加しない。',
 'eihy':'同じ呼称eisebによってraを、後で導入する座標系eihxから言語上言い分けられるという、第一の目的内容。',
 'eihz':'同じ呼称をraに固定して考えることで、対象の観念・把握を明確に定めるという第二の目的内容。',
 'eih2':'同じ著者が第二文でeisebを同じraの呼称として採用する行為内容。命題内容の略称や物理的な静止の主張へ替えない。',
 'eih3':'同じ命名行為eih2を行い、その同じ行為に対して言語上の区別eihyと観念の明確化eihzの二目的を結ぶ。目的の達成を現在の事実として実行しない。',
 'eih4':'第二文の命名と二目的eih3を主張として提示するメッセージ。第一文の設定指示と発話の力を区別する。',
 'eih5':'第二文を同じ著者・論説へ帰属し、第一文の後の別箇所として順序を保持する。導入と命名と後続参照が同じraを使う。',
}
LIMITS=[
 'Es liege ... vorは、Newton適格系を議論の設定として置く指示と読む。系の物理的実在・法則の実証を断言せず、法則を実現させる物理的な命令へ替えない。',
 '系の参照は既存のraに統一し、Newton適格性は既存eifb=vaとeisbdを再利用する。特定の相対速度、電磁法則、絶対静止、世界唯一の系を補わない。',
 'Wir nennenは著者が論述を進める声による現在の命名宣言と読む。著者以外の人数や読者全員の同意を補わず、仮定的な対象への呼称を採用できる。',
 'ruhende Systemの字面は対象を指す呼称として保持する。後続本文がこの系に対する静止を定義・述べることと、この名称そのものから静止の事実を導くことを区別する。',
 '後で導入する系は同じ論説の将来の対象群として読む。言語上の区別の目標へその全範囲を渡し、現在導入済みの別系の実在や特定の名称を原文へ補わない。',
 '二つのzurは同じ命名行為の二目的と読む。目的の達成、測定精度の向上、全読者の理解完了を現在の事実に替えない。',
 'この二文全体を記述する。次の物質点の位置指定及び第一節全体の定義・論証は別に進める。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=content('eiht',k('eifb',k('ra'),v('point')))
    text+=content('eihu',both(k('eisd3',k('eisec'),k('ra'),k('eirf'),v('point')),k('ug',k('eisec'),k('rd'),quote('eiht'),k('eirf'),v('point'))))
    text+='d eihv[] f[j m[k eihu[]]].\n'
    text+=define('eihw',[],both(k('eir3',k('eisec'),k('rd'),k('eirf'),quote('eihv'),k('ri')),k('ue',k('eisd2'),k('eisec'),k('ri')),op('u',op('e',k('eisd2'),k('eisec')))))
    text+=define('eihx',[('other','a'),('reference','d')],both(k('va',v('other')),k('eisd7',v('other'),k('eirf'),k('eised'),v('reference')),op('u',op('e',v('other'),k('ra')))))
    text+=content('eihy',k('eisd6',k('eiseb'),k('ra'),'r[p eihx]',k('eirf'),v('point')))
    text+=content('eihz',k('eisea',k('eiseb'),k('ra'),k('eirf'),v('point')))
    text+=content('eih2',k('eisd4',k('eised'),k('rd'),k('eiseb'),k('ra'),k('eirf'),v('point')))
    purposes=[k('eisd5',k('rd'),quote('eih2'),quote(goal),k('eirf'),v('point')) for goal in ('eihy','eihz')]
    text+=content('eih3',both(evaluate('eih2'),*purposes))
    text+='d eih4[] f[j s[k eih3[]]].\n'
    text+=define('eih5',[],both(k('eir3',k('eised'),k('rd'),k('eirf'),quote('eih4'),k('ri')),k('ue',k('eisec'),k('eised'),k('ri')),op('u',op('e',k('eisec'),k('eised')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDICES[0];doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[])) for n in ('eihw','eih5')]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='hypothetical_frame_introduction_and_two_purpose_naming',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=list(INDICES)).document
    ann=json.loads(read('data/kinematics-headings-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eiseb',role='designation',forms=[dict(text='ruhende System',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
