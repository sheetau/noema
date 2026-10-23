"""Compose conditional local time valuation by finding simultaneous indications."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_practical_time_convention import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-practical-time-convention.noema';PARENT_BASIS='data/practical-time-convention-basis-v1.json'
FULL='examples/v014/einstein-local-clock-valuation.noema';CORE='examples/v014/local-clock-valuation-core.noema'
BASIS='data/local-clock-valuation-basis-v1.json';ANNOTATIONS='data/local-clock-valuation-identifiers-v1.json';INDEX=234
BASE=[(n,'a') for n in ('observer','clock','hand','place','frame','unit')]+[('context','d')]
ASSIGN=BASE+[(n,'a') for n in ('event','eventplace','display')]+[('reading',R)]
METHOD=[(n,'a') for n in ('task','observer','clock','hand','place','frame','unit','document')]+[('reference','d')]
PRIMITIVES={
 'eish3':([(n,'a') for n in ('observer','event','display','hand','clock','frame')]+[('context','d')], 'observerが同じeventに時間的な対応を与えるため、同じclockのhandが示すdisplayを観察・読取りによって探し当てるという操作。単なる表示の存在や偶然の数値一致ではなく、対象と指示を照合する手段である。生起との局所的一致・表示値・割当の成立は合成で別に要求する。探索アルゴリズム・測定所要時間・光受信を新たに指定しない。'),
 'eish4':([(n,'a') for n in ('observer','event','clock','frame','unit')]+[('reading',R),('context','d')], 'observerがeventの時間的評価として、同じclock・frame・unitのreadingを対応付ける。局所時計の読みを対象出来事へ付与する行為・規約であり、別の信号の受信への割当、遠隔時計との比較や実際の実行済みを含意しない。可能性の内部で用いるときはその候補状況の対応を述べる。'),
 'eish5':([('event','a'),('clock','a'),('slot','b'),('context','d')], '同じeventを同じclockで評価する候補記録の個体欄を取り出す。整数slotの1は対象出来事の発生場所、2は対応させようとする指針表示出来事である。欠落・未知・範囲外を既定個体で埋めず、欄を取り出しただけでは近接や同時の対応が成立すると認定しない。'),
 'eish6':([(n,'a') for n in ('event','clock','unit')]+[('context','d')], '同じeventの候補記録で、同じclockとunitによって付与しようとする実数切断の値候補。候補状況ごとに選び得る表示と値であり、全知の正解生成器ではない。未知値を0や別出来事の値で埋めない。値の有効性・指針との対応・出来事の読みを別に要求する。'),
 'eish7':([(n,'a') for n in ('task','place','frame','document')]+[('reference','d')], '同じtaskの対象範囲eisgeが、同じdocumentのreferenceでplaceの直近で時間的に評価しようとする出来事の全範囲として定められている。局所的一致に用いる近接尺度を保ち、成功例だけの抜粋や遠隔出来事の混入を許さない。出来事が現実に何件起きたか、対応の成功はこの範囲設定から要求しない。'),
 'eisia':(METHOD+[('candidate','d')], 'referenceの同じtask・observer・clock・hand・place・frame・unitについて、観測者が指針の対応を探し出して時間的に評価する操作を実行し得る候補状況がcandidateである。同じ設置時計と場所・対象出来事・表示規約を保ち、結果が成功するかは合成側で判定する。別時計への交換、対象の選び直し、単なる願望・許可・論理上だけの可能性を候補にしない。実際に実行済み、全候補で成功する制御能力は加えない。'),
 'eisib':([], 'u0013で点Aに置かれると仮定する一つの時計への参照。著者の私有時計や前段落の原点の時計とは固定せず、後の点Bの時計と比較する同じA側の時計として追跡する。'),
 'eisic':([], 'u0013で点Aにいると設定する一人の観測者への参照。特定人物や著者本人に固定せず、その所在地と操作を評価可能性の内部で要求する。'),
 'eisid':([], 'u0013の同じA側の時計の指針表示部分への参照。短針一つに限定せず、一般のeisgsの役割に結ぶ。'),
 'eisie':([], 'u0013第一文で点Aの直近の出来事へ局所時計の時間的評価を与える課題。全対象をeish7とeisgeで固定し、別地点との共通時間を既に定義した課題としない。'),
}
RESULTS={'eish5':'a','eish6':R}
MEANINGS={
 'eiky':'同じ系の指定場所に時計が設置され、現在の所在もそこにあるという条件。観測者の存在や読取り成功をこの条件へ混ぜない。',
 'eikz':'対象出来事の場所が同じ系で指定場所と同一又は局所的一致を使える程度に近接している。場所の同一性だけへ狭めず、遠隔場所は許さない。',
 'eik2':'同じ場所の時計と観測者、一般の指針表示・校正・尺度を結ぶ局所的な読取り設定。座標原点や遠隔同期を要求しない。',
 'eik3':'近傍の同じ出来事とその場で同時の時計表示を観測者が探し当て、同じ有効実数の読みを出来事に付与する局所評価。表示と出来事の読みを共に確認し、別周期の同表示を許さない。',
 'eik4':'同じ出来事・時計・状況の発生場所と表示の候補欄、同じ単位の値候補をeik3へ結ぶ。別記録の場所や表示を組み合わせない。',
 'eik5':'同じ操作を実行し得る候補で局所設定が成立し、referenceで固定した全対象出来事について近傍性とeik4の対応が成り立つ。対象ごとに別候補へ逃げず、実際に出来事が起きたという非空性を追加しない。',
 'eik6':'同じ観測者・時計・場所・課題についてeik5を満たす一つの候補があるという局所評価の可能性。現実の実施済みや全候補での成功と区別する。',
 'eik7':'点Aの時計があるなら、同じAの観測者がその近傍の出来事を同時の指針表示を探すことによって時間的に評価できるという条件内容。Aは既存ziqへの共通参照である。',
 'eila':'条件付きの可能性eik7を主張するメッセージ。時計の現実の設置や操作成功を無条件の主張へ替えない。',
 'eilb':'既に前方参照の始点として導入したeish2で第一文を同じ著者・論説へ帰属し、前段落第三文から本文順序を保つ。',
}
LIMITS=[
 'Befindet sich ... so kannを、思考上導入した同じ時計が点Aにあるという条件の下で、同じAの代表的な観測者が局所評価を実行できる候補があるという読みで保持する。実在する観測者全員への保証、時計の世界唯一性、実測済みを補わない。',
 'M0002–M0004のAは全て既存ziqの同じ場所を指す。Aを座標原点と同一にせず、前段落の時計や観測者とも同一視しない。rbの時間単位を用いるが、時計の基準合わせや遠隔同期はここで要求しない。',
 'unmittelbare Umgebungを同一場所と既存eisfpの近接場所の範囲として読む。先行脚注の局所同時性の理想化を保持し、固定距離・光伝播時間の補正・計器精度を補わない。eisgmはこの理想化の下で対象と表示の生起を一致させる。',
 'Aufsuchenは同時の指針表示を観測して探し当てる手段として保持する。短針だけに限定せず、単に数値が一致することや別周期の同表示、遠隔から届いた光の受信を対象の生起へ替えない。',
 '同じ候補状況で全対象出来事の対応を要求し、対象範囲は元の状況へ固定する。候補欄の値は検査対象であって正解を返すオラクルではない。原文の一般的な出来事への方法説明を、現実の出来事の最低件数という存在主張へ替えない。',
 '第一文197非空白本文文字と三つの数式記号Aを対象とする。点Bの時計以降と、u0013全段落の判断は未完。',
]

def args(fs,context=None):return [v(context if n=='context' and context else n) for n,_ in fs]
def field(slot):return k('eish5',v('event'),v('clock'),'n p '+number_word(slot)+' b',v('context'))

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+RESULTS.get(n,'a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eiky',[(n,'a') for n in ('clock','place','frame')]+[('context','d')],both(k('ca',v('clock')),k('va',v('frame')),k('cb',v('clock'),v('place'),v('frame')),k('eisgf',v('clock'),v('place'),v('frame'),v('context'))))
    near=lambda p,s:op('x',op('e',p,v('place')),k('eisfp',p,v('place'),v('frame'),s))
    text+=define('eikz',[(n,'a') for n in ('event','place','frame')]+[('context','d')],both(k('zbd',v('event')),q('g','where','a',both(k('cb',v('event'),v('where'),v('frame')),near(v('where'),v('context'))))))
    text+=define('eik2',BASE,both(k('eiky',v('clock'),v('place'),v('frame'),v('context')),k('eisgr',v('observer'),v('context')),k('cb',v('observer'),v('place'),v('frame')),k('ci',v('unit')),k('eisdf',v('clock'),v('context')),k('eisgs',v('hand'),v('clock'),v('context'))))
    text+=define('eik3',ASSIGN,both(k('eik2',*args(BASE)),k('zbd',v('event')),k('zbd',v('display')),k('cb',v('event'),v('eventplace'),v('frame')),near(v('eventplace'),v('context')),k('cb',v('display'),v('place'),v('frame')),k('ba',v('reading')),k('eisgt',v('display'),v('hand'),v('clock'),v('reading'),v('context')),k('eisgm',v('event'),v('display'),v('clock'),v('frame'),v('context')),*[k('ce',v('clock'),v(n),v('frame'),v('unit'),v('reading')) for n in ('event','display')],k('eish3',*[v(n) for n in ('observer','event','display','hand','clock','frame','context')]),k('eish4',*[v(n) for n in ('observer','event','clock','frame','unit','reading','context')])) )
    text+=define('eik4',BASE+[('event','a')],k('eik3',*args(BASE),v('event'),field(1),field(2),k('eish6',v('event'),v('clock'),v('unit'),v('context'))))
    selected=k('eisge',v('task'),v('event'),v('reference'))
    every=q('f','event','a',op('y',selected,both(k('eikz',v('event'),v('place'),v('frame'),v('reference')),k('eik4',*args(BASE,'candidate'),v('event')))))
    text+=define('eik5',METHOD+[('candidate','d')],both(k('eisia',*args(METHOD),v('candidate')),k('eish7',v('task'),v('place'),v('frame'),v('document'),v('reference')),k('eik2',*args(BASE,'candidate')),every))
    text+=define('eik6',METHOD,q('g','candidate','d',k('eik5',*args(METHOD),v('candidate'))))
    text+=content('eik7',op('y',k('eiky',k('eisib'),k('ziq'),k('ra'),v('point')),k('eik6',*[k(n) for n in ('eisie','eisic','eisib','eisid','ziq','ra','rb','eirf')],v('point'))))
    text+='d eila[] f[j s[k eik7[]]].\n'
    text+=define('eilb',[],both(k('eir3',k('eish2'),k('rd'),k('eirf'),quote('eila'),k('ri')),k('ue',k('eishs'),k('eish2'),k('ri')),op('u',op('e',k('eishs'),k('eish2')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eilb',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='conditional_local_clock_valuation_by_simultaneous_indications',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/practical-time-convention-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
