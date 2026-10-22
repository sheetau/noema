"""Ground congregations, changed arrangements, completed assent and retention aims."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENTS=('data/legislative-touchstone-basis-v1.json','data/joint-petition-basis-v1.json')
LIBRARY='examples/v016/congregational-choices.noema'
BASIS='data/congregational-choices-basis-v1.json'
FAMILY='i[h[j[a] d d d] e]'
NAMES=('community','congregation','field','subject','institution')
FRAME='community a congregation a field a subject a'
FRAME_ARGS='v community v congregation v field v subject'
CONTEXT='reference d candidate d anchor d'
CONTEXT_ARGS='v reference v candidate v anchor'
PRIMITIVES={
 'h26dg':('[a a d] c',['congregation','community','reference'],'この継続的な宗教上の共同組織は、同じ政治的共同体の中で、地域の人々が共同の教えと実践を営む共同体として位置付けられる。都市・行政自治体そのもの、当日の参加者だけ、宗教を論じるだけの任意集団ではない。教会制度・宗教領域・成員は別に結び、国の公認・特定の聖職者の在職・全市民の所属を要求しない。'),
 'h26dh':('[a a d d] c',['congregation','field','reference','point'],'同じ宗教共同体・制度領域・固定基準について、制度配置の規則・手続・役割関係の内容を比較する全状況範囲。現に実施済みの一状態だけ、差が見つかった成功例だけへ範囲を縮めない。範囲の適切性は解釈入力の責任であり、未知の比較を偽で埋めない。'),
 'h26di':('[a a d d d] c',['agreement','congregation','reference','candidate','anchor'],'同じ候補履歴の基準点で、この合意がこの共同体自身の共同の決定として制度・慣行上帰属する。個人の私的な相談や外部の人による一方的な宣言とは区別する。全成員の満場一致・国家の許可・道徳的な正当性・実施済みは含意しない。'),
 'h26dj':('[a a d d d] c',['agreement','person','reference','candidate','anchor'],'同じ合意の同じ基準点に固定した意思形成の当事者の全範囲。現在の賛同者だけを後から選び直さず、過去の表明を探す際もこの当事者を保つ。共同体の全成員との一致や、表明・成員資格そのものは別条件である。'),
 'h26dk':('[a '+FAMILY+' j[a] d d d] c',['agreement','terms','bindings','reference','candidate','anchor'],'この同じ合意の決定対象は、この閉じた内容族に同じ順序付き対象列・固定基準・候補・基準点を渡す内容である。別版・別対象の合意への賛同を移送せず、内容の真理や実施は含意しない。'),
 'h26dl':('[a a a '+FAMILY+' j[a] d d d d] c',['person','activity','agreement','terms','bindings','reference','candidate','anchor','point'],'同じ本人がこの行為で、この合意対象の同じ内容族・対象列・固定文脈の内容を、共同の決定として採ることへの自分の同意を表明する。単なる受領・他人の発言の引用・偶然同じ行動とは区別する。生起と本人の行為は別に結び、履行・法的な拘束・全員の同時発言は要求しない。'),
 'h26dm':('[a '+FAMILY+' j[a] d d d] c',['holder','target','bindings','reference','candidate','anchor'],'この主体が同じ候補履歴の基準点で、この内容族と同じ対象列・固定文脈に指定された状態を今後の実践で選び維持したいという意向を持つ。共同体を主体とするときはその共同の方針として帰属する意向であり、一人の私的な希望から推定しない。単なる予測・現在状態への慣れ・反対意向の不在ではなく、実行・実現・法的な資格は含意しない。'),
}
MEANINGS={
 'r5fz':'同じ政治的共同体内の地域的な宗教共同体h26dgについて、既存r363の継続組織・宗教上の主題・共同実践・制度領域を結び、その固定基準の成員が非空で全員人間であることを要求する。空の名称・当日の集会・自治体だけを宗教共同体にしない。',
 'r5f2':'政治的共同体・宗教共同体・領域・宗教主題・制度配置の正確な五個体列をr5fzに結び、その同じ領域の制度配置h246wが評価点に実際に運用されるh246xという内容を返す。合意・意向・後の保護活動に同じ内容を渡せる。候補と基準点は型付き文脈の一部として保持する。',
 'r5f3':'同じ共同体と制度領域について、旧配置が同じ候補履歴の基準点で運用され、旧新双方が配置であり、固定した比較範囲の少なくとも一点で旧新の運用内容の真偽が異なる。別名だけでは変更とせず、客観的な改善や新配置の実施済みを要求しない。',
 'r5f4':'同じ当事者・合意・新配置の五対象列への同意表明について、有効な同じ履歴で基準点以前又は同時の点に、同じ本人が遂行する生起行為がある。内容を実行せず、表明の活動・点を後から本人の判断理由と結べるよう引数に保つ。',
 'r5f5':'同じ共同体への帰属、同じ変更内容、同じ合意対象の型付き内容割当てを保ち、基準点に固定した相異なる二人以上の当事者全員が同じ共同体の人間の成員で、それぞれr5f4の同意表明を済ませている。全成員の全員一致、全員の同時表明、合意内容の実施・正当性を補わない。本人のよりよい認識に基づくことはまだ別条件。',
 'r5f6':'正確な五対象列について、同じ有効履歴の基準点以降の評価点から先の全点でr5f2の同じ配置内容が続くという目標内容。有限の履歴を永遠とせず、今後の運用を対象にする。引用しただけなら維持を実行評価しない。',
 'r5f7':'同じ宗教共同体で同じ旧配置が基準点に現行であることと、その共同体自身が同じ五対象列のr5f6の維持内容を望む意向h26dmを結ぶ。改革への合意がないという否定から維持意向を導かず、維持の成功や全成員の同一心理は要求しない。',
}
LIMITS=[
 'u0013第七文のGemeinden、veränderte Religionseinrichtung、geeiniget hättenとbeim Alten ... bewenden lassenの依存群。Gemeindenは地域の宗教上の共同体、Einrichtungは教え・実践・組織の規則と役割の配置として読む。既存r363/h246w/h246xに同じ対象を渡す。',
 '制度変更は、固定した比較範囲で同じ運用内容が異なることとする。旧新の名前の不等号だけで済ませず、変更が客観的な改善であることも条件にしない。比較範囲・制度配置と具体的な運用内容の対応は入力が明示する責任を持つ。',
 '合意は共同体に帰属する共同の決定への複数当事者の同意として構成し、原文の一致を宗教上の宣誓や法的契約へ強めない。後続の保護の基準点までに同意したことを履歴で結ぶ。接続法とetwaは最終的な候補状況・文章の帰属に保持し、現実の改革共同体の存在をここで無条件に主張しない。',
 '当事者本人のnach ihren Begriffen der besseren Einsichtをまだ満たしたことにはしない。r5f4は同じ同意行為と時点を引数に残すので、その時点で保持している判断と理由を結ぶことができる。旧rlhの情報集合の増加だけへ戻さず、公的洞察の対象と本人の比較基準を区別する。',
 '維持意向は肯定的な意向関係であり、単なる改革合意の不在や現状の運用から推論しない。共同の意向の帰属を全員の同じ私的信念と同一視せず、意向の成立をその実現と同一視しない。',
 'r5f2/r5f6は段階0の内容族であり、提案内容の段階1の内側で引用・評価できる。合意と意向の検査ではそれらの内容を実行せず、保護活動と同じ内容に接続するため保持する。',
 '保護・非妨害そのもの、本人の比較判断、洞察が共同提案に足りる条件、期間の到達内容、談話・著者帰属と全文通読は残る。確認文字数を加算しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def seq(institution='institution'):return 'l[a]['+FRAME_ARGS+' v '+institution+']'
def definitions():
    timeline='k ta[i[at d][k h257z[v reference v candidate v at]] i[first d last d][k ic[v first v last v candidate]]]'
    text='d r5fz['+FRAME+' reference d] c['+both('k h26dg[v congregation v community v reference]',
        'k r363[v congregation v field v subject v reference]',
        'g person a[k h246c[v congregation v person v reference]]',
        'f person a[y[k h246c[v congregation v person v reference]][k aa[v person]]]')+'].\n'
    state=both('k r5fz['+FRAME_ARGS+' v reference]','k h246w[v institution v field v reference]','k h246x[v institution v field v point]')
    text+='d r5f2[bindings j[a] '+CONTEXT+'] e[b point['+bind(NAMES,state)+']].\n'
    text+='d r5f3['+FRAME+' older a newer a '+CONTEXT+'] c['+both('k r5fz['+FRAME_ARGS+' v reference]',
        'k h246w[v older v field v reference]','k h246w[v newer v field v reference]','k h246x[v older v field v anchor]',
        'g comparison d['+both('k h26dh[v congregation v field v reference v comparison]',
            'u[z[k h246x[v older v field v comparison]][k h246x[v newer v field v comparison]]]')+']')+'].\n'
    text+='d r5f4[person a activity a agreement a '+FRAME+' newer a '+CONTEXT+' point d] c['+both(timeline,
        'k h257z[v reference v candidate v anchor]','k h257z[v reference v candidate v point]',
        'x[e[v point][v anchor]][k ic[v point v anchor v candidate]]','k dg[v activity v point]','k f3[v person v activity v point]',
        'k h26dl[v person v activity v agreement r[p r5f2] '+seq('newer')+' '+CONTEXT_ARGS+' v point]')+'].\n'
    member=lambda n:'k h26dj[v agreement v '+n+' '+CONTEXT_ARGS+']'
    plural='g first a[g second a['+both(member('first'),member('second'),'u[e[v first][v second]]')+']]'
    consent='g activity a[g point d[k r5f4[v person v activity v agreement '+FRAME_ARGS+' v newer '+CONTEXT_ARGS+' v point]]]'
    text+='d r5f5[agreement a '+FRAME+' older a newer a '+CONTEXT+'] c['+both(
        'k r5f3['+FRAME_ARGS+' v older v newer '+CONTEXT_ARGS+']','k h26di[v agreement v congregation '+CONTEXT_ARGS+']',
        'k h26dk[v agreement r[p r5f2] '+seq('newer')+' '+CONTEXT_ARGS+']',plural,
        'f person a[y['+member('person')+']['+both('k aa[v person]','k h246c[v congregation v person v anchor]',consent)+']]')+'].\n'
    future='f later d[y['+both('k h257z[v reference v candidate v later]',
        'x[e[v point][v later]][k ic[v point v later v candidate]]')+'][t[k r5f2[v bindings '+CONTEXT_ARGS+']][v later]]]'
    text+='d r5f6[bindings j[a] '+CONTEXT+'] e[b point['+both(timeline,
        'k h257z[v reference v candidate v anchor]','k h257z[v reference v candidate v point]',
        'x[e[v anchor][v point]][k ic[v anchor v point v candidate]]',future)+']].\n'
    text+='d r5f7['+FRAME+' older a '+CONTEXT+'] c['+both('k r5fz['+FRAME_ARGS+' v reference]',
        'k h246w[v older v field v reference]','k h246x[v older v field v anchor]',
        'k h26dm[v congregation r[p r5f6] '+seq('older')+' '+CONTEXT_ARGS+']')+'].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r363','h246c','h246w','h246x','aa','dg','f3','ta','h257z','ic'],[])):
        for d in closure(source.document,roots) if roots else []:
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='same_congregation_arrangement_assent_and_retention',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
