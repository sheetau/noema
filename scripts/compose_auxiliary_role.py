"""Compose the exclusive auxiliary role and its theoretical introduction reason."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_vacuum_field_domain import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_relativity_conjecture import content
from scripts.compose_two_postulates import quote
from scripts.compose_electromotive_wording import DYNAMIC,POINT
from scripts.compose_limits import v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-physical-field-dependence.noema';PARENT_BASIS='data/physical-field-dependence-basis-v1.json'
FULL='examples/v014/einstein-auxiliary-role.noema';CORE='examples/v014/auxiliary-role-core.noema'
BASIS='data/auxiliary-role-basis-v1.json';ANNOTATIONS='data/auxiliary-role-identifiers-v1.json';INDICES=[171,172]
ROLE_CODE='i[h['+POINT+' d] c]'
CONSTRUCTION_CODE='i[h['+DYNAMIC+' '+POINT+' '+POINT+' '+POINT+'] '+POINT+']'
CONCEPT=[('theory','a'),('concept','a'),('context','d')]
USE=CONCEPT[:2]+[('use','a')]+CONCEPT[2:]
PRIMITIVES={
 'eisqz':([('concept','a'),('expression','a'),('role',ROLE_CODE),('context','d')], '同じ状況でexpressionが指定する表現がconceptを指し、その概念の値と物理的な役割を閉じたroleで解釈する。表現という対象と概念という対象を区別し、同じ語の別義へ交換しない。roleは値と状況を受け取り、対象・系・単位・作用を規定する。引用した規則の自動実行や物理法則の真理を含意しない。'),
 'eisq2':(USE, '同じtheoryにおけるconceptの物理的記述又は説明を構成する役割の一件がuseである。法則・定義・予測・説明に寄与する使用を、独立な量や仮定としての採用も含めて全規約から数える。置換に成功した使用だけへ範囲を狭めない。語の綴りへの言及、他説を紹介するだけの引用は数えず、未調査を不使用と扱わない。使用の形式と置換の成否は別関係である。'),
 'eisq3':(USE[:3]+[('construction',CONSTRUCTION_CODE)]+USE[3:], '同じtheory・concept・useで、当該概念が担う全ての箇所を、既存の量を引数にする閉じたconstructionで定義に従って展開できる。各引数は当該使用と同じ対象・過程・出来事・系・単位の量へ結び、その使用の物理的な内容と説明上の役割を保つ。値を別途自由に与える独立入力又は追加の物理仮定はこの展開で残さない。規則の型は動的応答・四座標・基準三成分・三速度から三成分への構成であり、特定の演算や特定の概念は規約に埋め込まない。全理論の保存拡張定理や現実の実験実施を要求する関係ではない。'),
 'eisq4':([('theory','a'),('concept','a'),('grounds','i[h[a d] c]'),('conclusion','i[h[a a d] c]'),('context','d')], '同じtheoryとcontextでgrounds(theory,context)という事情が、conclusion(theory,concept,context)という事柄を説明する理由として位置付けられる。理論上の理由の関係であり、単なる両命題の併記・論理含意、必要十分条件、歴史上の心理的な因果とは区別する。根拠・結論は閉じた型として固定し、同じ理論と対象への適用を保つ。両命題が成立するという内容は別に合成する。'),
}
MEANINGS={
 'ejzt':'同じ理論で導入された概念を、第一項の引用語eisqsと、その追加寄与の物理的役割ejygへ結ぶ。表現を概念そのものと取り違えず、近似式の真理を語の意味へ混ぜない。',
 'ejzu':'同じ理論・概念の構成的な使用が少なくとも一件あり、全ての使用で既存量からの残差ejx4への定義展開が成立する。使用範囲を成功例だけに狭めず、補助的な役割だけというnurを全称条件として保持する。',
 'ejzv':'同じ論説で展開した理論eisqwについて、同じ概念の導入・意味ejztと補助的な役割だけというejzuを結ぶ主節の内容。',
 'ejzw':'主節と同じ概念証人を保ち、同じ理論の系依存性ejzoを述べ、その事情が同じ概念の理論導入eiscwを説明する理由だと結ぶ第二文全体の内容。',
 'ejzx':'補助的な役割だけという主節を同じ著者の主張として提示する。',
 'ejzy':'主節の提示ejzxを述べるメッセージ。',
 'ejzz':'主節を同じ著者・論説へ帰属し、先に構成した系依存性の内容に続けて本文へ接続する。原文の語順を文番号だけで代用しない。',
 'ejz2':'主節・導入理由・系依存性を結んだ第二文全体ejzwを同じ著者が述べ、同じ内容を明白だと提示するMan siehtの役割をzdgで保持する。処理系が物理的真理を証明したとの主張ではない。',
 'ejz3':'第二文全体と明白さの提示ejz2を述べるメッセージ。',
 'ejz4':'同じ著者・論説の第二文全体の提示を本文へ接続し、主節の部分内容に続く別の記録として保持する。',
}
LIMITS=[
 '電動力はu0174第一項の引用語eisqsが指す同じ概念とする。物理的な意味はejyg、構成は動的な単位量応答から基準の電気側を引く残差ejx4である。一次近似sci2を厳密な定義へ交換しない。',
 'Hilfsbegriffは既存の物理量による定義上の補助として読む。nurは、その概念が担う全ての理論構成上の使用がこの役割に収まるという限定とする。非空の使用範囲と各使用の全箇所での定義展開を要求し、独立な物理入力としての使用を残さない。単なる一意な数値追加項だけではこの役割を尽くさない。',
 '構成的な使用の全範囲と物理的意味を保つ定義展開は明示した意味規約に従う。原著者のこの理論内での役割についての主張を記述するもので、全理論の保存拡張証明や電動力の不存在、語への言及禁止を追加しない。',
 'welcherとseineは主節と同じ概念の証人へ結ぶ。Einführungはeiscwによる理論への導入、verdanktは系依存性ejzoを根拠とした理論上の導入理由として読む。歴史上の誰の心理的動機かを補わず、単なる含意へ縮めない。',
 '電気・磁気の力の存在の非独立性は、両種の局所的な単位試験作用の有無の区分を理論全体で系の運動状態から独立にできないという先行の読みを保つ。同じ過程・出来事・単位の物理的実現と、各量種での許容反例をejzoへ結ぶ。全場・全速度で変わるとはしない。',
 'Man siehtは著者が第二文全体を明白として提示することを意味する。語り手以外の実在の観察者や実験実施は追加しない。冒頭の磁動力への類推は文169の既存の構成を保つ。',
]

def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] c.\n' for n,(fs,_) in PRIMITIVES.items())
    t,c,ctx=v('theory'),v('concept'),v('context');args=[t,c,ctx]
    text+=define('ejzt',CONCEPT,both(k('eisqz',c,k('eisqs'),'r[p ejyg]',ctx),k('eiscw',*args)))
    use=k('eisq2',t,c,v('use'),ctx)
    text+=define('ejzu',CONCEPT,both(q('g','use','a',use),q('f','use','a',op('y',use,k('eisq3',t,c,v('use'),'r[p ejx4]',ctx)))))
    p=v('point');shared=[k('ejzt',k('eisqw'),c,p),k('ejzu',k('eisqw'),c,p)]
    theory=k('eisqy',k('eisqw'),k('eirf'),quote('eigj'),k('zno'),p)
    text+=content('ejzv',both(theory,q('g','concept','a',both(*shared))))
    reason=k('eisq4',k('eisqw'),c,'r[p ejzo]','r[p eiscw]',p)
    text+=content('ejzw',both(theory,q('g','concept','a',both(*shared,k('ejzo',k('eisqw'),p),reason))))
    text+=content('ejzx',k('uh',k('zpv'),k('rd'),quote('ejzv'),k('zno'),p))
    text+='d ejzy[] f[j s[k ejzx[]]].\n'
    text+=define('ejzz',[],both(k('eir3',k('zpv'),k('rd'),k('eirf'),quote('ejzy'),k('ri')),k('ue',k('zpt'),k('zpv'),k('ri')),op('u',op('e',k('zpt'),k('zpv')))))
    text+=content('ejz2',both(k('uh',k('zpw'),k('rd'),quote('ejzw'),k('zno'),p),k('zdg',k('zpw'),k('rd'),quote('ejzw'),k('zno'),p)))
    text+='d ejz3[] f[j s[k ejz2[]]].\n'
    text+=define('ejz4',[],both(k('eir3',k('zpw'),k('rd'),k('eirf'),quote('ejz3'),k('ri')),k('ue',k('zpv'),k('zpw'),k('ri')),op('u',op('e',k('zpv'),k('zpw')))))
    return text

def build():
    old=parse(read(PARENT));assert len(old['statements'])==360
    assert not(set(PRIMITIVES)|set(MEANINGS))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=deepcopy(old['statements'])
    for i,n in zip(INDICES,('ejzz','ejz4')):doc['statements'][i]=dict(kind='assert',body=dict(kind='call',symbol=n,arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='exclusive_auxiliary_role_and_introduction_reason',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=INDICES).document
    ann=json.loads(read('data/physical-field-dependence-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
