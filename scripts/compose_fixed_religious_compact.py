"""Compose persistent religious arrangements and agreement without an oath."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,FALSE
from scripts.compose_protected_remarks import bind

PARENT='data/provisional-order-sentence-basis-v1.json'
LIBRARY='examples/v016/fixed-religious-compact.noema'
BASIS='data/fixed-religious-compact-basis-v1.json'
FAMILY='i[h[j[a] d d d] e]'
NAMES=('community','regime','audience','period')
ARGS=' '.join('v '+n for n in NAMES)
FIELDS=' '.join(n+' a' for n in NAMES)
CONTEXT='reference d candidate d anchor d'
CTX='v reference v candidate v anchor'
SEQ='l[a]['+ARGS+']'
HISTORY='i[at d][k h257z[v reference v candidate v at]]'
ORDER='i[first d last d][k ic[v first v last v candidate]]'
PRIMITIVES={
 'h26ex':('[a d d d d] c',['period','reference','candidate','start','end'],
   '同じ期間対象について固定基準と候補履歴で指定された開始と終了。期間対象は合意内容を評価する前に固定し、維持できた点だけへの切詰めや評価ごとの終点変更をしない。履歴上の順序・正の長さ・端点の一意性は合成側で検査する。無期限の範囲を有限の観測終点で代用しない。'),
 'h26ey':('[a a a d] c',['activity','regime','community','reference'],
   'この行為の記述内容が、同じ共同体の同じ制度配置を正しい又は妥当なものとして受け入れてよいかを疑問に付し、その受容を問い直す表明である。単に制度に言及する、事務上の質問をする、内心だけで疑う、別制度を批判する行為とは区別する。発言の公的宛先、本人、実行、反証の成功や正しさは別条件。実行可能な活動だけに限定した候補範囲ではない。'),
 'h26ez':('[a a d] a',['regime','community','reference'],
   '同じ制度配置と共同体の下で、誰が公にその制度を疑問に付してよいかを定める制度上の規範の出所。市民に限らず公的な表明をする人への規制を対象とする。固定基準で同じ出所を追跡し、禁止の成立に合わせて選び替えない。正当性・実際の服従・正しい評価規範との一致は含意せず、禁止の内容はh7kで別に与える。'),
 'h26e2':('[] a',[],'制度の受容を公に問い直す者として規範を受ける立場。特定の職務・聖職者・学位・市民資格を要件にせず、この立場の名称から許可や禁止、実際の活動を導かない。'),
}
MEANINGS={
 'r5hz':'固定した期間対象の開始・終了h26exが一意であり、同じ完全な候補履歴でr5fdの正の有界期間をなす。短さや制度の維持、許可は含めない。',
 'r5h2':'同じr5hzの期間の両端を含む全点が、同じ本人の完全な生涯範囲ibに入る。生涯を出生から死までとして供給し、tbで非空・連続・履歴内であることを検査する。本人は人間であり、期間の開始と終了が同じ一人の生涯に収まる。人数分の生涯の継ぎ合わせや単なる同時代性ではない。',
 'r5h3':'同じ人間・宗教制度・共同体・読者世界の公衆について、その同じ公衆へ向ける同じ制度の受容を問い直す活動候補。市民資格・書面・学位・実行済み・真理・許可を選別条件にしない。',
 'r5h4':'人・活動・制度・共同体・公衆の正確な五対象列について、同じ本人が同じ活動を遂行し、その活動が評価点で生起する内容。問い直す内容と公的宛先はr5h3の固定分類で結び、禁止対象にこの実行を引用する。',
 'r5h5':'同じ制度の下で、全ての人に公的な問い直しの活動候補があり、その全候補の同じ本人・活動への負極性要求h7kが同じ規範源・立場・点で成り立つ。公的に疑問を呈してはならないという制度上の規制であり、実際の沈黙・全員の信念・物理不能・単なる許可の不在とは区別する。',
 'r5h6':'共同体・制度・公衆・期間の正確な四対象列について、合意基準以後の同じ有界期間の全内点で、同じ制度配置が存続し、誰にも公的問い直しを認めないr5h5の規制が続く内容。開始を含み終了を含まない。合意対象として引用しただけではその実現を要求しない。',
 'r5h7':'同じ合意の同じ型付き内容族・束縛列・固定基準・候補・合意基準について、その基準以前又は同時の履歴点に、同じ本人が同じ実行行為でその内容への共同決定の同意を表明する。汎用の同意表明であり、宣誓・署名・履行・全員同時発言を要求しない。',
 'r5ja':'同じ合意基準の固定した相異なる二人以上の当事者が全員人間で、同じ内容族・束縛列を合意対象として全員がr5h7の同意表明を済ませた共同合意。引用された内容の成立、全住民の一致、国家の承認、宗教上の宣誓は要求しない。',
 'r5jb':'同じ共同体の宗教上の配置と公衆・期間について、r5h6の継続と公的問い直しの禁止を対象としたr5jaの合意。原文のsich einigenを先の相互宣誓へ強めず、合意と合意内容の実施を分ける。',
}
LIMITS=[
 'u0013第八文[2310,2677)の合意対象・公的疑義の規制・期間の依存群。全文の禁止判断、改善過程への影響、後世への害、auch nur等の談話と通読はまだ未接続。確認文字数は増やさない。',
 'beharrlichを、対象期間中に同じ配置を変えず存続させる合意内容として読む。auch nur binnen der Lebensdauer eines Menschenは、そうした固定化が一人の生涯内の期間に限られても、という時間的な限定として後で接続する。無限の永続と有限期間を同時に要求しない。この部品は有界期間を扱い、無期限の合意の一般化を済ませたとはしない。',
 'von Niemanden öffentlich zu bezweifelndeは、公に制度の受容を問い直してはならないという規範的な限定として読む。実際に誰も疑わない、疑う能力がないという読みにはしない。内心の疑いも別扱いとする。',
 'öffentlichは先行する公的理性使用に照らして読者世界の公衆への表明と読む。書面の実際の刊行・学識者の資格をこの句だけから要求しない。全ての人への候補範囲は、許可済み・実行可能・市民だけへ縮めない。',
 'h26exの期間は同じ対象へ一意に対応させる。生涯判定ではib(person,candidate,point)を出生から死までの全範囲として与える。この入力の完全性と適切な端点解釈は供給側の責任で、有限検査は現実の寿命の網羅性の証明ではない。',
 'sich einigenは固定した当事者全員の共同決定への同意として構成する。先の契約にある宣誓や後見目的を持ち込まず、合意の当事者を全住民と同一視しない。ある人の生涯が期間を限ることから、その本人が合意の当事者であるとは推定しない。',
 '原刊489頁の当該文を表示して確認し、AA VIII 39の28–32行と照合した。beharrlichのAdelung項は取得できず、辞書による確認済みとはしない。採用読解は本文の前後関係に基づく。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    before=lambda a,b:'x[e[v '+a+'][v '+b+']][k ic[v '+a+' v '+b+' v candidate]]'
    inside=both('k h257z[v reference v candidate v at]',before('start','at'),'k ic[v at v end v candidate]')
    unique='f first d[f last d[y[k h26ex[v period v reference v candidate v first v last]]['+both('e[v first][v start]','e[v last][v end]')+']]]'
    text='d r5hz[period a reference d candidate d start d end d] c['+both('k h26ex[v period v reference v candidate v start v end]',unique,'k r5fd[v reference v candidate v start v end]')+'].\n'
    closed=both('k h257z[v reference v candidate v at]',before('start','at'),before('at','end'))
    text+='d r5h2[person a period a reference d candidate d start d end d] c['+both('k aa[v person]','k r5hz[v period v reference v candidate v start v end]',
        'k tb['+HISTORY+' i[at d][k ib[v person v candidate v at]] '+ORDER+']','f at d[y['+closed+'][k ib[v person v candidate v at]]]')+'].\n'
    targets=('person','activity','regime','community','audience');arg=' '.join('v '+n for n in targets);fields=' '.join(n+' a' for n in targets);seq='l[a]['+arg+']'
    text+='d r5h3['+fields+' reference d] c['+both('k aa[v person]','k h26cs[v regime v community v reference]','k ce[v audience v reference]',
        'k cc[v activity v audience v reference]','k h26ey[v activity v regime v community v reference]')+'].\n'
    text+='d r5h4[bindings j[a]] e[b point['+bind(targets,both('k dg[v activity v point]','k f3[v person v activity v point]'))+']].\n'
    scope='k r5h3['+arg+' v reference]'
    prohibition='k h7k[k h26ez[v regime v community v reference] v person k h26e2[] r[p r5h4] '+seq+' '+FALSE+' v point]'
    text+='d r5h5[regime a community a audience a reference d point d] c['+both('k h26cs[v regime v community v reference]','k ce[v audience v reference]',
        'f person a[y[k aa[v person]][g activity a['+scope+']]]','f person a[f activity a[y['+scope+']['+prohibition+']]]')+'].\n'
    lasting=both('k h26cv[v regime v community v reference v candidate v at]','k r5h5[v regime v community v audience v reference v at]')
    terms=both('k h257z[v reference v candidate v anchor]','k h26cs[v regime v community v reference]','k ce[v audience v reference]',
        'g start d[g end d['+both('k r5hz[v period v reference v candidate v start v end]',before('anchor','start'),'f at d[y['+inside+']['+lasting+']]')+']]')
    text+='d r5h6[bindings j[a] '+CONTEXT+'] e[b point['+bind(NAMES,terms)+']].\n'
    generic='terms '+FAMILY+' bindings j[a] '+CONTEXT
    assent=both('k ta['+HISTORY+' '+ORDER+']','k h257z[v reference v candidate v anchor]','k h257z[v reference v candidate v point]',before('point','anchor'),
        'k dg[v activity v point]','k f3[v person v activity v point]','k h26dl[v person v activity v agreement v terms v bindings '+CTX+' v point]')
    text+='d r5h7[person a activity a agreement a '+generic+' point d] c['+assent+'].\n'
    member=lambda n:'k h26dj[v agreement v '+n+' '+CTX+']'
    plural='g first a[g second a['+both(member('first'),member('second'),'u[e[v first][v second]]')+']]'
    consent='g activity a[g point d[k r5h7[v person v activity v agreement v terms v bindings '+CTX+' v point]]]'
    text+='d r5ja[agreement a '+generic+'] c['+both('k ta['+HISTORY+' '+ORDER+']','k h257z[v reference v candidate v anchor]',
        'k h26dk[v agreement v terms v bindings '+CTX+']',plural,'f person a[y['+member('person')+']['+both('k aa[v person]',consent)+']]')+'].\n'
    text+='d r5jb[agreement a '+FIELDS+' '+CONTEXT+'] c['+both('k h26cs[v regime v community v reference]','k ce[v audience v reference]',
        'k r5ja[v agreement r[p r5h6] '+SEQ+' '+CTX+']')+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,['r5fd','tb','ib','aa','ce','cc','dg','f3','h26cs','h26cv','h26dj','h26dk','h26dl','h7k']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='bounded_fixed_religious_arrangement_and_collective_assent',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
