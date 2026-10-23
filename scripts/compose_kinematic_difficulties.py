"""Compose inadequate consideration as a foundational source of current difficulties."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_kinematic_foundation import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content,evaluate
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-kinematic-foundation.noema';PARENT_BASIS='data/kinematic-foundation-basis-v1.json'
FULL='examples/v014/einstein-kinematic-difficulties.noema';CORE='examples/v014/kinematic-difficulties-core.noema'
BASIS='data/kinematic-difficulties-basis-v1.json';ANNOTATIONS='data/kinematic-difficulties-identifiers-v1.json';INDEX=218
PRIMITIVES={
 'eisdm':([('practice','a'),('inquiry','a'),('fact','i[e]'),('reference','d')],'practiceがinquiryの理論的な記述・概念設定・推論において、factの事情をどのように取り扱い又は取り扱わずにいるかという知的実践のあり方である。同じ内容の対象・範囲を保ち、単なる言葉への言及や個人が心理的に知っていることとは区別する。完全な見落としから部分的な反映までを許すため、実際に注意を向けたという肯定条件は課さない。適切さ、事情の真理、困難への原因関係は別に要求する。'),
 'eisdn':([('practice','a'),('fact','i[e]'),('reference','d')],'同じpracticeがfactの事情を、対象の数量・意味・適用条件を取り違えずに記述し推論するために必要な範囲で十分に考慮している。事情を口にするだけでなく、その内容から必要になる区別・規約を概念設定や推論へ反映する。全ての知識・実務の完全性や数値化された注意量は要求しない。判断の基準は当該論点の課題であり、後に成功したという結果だけから十分と定めない。不明を不十分と判定せず、否定する場合にも取扱いと基準が明示される。'),
 'eisdo':([('difficulty','a'),('inquiry','a'),('reference','d')],'difficultyがinquiryの対象を整合した概念・数量・適用条件で記述し、説明や推論を進める際の支障・未解決問題である。単なる未知の値、肉体的な困苦、気分や語の難しさとは区別する。矛盾、指示規約の曖昧さ、記述間の不整合などを許すが、どの具体的問題かを原文にない列挙で限定しない。絶対に解けないことや、分野の全活動が不可能であることは要求しない。'),
 'eisdp':([('difficulty','a'),('inquiry','a'),('document','a'),('reference','d')],'同じdocumentの記述当時に、同じinquiryを進める研究がdifficultyに直面し、その解消が課題として残っている。研究分野が困難と戦うという言い方を、その概念的な仕事に対する支障と取組として解釈する。文字通りの軍事行動・敵意・特定の研究者の心理は要求しない。現在の読者や実行時刻を基準にせず、過去に解決済みの支障を当時の課題へ混ぜない。原因と未解決性は別関係で与える。'),
 'eisdq':([('practice','a'),('difficulty','a'),('inquiry','a'),('reference','d')],'同じinquiryにおけるpracticeのあり方が、difficultyを生じさせ又は持続させる基礎的な原因・説明の出所である。基本的な概念・数量・適用条件の扱いにある欠陥が、その後の記述や推論の支障につながるという根本の関係を指す。単なる同時発生、時間的な先行、軽微な寄与、著述順序と区別する。他の原因の併存や複合した原因を排除せず、あらゆる可能世界で必要十分という強い二値反実仮想を要求しない。植物の根という物体の同一視ではない。practiceの不十分さとdifficultyの範囲は別に合成する。'),
 'eisdr':([('difficulty','a'),('document','a'),('reference','d')],'difficultyが、このdocumentの論点で指される困難の全範囲に属する。原因が確認できた成功例だけを後から選ぶ一覧ではなく、論説の主題と時点で指定される範囲を保持する。世界のあらゆる問題や他分野の障害までを含めず、原文にない個別の問題名を補わない。複数性、分野への帰属、当時の未解決性、原因は別条件で要求する。'),
 'eisds':([], '固定原文einstein-1905:u0005[261,423)の第二文。同じ事情の不十分な考慮を、当時の動く物体の電気力学が直面する困難の根として述べる箇所。'),
}
MEANINGS={
 'eihf':'同じ研究分野で、前文の理論の主張の物理的指示関係eihaを取り扱う実践が、その同じ事情を十分に考慮していない。全く注意しない場合と一部だけ反映する場合を許し、単なる未知や語の不使用で代用しない。',
 'eihg':'同じ困難が同じ研究分野における概念的な支障であり、同じ論説の記述当時にその研究が直面する未解決の課題である。',
 'eihh':'同じ研究分野が既存eie6の動く物体の電気力学であり、論説が指す困難の範囲に異なる二つ以上が存在し、その全てが同じ分野・当時にeihgを満たす。',
 'eihi':'同じ実践・研究分野・判断点で不十分な考慮eihfと当時の困難群eihhを結び、その全困難に対して同じ実践が基礎的な原因であることを要求する。対象や原因を途中で交換しない。',
 'eihj':'前文の同じ事情eihaを保持し、その事情の不十分な考慮が当時の困難群の根であるという、同じ実践と研究分野の存在内容。事情自体が偽であるという主張ではない。',
 'eihk':'第二文の全内容eihjを主張するメッセージ。原因の診断を単なる可能性、質問、命令へ替えない。',
 'eihl':'第二文を同じ著者・論説へ帰属し、第一文に続く別の箇所として本文順序を保持する。',
}
LIMITS=[
 'dieses Umstandesは、第一文の理論の主張が剛体・時計・電磁過程の関係を扱う事情eihaを指すと読む。予定理論の完成、光速度の実証、第三者の別の見解へ参照を移さない。',
 'nicht genügende Berücksichtigungは必要な意味・数量・適用条件への反映の不足と読む。単なる知識の不在、発話回数や注意量の閾値とはせず、完全な見落としも部分的な考慮も許す。',
 'Wurzelは概念的な扱いの欠陥が支障を生む又は持続させる基礎的な原因と読む。軽微な寄与や相関に弱めず、唯一原因・全問題の必要十分条件・解消すれば必ず全て解決するという主張は加えない。',
 'gegenwärtigは論説の記述当時（1905年）へ結ぶ。困難と戦うという表現は当該研究が未解決の支障に直面し解消を課題とすることと読み、軍事的な出来事や特定人物の心理を補わない。',
 '複数の困難を論説の同じ範囲全体で扱う。具体的な問題名を発明せず、原因を説明できたものだけを量化範囲に選ばない。因果関係の歴史的な実証を、有限例や翻訳の通読によって証明したとはしない。',
 '第二文全体を記述する。二文全体の参照・理由・原因の接続を再読する段落判断は別記録で行う。',
]

def selected(d,point):return k('eisdr',d,k('eirf'),point)

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    fs=[('practice','a'),('inquiry','a'),('reference','d')]
    text+=define('eihf',fs,both(k('eisdm',v('practice'),v('inquiry'),quote('eiha'),v('reference')),op('u',k('eisdn',v('practice'),quote('eiha'),v('reference')))))
    text+=define('eihg',[('difficulty','a'),('inquiry','a'),('reference','d')],both(k('eisdo',v('difficulty'),v('inquiry'),v('reference')),k('eisdp',v('difficulty'),v('inquiry'),k('eirf'),v('reference'))))
    plural=q('g','left','a',q('g','right','a',both(op('u',op('e',v('left'),v('right'))),selected(v('left'),v('reference')),selected(v('right'),v('reference')))))
    every=q('f','difficulty','a',op('y',selected(v('difficulty'),v('reference')),k('eihg',v('difficulty'),v('inquiry'),v('reference'))))
    text+=define('eihh',[('inquiry','a'),('reference','d')],both(k('eie6',v('inquiry'),v('reference')),plural,every))
    roots=q('f','difficulty','a',op('y',selected(v('difficulty'),v('reference')),k('eisdq',v('practice'),v('difficulty'),v('inquiry'),v('reference'))))
    text+=define('eihi',fs,both(k('eihf',v('practice'),v('inquiry'),v('reference')),k('eihh',v('inquiry'),v('reference')),roots))
    text+=content('eihj',both(evaluate('eiha'),q('g','practice','a',q('g','inquiry','a',k('eihi',v('practice'),v('inquiry'),v('point'))))))
    text+='d eihk[] f[j s[k eihj[]]].\n'
    text+=define('eihl',[],both(k('eir3',k('eisds'),k('rd'),k('eirf'),quote('eihk'),k('ri')),k('ue',k('eisdl'),k('eisds'),k('ri')),op('u',op('e',k('eisdl'),k('eisds')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eihl',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='inadequate_consideration_as_foundational_cause',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/kinematic-foundation-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
