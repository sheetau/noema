"""Compose public peace, civic concord and assessed absence of warranted threats."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/spreading-spirit-sentence-basis-v1.json'
LIBRARY='examples/v016/civic-peace-concord.noema';BASIS='data/civic-peace-concord-basis-v1.json'
FRAME=('government','office','community','group','topic')
FIELDS=' '.join(n+' a' for n in FRAME)+' reference d assessment d'
ARGS=' '.join('v '+n for n in FRAME)+' v reference v assessment'
PRIMITIVES={
 'h26qp':('[a a d d] c',['episode','community','reference','point'],
   'この出来事の働きが、同じ共同体の人々が公的な共同生活を通常に営める状態を、この点で妨げ又は乱す。集団としての安全な往来・共同事務・社会的相互作用に対する作用であり、出来事の単なる地域的一致、統治者が不快に思う意見、別人の無関係な私事とは分ける。生起と出来事の強制・敵対的な性格は別に構成し、妨害の未観測を既知の不在としない。'),
 'h26qq':('[a d] c',['episode','reference'],
   'この出来事は、暴力、実力による威嚇、又は互いに押し切ろうとする集団的な衝突を含む種類である。記述された内容の批判・信条の相違・平穏な討論だけとは分ける。現に生起したことや共同生活への影響は別に結び、正当性の判定や個々人の負傷を分類の必須条件にはしない。'),
 'h26qr':('[a a a d d] c',['first','second','community','reference','point'],
   '第一集団が同じ共同体の第二集団と、異なる立場を持つ者同士として同じ公的共同生活に属し続けることを拒む、集団としての敵対的な対立がこの点である。単なる政策・宗教・学問上の不同意、孤立した個人の不満、相互批判と区別する。第一集団から第二集団への向きを保ち、相手も同じ拒否をすることや暴力の発生は要求しない。各集団の成員範囲と共同生活全体への作用は別に検査する。'),
 'h26qs':('[a a a d d] c',['first','second','community','reference','point'],
   'この二集団間の対立は同じ共同体において、一時的で局所的な意見の相違にとどまらず、互いに同じ政治的共同生活の一員として関わり続ける結び付きを損なう広がり又は持続を持つ。全員の思想的一致や単一宗派を要求せず、対立の当事者・向き・実在は別に結ぶ。文脈に即した公的な分裂の基準で、少数者への単なる不人気や政府の呼称を根拠に真にしない。'),
}
for name,meaning in (
 ('h26qt','同じ政府・最高職・共同体・全対象集団・宗教主題・固定基準・評価点について、公的生活への懸念を判定する関連する実践的な可能経過の全範囲。自由がある経過だけ、危害がない経過だけ、評価済みの経過だけへ事後選別しない。評価点における背景を固定し、候補は経過全体を評価できる状況で、単なる想像可能性や観測標本と同一視しない。'),
 ('h26qu','同じ設定・固定基準・評価点のこの候補経過について、自由条件、共同体の平穏と一致への危害、その経過を懸念として見込む根拠の評価がそろっている。これは情報の充足であり、無害・危害・高確率のいずれも自動的に帰結しない。未評価を根拠なしへ補わない。'),
 ('h26qv','同じ設定・固定基準・評価点で採る証拠と実践的な判断基準に照らし、この候補経過を現実に生じうるものとして見込みに入れる十分な根拠がある。単なる論理的可能性、政府の心理的な不安、著者が不安だと語ること、現実の出来事の発生と区別する。数値確率や多数決を補わず、未知と根拠の既知の不在を区別する。')):
    PRIMITIVES[name]=('[a a a a a d d d] c',[*FRAME,'reference','assessment','outcome'],meaning)
MEANINGS={
 'r57y':'固定基準で同じ政治的共同体の成員である人が少なくとも一人いる。存在しない人口の上で平穏や一致を空虚に成立させない。',
 'r57z':'同じ生起する出来事dgが、強制的又は敵対的衝突の種類h26qqに属し、同じ共同体の公的共同生活を実際に乱すh26qp。単なる反対意見・別地域の事件・未生起の可能な出来事だけでは満たさない。',
 'r572':'同じ非空の共同体r57yについて、公的共同生活を乱すr57zの出来事がこの点で存在しない。öffentliche Ruheを公的な平穏として読む内容。無音、全活動の停止、全批判の不在、他の全種類の損失の不在へ強めない。',
 'r573':'固定基準で同じ集団の成員h246cが非空で、その全成員が同じ政治的共同体の人である。別の共同体の成員や集団の名前だけで内部の派を作らない。',
 'r574':'同じ共同体に含まれる非空で互いに重ならない二集団があり、その少なくとも一方向にh26qrの共同所属を拒む対立があり、二集団の結び付きを損なう公的な広がり・持続h26qsを伴う。思想的一致の欠如だけや局所的な不満では成立せず、無暴力の社会的分裂も扱う。',
 'r575':'同じ非空の共同体r57yに、r574の公的な分裂をなす集団対立がない。Einigkeitを共通の政治的共同生活への結び付きがそのような対立で壊れない一致として読む。全員の同じ意見・宗派・政府支持・常時協同行為を要求しない。',
 'r576':'同じ共同体・固定基準・候補点に、r572の平穏又はr575の一致の少なくとも一方の不成立がある。両方が同時に失われる場合だけへ危害を狭めず、別共同体の二つの状態を混ぜない。',
 'r577':'同じ条件内容を満たす関連候補が少なくとも一つあり、その全候補について評価がそろい、根拠を持って見込む候補のどれにも同じ危害内容がない。論理的に可能な全危害の禁止や今の無害、主観的不安の不在とは区別する。条件不能・未評価から懸念なしを補わない。',
 'r6aa':'同じ政府・最高職・共同体・全対象集団・宗教主題の適格設定r56iで、同じr56hの自由が成り立つ候補について、同じ共同体のr576の危害を見込む根拠がないというr577を構成する。候補・評価・根拠には全て同じ設定・固定基準・評価点を渡す。',
}
LIMITS=[
 'u0015第四文のfür die öffentliche Ruhe und Einigkeit des gemeinen Wesens nicht das mindeste zu besorgenへの依存群。平穏と一致を別内容にし、自由の下でどちらかを損なう経過について根拠ある懸念がないと読む。本文の例示、前文の同じ政府、Denn/doch、全文帰属と通読はまだ含めない。',
 '公共の平穏を、強制・威嚇・集団衝突によって通常の公的共同生活が乱されていない状態として扱う。静音・服従・無批判へは縮めない。共同体の一致は、同じ公的共同生活に属し続ける結び付きが公的規模の集団対立で壊れないこととし、全員の同じ信仰・政策意見を加えない。',
 '集団は固定基準の全成員をh246cで指定し、非空・同じ共同体への所属・二集団の不重複を合成する。集団対立の広がりや持続の解釈基準は入力として公開し、有限検査の集団だけを現実の全社会集団と主張しない。',
 'nicht das mindesteは、同じ二状態に対して見込む根拠のある危害候補が一つもないという否定全称で扱う。平均的な危害が小さいこと、最大の危害だけの不在、一方の安全だけへ弱めない。平穏と一致自体の成否と、現在の根拠に基づく見込みは別である。',
 '可能経過の範囲、評価完備性、見込みの根拠を分離する。自由が成立する候補を非空に要求し、条件不能や評価漏れで懸念なしを作らない。自由下の関連候補が全て評価済みなら、根拠のない可能な危害は直ちに懸念には数えない。未知は根拠なしや無害へ補わない。',
 '自由の内容は既存r56hの同じ宗教的自己選択と公的提示の型。特定の世俗活動全般の自由や全未来の確実な無害を補わず、外国政府の心理的信念やその政府が実際に自由を与えたことはこの内容から要求しない。',
 '本文115主張、17全単位判断と追加三文899文字を保存し、第四文の意味確認文字数は増やさない。原刊istと固定本文・AAのsei差を保持する。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    member=lambda p:'k h246c[v group v '+p+' v reference]'
    citizen=lambda p:both('k aa[v '+p+']','k h237c[v '+p+' v community v reference]')
    text='d r57y[community a reference d] c[g person a['+citizen('person')+']].\n'
    text+='d r57z[episode a community a reference d point d] c['+both('k dg[v episode v point]','k h26qq[v episode v reference]','k h26qp[v episode v community v reference v point]')+'].\n'
    text+='d r572[community a reference d] e[b point['+both('k r57y[v community v reference]','u[g episode a[k r57z[v episode v community v reference v point]]]')+']].\n'
    text+='d r573[group a community a reference d] c['+both('g person a['+member('person')+']','f person a[y['+member('person')+']['+citizen('person')+']]')+'].\n'
    disjoint='f person a[u['+both('k h246c[v first v person v reference]','k h246c[v second v person v reference]')+']]'
    opposing='x[k h26qr[v first v second v community v reference v point]][k h26qr[v second v first v community v reference v point]]'
    text+='d r574[first a second a community a reference d point d] c['+both('k r573[v first v community v reference]','k r573[v second v community v reference]',disjoint,opposing,
        'k h26qs[v first v second v community v reference v point]')+'].\n'
    text+='d r575[community a reference d] e[b point['+both('k r57y[v community v reference]','u[g first a[g second a[k r574[v first v second v community v reference v point]]]]')+']].\n'
    text+='d r576[community a reference d] e[b point[x[u[t[k r572[v community v reference]][v point]]][u[t[k r575[v community v reference]][v point]]]]].\n'
    selected=both('c[v scope][v outcome]','t[v condition][v outcome]')
    text+='d r577[condition e harm e scope h[d] c assessed h[d] c warranted h[d] c] c['+both('g outcome d['+selected+']',
        'f outcome d[y['+selected+'][c[v assessed][v outcome]]]',
        'u[g outcome d['+both(selected,'c[v warranted][v outcome]','t[v harm][v outcome]')+']]')+'].\n'
    funcs=' '.join('i[outcome d][k '+n+'['+ARGS+' v outcome]]' for n in ('h26qt','h26qu','h26qv'))
    frame=' '.join('v '+n for n in FRAME)+' v reference'
    text+='d r6aa['+FIELDS+'] c['+both('k r56i['+frame+']','k r57y[v community v reference]',
        'k r577[k r56h['+frame+'] k r576[v community v reference] '+funcs+']')+'].\n'
    return text
def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,['aa','h237c','h246c','dg','r56i','r56h']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='civic_peace_concord_and_warranted_threat_absence_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
