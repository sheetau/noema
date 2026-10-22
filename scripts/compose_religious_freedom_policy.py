"""Compose full religious choice separately from its duty and self-judgment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind

PARENT='data/named-epoch-sentence-basis-v1.json'
LIBRARY='examples/v016/religious-freedom-policy.noema';BASIS='data/religious-freedom-policy-basis-v1.json'
ONE='i b[h[j[a] d] e]';TWO='i c[h[j[a] d] e]'
NAMES=('actor','person','community','undertaking','topic')
FIELDS=' '.join(n+' a' for n in NAMES)+' reference d'
ARGS=' '.join('v '+n for n in NAMES)+' v reference'
ROLE='k h26hn[v person v community v reference]'
THREE='l[a][v person v undertaking v topic]'
FIVE='l[a][v person v community v undertaking v topic '+ROLE+']'
POLICY_NAMES=('actor','group','community','topic')
POLICY=' '.join(n+' a' for n in POLICY_NAMES)+' reference d'
PARGS=' '.join('v '+n for n in POLICY_NAMES)+' v reference'
DUTY_NAMES=('source','actor','office','group','community','topic')
DUTY=' '.join(n+' a' for n in DUTY_NAMES)+' reference d'
DARGS=' '.join('v '+n for n in DUTY_NAMES)+' v reference'
PRIMITIVES={
 'h26nc':('[a a a d] c',['person','undertaking','topic','reference'],
   '同じ本人自身の営み内容が、指定した領域の信念・教え・実践の採否、吟味、判断又はこれに基づく行動に関わる、本人に委ねられる選択の全範囲に属する。h26j7で宗教領域を別に確認する。h246eで具体的内容を与え、現に信仰を持つ、救済に必要と信じる、実行する、許可される又は成功する場合だけへ縮めない。公的職務を他人に代わって遂行する次元の規律と、本人の宗教的自己選択への指図を区別する。'),
 'h26nd':('[a a a a a d d] c',list(NAMES)+['reference','point'],
   '同じ統治側・本人・共同体・営み・宗教主題と固定基準について、この点で、その本人の宗教的自己選択の立場への正負の要求と許可、同じ統治側が関与する権威的・強制的介入の有無が評価されている。未知を不在とみなさず、自由の成立や実行能力そのものとは分ける。全候補の範囲は結果に先立ち固定する。'),
 'h26ne':('[a a a '+TWO+' j[a] d c d] c',['source','person','role','target','bindings','reference','polarity','point'],
   '指定した規範の出所が同じ本人へ同じ立場で、段階2の閉じた内容族に同じ対象列・基準を適用した内容の指定極性を要求する。h237zと同じ非事実的な要求関係を一段高い内容へ用いる。要求時に対象を実行せず、現実の履行・許可・本人の信念・正当性を導かない。'),
 'h26nf':('[a i d[e] d] c',['person','content','point'],
   '本人がこの点で、段階3の閉じた内容を成り立つものとして受け入れ判断している。h26hmと同じ誤りうる判断を高い内容段階に保つ。内容の実行又は真理、知識、確信、誠実な報告、実際の行動を要求しない。'),
}
MEANINGS={
 'r5vw':'同じ人・宗教主題・基準について、本人自身の営み内容h26hkとその全宗教的選択範囲h26ncを結ぶ。救済に必要だという本人の判断や現実の実行によって範囲を狭めない。',
 'r5vx':'本人・営み・主題の正確な三対象列と基準を同じr5vwの内容へ結び、h246eのNoema内容を実際に評価する。後続の要求・許可ではこれを段階1で引用し、行為を実行しない。',
 'r5vy':'本人・共同体・営み・主題・立場の正確な五対象列を、同じh26hnの宗教的自己選択の立場とr5vxの営みへ結ぶ。市民的職務の別の規律への介入を同一視しない。',
 'r5vz':'同じ統治側から同じ本人・立場・営み・宗教主題・基準・点へ、実行要求も不実行要求もない。許可・能力・実行・無介入とは別の非指図条件。',
 'r5v2':'r5vzと同じ対象について、実行と不実行の両極性がh245cで積極的に許可されている。反対要求との衝突を除き、沈黙だけを全面的な選択の許容にしない。',
 'r5v3':'同じ点で生起する同じ活動に同じ統治側が参加し、同じ本人のr5vyで指定された宗教的自己選択へh26hoの介入がある。本人・活動・立場・内容・点を別事例から寄せ集めない。',
 'r5v4':'同じ宗教的営み候補についてr5v2の両方向の選択の許容と、統治側が関与するr5v3の介入の不在を連言する。身体的能力や実行成功、他の独立主体からの無限定な自由は要求しない。',
 'r5v5':'非空で全員人間の同じ固定集団と宗教主題について、各人に少なくとも一つの宗教的選択候補があり、その全候補の同じ統治側・立場への規範と介入評価が済む。空範囲・評価不足を自由の証拠にしない。',
 'r5v6':'r5v5と同じ固定集団の全成員・全宗教的選択について、同じ点でr5vzの非指図を要求する内容。現在信仰する人又は成功した候補だけに限らない。',
 'r5v7':'r5v5の同じ全範囲についてr5v4の両方向の許容と非介入を要求する方針内容。非指図r5v6を含むが、単なる非指図より強く、全員の現在の行動は含まない。',
 'r5wa':'統治側・集団・共同体・宗教主題の正確な四対象列と基準からr5v7の方針を返す。外側の義務へ段階2で引用する。',
 'r5wb':'規範出所・本人・公的立場と同じ方針の対象を保ち、その本人が同じ全体方針r5waを満たすよう正極性で要求される内容。方針の出所となる本人と、その本人の義務を定める規範出所を分ける。',
 'r5wc':'六個体と固定基準の閉じた名前を、r5wbへ適用して得る段階3の義務内容記述。原文の方針の代わりに未知の義務フラグを渡さない。',
 'r5wd':'r5wcへ渡す六個体と固定基準の各呼称を脱引用して元の対象と照合する。名前が別人物・別集団・別出所を指す場合を、その内容を信じていない例へ隠さない。',
 'r5we':'同じ本人が、r5wdで参照を確認した同じr5wbの義務内容を受け入れ判断していること。義務や方針の実際の真理・実行とは別で、判断内容は同じ本人の同じ方針に固定する。',
}
LIMITS=[
 'u0015第一文の「宗教上何も指図せず、全面的な自由を残すことを義務と考える」という内容依存群。本人がそのように発言することを品位に反しないと判断する外側の埋込み、名称拒否、称賛と解放の功績、全文帰属はまだ接続しない。本文112主張と全単位17判断を変更せず、意味確認文字数は加算しない。',
 '対象は同じ固定集団の人々全員の全宗教的自己選択。宗教主題h26j7は教派や本人の信仰の有無に限定しない。旧r5nqの救済に必要と信じる営みだけでも、既に能力を持つ人だけでもない。原文への統合時に集団・共同体・基準を固定し、その範囲の完全な供給は解釈入力の責任として明示する。',
 'volle Freiheitは同じ統治側に相対的な、本人の宗教的選択の実行と不実行の許容、両方向の指図の不在、その統治側が関与する権威的・強制的介入の不在として読む。許可の新たな発令や立法の一事件、本人の実行・能力、全規範源の消滅、全ての外的行為への無制限な自由は加えない。',
 '選択の立場h26hnを内容へ明示し、本人の信仰・判断・実践への介入と、公的職務の別次元の規律を区別する。この区別を、秩序という名前だけで同じ宗教的介入を正当化する免除には用いない。助言・説得・不賛同だけはh26hoの介入ではない。',
 '全称範囲は固定基準の集団・営み候補から取り、許可がない候補や現在実行されない候補を除かない。各人の候補非空と全候補の評価を要求する。未評価又は未知の要求・介入を不在とみなさない。',
 '義務の出所、義務を負う本人と立場、方針の適用先の人々を別々に保持する。本人が義務と考えることは、実際の義務・自由政策の成立・誠実な発言を含意しない。外側の品位判断はさらにこの自己報告を対象とするため、今回のr5weをそのまま無条件の前件にしない。',
 '行為内容は段階1、規範と介入を含む方針は段階2、方針への義務は段階3で引用する。未知の内容を低い段階に落とさず、全ての対象列と参照を保持する。有限モデル検査は意味同値の自動認定ではない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    candidate='k r5vw[v person v undertaking v topic v reference]'
    text='d r5vw[person a undertaking a topic a reference d] c['+both('k aa[v person]','k h26j7[v topic v reference]',
        'k h26hk[v undertaking v person v reference]','k h26nc[v person v undertaking v topic v reference]')+'].\n'
    text+='d r5vx[bindings j[a] reference d] e[b point['+bind(('person','undertaking','topic'),both(candidate,'t[s[k h246e[v undertaking v reference]]][v point]'))+']].\n'
    text+='d r5vy[bindings j[a] reference d] e[b point['+bind(('person','community','undertaking','topic','role'),
        both('e[v role]['+ROLE+']','t[k r5vx['+THREE+' v reference]][v point]'))+']].\n'
    norm=lambda sign:'k h237z[v actor v person '+ROLE+' r b[p r5vx] '+THREE+' v reference '+sign+' v point]'
    permit=lambda sign:'k h245c[v actor v person '+ROLE+' r b[p r5vx] '+THREE+' v reference '+sign+' v point]'
    text+='d r5vz['+FIELDS+' point d] c['+both('u['+norm(TRUE)+']','u['+norm(FALSE)+']')+'].\n'
    text+='d r5v2['+FIELDS+' point d] c['+both('k r5vz['+ARGS+' v point]',permit(TRUE),permit(FALSE))+'].\n'
    intervention='k h26ho[v activity v person r b[p r5vy] '+FIVE+' v reference v point]'
    text+='d r5v3['+FIELDS+' activity a point d] c['+both('k dg[v activity v point]','k df[v actor v activity v point]',intervention)+'].\n'
    text+='d r5v4['+FIELDS+' point d] c['+both(candidate,'k r5v2['+ARGS+' v point]','u[g activity a[k r5v3['+ARGS+' v activity v point]]]')+'].\n'
    member='k h246c[v group v person v reference]'
    assessed=both('g undertaking a['+candidate+']','f undertaking a[y['+candidate+'][k h26nd['+ARGS+' v point]]]')
    text+='d r5v5['+POLICY+' point d] c['+both('k r5ty[v group v reference]','k h26j7[v topic v reference]','f person a[y['+member+']['+assessed+']]')+'].\n'
    for n,target in (('r5v6','r5vz'),('r5v7','r5v4')):
        all_choices='f person a[f undertaking a[y['+both(member,candidate)+'][k '+target+'['+ARGS+' v point]]]]'
        text+='d '+n+'['+POLICY+'] e[b point['+both('k r5v5['+PARGS+' v point]',all_choices)+']].\n'
    text+='d r5wa[bindings j[a] reference d] e[b point['+bind(POLICY_NAMES,'t[k r5v7['+PARGS+']][v point]')+']].\n'
    target='r c[p r5wa] l[a]['+' '.join('v '+n for n in POLICY_NAMES)+'] v reference'
    text+='d r5wb['+DUTY+'] e[b point[k h26ne[v source v actor v office '+target+' '+TRUE+' v point]]].\n'
    text+='d r5wc['+' '.join(n+' i[a]' for n in DUTY_NAMES)+' reference i[d]] i d[e][o a[r d[p r5wb]]['+' '.join('v '+n for n in (*DUTY_NAMES,'reference'))+']].\n'
    names=['k h223g[v '+n+']' for n in DUTY_NAMES]+['k h223h[v reference]']
    correct=['e[s['+code+']][v '+n+']' for code,n in zip(names,(*DUTY_NAMES,'reference'),strict=True)]
    text+='d r5wd['+DUTY+'] c['+both(*correct)+'].\n'
    text+='d r5we['+DUTY+' point d] c['+both('k r5wd['+DARGS+']','k h26nf[v actor k r5wc['+' '.join(names)+'] v point]')+'].\n'
    return text
def build():
    old=parent();doc=deepcopy(old.document)
    roots=['aa','h26j7','h26hk','h246e','h26hn','h237z','h245c','h26ho','dg','df','r5ty','h223g','h223h','rdr']
    doc.update(declarations=closure(doc,roots),statements=[]);imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='religious_nonprescription_full_choice_policy_and_fallible_duty_judgment',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256=dict(old.source_sha256),limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
