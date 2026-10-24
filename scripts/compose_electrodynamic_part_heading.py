"""Attach the second numbered part to the existing electrodynamic topic."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_kinematic_transition_claim import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_limits import call as k,op,both

PARENT='examples/v014/einstein-kinematic-transition-claim.noema'
PARENT_BASIS='data/kinematic-transition-claim-basis-v1.json'
FULL='examples/v014/einstein-electrodynamic-part-heading.noema'
CORE='examples/v014/electrodynamic-part-heading-core.noema'
BASIS='data/electrodynamic-part-heading-basis-v1.json'
ANNOTATIONS='data/electrodynamic-part-heading-identifiers-v1.json'
INDEX=356
PRIMITIVES={
 'eispb':'この論説の第二部という文書区分。固定原文u0151の部見出しから記事末までを案内し、第六節から第十節を下位に持つ。末尾にまとめられた注は本文中の参照位置へ付随させ、一覧順だけで第一部への注を第二部へ移さない。部番号・階層・電気力学の主題は合成で指定し、区分名だけで内容を代用しない。',
 'eispc':'固定原文einstein-1905:u0151全体の第二部見出しの箇所。区分eispb、前の移行znj、次の第六節見出しu0152とは別の箇所である。',
}
MEANINGS={
 'ejsi':'第一部eisdxとは別の第二部eispbが同じ論説eirfに直接属する深さ1・表示番号2の区分であり、見出しeispcが電気力学eie5の主題を案内する。直前の応用への移行znjからの本文順序と箇所の区別を保つ。見出しから物理的法則の真理や応用課題の達成を要求しない。',
}
LIMITS=[
 'u0151全文II. Elektrodynamischer Teil.を原刊907頁で照合する。ローマ数字IIを表示番号2、Teilを部という階層深さ1へ結ぶ。字形と中央配置は固定原文・画像に残し、物理量や追加の命題にはしない。',
 '第二部は同じ論説に直接属し、第一部とは別の区分である。第六節から第十節は下位節であり、部が変わっても節番号を1へ戻さない。部見出しと節見出しを一つの箇所や同じ階層へまとめない。',
 '主題は既存eie5を用い、電荷輸送eibf・電気作用eibs・磁気作用eicoに基づく電気力学の研究領域へ結ぶ。静電気だけ、Maxwellの特定理論だけ、磁石と導体の一例だけへ狭めない。',
 '見出しは区分全体を案内し、後続各文が電気力学という語を含むことや全分野を網羅することは要求しない。末尾の謝辞・場所日付・受付表示を物理的な主張へ変換せず、記事末までという文書区分の範囲と主題を述べる役割を区別する。',
 '固定転記は注u0279–u0282を末尾に集めている。単なる配列順で全てを第二部に含めず、注は本文の参照位置に従って読む。この見出しの意味確認から下位節・注の内容の確認完了は導かない。',
 '同じ著者の論説内で、u0150後半の移行znjに続く見出しとして記述する。既存eisdv/eisdwの見出しの役割を使い、本文の断言や目標達成の発話へ変更しない。',
 '有限対照は部番号・深さ・親・主題・順序・同一性と未知入力の拒否を検査する。引用された物理的な主題をその場で実行せず、全物理領域の真理や原文との意味同値を自動証明しない。u0152以降は残る。',
]


def definitions():
    text='r eispb[] a.\nr eispc[] a.\n'
    heading=k('eihq',k('eispc'),k('eispb'),k('eirf'),k('eirf'),'n p b b','n p c b','r[p eie5]',k('ri'))
    text+=define('ejsi',[],both(heading,k('ue',k('znj'),k('eispc'),k('ri')),op('u',op('e',k('znj'),k('eispc'))),op('u',op('e',k('eispb'),k('eisdx')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX
    doc=deepcopy(old);doc['statements']=[]
    assert not (set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions())
    doc['statements']=deepcopy(old['statements'])+[dict(kind='assert',body=dict(kind='call',symbol='ejsi',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=PRIMITIVES[d['name']]) for d in added if d['kind']=='primitive'}
    basis=dict(status='second_part_with_existing_electrodynamic_topic',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/kinematic-transition-claim-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
