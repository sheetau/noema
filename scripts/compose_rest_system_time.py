"""Name the just-defined time by its stationary-clock frame dependence."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_empirical_light_constant import ROOT,read
from scripts.compose_material_relative_frame import define
from scripts.compose_two_postulates import quote
from scripts.compose_relativity_conjecture import content
from scripts.compose_limits import R,v,call as k,op,both,quant as q

PARENT='examples/v014/einstein-empirical-light-constant.noema';PARENT_BASIS='data/empirical-light-constant-basis-v1.json'
FULL='examples/v014/einstein-rest-system-time.noema';CORE='examples/v014/rest-system-time-core.noema'
BASIS='data/rest-system-time-basis-v1.json';ANNOTATIONS='data/rest-system-time-identifiers-v1.json';INDEX=246
FIELDS=[(n,'a') for n in ('event','clock','place','frame')]+[('value',R),('context','d')]
PRIMITIVES={
 'eisks':([], 'u0022で直前に定義した時間規約を呼ぶための呼称個体。印字形die Zeit des ruhenden Systemsを識別表記に保持し、指示対象は命名行為で結ぶ。字面から絶対時間や全系の共通時間を導かない。'),
 'eiskt':([], 'u0022の、静止系に静止する時計による定義の重要性と、その系への所属を理由とした命名を述べる箇所。'),
 'eisku':([('time','a'),('rule','i[h[a a a '+R+' d] c]'),('frame','a'),('unit','a'),('document','a'),('context','d')], 'timeという時間規約の時刻付与の適用基準が、同じdocumentの同じframe・unitで閉じたruleにより与えられるという規約と規則の対応。ruleは出来事・時計・場所・指示値・状況の関係型であり、同じtimeの値の解釈と比較を保持する。規則の採用済み、時計の静止、各対象への実際の読取りの存在はこの対応だけから導かず、別に合成する。候補の別時間、局所規約一つ、全系共通の規約へ黙って交換しない。'),
 'eiskv':([('node','a'),('author','a'),('content','i[e]'),('document','a'),('context','d')], 'authorがnodeでcontentの条件を、同じdocumentの定義の意味と適用範囲を理解する上で肝要なものとして取り立てる。論述上の重要性の帰属であり、論理的必然性の演算子、感情的な好み、内容の自明性や証明済みの認定とは区別する。条件の内容とその成立は合成側で保つ。'),
}
MEANINGS={
 'einx':'同じ出来事・時計・場所・値・状況がeingの時刻付与条件を満たすなら、その時計と共通参照時計が指定frameで静止し、局所時計が指定場所にあるという条件。原文の時計による方法の範囲を取り出し、実際の時計の存在を追加しない。',
 'einy':'全ての出来事・時計・場所・実数表現について、時刻付与の規則eingの適用が同じ静止系raのeinxを満たすという内容。有限標本への限定ではなく、定義本体の連言から得る一般的な条件である。',
 'einz':'先に提案・定義した同じ時間規約eisjdを、同じ系ra・単位rbのeingへ結び、その適用で時計がraに静止するeinyを合わせる。時間の当該系への所属をこの操作上の依存として読む。',
 'ein2':'直前の箇所rjで行った定義採用einiと、同じ規約・時計・系への依存einzを合わせ、先にこの方法で時間を定義したことを保持する。',
 'ein3':'同じ著者が現在の箇所でeisksという呼称を、直前に定義した同じ時間規約eisjdに採用する命名行為。新しい時間規約を定義し直す行為とはしない。',
 'ein4':'先の静止時計による定義ein2の成立と重要性、現在の命名ein3、その理由としての系への所属einzを同じ文で結ぶ。重要性と理由の向きを取り違えない。',
 'ein5':'定義の重要性・所属・理由付き命名ein4を述べるメッセージ。静止系の名称を絶対静止や全系共通の時間の主張へ替えない。',
 'ein6':'著者・論説への帰属、直前の定義箇所rjを受ける振り返り、速度定数の採用tmからの本文順序を保持する。改頁標識は新たな命題としない。',
}
LIMITS=[
 'u0022全207文字・177非空白本文文字を、原刊894頁末から895頁冒頭へ続く一文として読む。セミコロン前後の定義の重要性と理由付き命名を共に保持する。A0006は空の改頁標識であり、追加内容や脚注命題ではない。',
 'die eben definierte Zeitは直前にeingで定義した同じ時刻規約を指す。先の共通時間候補eisjdがその規約として採用されたという連続性を明示し、別の時間規約や局所A時間だけへ替えない。',
 '時計の同じ系での静止と所在はeing→qu→qt→saf/saeの連言から取り出す。全実数表現に量化した条件einyを有限標本で評価せず、この限定された含意は定義の展開と連言除去によって確認する。',
 'Zugehörigkeitを、同じ系に静止する時計と同じ参照時計を用いて時刻を与えるという操作上の系への依存として読む。物体の容器への所属、時間が空間内に物として存在すること、絶対静止や全系で共通の時刻を意味させない。',
 'Wesentlichは定義理解にとっての重要性の帰属であり、論理的必然性や自明性の主張にはしない。wegenは系への所属einzから命名ein3へ向かう理由として保持し、名前が静止条件を生むという逆向きにしない。',
 'wir nennenは著者が議論を進める声による現在の命名宣言。引用形を保持し、同じ名称と対象を既存eisd4で結ぶ。著者以外の人数、社会全体の承認、既に他者がその名を使った事実は補わない。',
 '定義の採用と名前の使用は物理的な読取りの実施ではない。有限例は規則の結合・別系への交換・命名・提示を検査し、全物理状況や原文との意味同値の自動証明とはしない。u0023以降の第二節は残る。',
]


def definitions():
    text=''.join('r '+n+'['+' '.join(t for _,t in fs)+'] '+('a' if not fs else 'c')+'.\n' for n,(fs,_) in PRIMITIVES.items())
    conclusion=both(k('ca',v('clock')),k('cc',v('clock'),v('frame')),k('cb',v('clock'),v('place'),v('frame')),k('cc',k('rc'),v('frame')))
    text+=define('einx',FIELDS,op('y',k('eing',*[v(n) for n in ('event','clock','place','value','context')]),conclusion))
    general=k('einx',v('event'),v('clock'),v('place'),k('ra'),v('value'),v('point'))
    for name,sort in reversed([('event','a'),('clock','a'),('place','a'),('value',R)]):general=q('f',name,sort,general)
    text+=content('einy',general)
    text+=content('einz',both(k('eisku',k('eisjd'),'r[p eing]',k('ra'),k('rb'),k('eirf'),v('point')),'t[k einy[]][v point]'))
    text+=content('ein2',both('t[k eini[]][v point]','t[k einz[]][v point]'))
    text+=content('ein3',k('eisd4',k('eiskt'),k('rd'),k('eisks'),k('eisjd'),k('eirf'),v('point')))
    text+=content('ein4',both('t[k ein2[]][v point]','t[k ein3[]][v point]',k('eiskv',k('eiskt'),k('rd'),quote('ein2'),k('eirf'),v('point')),k('eisdk',k('eirf'),quote('einz'),quote('ein3'),v('point'))))
    text+='d ein5[] f[j s[k ein4[]]].\n'
    text+=define('ein6',[],both(k('eir3',k('eiskt'),k('rd'),k('eirf'),quote('ein5'),k('ri')),k('eiskq',k('eiskt'),k('rd'),k('rj'),k('eirf'),k('ri')),k('ue',k('tm'),k('eiskt'),k('ri')),op('u',op('e',k('tm'),k('eiskt')))))
    return text


def build():
    old=parse(read(PARENT));assert len(old['statements'])==INDEX;doc=deepcopy(old);doc['statements']=[]
    assert not(set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']+[dict(kind='assert',body=dict(kind='call',symbol='ein6',arguments=[]))]
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,_ in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='stationary_clock_definition_and_reasoned_time_naming',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=[],statement_indices=[INDEX]).document
    ann=json.loads(read('data/empirical-light-constant-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    ann['entries'].append(dict(symbol='eisks',role='designation',forms=[dict(text='die Zeit des ruhenden Systems',language='de',role='printed_identifying_form')]))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
