"""Compose local adequacy, remote inadequacy and equivalent temporal tasks."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_clock_definition_proposal import ROOT,read,BASE,PROPOSAL
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-clock-definition-proposal.noema';PARENT_BASIS='data/clock-definition-proposal-basis-v1.json'
FULL='examples/v014/einstein-clock-definition-scope.noema';CORE='examples/v014/clock-definition-scope-core.noema'
BASIS='data/clock-definition-scope-basis-v1.json';ANNOTATIONS='data/clock-definition-scope-identifiers-v1.json';INDEX=230
LOCAL=BASE+[('event','a'),('display','a'),('place','a'),('reading',R)]
RULE='i[h['+' '.join(t for _,t in LOCAL)+'] c]'
KIND=[(n,'a') for n in ('task','clock','frame','unit','document')]+[('context','d')]
KCODE='i[h['+' '.join(t for _,t in KIND)+'] c]'
ADEQUACY=[(n,'a') for n in ('proposal','task','speaker','clock','hand','frame','unit','document')]+[('context','d')]
PRIMITIVES={
 'eisgd':([('task','a'),('problem','a'),('author','a'),('document','a'),('context','d')],'同じdocumentのcontextでauthorが取り組もうとする具体的なtaskがproblemという時間定義の問題に属する。es sich darum handeltに当たる課題の設定であり、既に達成したことや単なる無関係の課題名ではない。条件文で用いるとき、全ての課題が実際に取り組まれているとは主張しない。'),
 'eisge':([('task','a'),('event','a'),('context','d')],'同じtaskで時間を規定する対象となる出来事の全範囲の一員がeventである。成功した測定や時計のそばにある出来事だけを後から選別せず、課題で指定した対象を保つ。非空性・場所の限定・出来事型は合成側で要求する。'),
 'eisgf':([('clock','a'),('place','a'),('frame','a'),('context','d')],'同じclockがframeでcontextの時点にまさに所在する場所がplaceである。ebenを現在の所在の指定として保持し、時計が以前いた場所や後で運ぶ先へ交換しない。世界線全体で静止することや絶対位置は要求しない。既存cbによる配置とも結ぶ。'),
 'eisgg':(KIND,'taskは、対象出来事に同じclockを基準とする時間の値を与えるという時間的評価の課題である。何を出来事の時刻とするかを定め、その値によって同時・先後等を比較できることを目指す。時計の表示出来事の値を対象出来事へどう結ぶかも課題に含み、受信時刻との無条件な同一視、計器を読むだけの行為、倫理的な評価ではない。場所・達成・規則の十分性は別に定める。'),
 'eisgh':([('task','a'),('series','a'),('place','a'),('frame','a'),('context','d')],'同じtaskで相互の時間関係を定めようとする出来事系列の一つがseriesで、その系列がplaceで起こるものとして指定される。系列は出来事の継起を局所的な順にまとめた対象で、単なる文字列、物体の集合、一つの時刻値とは区別する。eisgiがその全構成出来事を与える。各系列内の順序を保ったまま系列間の時間対応を問題にし、系列間の同期や既知の相対時刻は先取りしない。'),
 'eisgi':([('series','a'),('event','a'),('context','d')],'同じseriesを構成する出来事の全範囲にeventが属する。各系列内の継起の同一性を保つ構成関係であり、系列同士の時間対応が既に確定したことではない。系列の位置や実際の出来事型は合成側で確認し、都合のよい構成員の抜粋にしない。'),
 'eisgj':(KIND,'taskは、同じframe・unitで異なる場所の出来事系列を相互に時間的に結ぶ課題である。各系列内の継起を保持して、どの出来事が他系列のどの時刻・同時性・先後に対応するかを同じclockに結び付けた尺度で定めることを目指す。単なる空間的な連結、各系列を別々に番号付けしただけ、既に同期済みの断言ではない。少なくとも二つの異なる系列と場所、および全構成出来事は別に要求する。'),
 'eisgk':([('task','a'),('requirement','a'),('document','a'),('context','d')],'requirementは同じtaskをその指定範囲で完了するために満たすべき規約上の必要条件の一つである。対象全体に値を与えられること、同じ対象に曖昧な値を残さないこと、要求された時間比較を保つこと等、当該課題の全必要条件を指定する。成功するものだけに範囲を狭めず、未知の条件を不成立又は空集合として扱わない。'),
 'eisgl':(ADEQUACY[:-1]+[('requirement','a'),('rule',RULE),('context','d')],'同じproposalの時計指示による規則を、ruleが記述する局所的な指示と出来事の対応として用いるだけで、同じtaskのrequirementが満たされる。話者・時計・短針・系・尺度・文脈を保ち、別の時計の追加、未指定の遠隔同期や光伝播補正による解決を、この規則だけの充足へ混ぜない。個別の条件の充足を指定し、全条件について十分であるかは合成で量化する。実際の測定済みを必要としない規則の適用能力である。'),
 'eisgm':([('event','a'),('display','a'),('clock','a'),('frame','a'),('context','d')],'局所的な同一場所の理想化の下で、対象eventの生起と同じclockのdisplayという指示出来事がその場で一致して対応する。時計の針が一周した別時点の同じ表示や遠方から届いた信号の受信を、対象の生起そのものへ交換しない。局所的な出来事一致の対応を与え、未知の遠隔時計の同時性や普遍的時刻の値から逆算しない。両出来事の場所・読みは合成で確認する。'),
 'eisgn':([('solution','a'),('kind',KCODE),('clock','a'),('frame','a'),('unit','a'),('document','a'),('context','d')],'solutionが、kindの閉じた型で記述する種類の時間的課題を同じclock・frame・unitで満たす手続きである。系列とその構成出来事という同じ対象範囲を保ち、系列間の比較を要求する記述と、個々の遠隔出来事の時刻を要求する記述を替えた際も、別の出来事や尺度にすり替えない。手続きの適用範囲と得られる時刻・比較を同じものとして評価する。種類間の同等性はこの入力だけでは断言せず、両種類の解となる手続きの一致を合成で要求する。'),
 'eisgo':([('node','a'),('author','a'),('claim','i[e]'),('document','a'),('context','d')],'authorがnodeでclaimの限定を保った内容を、単なる見かけの可能性ではなく実際に成り立つこととして確認して提示する。in der Tatの確認の働きであり、限定を外した先行見込みの全承認、独立の実験証明、読み手の確信を要求しない。内容自体の成立は別の合成で保持する。'),
 'eisgp':([('node','a'),('author','a'),('target','i[e]'),('explanation','i[e]'),('document','a'),('context','d')],'authorがnodeでtargetの課題の記述を述べる途中に、explanationを言い換えの理由を示す挿入として提示する。二つの言い方が同じ課題に帰着するという説明を保持し、無関係な代案の列挙、別の選択肢との排他的な選択、時間的な後続へ替えない。内容は引用して同定し、挿入という提示だけからその真理を導かない。'),
 'eisgq':([], '固定原文einstein-1905:u0011[201,639)の第二文。前文の同じ定義案の局所的十分性と異所での不十分性、遠隔出来事の時間的評価との言い換えを述べる箇所。'),
}
MEANINGS={
 'eijr':'同じ短針の指示eijiを同じ場所の対象出来事と局所的一致eisgmで対応させ、対象と表示の同じ読みを結ぶ時刻付与規則。現在の時計所在を保ち、全体静止・遠隔同期・周期回数を追加しない。',
 'eijs':'taskの対象出来事が非空で、その全てが同じplace・frameにあるという範囲。局所で成功した一部だけに限定しない。',
 'eijt':'同じ時計に基づく時間的評価の課題で、その時計の現在の所在場所だけを対象とするeijsを満たす。異所を一つでも含む課題や空の課題はこの局所限定へ入れない。',
 'eiju':'系列の全構成出来事が非空で、同じplace・frameにある。系列間の時間対応はここで要求しない。',
 'eijv':'同じ時計の尺度へ異所の出来事系列を相互に時間的に結ぶ課題。少なくとも二つの異なる系列・場所を持ち、指定された全系列の構成出来事がその指定場所にある。',
 'eijw':'同じ時計に基づき、現在の時計の場所から局所的に離れた場所の出来事へ時間的評価を与える課題。対象出来事は非空で全てその遠隔範囲にあり、単なる近接場所を遠隔として扱わない。',
 'eijx':'同じtaskに非空の必要条件範囲があり、その全条件を同じproposalの局所規則eijrだけで満たせるという十分性。',
 'eijy':'同じtaskの必要条件のうち少なくとも一つを同じproposalの局所規則eijrだけでは満たせないという不十分性。規則も条件も未知の場合を偽として補わない。',
 'eijz':'同じ対象・時計・系・尺度について、異所の系列を時間的に結ぶeijvと遠隔出来事を時間的に評価するeijwの解となる手続きが両方向に一致する。手続きの実装済みや存在は追加せず、二つの課題の同等性を述べる。',
 'eij2':'同じ時間定義に取り組む全課題について、時計の現在の場所だけを対象とするなら同じ案が十分であるという条件内容。',
 'eij3':'同じ時間定義に取り組む全課題について、異所系列の連結又は遠隔出来事の時間的評価を対象とするなら同じ案は不十分であるという条件内容。適用範囲が変わると通用しなくなることであり、時計が経年劣化するという意味ではない。',
 'eij4':'同じclock・frame・unit・論説についてeijzを述べる挿入説明の内容。',
 'eij5':'前文と同じ定義案eijjを保持し、局所の十分性eij2、遠隔の不十分性eij3、二課題の同等性eij4を同じ評価文脈で結ぶ。',
 'eij6':'第二文の全内容eij5を主張するメッセージ。見かけの可能性に弱めず、前文の全困難の解決を無条件に承認しない。',
 'eij7':'同じ著者・論説への帰属、局所の成立を実際の確認として提示するin der Tat、局所と遠隔の対比、同等性の挿入説明、第一文からの順序を結ぶ。',
}
LIMITS=[
 'Eine solche Definitionは前文の同じ案eisf5・時間定義の問題eisf6を指す。同じ著者の時計eisf7・短針eisga・ra・尺度eisgbを保持する。新たな同期方式や7時の例を追加しない。',
 'genügtは課題の非空の全必要条件を当該規則だけで満たせるという十分性、genügt nicht mehrは必要条件を少なくとも一つ満たせないという不十分性として読む。実際の測定済み・時計の故障・時間の経過による劣化とはしない。',
 'ausschließlichとebenは現在の時計所在だけに対象を限定する。表示と対象出来事の局所的一致を結び、別周期の同じ針位置や遠隔信号の受信を対象生起そのものに替えない。脚注で述べた局所的理想化の留保を維持する。',
 'Ereignisreihenは各場所で局所的に順を持つ出来事系列であり、系列間の時間対応を与える課題とする。固定された全構成員と場所を保持し、単に異なる二つの名前があることへ縮めない。',
 '遠隔は同一場所でも同じ局所尺度で近接した場所でもない範囲と読む。数値距離、光速補正、遠隔時計の存在・同期を原文へ追加しない。二つの課題の同等性は同じ対象と尺度の解手続きの両方向一致として読む。',
 'wennとsobaldは課題の適用範囲による条件を保持する。in der Tatは限定した局所内容の確認、aberは対比、oder以下は同じ課題に帰着する挿入説明として記述する。',
 '必要条件・個別充足・手続きの適合範囲は意味規約を持つ入力であり、有限対照例から物理的妥当性や任意の課題の解法を自動証明しない。第二文373文字を記述した後、第一文と合わせた全段落545文字の通読判断を別に行う。',
]

def args(fs):return [v(n) for n,_ in fs]
def exists(fs,body):
    for n,t in reversed(fs):body=q('g',n,t,body)
    return body
def allof(fs,body):
    for n,t in reversed(fs):body=q('f',n,t,body)
    return body

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    located=lambda obj,place:k('cb',v(obj),v(place),v('frame'))
    current=both(located('clock','place'),k('eisgf',v('clock'),v('place'),v('frame'),v('context')))
    text+=define('eijr',LOCAL,both(k('eiji',*args(BASE),v('display'),v('reading')),current,k('zbd',v('event')),k('zbd',v('display')),located('event','place'),located('display','place'),k('eisgm',v('event'),v('display'),v('clock'),v('frame'),v('context')),k('ce',v('clock'),v('event'),v('frame'),v('unit'),v('reading'))))
    for name,owner,membership in (('eijs','task','eisge'),('eiju','series','eisgi')):
        member=lambda:k(membership,v(owner),v('event'),v('context'))
        members_at_place=q('f','event','a',op('y',member(),both(k('zbd',v('event')),located('event','place'))))
        text+=define(name,[(owner,'a'),('place','a'),('frame','a'),('context','d')],both(q('g','event','a',member()),members_at_place))
    text+=define('eijt',KIND,both(k('ca',v('clock')),k('va',v('frame')),k('ci',v('unit')),k('eisgg',*args(KIND)),q('g','place','a',both(current,k('eijs',v('task'),v('place'),v('frame'),v('context'))))))
    series=lambda s,p:k('eisgh',v('task'),v(s),v(p),v('frame'),v('context'))
    text+=define('eijv',KIND,both(k('ca',v('clock')),k('va',v('frame')),k('ci',v('unit')),k('eisgj',*args(KIND)),exists([(n,'a') for n in ('first','second','left','right')],both(op('u',op('e',v('first'),v('second'))),op('u',op('e',v('left'),v('right'))),series('first','left'),series('second','right'))),allof([('series','a'),('place','a')],op('y',series('series','place'),k('eiju',v('series'),v('place'),v('frame'),v('context'))))))
    remote=q('g','remoteplace','a',both(located('event','remoteplace'),op('u',op('e',v('remoteplace'),v('place'))),op('u',k('eisfp',v('remoteplace'),v('place'),v('frame'),v('context')))))
    member=lambda:k('eisge',v('task'),v('event'),v('context'))
    text+=define('eijw',KIND,both(k('ca',v('clock')),k('va',v('frame')),k('ci',v('unit')),k('eisgg',*args(KIND)),q('g','place','a',both(current,q('g','event','a',member()),q('f','event','a',op('y',member(),both(k('zbd',v('event')),remote)))))))
    required=lambda:k('eisgk',v('task'),v('requirement'),v('document'),v('context'))
    met=lambda:k('eisgl',*args(ADEQUACY[:-1]),v('requirement'),'r[p eijr]',v('context'))
    text+=define('eijx',ADEQUACY,both(q('g','requirement','a',required()),q('f','requirement','a',op('y',required(),met()))))
    text+=define('eijy',ADEQUACY,q('g','requirement','a',both(required(),op('u',met()))))
    fs=KIND[1:];solution=lambda name:k('eisgn',v('solution'),'r[p '+name+']',*args(fs))
    text+=define('eijz',fs,q('f','solution','a',both(op('y',solution('eijv'),solution('eijw')),op('y',solution('eijw'),solution('eijv')))))
    fixed=[k(n) for n in ('eisf7','ra','eisgb','eirf')]+[v('point')]
    involved=k('eisgd',v('task'),k('eisf6'),k('rd'),k('eirf'),v('point'))
    adequacy=[k('eisf5'),v('task'),k('rd'),k('eisf7'),k('eisga'),k('ra'),k('eisgb'),k('eirf'),v('point')]
    text+=content('eij2',q('f','task','a',op('y',both(involved,k('eijt',v('task'),*fixed)),k('eijx',*adequacy))))
    text+=content('eij3',q('f','task','a',op('y',both(involved,op('x',k('eijv',v('task'),*fixed),k('eijw',v('task'),*fixed))),k('eijy',*adequacy))))
    text+=content('eij4',k('eijz',*fixed))
    setup=k('eijj',*[k(n) for n in ('eisf5','rd','eisf6','eisf7','eisga','ra','eisgb','eirf')],v('point'))
    text+=content('eij5',both(setup,*['t[k '+n+'[]][v point]' for n in ('eij2','eij3','eij4')]))
    text+='d eij6[] f[j s[k eij5[]]].\n'
    text+=define('eij7',[],both(k('eir3',k('eisgq'),k('rd'),k('eirf'),quote('eij6'),k('ri')),k('eisgo',k('eisgq'),k('rd'),quote('eij2'),k('eirf'),k('ri')),k('zbc',k('eisgq'),k('rd'),quote('eij2'),quote('eij3'),k('eisf6'),k('ri')),k('eisgp',k('eisgq'),k('rd'),quote('eij3'),quote('eij4'),k('eirf'),k('ri')),k('ue',k('eisgc'),k('eisgq'),k('ri')),op('u',op('e',k('eisgc'),k('eisgq')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eij7',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='local_clock_definition_adequacy_and_remote_task_limit',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/clock-definition-proposal-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
