"""Compose frank criticism of the same already enacted legislation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE
from scripts.compose_protected_remarks import bind
from scripts.compose_legislative_thoughts import FRAME,FIELDS,ARGS,PUBLIC,NAMES,TARGET

PARENT='data/religious-emphasis-sentence-basis-v1.json'
DEPENDENCIES=('data/legislative-thoughts-basis-v1.json','data/legislative-formulations-basis-v1.json')
LIBRARY='examples/v016/frank-legal-criticism.noema';BASIS='data/frank-legal-criticism-basis-v1.json'
PRIMITIVES={
 'h26tj':('[a a a a a d] c',['criterion','standard','law','form','community','reference'],
   '指定の評価条件は、同じ評価観点の束の下で、この共同体の同じ法内容を同じ定式で定める上で備えるべき性質を問う条件である。条件の適用対象・定式・観点を固定し、単なる否定、別法の欠点、現在の不充足を見てからの条件選びにしない。条件を満たすかはh243uの内容へ分離し、唯一の正しい立法理論を要求しない。'),
 'h26tk':('[a a a a d] c',['person','activity','target','form','reference'],
   '同じ本人のこの発表活動は、指定対象の同じ定式について自分の評価を公に示す企てである。どの対象について何を評価する発表なのかを、その構成・問題設定から定め、実際に口にした項目だけから後付けで縮めない。活動の実行、全私生活の開示、評価の正しさはこの関係から導かない。'),
 'h26tl':('[a a a i[h[a d] e] d d] c',['person','activity','item','provider','reference','point'],
   'この本人の同じ発表の問題設定に関係し、本人がこの評価点で保持する評価の全範囲に、この代表内容項目が属する。実際に発表された項目だけでなく、意図的に伏せられた評価や歪められる前の評価も含める。無関係な内心の全開示は要求せず、項目の全内容を同じ供給関数と固定基準に保持する。実際の発表・許可・好都合な評価だけを選別条件にしない。範囲の網羅的な供給は解釈入力の責任である。'),
 'h26tm':('[a a a i[h[a d] e] d d] c',['person','activity','item','provider','reference','point'],
   '本人が同じ発表活動において、同じ代表内容について自分の評価をそのまま表に出すことを意図的に避ける。伏せる、別の評価に見せる、評価の強さや留保を実際の立場と違えて和らげる仕方を含み、権威への遠慮・迎合・不利益を恐れるための回避も含める。単なる短縮、礼儀ある表現、本人の不確実さを正確に述べること、恐怖という感情だけ、意図しない言い間違いを回避と同一視しない。回避の成功や相手が誤解したことを要求しない。'),
}
MEANINGS={
 'r6cz':'同じ比較元の全法内容・定式・観点をr6ctとh26tjで固定し、同じ代表項目が、その法の備えるべき条件h243vの不充足r326を論点として分析・説明・指摘するh243xへ結ぶ。否定一般を批判とせず、項目の全内容や現実の欠点の真理を一つの否定命題へ縮めない。',
 'r6c2':'同じ批判項目を本人の保持判断r53nと、同じ学識者の立場・公衆への本人名義の提示r53qへ結び、同じ活動で自分の理解力を使うab/acを要求する。単なる他人の批判の引用や別活動への提示では満たさない。',
 'r6c3':'同じ本人・発表・対象と定式の企てh26tkについて、h26tlが供給する全関連保持評価を調べ、各代表項目の妥当性・同じ本人の保持判断と、h26tmの意図的な隠蔽・歪曲・回避の不在を要求する。発表項目列の範囲だけで率直さを作らず、無関係な私的判断の全開示や恐怖の不在を要求しない。',
 'r6c4':'非空の批判項目列の各項目に、同じ本人・活動・公衆・法・定式・観点でr6c2と全関連評価範囲への所属を要求し、r6c3の回避の不在を結ぶ。条件選択関数は同じ代表項目へ適用し、各項目で異なる評価条件を許す。同じ全法内容の先行採択r6coは固定した履歴と起点で検査し、現在の君主が過去の制定者だったとは要求しない。',
 'r6c5':'同じ一つの公的活動に、非空の改善についての自分の思想r6cwと、同じ比較元の制定済み法への率直な批判r6c4を結ぶ。思想だけの提示は既存r6cwで保持し、批判のある提示は追加の複合行為として扱う。各項目は重なってもよく、批判の真理や完成した代替法案を要求しない。',
 'r6c6':'思想列・批判列・評価条件選択と先行採択の履歴・起点を固定し、正確な十対象列と固定基準から同じr6c5の実行内容を返す。採択は固定起点より前であり、後の発表評価点までに採択されればよいという読みにはしない。',
 'r6c7':'二つの項目列・条件選択・履歴・起点の閉じた記述から、十対象列と固定基準を受ける段階1の複合提示内容を引用として作る。現在の批判保持・発表・回避の不在や制定を引用の外側で実行しない。全候補への許可とsogarは後で同じ内容へ結ぶ。',
}
LIMITS=[
 '第九段落第二文mit einer freimüthigen Kritik der schon gegebenenを、同じ既存法の問題点を自分の評価として隠さず公に述べる批判という読みで構成する。Kritik一般のあらゆる用例を否定的評価だけに還元する定義ではない。肯定的な評価・留保を併せて述べることは思想列と全関連評価範囲で許す。',
 '批判は同じ法の備えるべき条件の不充足を論点として分析・説明・指摘する。以前のr326・h243v・h243xを再利用し、全命題内容はr53n/r53qの同じ代表項目・h26aeに保持する。本人の誤りうる批判、成立しない欠点、未採択の改善案を排除しない。法全体への批判を一つの条件付き命令に狭めない。',
 'freimüthigは、同じ評価を本人名義で公に示し、その発表で扱う自分の評価を意図的に隠す・歪める・迎合的に和らげる回避がない、と読む。全ての内心の開示、礼儀の欠如、感情として恐怖が全くないこと、実際の危険、批判の正当性、受け手の同意を要求しない。',
 'h26tlの範囲は発表の問題設定から定まり、実際に発表した列とは独立である。列外の関連評価を故意に隠せばr6c3は不成立になる。一方、全項目の逐語的な列挙を強制せず、意図的な隠蔽を伴わない要約・関連のない私的見解の省略は排除しない。入力が本当に全範囲を供給したことは有限模型では証明できず、意味規約と実例の解釈に責任を残す。',
 'der schon gegebenenは、同じ比較元の全法内容・定式が同じ履歴上の固定起点より前に採択済みである、と読む。制定者を現在の国家元首と同一視せず、現在も法が有効であることを追加しない。すでにの期待との比較や前提投射は全文の談話解釈で扱う。',
 '思想の提示と批判の提示は同じ本人・一つの活動・学識者・公衆・立法課題へ結ぶ。異なる項目に異なる評価条件を使え、列間の重複も許す。引用対象は両提示の連言であり、片方への許可だけから両方への許可を推論しない。本文にない審査目的も追加しない。',
 '今回の依存群を第二文全体の意味判断へ換算しない。全臣民・全候補への許可、公的理性使用一般、sogar、危険と洞察、国家元首の思考態度・啓蒙への照応・拡張、実例・尊敬する君主の先行者不在、全文提示と通読を残す。正本118主張・18全単位判断・第一文336文字を保持する。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def dependencies():return tuple(load_catalog(ROOT,p) for p in DEPENDENCIES)

def definitions():
    canonical='k h26ag[v item v reference]'
    text='d r6cz[item a criterion a '+FIELDS+'] c['+both('k r6ct['+ARGS+']','k h26ad[v item v reference]',
        'k h26tj[v criterion v standard v baseline v oldform v community v reference]',
        'k h243v[v criterion v baseline v reference]',
        'k h243x['+canonical+' v baseline v criterion r[p r326] v reference]')+'].\n'
    pfields=' '.join(n+' a' for n in PUBLIC);pargs=' '.join('v '+n for n in PUBLIC)
    held='g judgment a[k r53n[v person v judgment v item v reference v point]]'
    own='g faculty a['+both('k ab[v faculty v person v point]','k ac[v person v faculty v activity v point]')+']'
    text+='d r6c2['+pfields+' item a criterion a '+FIELDS+' point d] c['+both('k r6cz[v item v criterion '+ARGS+']',
        held,'k r53q['+pargs+' v item v reference v point]',own)+'].\n'
    relevant='k h26tl[v person v activity v item r[p h26ae] v reference v point]'
    open_=both('k h26ad[v item v reference]','e['+canonical+'][v item]',held,
        'u[k h26tm[v person v activity v item r[p h26ae] v reference v point]]')
    text+='d r6c3[person a activity a baseline a oldform a reference d point d] c['+both(
        'k h26tk[v person v activity v baseline v oldform v reference]','f item a[y['+relevant+']['+open_+']]')+'].\n'
    controls='criteria h[a] a '+FIELDS+' candidate d anchor d point d'
    rest='v criteria '+ARGS+' v candidate v anchor v point'
    peritem=both('k r6c2['+pargs+' v item c[v criteria]['+canonical+'] '+ARGS+' v point]',
        'k h26tl[v person v activity '+canonical+' r[p h26ae] v reference v point]')
    text+='d r6c4['+pfields+' items j[a] '+controls+'] c['+both(
        'k r6co[v ruler v people v community v baseline v oldform v reference v candidate v anchor]',
        'k r6c3[v person v activity v baseline v oldform v reference v point]',
        'u[e[d[v items]][n p a b]]','q[v items]['+TRUE+'][i[ok c item a]['+both('v ok',peritem)+']]')+'].\n'
    text+='d r6c5['+pfields+' thoughts j[a] criticisms j[a] '+controls+'] c['+both(
        'k r6cw['+pargs+' v thoughts '+ARGS+' v point]',
        'k r6c4['+pargs+' v criticisms '+rest+']')+'].\n'
    text+='d r6c6[thoughts j[a] criticisms j[a] criteria h[a] a candidate d anchor d bindings j[a] reference d] e[b point['+bind(NAMES,
        'k r6c5['+pargs+' v thoughts v criticisms '+rest+']')+']].\n'
    template='r b[i[thoughts j[a] criticisms j[a] criteria h[a] a candidate d anchor d][i[bindings j[a] reference d][k r6c6[v thoughts v criticisms v criteria v candidate v anchor v bindings v reference]]]]'
    return text+'d r6c7[thoughts i[j[a]] criticisms i[j[a]] criteria i[h[a] a] candidate i[d] anchor i[d]] '+TARGET+'[o a['+template+'][v thoughts v criticisms v criteria v candidate v anchor]].\n'

def build():
    old=parent();deps=dependencies();sources=(old,*deps)
    roots=(('r326','h243x','h243v'),('r6cw','r6ct','r53n','r53q'),('r6co',))
    doc=deepcopy(old.document);doc.update(declarations=[],statements=[]);imported={}
    for source,rs in zip(sources,roots):
        for d in closure(source.document,rs):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(imported)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(s.source_sha256 for s in sources))
    basis=dict(status='frank_criticism_of_already_enacted_legislation_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
