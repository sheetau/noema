"""Compose a substantial practical comparison and a forward reasoning reference."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_reception_position_dependence import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-reception-position-dependence.noema';PARENT_BASIS='data/reception-position-dependence-basis-v1.json'
FULL='examples/v014/einstein-practical-time-convention.noema';CORE='examples/v014/practical-time-convention-core.noema'
BASIS='data/practical-time-convention-basis-v1.json';ANNOTATIONS='data/practical-time-convention-identifiers-v1.json';INDEX=233
RULE='i[h[a a a h[b] c d] c]'
COMPARE=[(n,'a') for n in ('new','old','task','criterion','higher','lower','document')]+[('context','d')]
PRIMITIVES={
 'eishq':([], 'この論説のu0013からu0018へ進む考察で得る、同期した局所時計による時間的規定の方式。旧方式eisg7とは別の提案対象であり、規則と定義箇所はeishxで結ぶ。名前だけから実現済み・優秀・無矛盾とは認定しない。'),
 'eishr':([], '固定原文u0013の二地点の時計からu0018の同期時計と出来事の時刻の定義へ進む一続きの考察。その本文範囲を指す談話上の対象であり、内容全体の真偽入力ではない。'),
 'eishs':([], '固定原文einstein-1905:u0012[489,569)の第三文の箇所。'),
 'eisht':([], '同じ時間的評価の課題について、複数地点の出来事を共通の時刻規約で扱うための使いやすさ・適用のしやすさを比べる実用性の基準。費用や道徳的価値や理論の真理確率ではなく、前文の観測者位置依存の不都合を背景とする文脈上の基準。固定の数値重み・全評価項目での優越・最適性は補わない。'),
 'eishu':([(n,'a') for n in ('scheme','task','criterion','degree','document')]+[('context','d')], '同じ課題・文書・状況で、schemeの実用性をcriterionの共通の順序尺度のdegreeに位置付ける評価。degreeは質的な程度でよく、実測された数値・絶対単位・任意の好みとはしない。双方の評価基準と適用範囲を共有し、評価の成立と比較を分ける。'),
 'eishv':([(n,'a') for n in ('higher','lower','criterion')]+[('context','d')], 'criterionの同じ順序尺度でhigherがlowerより厳密に高い。反射的な以上・単なる相違と区別し、順序の向きと推移的な比較規約を固定する。この関係だけでは差の大きさを認めない。'),
 'eishw':([(n,'a') for n in ('higher','lower','criterion')]+[('context','d')], '同じcriterionで二程度の開きが文脈上顕著に大きいと認められるという程度差の基準。weitの強さを保持し、任意の小差へ弱めない。厳密な優越方向は別に要求し、数値差・比率・普遍的な閾値を原文へ追加しない。'),
 'eishx':([(n,'a') for n in ('convention','task')]+[('rule',RULE)]+[(n,'a') for n in ('definition','document')]+[('context','d')], 'conventionは同じtaskについて、definitionの箇所でruleを時間的な値の付与規則として採る規定である。ruleの引数と対象を保持する参照対応であり、任意の出来事への値の存在、実験済み、規則の全適用や処理系による証明を含意しない。定義箇所への前方参照も許す。'),
 'eishy':([(n,'a') for n in ('author','consideration','convention','task','document')]+[('context','d')], 'authorが同じtaskのconventionを定めるに至る手段としてconsiderationの考察を用いるという論述上の到達関係。考察の理由付けと規定の導入を結び、単に後で規定するという時間順序や、無関係な考察への言及に替えない。論説の展開をたどるwirを著者の声と読み、複数の実験者・読者の実行・形式的な演繹の完了を要求しない。'),
 'eishz':([(n,'a') for n in ('node','author','consideration','begin','end','document')]+[('context','d')], 'authorがnodeでconsiderationを、この後に続くbeginからendまでの考察として予告し指し示す談話上の前方参照。箇所は同じdocument内で、その順序を別に確認する。対象の引用・指示だけで考察中の全命題の真理を実行しない。'),
 'eish2':([], '固定原文einstein-1905:u0013の冒頭、点Aの時計とその近傍の局所的な時間的評価を導入する箇所。後続考察の始点であり、二地点の時計の段落全体を検査済みとする記号ではない。'),
}
MEANINGS={
 'eiks':'同じ課題・評価基準・文書・状況で二方式の程度を結び、新方式の程度が厳密に高く、かつ差が顕著に大きい。程度の差と方向を別に要求する。',
 'eikt':'二方式についてeiksを満たす同じ二程度が存在する。片方の評価や別基準の差だけで成立させず、具体的な数値閾値を補わない。',
 'eiku':'新規定eishqを同じ課題eisheと既存の時刻付与規則qu・定義箇所rjへ結ぶ。同期時計の規則を引用して参照し、その全適用をこの導入内で評価しない。',
 'eikv':'同じ新規定と旧方式を同じ課題・基準で比較し、その新規定へ著者が後続の同じ考察を通じて至るという第三文の内容。',
 'eikw':'第三文eikvを主張するメッセージ。単なる希望や問いへ弱めず、後続の考察の全命題の証明完了を補わない。',
 'eikx':'第三文を同じ著者・論説へ帰属し、第二文からの順序と、次段落から時刻定義rjまでの考察への前方参照を保つ。',
}
LIMITS=[
 'Festsetzungを同期した局所時計で時刻を付与する規定への予告と読み、既存のquとその定義箇所rjへ参照を固定する。同期の全導出やu0013以降の全内容はこの一文へ取り込まない。',
 'praktischerの比較先を前二文の受信方式eisg7、課題を同じeisheと読む。共通規約で複数地点の出来事を扱う実用性として解釈し、最良・唯一・全ての面での優越・絶対的な客観時刻とはしない。',
 'weitを同じ質的な程度尺度で顕著に大きい開きとして保持する。両方式の程度の帰属、厳密な優越、大きな差を別々に結び、任意の微小な改善や固定数値へ替えない。評価尺度と大きさの基準は明示した意味規約付き入力である。',
 'gelangen wir durchを著者の論述で同じ考察を手段として規定へ至る関係と読む。folgendeはu0013冒頭からu0018の時刻付与定義までの考察への前方参照。そこに含む仮定や定義を全て実証済みとする帰属ではない。',
 '第三文71非空白文字を記述する。第一・第二文の固定判断は保持し、全三文の意味判断は別の通読記録で行う。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    values=lambda ns:[v(n) for n in ns]
    text+=define('eiks',COMPARE,both(k('eishu',*values(('new','task','criterion','higher','document','context'))),k('eishu',*values(('old','task','criterion','lower','document','context'))),k('eishv',*values(('higher','lower','criterion','context'))),k('eishw',*values(('higher','lower','criterion','context'))),op('u',op('e',v('higher'),v('lower')))))
    fields=[f for f in COMPARE if f[0] not in ('higher','lower')]
    text+=define('eikt',fields,q('g','higher','a',q('g','lower','a',k('eiks',*values(n for n,_ in COMPARE)))))
    text+=content('eiku',k('eishx',k('eishq'),k('eishe'),'r[p qu]',k('rj'),k('eirf'),v('point')))
    text+=content('eikv',both('t[k eiku[]][v point]',k('eikt',k('eishq'),k('eisg7'),k('eishe'),k('eisht'),k('eirf'),v('point')),k('eishy',k('rd'),k('eishr'),k('eishq'),k('eishe'),k('eirf'),v('point'))))
    text+='d eikw[] f[j s[k eikv[]]].\n'
    text+=define('eikx',[],both(k('eir3',k('eishs'),k('rd'),k('eirf'),quote('eikw'),k('ri')),k('eishz',k('eishs'),k('rd'),k('eishr'),k('eish2'),k('rj'),k('eirf'),k('ri')),k('ue',k('eishp'),k('eishs'),k('ri')),k('ue',k('eishs'),k('eish2'),k('ri')),k('ue',k('eish2'),k('rj'),k('ri')),op('u',op('e',k('eishp'),k('eishs'))),op('u',op('e',k('eishs'),k('eish2'))),op('u',op('e',k('eish2'),k('rj')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eikx',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='practical_time_convention_comparison_and_forward_reference',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/reception-position-dependence-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
