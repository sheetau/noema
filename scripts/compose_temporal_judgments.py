"""Compose temporal judgments as accounts involving simultaneity relations."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_motion_time_description import ROOT,read,exists
from scripts.compose_material_relative_frame import define
from scripts.compose_kinematics_headings import SIM
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-motion-time-description.noema';PARENT_BASIS='data/motion-time-description-basis-v1.json'
FULL='examples/v014/einstein-temporal-judgments.noema';CORE='examples/v014/temporal-judgments-core.noema'
BASIS='data/temporal-judgments-basis-v1.json';ANNOTATIONS='data/temporal-judgments-identifiers-v1.json';INDEX=226
PRIMITIVES={
 'eisev':([('judgment','a'),('speaker','a'),('document','a'),('context','d')],'judgmentが、speakerがdocumentで「われわれの判断」として論じる、人が物理的な対象・出来事について行う判断の全範囲に属する。原文に列挙された文、著者本人の実際の発言、正しい判断、既に検査した例だけへ限定しない。判断は対象・評価条件・肯否を持つ内容として同定し、文字列の出現数や無関係な精神活動とは区別する。'),
 'eisew':([('judgment','a'),('document','a'),('context','d')],'judgmentの内容又は適用条件に、出来事への時刻付与・先後・持続などの時間的な規定が関わる。時間という語が綴られているかだけで判定せず、時間的な規定を取り去ると同じ判断にならないという関与である。判断の肯定・否定や真偽を条件にしない。'),
 'eisex':([('judgment','a'),('account','a'),('document','a'),('context','d')],'accountが、同じjudgmentの時間に関わる内容を何についての判断として理解するかを示す説明である。対象、肯否、量化、条件、時間的規定の役割を保持し、時間と無関係な部分まで捨てて別の主張にしない。単なる語の置換や一つの都合のよい例ではなく、元の判断の時間的内容の全体を解釈する。説明中の関係項目の範囲と内容は別に合成する。説明可能性を自動判定する機械的同義証明ではない。'),
 'eisey':([('account','a'),('part','a'),('context','d')],'partが、同じaccountで時間的内容を説明する際に用いる関係適用項目の全範囲に属する。成り立つ項目、肯定形、検査済み項目だけを後から選ばず、否定・比較・条件の中の適用もその作用範囲を保って含む。範囲の非空性と各項目の型は別に要求する。'),
 'eisez':([('part','a'),('first','a'),('second','a'),('frame','a'),('unit','a'),('relation',SIM),('context','d')],'partが、同じ二出来事firstとsecondに、同じ基準系・時間単位・文脈でrelationの閉じた関係を適用する判断の項目である。関係記述と五つの引数位置を保持し、別の出来事・系・単位を混ぜない。項目が何の関係について判断するかを指定する対応であり、relationをここで実行したり、肯定・否定・条件内の項目を全て真にしたりしない。項目の論理的位置はaccountで保持する。'),
 'eise2':([('agent','a'),('fact','i[e]'),('document','a'),('context','d')],'agentが同じdocumentの議論を適切に進めるために、factで記述された事情を考慮に入れなければならないという、当該論点での方法上の要請。単なる注意の実績、今後そうするという意図、法的義務、読者全員の心理状態ではない。事柄の対象・範囲・限定を推論に反映すべきことを意味し、実際に十分な考慮が完了したことは含意しない。要請の対象内容は引用し、その真理は別に保持する。'),
 'eise3':([], '固定原文einstein-1905:u0010[338,481)の第三文。時間の関わる全判断は同時的出来事についての判断であるという事情を考慮すべきことを述べる箇所。'),
}
MEANINGS={
 'eiiu':'一つの判断項目が、既存eihmの同時性関係を同じ二出来事・基準系・時間単位・文脈に適用する項目である。何を判断するかを指定し、出来事が実際に同時であることや判断の肯定を要求しない。',
 'eiiv':'同じ説明accountの時間的内容を構成する関係項目が少なくとも一つあり、その全てがeiiuの同時性についての項目である。空の説明や成功例の一部だけで済ませない。',
 'eiiw':'同じjudgmentの時間的内容を保持する説明が存在し、その同じ説明の全関係項目が同時性を扱うeiivを満たす。無関係な別判断に対する説明を取り替えない。',
 'eiix':'同じ論説でいうわれわれの全判断のうち、時間が関わる全判断についてeiiwを要求する内容。alleとimmerを例外なしの全称として保ち、全判断を一つの同時性の肯定文へ還元しない。',
 'eiiy':'eiixの事情の成立と、同じ内容を著者が議論で考慮しなければならないeise2の要請を結ぶ。要請だけで事情の内容を省かず、要請から実際の考慮完了を導かない。',
 'eiiz':'時間判断の一般的な性質と、その考慮の要請eiiyを主張するメッセージ。',
 'eii2':'同じ著者・論説へeiizを帰属し、時間の意味を先に明確にすべき前文からの本文順序を保持する。',
}
LIMITS=[
 'unsere Urteileは、物理的な時間を論じる人間の判断一般として読む。著者の既発表の文だけや成功した時刻測定だけへ狭めない。時間が関わることは語の出現ではなく内容上の関与である。',
 'immer Urteile über gleichzeitige Ereignisseは、時間に関わる判断内容を同時性の関係についての判断によって説明できるという読みを採る。全判断の対象出来事が同時であるという物理的な断言や、否定・先後・持続を捨てた同一の肯定文への置換にはしない。',
 '時刻付与や比較では、出来事と時計の表示などの同時性を判断することで時間的規定を与える。各判断を一つの出来事対に限定せず、説明が必要とする非空の全関係項目を保持する。個々の説明の意味保持と項目の完全な範囲は明示した意味規約の入力であり、自動的な翻訳アルゴリズムや全判断の決定手続きを主張しない。',
 '同時性の意味には既存eihmの同じ系・単位で有効かつ一意に付与された時刻の一致を再利用する。関係を引用することから実際の時計同期や時刻付与を実行せず、未付与を非同時と認定しない。全系で不変の絶対同時性も追加しない。',
 'Wir haben zu berücksichtigenは、その事情を考慮に入れなければならないという方法上の要請として読む。著者の論述上の声を保ち、人数、読者の現実の注意、考慮の完了、法的義務を加えない。',
 'u0010第三文の123非空白文字を扱う。第四文の列車・時計の引用例、脚注u0279の抽象化と不議論の留保、本文からの脚注参照、段落全体の意味判断は未完である。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    fields=[(n,'a') for n in ('first','second','frame','unit')]
    text+=define('eiiu',[('part','a'),('context','d')],exists(fields,k('eisez',v('part'),*[v(n) for n,_ in fields],'r[p eihm]',v('context'))))
    selected=lambda:k('eisey',v('account'),v('part'),v('context'))
    text+=define('eiiv',[('account','a'),('context','d')],both(q('g','part','a',selected()),q('f','part','a',op('y',selected(),k('eiiu',v('part'),v('context'))))))
    text+=define('eiiw',[('judgment','a'),('document','a'),('context','d')],q('g','account','a',both(k('eisex',v('judgment'),v('account'),v('document'),v('context')),k('eiiv',v('account'),v('context')))))
    text+=content('eiix',q('f','judgment','a',op('y',both(k('eisev',v('judgment'),k('rd'),k('eirf'),v('point')),k('eisew',v('judgment'),k('eirf'),v('point'))),k('eiiw',v('judgment'),k('eirf'),v('point')))))
    text+=content('eiiy',both('t[k eiix[]][v point]',k('eise2',k('rd'),quote('eiix'),k('eirf'),v('point'))))
    text+='d eiiz[] f[j s[k eiiy[]]].\n'
    text+=define('eii2',[],both(k('eir3',k('eise3'),k('rd'),k('eirf'),quote('eiiz'),k('ri')),k('ue',k('eiseu'),k('eise3'),k('ri')),op('u',op('e',k('eiseu'),k('eise3')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eii2',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='temporal_judgments_as_simultaneity_accounts_with_consideration_requirement',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/motion-time-description-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
