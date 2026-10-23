"""Compose a tentative appearance of solving time-definition difficulties."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_local_simultaneity_note import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-local-simultaneity-note.noema';PARENT_BASIS='data/local-simultaneity-note-basis-v1.json'
FULL='examples/v014/einstein-clock-definition-proposal.noema';CORE='examples/v014/clock-definition-proposal-core.noema'
BASIS='data/clock-definition-proposal-basis-v1.json';ANNOTATIONS='data/clock-definition-proposal-identifiers-v1.json';INDEX=229
BASE=[(n,'a') for n in ('speaker','clock','hand','frame','unit')]+[('context','d')]
INDICATION=BASE+[('display','a'),('reading',R)]
RULE='i[h['+' '.join(t for _,t in INDICATION)+'] c]'
PROPOSAL=[(n,'a') for n in ('proposal','speaker','task','clock','hand','frame','unit','document')]+[('context','d')]
PRIMITIVES={
 'eisfw':([('task','a'),('document','a'),('context','d')],'taskは同じdocumentで物理的な時間の意味を定める課題である。出来事に何を時刻として与え、どの出来事を同時又は先後として扱うかという適用規約を明らかにする仕事を指す。単なる文字列Zeit、経過時間一個の計算、時計の購入、形而上学上の全問題の解決へ替えない。定義の仕事であることは既存eisduとも結ぶ。'),
 'eisfx':(PROPOSAL[:-1]+[('rule',RULE),('context','d')],'proposalはspeakerがtaskの時間という概念を定義するため、その代わりに同じclockの小さい針handの位置を用いるという規則の案である。ruleはその針が同じframeとunitで示す位置・時刻表示の対応を記述する閉じた関係型であり、同じ対象の指示を保持して時間値として用いる。引用符はこの二つの定義上の表現を取り上げる働きと読み、語の綴りだけの置換、針という物体そのものと時間の同一視、別人の時計への交換ではない。この規則の提示とその十分性・実際の使用成功は別であり、全出来事に値が付くとはここでは要求しない。'),
 'eisfy':([('difficulty','a'),('task','a'),('document','a'),('reference','d')],'difficultyは同じtaskの時間の定義を確定する際の困難である。何を時刻値とするか、異なる出来事にどう一貫して対応させるか等の未確定・曖昧・不足のために規約を満たせない論点を指す。指定された課題に属する困難の全範囲をreferenceで固定し、後で解決できたものだけを選ばず、単なる精神的な苦痛や実機の故障に限定しない。未知の範囲を空集合とはしない。'),
 'eisfz':([('proposal','a'),('difficulty','a'),('document','a'),('reference','d'),('result','d')],'referenceで同じdifficultyとして残っていた規約上の障害が、proposalの規則を採用することによってresultでは取り除かれるという手段と結果の関係。無関係な方法で解決したこと、単なる時間的後続、困難を論じないことへ替えない。個々の論点と採用案を保持し、他の全困難の解決や現実での実施はこの一関係から導かない。'),
 'eisf2':([('proposal','a'),('task','a'),('document','a'),('reference','d'),('result','d')],'同じproposalをtaskの定義として採用することをreferenceから考えたとき、resultがその採用によって可能な結果状況に属する。対象・課題・規則の指示を保ち、成功結果だけを選別せず、実際の採用済みやどの結果でも成功する制御能力とは区別する。成功する結果の存在は合成側で別に要求する。'),
 'eisf3':([('claim','i[e]'),('document','a'),('reference','d'),('perspective','d')],'同じdocumentのreferenceでclaimを考えるとき、perspectiveが議論上可能な初期の見方に属するという留保付きの導入。現実に著者がその見方を信じたこと、確実にそう見えること、任意の論理的可能世界とは区別する。claimがその見方でどう見えるかをこの関係へ先取りせず、同じ内容と対象を固定した候補だけを与える。'),
 'eisf4':([('claim','i[e]'),('document','a'),('perspective','d'),('candidate','d')],'perspectiveから同じclaimがどう見えるかを、その見方で利用できる情報に沿って評価するcandidateの全範囲。claimを真にする状況だけを選ばず、同じ対象と論点を保持する。非空性と全候補における内容の成立は合成側で要求する。現実の真理、信念の確信度、実際の採用の可能な結果範囲とは別の見かけの評価範囲である。'),
 'eisf5':([], 'u0011で検討する、時間の代わりに自分の時計の短針の位置を用いる同じ定義案への参照。内容はeisfxと合成定義で指定し、名称だけで解決を主張しない。'),
 'eisf6':([], 'u0011で対象とする物理的時間の定義の同じ課題。課題の意味と困難の範囲はeisfw・eisdu・eisfyで保持する。'),
 'eisf7':([], 'u0011のmeiner Uhrが指す、定義案を考える著者の自分の時計。先行例と同じ第一人称の声を保つが、列車到着の特定の時計個体や7時表示と同一であることを補わない。'),
 'eisga':([], 'u0011で同じ自分の時計に属する短針の指示対象。時針という役割をeise7で要求し、単なる小さい棒としない。'),
 'eisgb':([], 'u0011の同じ時計の短針の位置を時刻表示として解釈する時間単位。既存ciと時計の校正による読みへ結ぶ。7という特定の数値・日付・午前午後を追加しない。'),
 'eisgc':([], '固定原文einstein-1905:u0011[0,200)の第一文の箇所。時計の短針の位置を用いれば全ての定義上の困難を克服できるように思えるという留保を述べる。'),
}
MEANINGS={
 'eijh':'同じ話者が自分の時計として用いる同じclock、その時針hand、系frame、時間単位unitと校正を結ぶ。列車・7時・時計世界線全体の静止を要求しない。',
 'eiji':'eijhの同じ時計の短針が有効な実数readingに対応する位置を示すdisplayと、その同じ出来事の同じ時計・系・単位での読みを結ぶ。全実数の値域を有限標本へ縮めず、時針だけで日付や周期回数を復元しない。',
 'eijj':'同じ時間定義の課題と、自分の時計の短針の位置を時間の代わりに用いる同じproposalを結ぶ。eijiの関係型を規則として引用し、任意の出来事で既に実行できたとは主張しない。',
 'eijk':'referenceで同じ時間定義に属する困難が存在し、その全てが同じproposalの採用によって同じresultで克服される。困難ごとに別の結果を選ばず、成功した論点だけを範囲へ入れない。',
 'eijl':'同じproposalを同じtaskへ採用する可能な結果があり、その結果に同じ定義案eijjと全困難の克服eijkが成立する。現実の解決や全結果での成功保証とは別の可能性。',
 'eijm':'著者の同じ時計・短針・時間尺度・系と同じ課題・定義案についてeijlを述べる閉じた内容。後で見かけの各候補で評価する対象を固定する。',
 'eijn':'同じeijmの見かけの評価候補が非空で、その全てでeijmが成立する。実際のreferenceでの成功を要求しない。',
 'eijo':'同じeijmについて議論上可能な初期の見方があり、その見方でeijnの意味で解決可能に見えるという留保付き内容。見かけの候補と採用結果を分ける。',
 'eijp':'留保付きの第一文eijoを主張するメッセージ。中の全困難の実際の克服を無条件に主張しない。',
 'eijq':'同じ著者・論説へeijpを帰属し、本文の直前の列車例から順序を結ぶ。別単位の脚注を本文中の物理的又は時間的な前提へ替えない。',
}
LIMITS=[
 '第一人称は著者が検討する自分の時計を指す。先行例と声と系を共有するが、特定の列車・7時・時計個体の同一性を補わない。',
 '時間と短針の位置を定義上の表現として取り上げる引用と読む。位置は校正された指示関係であり、語の綴りや針という物体そのものではない。時針だけから日付・周期回数・遠隔の時刻を復元したとはしない。',
 'könnte scheinenは、議論上可能な初期の見方があり、その非空の見かけの候補全てで内容が成立するという控えた導入として読む。könntenはその中で同じ定義案の採用による成功結果の可能性として別に保持する。見かけが必ず偽であるとも主張しない。',
 'alleの範囲は同じ時間定義の困難全てで、解決済みの部分集合に限定しない。複数形は困難の存在として保持し、原文にない最低件数は指定しない。同じ一つの採用結果で全てを克服する読みを採る。',
 '概念の定義案、論点の範囲、手段による克服、可能な採用結果と見かけの候補は意味規約を持つ入力。有限モデルはその結合と量化を点検し、物理的な定義の十分性や任意自然言語の自動変換を証明しない。',
 'u0011第一文172非空白文字を対象とする。第二文の局所に限った十分性、遠隔の二課題とその同等性、段落全体の意味判断は未完。',
]

def args(fs,context=None):return [v(context if n=='context' and context else n) for n,_ in fs]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    text+=define('eijh',BASE,both(k('ca',v('clock')),k('ci',v('unit')),k('va',v('frame')),k('eisdf',v('clock'),v('context')),k('eise6',v('clock'),v('speaker'),v('context')),k('eise7',v('hand'),v('clock'),v('context'))))
    text+=define('eiji',INDICATION,both(k('eijh',*args(BASE)),k('ba',v('reading')),k('eisfc',v('display'),v('hand'),v('clock'),v('reading'),v('context')),k('ce',v('clock'),v('display'),v('frame'),v('unit'),v('reading'))))
    text+=define('eijj',PROPOSAL,both(k('eijh',*args(BASE)),k('eisdu',v('task'),v('context')),k('eisfw',v('task'),v('document'),v('context')),k('eisfx',*args(PROPOSAL[:-1]),'r[p eiji]',v('context'))))
    scope=lambda:k('eisfy',v('difficulty'),v('task'),v('document'),v('reference'))
    fields=[(n,'a') for n in ('proposal','task','document')]+[('reference','d'),('result','d')]
    text+=define('eijk',fields,both(q('g','difficulty','a',scope()),q('f','difficulty','a',op('y',scope(),k('eisfz',v('proposal'),v('difficulty'),v('document'),v('reference'),v('result'))))))
    text+=define('eijl',PROPOSAL[:-1]+[('reference','d')],q('g','result','d',both(k('eisf2',v('proposal'),v('task'),v('document'),v('reference'),v('result')),k('eijj',*args(PROPOSAL,'result')),k('eijk',v('proposal'),v('task'),v('document'),v('reference'),v('result')))))
    text+=content('eijm',k('eijl',*[k(n) for n in ('eisf5','rd','eisf6','eisf7','eisga','ra','eisgb','eirf')],v('point')))
    candidates=lambda:k('eisf4',quote('eijm'),v('document'),v('perspective'),v('candidate'))
    text+=define('eijn',[('document','a'),('perspective','d')],both(q('g','candidate','d',candidates()),q('f','candidate','d',op('y',candidates(),'t[k eijm[]][v candidate]'))))
    text+=content('eijo',q('g','perspective','d',both(k('eisf3',quote('eijm'),k('eirf'),v('point'),v('perspective')),k('eijn',k('eirf'),v('perspective')))))
    text+='d eijp[] f[j s[k eijo[]]].\n'
    text+=define('eijq',[],both(k('eir3',k('eisgc'),k('rd'),k('eirf'),quote('eijp'),k('ri')),k('ue',k('eisfm'),k('eisgc'),k('ri')),op('u',op('e',k('eisfm'),k('eisgc')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eijq',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='tentative_clock_hand_definition_proposal_and_possible_all_difficulty_resolution',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/local-simultaneity-note-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
