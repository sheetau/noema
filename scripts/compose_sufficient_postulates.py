"""Compose sufficiency of the same postulates for a qualified theory development."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_two_postulates import ROOT,read,quote
from scripts.compose_material_body_motion import FIELDS as BODY
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-two-postulates.noema';PARENT_BASIS='data/two-postulates-basis-v1.json'
FULL='examples/v014/einstein-sufficient-postulates.noema';CORE='examples/v014/sufficient-postulates-core.noema'
BASIS='data/sufficient-postulates-basis-v1.json';ANNOTATIONS='data/sufficient-postulates-identifiers-v1.json';INDEX=215
REST='i[h['+' '.join(t for _,t in BODY)+'] c]'
PRIMITIVES={
 'eiscm':([('theory','a'),('inquiry','a'),('reference','d')],'theoryがinquiryの研究対象を記述・説明する法則と概念の体系であるという対応。対象の同一性、法則の適用範囲、量と記号の解釈が定められた非空の体系を指し、単なる主題名や無関係な命題集とは区別する。構成可能な理論の候補も個体として扱え、既に出版・実証されたこと、真理、単純さ、無矛盾をこの対応だけで要求しない。'),
 'eiscn':([('basis','a'),('source','a'),('rest',REST),('reference','d')],'basisがsourceの理論を、restで指定する物体の基準系に対する静止の範囲で基礎として用いるための法則・概念・数量規約を保持する。閉じたrest型は物体・全物質点・全区間・系・単位を同じ意味で指定し、当該範囲の必要な法則を都合よく抜粋しない。ここでの物体は巨視的に記述する物質的な物体であり、静止を微視的熱運動の全消滅としない。静止物体の場合にも電磁場や電流の時間変化を許し、静電気・静磁気だけや絶対静止へ理論を狭めない。範囲指定の引用は実在する静止物体の存在や全実数履歴をその場で評価する要求ではない。'),
 'eisco':([('route','a'),('basis','a'),('theory','a'),('reference','d')],'routeが、同じbasisの法則・数量規約と明示した追加の物理的前提を用いてtheoryの全主張・適用規約へ到達できる、論理的・数学的に許容される理論構成の方法である。単に前提と結論が共に真であること、名札、願望、循環した根拠付けとは区別する。利用する追加前提はeiscpの全範囲に現れ、隠れた独立の物理仮説を認めない。定義・数学的操作や既定の推論規則の使用は許す。方法の可能性を述べ、著者による実行・記述・実験・計算器による証明の完了は要求しない。どの前提で足りるかと到達先の性質は別に合成する。'),
 'eiscp':([('premise','a'),('route','a'),('reference','d')],'同じrouteに供給する追加の物理的前提の全範囲にpremiseが属する。基礎理論に既にある法則や定義・数学的規則とは分け、経路が実際に必要とする独立の物理仮定を隠さない。供給された前提は論理的に冗長であってもよく、全てが必要不可欠だとは要求しない。成功した前提だけを選んだ標本や、単に名称が二つあるという一覧ではない。'),
 'eiscq':([('premise','a'),('claim','i[e]'),('reference','d')],'premiseという前提記録が同じ閉じたclaimの内容を仮定として供給するという内容対応。異なる内容が同じ真偽値を持つだけでは一致とせず、作用範囲・対象・量化・留保を保つ。前提の引用からclaimの現実での真理や実証を要求しない。'),
 'eiscr':([('theory','a'),('claim','a'),('reference','d')],'同じtheoryの意味規約と採用した推論規則に従う全ての主張・論理的帰結の範囲にclaimの内容が属する。原理の有限一覧、既に人が導出した結果、検査済み標本だけに狭めない。各claimは対象・量・評価条件を固定した命題内容を持ち、異なる系の値を無条件に同一視しない。未調査の帰結を範囲から除外して無矛盾と扱わず、全域の帰属が不明なら判断は不明である。'),
 'eiscs':([('first','a'),('second','a'),('reference','d')],'firstとsecondが、同じ対象・時点・条件・量と記号の解釈の下で、一方が他方の論理的否定となる命題内容を持つ。単なる語形の反対、異なる系での座標値の差、異なる条件下での結論を矛盾としない。順序を交換しても同じ対立であり、理論がこれらの内容を主張するかは別関係で与える。'),
 'eisct':([('theory','a'),('scope','a'),('reference','d')],'scopeの研究上の説明基準に照らし、theoryの基本概念・独立の原理・個別の場合分けが少なく、同じ共通の規約で対象を扱えるという単純さの評価が成立する。対象の範囲と説明能力を落として短くしただけのものを単純と認定しない。文の字数、処理速度、唯一の最小公理系、数値化した複雑度の閾値とは区別する。比較尺度は論説の論点に依存するという文脈的な読みを採り、特定の競合理論や数値を原文へ補わない。真理や無矛盾とは別に評価する。'),
 'eiscu':([], '固定原文einstein-1905:u0004[890,1081)の第三文。同じ二前提を用い、静止物体のMaxwell理論を基礎として、単純で無矛盾な動く物体の電気力学へ至る十分性を述べる箇所。'),
}
MEANINGS={
 'eige':'同じtheoryが、動く物体の電気力学という既存eie6の主題に属するinquiryを記述する理論体系である。主題と理論個体を無条件に同一視せず、同じ研究対象への対応を存在量化で結ぶ。',
 'eigf':'basisが同じMaxwell理論eisaxの静止物体の場合を基礎とする。全物質点・全区間による既存eiahの静止を閉じた型として渡し、絶対静止や静的な場へ替えない。',
 'eigg':'同じ理論の全主張・全論理的帰結に、同じ条件で否定し合う二内容が存在しないという無矛盾。明示された公理だけや検査済み結果だけの検査へ縮めない。',
 'eigh':'同じrouteに異なる二つの前提記録を供給し、それぞれをfirst・secondの内容へ結ぶ。全追加前提はこの二内容のいずれかであり、第三の物理仮定を隠さない。二前提がともに必要不可欠又は最小であるとは述べない。',
 'eigi':'同じ構成方法・基礎・到達先・判断点について、許容される構成方法、静止物体のMaxwell理論を基礎とすること、動く物体の電気力学という対象、単純さ、無矛盾、同じ二内容eifj/eify以外に追加物理前提を要しないことを結ぶ。',
 'eigj':'eigiを満たす同じ方法・基礎・理論が存在するという、二前提から所定の理論へ到達する十分性の内容。存在するのは構成可能性の証人であり、著者が既に全導出を終えた事実ではない。',
 'eigk':'二前提の十分性eigjを主張するメッセージ。単なる願望、問い、二原理の現在の真理の主張へ替えない。',
 'eigl':'第三文のeigkを同じ著者・論説へ帰属し、第二文の二仮定の導入に続く別箇所として本文順序を保持する。',
}
LIMITS=[
 'genügenは、指定の基礎理論と二前提を与えれば、記述した性質の理論へ至る許容方法があるという構成可能性の読みを採る。二前提の必要性・最小性、唯一の構成法、導出や実証の完了を補わない。',
 '静止物体は同じ物体の巨視的な全物質点が基準系に対して全区間で静止する場合とする。場・電流まで時間一定とせず、全微視的運動の消滅や絶対静止も要求しない。',
 'einfachは同じ説明範囲を保って少数の共通原理・概念・場合分けで扱えるという文脈的な評価とする。数値尺度や特定の競合理論を原文へ追加しない。',
 'widerspruchsfreiは同じ意味規約の下で全論理的帰結に否定し合う内容がないという内的無矛盾とする。理論の物理的真理・全ての問題の解決・処理系による全帰結検査とは別である。',
 '方法の許容性、帰結への帰属、論理的否定、文脈的単純さは意味を明示した基礎入力である。一般的な理論生成器や無矛盾決定手続きをここで実装したとはしない。',
 '第三文全体を記述する。第四文の光エーテル不要と、第二段落四文全体の通読判断は残る。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    fields=[('theory','a'),('reference','d')]
    text+=define('eige',fields,q('g','inquiry','a',both(k('eiscm',v('theory'),v('inquiry'),v('reference')),k('eie6',v('inquiry'),v('reference')))))
    text+=define('eigf',[('basis','a'),('reference','d')],k('eiscn',v('basis'),k('eisax'),'r[p eiah]',v('reference')))
    text+=define('eigg',fields,op('u',q('g','first','a',q('g','second','a',both(k('eiscr',v('theory'),v('first'),v('reference')),k('eiscr',v('theory'),v('second'),v('reference')),k('eiscs',v('first'),v('second'),v('reference')))))))
    selected=lambda p:k('eiscp',p,v('route'),v('reference'))
    matches=lambda p,c:k('eiscq',p,v(c),v('reference'))
    distinct=op('u',op('e',v('left'),v('right')))
    witnesses=q('g','left','a',q('g','right','a',both(distinct,selected(v('left')),selected(v('right')),matches(v('left'),'first'),matches(v('right'),'second'))))
    exhaustive=q('f','premise','a',op('y',selected(v('premise')),op('x',matches(v('premise'),'first'),matches(v('premise'),'second'))))
    text+=define('eigh',[('route','a'),('first','i[e]'),('second','i[e]'),('reference','d')],both(witnesses,exhaustive))
    fields=[('route','a'),('basis','a'),('theory','a'),('reference','d')]
    text+=define('eigi',fields,both(k('eisco',v('route'),v('basis'),v('theory'),v('reference')),k('eigf',v('basis'),v('reference')),k('eige',v('theory'),v('reference')),k('eigg',v('theory'),v('reference')),k('eisct',v('theory'),k('eirf'),v('reference')),k('eigh',v('route'),quote('eifj'),quote('eify'),v('reference'))))
    body=k('eigi',v('route'),v('basis'),v('theory'),v('point'))
    for name in ('theory','basis','route'):body=q('g',name,'a',body)
    text+=content('eigj',body)
    text+='d eigk[] f[j s[k eigj[]]].\n'
    text+=define('eigl',[],both(k('eir3',k('eiscu'),k('rd'),k('eirf'),quote('eigk'),k('ri')),k('ue',k('eiscl'),k('eiscu'),k('ri')),op('u',op('e',k('eiscl'),k('eiscu')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='eigl',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='two_postulates_sufficient_for_simple_consistent_moving_body_theory',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/two-postulates-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
