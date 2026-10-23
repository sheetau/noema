"""Compose the optional assignment of a receiving observer's clock indication."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_clock_definition_scope import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-clock-definition-scope.noema';PARENT_BASIS='data/clock-definition-scope-basis-v1.json'
FULL='examples/v014/einstein-reception-time-alternative.noema';CORE='examples/v014/reception-time-alternative-core.noema'
BASIS='data/reception-time-alternative-basis-v1.json';ANNOTATIONS='data/reception-time-alternative-identifiers-v1.json';INDEX=231
SETUP=[(n,'a') for n in ('observer','clock','hand','origin','frame','unit')]+[('context','d')]
ARRIVAL=[('task','a')]+SETUP+[(n,'a') for n in ('event','signal','departure','reception')]
ASSIGNMENT=ARRIVAL+[('display','a'),('reading',R)]
RECORD=[('task','a'),('record','a')]+SETUP
RCODE='i[h['+' '.join(t for _,t in RECORD)+'] c]'
METHOD=[(n,'a') for n in ('scheme','task','observer','clock','hand','origin','frame','unit','document')]+[('context','d')]
PRIMITIVES={
 'eisgr':([('observer','a'),('context','d')],'observerは物理的な出来事を、届く信号の検知と計器の読取りによって識別し、量の対応付けを行う観測者である。思考上の設定も許すが、単なる座標値や光線そのものと区別する。特定人物、実際の実験履歴、観測結果の正しさをこの分類から要求しない。'),
 'eisgs':([('hand','a'),('clock','a'),('context','d')],'handは同じclockで時間の読みを示す指針又は指針の配置を追跡する表示部分である。校正された目盛に対する位置として値を示すもので、針の物質そのものを時間と同一視しない。この文のUhrzeigerstellungを短針一つに限定せず、必要な指針の配置を同じ表示対象として保持する。'),
 'eisgt':([('display','a'),('hand','a'),('clock','a'),('reading',R),('context','d')],'displayは同じclockの指針表示handが、その時計の校正規約でreadingに対応する位置又は配置を示す出来事である。別の時計・別の表示時点・単なる数字の記載へ交換しない。値の実数としての有効性・時計の読み・受信との一致は別に確認する。日付や表示周期回数をこの位置だけから新たに復元しない。'),
 'eisgu':([('event','a'),('signal','a'),('departure','a'),('observer','a'),('frame','a'),('context','d')],'signalがeventの生起をobserverへ知らせる光学的な証拠となり、departureがその同じ信号を対象の側から追跡し始める出来事である。発光・散乱・変調等によって対象出来事の生起に結び付いた信号であり、無関係の光や他の出来事からの報せへ替えない。対象出来事と信号の出発を役割として分け、両者を必ず異なる時刻としたり、対象を発光出来事だけへ限定したりしない。'),
 'eisgv':([('signal','a'),('departure','a'),('reception','a'),('observer','a'),('frame','a'),('context','d')],'同じsignalがdepartureから伝播しobserverへ到達し、その到達をreceptionという受信出来事として識別する。終点が同じ観測者の所であることを保持し、途中の別信号や他者の受信に取り替えない。伝播の経路内部が空虚であるか、時計の指示、原出来事の時刻、光速値はこの関係だけから導かない。'),
 'eisgw':([('task','a'),('record','a'),('observer','a'),('frame','a'),('context','d')],'同じtaskで評価する出来事を知らせ、真空を通って同じobserverへ届く各光信号についての対応記録の全範囲にrecordが属する。各該当到達を含め、指針の割当が成功したものだけを抜粋しない。記録内の対象・信号・出発・受信・表示候補と値候補を後で同じものとして検査する。届く信号のないあらゆる出来事にも記録が存在するとは追加しない。'),
 'eisgx':([('record','a'),('slot','b'),('context','d')],'同じrecordの指定欄の個体を取り出す。整数slotの1は原出来事、2は光信号、3は追跡区間の出発、4は受信出来事、5は割り当てる指針表示出来事の候補である。五つの役割と順を保持し、欄の欠落・範囲外・未知値を別欄や既定の個体で埋めない。候補を取り出すことはその物理的な正しさや割当の成功を意味しない。'),
 'eisgy':([('record','a'),('task','a'),('observer','a'),('frame','a'),('context','d')],'recordが同じtask・observer・frame・contextに属する五つの個体欄を持つ対応記録として整っている。欄の役割はeisgxの規約に従う。数値候補は同じ記録と時計・尺度についてeisgzが与える。欄の全数・役割・帰属の条件であり、光の証拠・受信・表示・割当の実際の成立は別に合成する。'),
 'eisgz':([('record','a'),('clock','a'),('unit','a'),('context','d')],'同じrecordの表示候補について、同じclockとunitで割り当てようとする時刻値の候補を与える。値は実数の下側切断として表し、有効性と物理的読取りへの対応を合成で別に要求する。値が不明なら0や受信前の時刻を推測せず、原出来事の正しい時刻を返す全知関数とはしない。'),
 'eisg2':([('observer','a'),('task','a'),('event','a'),('signal','a'),('reception','a'),('display','a'),('clock','a'),('frame','a'),('unit','a'),('reading',R),('context','d')],'observerが同じtaskの時間的評価の方法として、eventを知らせたsignalに、reception時の同じclockのdisplayという指針表示とreadingを対応付ける。この対応によって元のeventを時間的に評価するが、割当の行為・規約であって原出来事の物理的生起時刻と受信時刻が等しいという認定ではない。信号の到着と同じ表示を使う向きを保ち、伝播時間の補正や別の時計の同期を加えない。'),
 'eisg3':(METHOD[:-1]+[('rule',RCODE),('context','d')],'schemeが同じtaskに用いる時刻評価の方式で、同じobserver・clock・hand・origin・frame・unitについてruleの閉じた型で指定する各到達記録への対応を用いる。方式名だけではなく、原出来事・光・出発・受信・指針表示・値を保持する検査可能な関係型へ結ぶ。全記録についてその対応が成立すること、方式を採用してよいという態度は別に合成する。'),
 'eisg4':([('author','a'),('scheme','a'),('task','a'),('document','a'),('reference','d'),('candidate','d')],'同じdocumentのreferenceで、authorが同じtaskをschemeで扱うことを考えたとき、candidateがその採用を考えられる状況に属する。方式と課題の指示を保ち、実際の採用済み、必ず成功する制御能力、物理的に正しい座標時刻の確定と同一視しない。方式の内容とそれだけで済ませる態度は候補の内部で別に要求する。'),
 'eisg5':([('author','a'),('scheme','a'),('task','a'),('document','a'),('context','d')],'authorが同じtaskのためにはschemeという方式でひとまず済ませ、それ以上の規定をこの選択の時点では求めないという採用上の態度をとる。sich begnügenに当たる限定した満足・選択であり、感情的な喜び、最善性、欠点の不存在、将来の改善の禁止ではない。この態度の可能性と実際の態度を分ける。'),
 'eisg6':([('node','a'),('author','a'),('prior','i[e]'),('alternative','i[e]'),('document','a'),('context','d')],'authorがnodeでpriorの限界を踏まえつつ、alternativeをひとまず認め得る別の取り方として譲歩的に持ち出す。allerdingsの働きであり、先行の限界を撤回すること、後の欠点を解決済みとすること、二内容の論理的な矛盾を要求しない。引用した可能性の留保を保持し、代案を既に実施した断言へ替えない。'),
 'eisg7':([], 'u0012で考える、原点で光信号を受け取る際の時計指示を対応付ける同じ方式への談話上の参照。次文のEine solche Zuordnungが引き継ぐ対象となる。'),
 'eisha':([], 'u0012の代案の設定で導入される一人の観測者への参照。著者本人や固有名の人物と同一視せず、設定の成立は可能性の内部で要求する。'),
 'eishb':([], 'u0012の同じ観測者とともにある時計への参照。法的所有や前段の特定時計個体との同一性を加えない。'),
 'eishc':([], 'u0012の同じ時計の指針表示部分への参照。具体的な針数・短針だけという限定は与えず、eisgsで表示の役割を要求する。'),
 'eishd':([], 'u0012で観測者と時計が位置する、同じ系の座標原点への参照。原点への割当zbvと同所配置を内容内で確認する。'),
 'eishe':([], 'u0012で対象出来事に時間的評価を与えようとする同じ課題への参照。対象範囲はeisge、各信号の対応記録の全範囲はeisgwで固定する。'),
 'eishf':([], 'u0012の同じ時計の読みを表す時間尺度への参照。ciと時計の校正へ結び、特定の時刻値や日付を補わない。'),
 'eishg':([], '固定原文einstein-1905:u0012[0,309)の第一文の箇所。受信光信号に指針表示を対応付ける譲歩付きの代案を述べる。'),
}
RESULTS={'eisgx':'a','eisgz':R}
MEANINGS={
 'eika':'同じ観測者・時計・指針表示・座標原点・系・時間尺度について、型、時計校正、原点への割当、観測者と時計の同所配置を結ぶ。所有・短針限定・世界線全体の静止は加えない。',
 'eikb':'同じ課題の原出来事を知らせる同じ光信号が、指定した出発から真空を通って同じ原点の観測者に届く受信出来事を結ぶ。原出来事と受信は別の役割として保持し、同時性は要求しない。',
 'eikc':'eikbの同じ受信に局所的に一致する時計の指針表示と、有効な実数の同じ読みを結び、その表示を同じ信号へ割り当てて原出来事を時間的に評価する。元の出来事への正しい座標時刻の付与は断言しない。',
 'eikd':'同じ到達記録の五つの個体欄と値候補を取り出し、eikcへ同じ順・同じ時計・尺度・文脈で渡す。原出来事・光・出発・受信・表示を別々の記録から集めない。',
 'eike':'同じ方式がeikdを記録ごとの規則とし、同じ観測者に届く該当信号の非空の全記録にその対応が成立する。信号の届かない全出来事まで覆うとは追加しない。',
 'eikf':'この代案で導入した同じ方式・課題・観測者・時計・表示・原点・系・尺度についてeikeを述べる閉じた内容。',
 'eikg':'referenceから同じ方式の採用を考えられるcandidateがあり、その候補で同じeikfの対応方式が成立し、著者がそれでひとまず済ませる態度を持つという候補条件。',
 'eikh':'同じ方式の採用候補eikgが存在するという可能性の内容。現実の採用・欠点の消滅・最善性を主張しない。',
 'eiki':'第一文の可能性eikhを主張するメッセージ。中の観測実行や著者の態度を現実の事実として断言しない。',
 'eikj':'同じ著者・論説への帰属、先行する局所定義の限界を踏まえた譲歩的な代案の提示、前段落からの本文順序を結ぶ。',
}
LIMITS=[
 'Wirは方法を検討する著者の論述上の声と読む。導入する観測者を著者本人や特定人物に固定せず、einの対象を代案内部で導入した同じ観測者として追跡する。',
 '時計と観測者は同じraの原点に位置する。法的所有、全軌道での静止、短針だけ、特定の表示時刻を補わない。原点の割当と実際の設定は可能な採用状況の内部に置く。',
 '光は既存eisb5の物理的伝播、空虚な経路内部はeiscaの真空規約を再利用する。対象出来事を知らせる証拠、信号の出発、到達、受信を分け、媒質や光速値、距離補正、遠隔時計の同期を追加しない。',
 'jedemは該当する全到達の記録へ量化し、割当成功例の抜粋にしない。出来事が評価対象であり、それを知らせる各受信信号がこの方式の直接の対応対象である。信号が届かない出来事の観測可能性は補わない。',
 '対応する指針位置は受信に局所的に一致する表示と読みとして保持する。別周期の同じ表示や原出来事自身の時計の読みを受信指示へ代入しない。時刻値候補と未知入力を分け、有限標本で全実数の有効性を保証しない。',
 'könnten uns begnügenは、この方式を採用してひとまず済ませる態度を持つ候補の存在として読む。allerdingsは先行する限界を踏まえた譲歩的な代案であり、既に実施した事実や後続の欠点の否定にしない。',
 '第一文269非空白文字を対象とする。第二文の観測者位置への依存と経験による知識、第三文のより実用的な取り決めへの導入、段落全体の意味判断は未完。',
]

def args(fs):return [v(n) for n,_ in fs]
def slot(n):return k('eisgx',v('record'),'n p '+number_word(n)+' b',v('context'))

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+RESULTS.get(n,'a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eika',SETUP,both(k('eisgr',v('observer'),v('context')),k('ca',v('clock')),k('ci',v('unit')),k('va',v('frame')),k('eisdf',v('clock'),v('context')),k('eisgs',v('hand'),v('clock'),v('context')),k('zbv',v('frame'),v('origin'),v('context')),k('cb',v('observer'),v('origin'),v('frame')),k('cb',v('clock'),v('origin'),v('frame')),k('eisgf',v('clock'),v('origin'),v('frame'),v('context'))))
    text+=define('eikb',ARRIVAL,both(k('eika',*args(SETUP)),k('eisge',v('task'),v('event'),v('context')),*[k('zbd',v(n)) for n in ('event','departure','reception')],k('eisb5',v('signal'),v('frame'),v('context')),k('eisgu',*[v(n) for n in ('event','signal','departure','observer','frame','context')]),k('eisgv',*[v(n) for n in ('signal','departure','reception','observer','frame','context')]),k('eisca',*[v(n) for n in ('signal','departure','reception','frame','context')]),k('cb',v('reception'),v('origin'),v('frame'))))
    text+=define('eikc',ASSIGNMENT,both(k('eikb',*args(ARRIVAL)),k('zbd',v('display')),k('ba',v('reading')),k('eisgt',*[v(n) for n in ('display','hand','clock','reading','context')]),k('cb',v('display'),v('origin'),v('frame')),k('eisgm',v('reception'),v('display'),v('clock'),v('frame'),v('context')),*[k('ce',v('clock'),v(n),v('frame'),v('unit'),v('reading')) for n in ('display','reception')],k('eisg2',*[v(n) for n in ('observer','task','event','signal','reception','display','clock','frame','unit','reading','context')])) )
    text+=define('eikd',RECORD,both(k('eisgy',v('record'),v('task'),v('observer'),v('frame'),v('context')),k('eikc',v('task'),*args(SETUP),*[slot(n) for n in range(1,6)],k('eisgz',v('record'),v('clock'),v('unit'),v('context')))))
    selected=lambda:k('eisgw',v('task'),v('record'),v('observer'),v('frame'),v('context'))
    text+=define('eike',METHOD,both(k('eika',*args(SETUP)),k('eisg3',*args(METHOD[:-1]),'r[p eikd]',v('context')),q('g','record','a',selected()),q('f','record','a',op('y',selected(),k('eikd',*args(RECORD))))))
    text+=content('eikf',k('eike',*[k(n) for n in ('eisg7','eishe','eisha','eishb','eishc','eishd','ra','eishf','eirf')],v('point')))
    text+=define('eikg',[('reference','d'),('candidate','d')],both(k('eisg4',k('rd'),k('eisg7'),k('eishe'),k('eirf'),v('reference'),v('candidate')),'t[k eikf[]][v candidate]',k('eisg5',k('rd'),k('eisg7'),k('eishe'),k('eirf'),v('candidate'))))
    text+=content('eikh',q('g','candidate','d',k('eikg',v('point'),v('candidate'))))
    text+='d eiki[] f[j s[k eikh[]]].\n'
    text+=define('eikj',[],both(k('eir3',k('eishg'),k('rd'),k('eirf'),quote('eiki'),k('ri')),k('eisg6',k('eishg'),k('rd'),quote('eij5'),quote('eikh'),k('eirf'),k('ri')),k('ue',k('eisgq'),k('eishg'),k('ri')),op('u',op('e',k('eisgq'),k('eishg')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eikj',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='optional_origin_observer_reception_clock_assignment',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/clock-definition-scope-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
