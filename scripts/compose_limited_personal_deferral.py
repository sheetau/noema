"""Compose permitted personal deferral and nontrivial restrictions on suspension."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind

PARENTS=('data/personal-enlightenment-choice-basis-v1.json','data/fixed-compact-sentence-basis-v1.json')
LIBRARY='examples/v016/limited-personal-deferral.noema'
BASIS='data/limited-personal-deferral-basis-v1.json'
NAMES=('actor','subject','response','period')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
FOUR='l[a]['+ARGS+']'
SOURCE='k h26ax[]'
ROLE='k h26fz[]'
REF='k h26f2[]'
ANCHOR='k h26fw[v response v reference]'
PRIMITIVES={
 'h26fy':('[a a a a d d] c',list(NAMES)+['reference','candidate'],'同じ選択主体・対象本人・応答行為・期間対象と固定基準について検討する、相互に矛盾しない仮定経過の完全な範囲。主体と対象本人を初めから同一に限定せず、期間の長短・終了の有無、方針採用や実行、規範的許容を見て成功例だけへ選別しない。現在の本人の気分や実際の選択を固定条件とせず、履歴の整合性・実行・期間の構成・許可は別に確認する。'),
 'h26fz':('[] a',[],'人として知るべき事柄について自ら理解し判断する営みと、その進め方を選ぶ側としての立場。国家の立法者・聖職者の職務・他者の後見資格とは区別する。この立場を選択主体へ用いても、他者の啓蒙を処分する正当な権能や無限定の許可を導かない。'),
 'h26f2':('[] d',[],'第九文の本人の啓蒙延期と本人・後世についての放棄を検討する固定基準。全人・義務事項・自己判断対象の対応・選択候補・全履歴・期間の範囲を解釈する。立法者や現在の合意の当事者だけへ狭めず、結果や許可に応じて範囲を替えない。真偽評価h26ar、選択点h26fw、文章の提示文脈とは区別する。'),
}
MEANINGS={
 'r5kw':'同じ二人・応答・期間・固定基準の全仮定範囲h26fyで、主体と対象が人であり、対象本人の全義務事項の対応r5knが有効で、全履歴は厳密な全順序、同じ固定選択点は履歴内にある。主体と対象の一致、有界期間、方針採用、実際の選択、許可では候補を選別しない。',
 'r5kx':'正確な主体・対象本人・応答・期間の四対象列から、同じ固定選択点に始まる有界又は終点なしの期間r5jf内に、その対象本人の知るべき事柄へのr5kqの営みがある内容を返す。実行する人は対象本人であり、方針を選ぶ主体へ取り替えない。',
 'r5ky':'同じ四対象列について、有界期間r5jdの終了以後の全履歴に同じ対象本人のr5kqの営みがある内容。終了点ちょうどを含む。終点なしの期間では成立せず、再開の方針の対象に用いる。',
 'r5kz':'同じ四対象列について、対象本人の全義務事項の対応と固定選択点からの有効な期間を保ち、その点で主体が実行する同じ応答で、期間内の対象本人の営みr5kxを負極性の方針として採用し、反対向きの同時採用がない。検討対象となる広い中断選択であり、本人自身・有界・再開の条件を初めから入れない。',
 'r5k2':'同じ四対象の中断選択r5kzに、人間の啓蒙・進展の規範h26axから選択主体の立場h26fzへの衝突のない積極的許可r37cがある。同じ候補を規範評価点とし、別候補の許可を借りない。引用した選択の実行を許可の判定だけでは要求しない。',
 'r5k3':'同じ四対象の限定条件。主体と対象本人が一致し、同じ選択点からの期間が有界で、同じ応答に終了以後の営みr5kyの正極性の方針があり、逆向きも既存r5kuによる全未来継続の拒否もない。実際の再開や能力の獲得を加えない。',
 'r5k4':'同じ一つの仮定経過でr5kwの全候補枠組み、中断の実行r5kz、衝突のない許可r5k2、本人・有界・再開という限定r5k3がそろう。実行と許可を別々の候補から集めない。',
 'r5k5':'同じ人と固定基準について、本人自身を対象とする一つの応答・期間・仮定経過にr5k4がある。本人の限定された延期が許容される可能性であり、全ての有界期間への許可、現実の選択や将来の成功は要求しない。候補が空なら偽。',
 'r5k6':'同じ人と固定基準のr5k5を内容として返す。外側の評価点で候補・規範・期間を取り替えず、全文の個人一般への量化と談話の焦点に用いる。',
 'r5k7':'同じ固定基準の全主体・対象本人・応答・期間・仮定経過について、r5kw内で実行された同じ中断選択に衝突のない積極的許可があるなら、r5k3の本人・有界・再開という限定を要求する。全候補を最初から有界・本人だけに狭めて恒真化せず、許可のない例から禁止を自動導出しない。',
 'r5la':'固定基準h26f2で、全人についてr5k5の限定された延期の可能性があり、全仮定候補についてr5k7の必要な限定が守られるという内容。可能性と必要条件を併記し、必要条件を満たす任意の期間の一括許可へ逆向きに推論しない。',
}
LIMITS=[
 '第九文前半のkannを、本人自身の一時延期を規範的に許容する仮定を置き得ることと読む。規範は人間の啓蒙・進展を根拠に評価する既存h26ax、立場は自ら判断し進め方を選ぶh26fz、固定基準はh26f2。現在の身体能力や現実の意欲だけにせず、許可だけで実行可能な候補を補わない。',
 'für seine Personとnur auf einige Zeitは、許容される中断選択が本人自身を対象とし、有界な期間を設け、後に続ける方針を保つという必要な限定として読む。期間の数値上限・一律の短さ・全ての有限期間への許可は原文から追加しない。各人には少なくとも一つの許容される限定構成があるという一般的可能性と、限定条件の必要性を別に保つ。',
 '限定の非自明性を保つため、候補の中断選択r5kzは他者を対象にする場合と終点なしの場合も表せる。後に続ける方針を持たない場合も広い中断選択には含む。これらを仮定範囲から落とさず、許容された実行例であればr5k7を満たせないようにする。現実の他者に影響しないことまで本人という限定から導かない。',
 'r5kwは実際の中断・許可で選別しない。r5k7はその全範囲のうち仮定内で中断が実行され許容される場合の必要条件であり、同じ仮定内の構成を評価する。実世界の実行済みの例だけに限るものではない。仮定範囲の完全性と現実への適合は入力の責任である。',
 '自己の場合の有界部分について、r5kx/r5kyは前群r5kr/r5ksと明示した対象列・規範・立場の対応の下で内容評価が一致する。引用記述は異なるので、同じ態度や許可が自動的に別の引用へ移るとはしない。新しい四対象の引用について方針を明示入力する。',
 '方針採用・実行・規範評価は同じ応答・主体・対象・期間・候補・基準へ結ぶ。未許可を禁止と同一視せず、反対要求と衝突する許可を正当な許容として数えない。後世についての放棄と権利侵害はこの前半の必要条件だけから導かない。',
 '個人一般の全称はaaの全人を対象とし、義務事項を欠く人や不許可の人を成功例選別で除外しない。誰かが全義務事項の対応を欠く場合、その模型では可能性を主張する全称命題は成立しない。全人の存在や無限の現実候補を有限検査で証明するわけではない。',
 '後世についての放棄、神聖な人類の権利と侵害・踏みにじる見立て、zwar/aber/mehr noch、同じ全文への帰属と通読は残る。第九文の意味確認文字数と本文104主張は増やさない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    knowledge='k r5kn['+SOURCE+' v subject '+ROLE+' v reference]'
    history='i[at d][k h257z[v reference v candidate v at]]'
    order='i[first d last d][k ic[v first v last v candidate]]'
    frame=both('k aa[v actor]','k aa[v subject]',knowledge,'k h26fy['+ARGS+' v reference v candidate]',
        'k ta['+history+' '+order+']','k h257z[v reference v candidate '+ANCHOR+']')
    text='d r5kw['+FIELDS+' reference d candidate d] c['+frame+'].\n'
    acts='g activity a[g topic a[k r5kq['+SOURCE+' v subject '+ROLE+' v activity v topic v reference v candidate v point]]]'
    valid='k r5jf[v period v reference v candidate '+ANCHOR+']'
    bounded='k r5jd[v period v reference v candidate '+ANCHOR+' v end]'
    during=both(valid,'g point d['+both('k h26e3[v period v reference v candidate v point]',acts)+']')
    after='g end d['+both(bounded,'g point d['+both('k h257z[v reference v candidate v point]',
        'x[e[v end][v point]][k ic[v end v point v candidate]]',acts)+']')+']'
    for name,body in (('r5kx',during),('r5ky',after)):
        text+='d '+name+'[bindings j[a] reference d] e[b candidate['+bind(NAMES,body)+']].\n'
    def policy(target,sign):return 'k h26ft[v actor v response r[p '+target+'] '+FOUR+' v reference '+sign+' '+ANCHOR+']'
    raw=both(knowledge,valid,'t[k zzq[v actor v response]]['+ANCHOR+']',policy('r5kx',FALSE),'u['+policy('r5kx',TRUE)+']')
    text+='d r5kz[bindings j[a] reference d] e[b candidate['+bind(NAMES,raw)+']].\n'
    text+='d r5k2['+FIELDS+' reference d candidate d] c[k r37c['+SOURCE+' v actor '+ROLE+' r b[p r5kz] '+FOUR+' v reference v candidate]].\n'
    no_renunciation='u[k h26ft[v actor v response r[p r5ku] l[a]['+SOURCE+' v subject '+ROLE+' v response] v reference '+FALSE+' '+ANCHOR+']]'
    qualified=both('e[v actor][v subject]','g end d['+bounded+']',policy('r5ky',TRUE),'u['+policy('r5ky',FALSE)+']',no_renunciation)
    text+='d r5k3['+FIELDS+' reference d candidate d] c['+qualified+'].\n'
    common=ARGS+' v reference v candidate';actual='t[k r5kz['+FOUR+' v reference]][v candidate]'
    text+='d r5k4['+FIELDS+' reference d candidate d] c['+both('k r5kw['+common+']',actual,'k r5k2['+common+']','k r5k3['+common+']')+'].\n'
    text+='d r5k5[person a reference d] c[g response a[g period a[g candidate d[k r5k4[v person v person v response v period v reference v candidate]]]]].\n'
    text+='d r5k6[person a reference d] e[b point[k r5k5[v person v reference]]].\n'
    condition=both('k r5kw['+common+']',actual,'k r5k2['+common+']')
    all_cases='f candidate d[y['+condition+'][k r5k3['+common+']]]'
    for n in reversed(NAMES):all_cases='f '+n+' a['+all_cases+']'
    text+='d r5k7[reference d] c['+all_cases+'].\n'
    text+='d r5la[] e[b point['+both('f person a[y[k aa[v person]][k r5k5[v person '+REF+']]]','k r5k7['+REF+']')+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5kn','r5kq','r5ku','r5kr','r5ks','r5kt'],['r5jf','r37c','h26ax'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='personal_deferral_possibility_and_necessary_self_bounded_limits',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
