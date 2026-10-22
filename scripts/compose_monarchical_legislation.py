"""Compose shared legislative limits and the public will grounding authority."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,FALSE
from scripts.compose_protected_remarks import bind

PARENT='data/personal-renunciation-sentence-basis-v1.json'
LIBRARY='examples/v016/monarchical-legislation.noema'
BASIS='data/monarchical-legislation-basis-v1.json'
NAMES=('actor','people','community','law')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
FOUR='l[a]['+ARGS+']'
THREE='l[a][v people v community v law]'
OFFICE_NAMES=NAMES[:3]
OFFICE='l[a][v actor v people v community]'
REF='k h26b7[]'
FAMILY='i b[h[j[a] d] e]'
PRIMITIVES={
 'h26go':('[] a',[],'同じ政治的共同体の君主的な統治者が、その人民に公的な規律を定める立法上の立場。君主という役職の構成はr2ujで同じ人・共同体・点へ結ぶ。この立場の名から採択への正当な資格や個人の私的な裁量を導かない。'),
 'h26gp':('[a a a d] c',['will','bearer','community','reference'],'この意志は、同じ固定基準で、指定した主体に帰属する、同じ共同体の公的な決定をどう引き受けるかという実践的・規範的な方向づけである。主体は個人又は集団でよい。私的な欲望の強さ、全成員の心理的一致、実際の投票・採択と区別し、引き受け得る内容の範囲は別に示す。'),
 'h26gq':('[a a d] c',['will','law','reference'],'同じ固定基準におけるこの実践的な意志の規律の下で、この法案を公的決定として引き受け得る。可能な引受け内容の範囲を表し、全ての案を同時に採択することや、既にその法を望んでいる心理状態ではない。人民全体への帰属、理性的な自己賦課との対応、他の意志との統合は別に構成する。'),
 'h26gr':('[a a d] c',['encompassing_will','incorporated_will','reference'],'同じ固定基準で、後の意志が前の意志の中に、その公的な決定を方向づける構成的な規律として取り込まれている。二つの意志の偶然の賛否一致、名称の同一、対外的な引用だけと区別する。全内容の保持や、取り込まれる意志の担い手・正当性は別に検査する。'),
 'h26gs':('[a a a d d] c',['actor','community','role','reference','candidate'],'同じ評価基準と候補において、この主体が同じ共同体に対して指定立場で公的規律を定めることを正当に主導する資格・権威を持つ。実力・名声・好感・事実上の役職保持だけとは区別する。あらゆる個別決定への許可、実際の採択、権威の規範的根拠はこの関係だけから導かない。'),
 'h26gt':('['+FAMILY+' j[a] '+FAMILY+' j[a] d d] c',['ground','ground_bindings','standing','standing_bindings','reference','candidate'],'同じ固定基準・候補で、第一の閉じた内容族と対象列が示す構成を、第二の閉じた内容族と対象列が示す規範的資格の成立を支える根拠として位置付ける。物理的な原因、単なる同時成立、著者が理由として述べる談話関係とは区別する。必要性・十分性、引用内容の現実の成立は別に述べ、この関係だけで任意の個別行為を許可しない。'),
}
MEANINGS={
 'r5mb':'同じ人民・共同体・法案の全仮定枠r5epと固定基準を保ち、その履歴のどこかで同じ主体が同じ共同体の君主r2ujである。否定的要求や実際の採択を範囲の選別条件にしない。',
 'r5mc':'正確な主体・人民・共同体・法案の四対象列と基準から、有効な全履歴内の同じ一点で主体が君主r2ujであり、同じ主体・人民・法の公的採択r5ekを行う内容を返す。役職保持と採択を別々の点から寄せ集めない。',
 'r5md':'同じ人民・共同体・法案について、既存の自己賦課r5enを、理性的公的規律の規範h26cgから人民の立場h26chへ負極性で要求する。単なる許可の未発見、実行不能、現在の制度上の権能不足へ替えない。',
 'r5me':'同じ主体・人民・共同体・法案の君主としての採択r5mcを、公的立法の規範h26cjから君主の立法上の立場h26goへ負極性で要求する。人民の自己決定の引用を君主の引用へ自動転用せず、同じ内容について二つの要求を別に保持する。',
 'r5mf':'同じ四対象列・基準・候補について、人民自身の自己決定がr5mdで禁じられるなら、君主による同じ法案の同じ人民への採択にもr5meがあるという条件内容。実際の採択や違反は条件にしない。',
 'r5mg':'全主体・人民・共同体・法案・仮定候補について、r5mbの範囲ならr5mfの同じ決定内容への不許可の対応を述べる。許容される自己決定から君主への一括許可を逆推論しない。',
 'r5mh':'同じ共同体の完全な人民r45dに同じ公的意志h26gpが帰属し、非空の全法案r5eiについて、その意志の引受け可能範囲h26gqが理性的な自己賦課可能性r5esと一致する。全人民意志をこの文脈の理性的な公的決定範囲として操作化し、一部の法案・一部の支持者だけで済ませない。',
 'r5mi':'同じ主体の同じ共同体に関する公的意志の中に、r5mhの全人民意志を構成的な規律として取り込み、同じ全法案について引受け得る範囲を過不足なく保持する。統合関係だけでも偶然の賛否一致だけでも足りず、私的な付加決定で公的な限界を越えない。',
 'r5mj':'正確な主体・人民・共同体の三対象列と基準から、同じ本人の意志と同じ全人民意志にr5miの統合がある内容を返す。実際の全員投票や全法案の同時採択を加えない。',
 'r5mk':'同じ三対象列から、同じ完全な人民に対応する共同体について、主体が同じ君主的立法の立場h26goで正当な権威h26gsを持つ内容を返す。特定の法律への許可ではない。',
 'r5ml':'同じ三対象列・基準・候補の意志統合r5mjを、同じ君主的立法権威r5mkの規範的根拠h26gtへ結ぶ内容。談話上のdennによる理由提示とは分ける。',
 'r5mm':'同じ完全な人民・共同体・固定基準と厳密全順序の履歴に、同じ主体が同じ共同体の君主である点があるという範囲。権威や意志統合を既に満たす主体だけに狭めず、法案の採択実行を要求しない。',
 'r5mn':'全主体・人民・共同体・候補のr5mmの範囲で、同じ意志統合が同じ立法権威の根拠r5mlであり、正当な権威があるならその意志統合があると要求する。全ての現実の君主が正当であるという経験的断言や、統合だけからの十分性は追加しない。',
 'r5mo':'固定基準h26b7での、人民と君主の同じ決定内容への否認の対応r5mgと、全人民意志の統合に立法権威の根拠を置くr5mnを結ぶ。比較・強調・理由の提示と全文帰属は別に接続する。',
}
LIMITS=[
 '第十文のbeschließenを、同じ人民の外的な共同生活を拘束する公的な規律の採択と読む。既存r5eiの全法案は特定の法形式に限らず、要求・許可・資格・権能とその維持や変更を含む全条項を持つ。直前の宗教体制だけへ限定せず、無関係な私的な希望まで対象へ拡げない。',
 'darf nichtは同じ内容への負極性の規範要求として保持する。r5esの不存在だけを不許可としないため、実行方法がない候補や未知の許可から禁止を補わない。人民の規範h26cg/立場h26chと、公的立法のh26cj/君主の立場h26goを区別する。',
 '君主は既存r2ujの同じ共同体の君主的な役職として扱う。採択の引用内では役職保持と同じr5ekの採択を同一点に結ぶ。権威・許可・実行を役職の存在だけから推論しない。',
 '全人民意志は、先の立法の試金石と同じ、理性的に可能な人民の自己賦課にかかわる公的な引受けの全範囲という規範的読解を採る。現在の全員の心理的一致、単純多数決、実際の採択法の集合ではない。人民の全成員と関連する全法案を固定し、適合する一部分だけを拾わない。',
 '引受け得る内容は選択可能な範囲であり、互いに両立しない全法案を一度に採択する意思ではない。君主自身の公的意志への統合は、構成的な取り込みと全範囲の対応を別に要求する。人民意志とたまたま同じ選択をすることや、一部の支持を代表するだけでは足りない。',
 'gesetzgebendes Ansehenは正当な立法上の資格・権威と読む。beruht daraufは意志統合をその規範的根拠に置き、権威が成立するなら統合を必要とする構成とする。全ての事実上の君主がこの根拠を備えるという断言、権威だけからの任意立法への許可、統合だけからの十分性は追加しない。',
 'この規範的な全人民意志の操作化は採用解釈であり、カントの全時期の意志論を定義したという主張ではない。固定原文と原刊490頁、AA VIII39末–40冒頭に照らして意味規約を明示する。',
 'nicht einmal/noch wenigerの比較、冒頭aber、dennの理由提示、ebenの根拠への焦点、同じ全体への帰属と通読は残る。本文105主張と意味確認済み文字数は増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    history='i[point d][k h257z[v reference v candidate v point]]'
    order='i[first d last d][k ic[v first v last v candidate]]'
    monarch='g point d['+both('k h257z[v reference v candidate v point]','k r2uj[v actor v community v point]')+']'
    ref='e[v reference]['+REF+']'
    frame=both(ref,'k r5ep[v people v community v law v candidate]',monarch)
    text='d r5mb['+FIELDS+' reference d candidate d] c['+frame+'].\n'
    enacted='g point d[g activity a['+both('k h257z[v reference v candidate v point]','k r2uj[v actor v community v point]',
        'k r5ek['+ARGS+' v activity v reference v candidate v point]')+']]'
    text+='d r5mc[bindings j[a] reference d] e[b candidate['+bind(NAMES,both('k ta['+history+' '+order+']',enacted))+']].\n'
    text+='d r5md[people a community a law a reference d candidate d] c[k h237z[k h26cg[] v people k h26ch[] r b[p r5en] '+THREE+' v reference '+FALSE+' v candidate]].\n'
    text+='d r5me['+FIELDS+' reference d candidate d] c[k h237z[k h26cj[] v actor k h26go[] r b[p r5mc] '+FOUR+' v reference '+FALSE+' v candidate]].\n'
    condition='y[k r5md[v people v community v law v reference v candidate]][k r5me['+ARGS+' v reference v candidate]]'
    text+='d r5mf[bindings j[a] reference d] e[b candidate['+bind(NAMES,condition)+']].\n'
    def quantify(names,body):
        body='f candidate d['+body+']'
        for n in reversed(names):body='f '+n+' a['+body+']'
        return body
    text+='d r5mg[reference d] e[b point['+quantify(NAMES,'y[k r5mb['+ARGS+' v reference v candidate]][t[k r5mf['+FOUR+' v reference]][v candidate]]')+']].\n'
    laws='k r5ei[v people v community v law v reference]'
    accepted='k h26gq[v will v law v reference]'
    public=both(ref,'k r45d[v people v community v reference]','k h26gp[v will v people v community v reference]',
        'g law a['+laws+']','f law a[y['+laws+'][z['+accepted+'][k r5es[v people v community v law]]]]')
    text+='d r5mh[people a community a will a reference d] c['+public+'].\n'
    incorporation=both('k r5mh[v people v community v public v reference]',
        'k h26gp[v own v actor v community v reference]','k h26gr[v own v public v reference]',
        'f law a[y['+laws+'][z[k h26gq[v own v law v reference]][k h26gq[v public v law v reference]]]]')
    text+='d r5mi[actor a people a community a own a public a reference d] c['+incorporation+'].\n'
    text+='d r5mj[bindings j[a] reference d] e[b candidate['+bind(OFFICE_NAMES,
        'g own a[g public a[k r5mi[v actor v people v community v own v public v reference]]]')+']].\n'
    authority=both('k r45d[v people v community v reference]','k h26gs[v actor v community k h26go[] v reference v candidate]')
    text+='d r5mk[bindings j[a] reference d] e[b candidate['+bind(OFFICE_NAMES,authority)+']].\n'
    grounding='k h26gt[r b[p r5mj] '+OFFICE+' r b[p r5mk] '+OFFICE+' v reference v candidate]'
    text+='d r5ml[bindings j[a] reference d] e[b candidate['+bind(OFFICE_NAMES,grounding)+']].\n'
    text+='d r5mm[actor a people a community a reference d candidate d] c['+both(ref,'k r45d[v people v community v reference]',
        'k ta['+history+' '+order+']',monarch)+'].\n'
    necessary='y[t[k r5mk['+OFFICE+' v reference]][v candidate]][t[k r5mj['+OFFICE+' v reference]][v candidate]]'
    grounds=both('t[k r5ml['+OFFICE+' v reference]][v candidate]',necessary)
    text+='d r5mn[reference d] e[b point['+quantify(OFFICE_NAMES,'y[k r5mm[v actor v people v community v reference v candidate]]['+grounds+']')+']].\n'
    text+='d r5mo[] e[b point['+both('t[k r5mg['+REF+']][v point]','t[k r5mn['+REF+']][v point]')+']].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,['r5ep','r5ek','r5en','r2uj','r5es','r45d','h237z','h26cg','h26ch','h26ci','h26cj']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='same_legislative_limits_and_complete_public_will_as_authority_ground',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
