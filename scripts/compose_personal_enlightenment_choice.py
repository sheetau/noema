"""Separate a person's temporary deferral from renunciation of enlightenment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind

PARENT='data/fixed-compact-sentence-basis-v1.json'
LIBRARY='examples/v016/personal-enlightenment-choice.noema'
BASIS='data/personal-enlightenment-choice-basis-v1.json'
FAMILY='i[h[j[a] d] e]'
NAMES=('source','person','role','response','period')
FOUR_NAMES=NAMES[:4]
FIVE='l[a]['+' '.join('v '+n for n in NAMES)+']'
FOUR='l[a]['+' '.join('v '+n for n in FOUR_NAMES)+']'
ANCHOR='k h26fw[v response v reference]'
PRIMITIVES={
 'h26ft':('[a a '+FAMILY+' j[a] d c d] c',['person','response','content_family','bindings','reference','polarity','point'],'本人は同じ反応において、閉じた内容関数へ同じ対象列と固定基準を渡す内容を、指定極性で自分の実践上の方針として明確に引き受ける。既存h244jと同じ方針採用の区別を固定基準付きの内容族に保ち、発言による表明又は行動上の選択を指す。予測・希望・未達成・能力不足とは区別し、実行成功、内容の真理、外からの要求、正当性は含意しない。'),
 'h26fu':('[a a d] c',['topic','item','reference'],'この固定基準で、指定した自己判断の事柄は、指定した認識項目の内容に関わる同じ事柄である。認識項目h26aeと判断対象h226uの対応を明示する関係であり、名前の一致、別の成功例からの借用、どちらかの知識・自立の達成によって対応を選び直すことではない。'),
 'h26fv':('[a a '+FAMILY+' j[a] d d] c',['person','activity','goal','bindings','reference','point'],'本人が同じ活動・点で、閉じた内容関数と同じ対象列・固定基準が表す内容を、その活動の目標として目指している。目標記述は引用のまま保持し、実際の達成、単なる予測、別の活動の目的、後付けの理由に置き換えない。目標へ向かう活動の種類と生起は別に結ぶ。'),
 'h26fw':('[a d] d',['response','reference'],'同じ選択・応答行為を評価する固定基準の下で、その選択の基準点を指す。比較候補や成功結果に合わせて移動させず、実際にその選択が行われるか、前後期間や規範との関係は別に検査する。'),
 'h26fx':('[a a a d] c',['person','activity','topic','reference'],'同じ本人のこの活動は、固定した同じ事柄について、自分で理解し理由を吟味するための学習・探究・検討という活動構成を持つ。単なる情報の受け渡し、無関係な休息、他者の結論への機械的服従とは区別する。目的関係・実行・判断の成功・通常の自立能力の獲得は別に確認する。'),
}
MEANINGS={
 'r5kl':'本人・認識項目の正確な二対象列と固定基準から、同じ本人がその内容を把握し、理由に基づいて保持する認識r5clを返す。内容の真偽評価h26ar(reference)を固定し、知るべき対象の規範的指定に引用できる。',
 'r5km':'同じ人・規範の出所・立場・固定基準で、全認識範囲h26adに属する同じ項目のr5klを正極性で要求するh237zがある。知っていること、学びたいこと、真であることだけで知るべき対象を選ばない。規範の評価点を基準に固定し、実際の認識達成を要求しない。',
 'r5kn':'同じ人について知るべき項目が非空で、その全項目に、同じ本人の固定判断領域h226u内の事柄とのh26fuの対応がある。未対応の義務項目を落としたり、空の範囲で本人の啓蒙を表したりしない。',
 'r5ko':'同じ本人の固定判断領域に属し、同じ規範・立場で知るべき項目と対応する事柄。義務のある認識内容と自己判断の対象を同じ基準へ結び、無関係な対象の自立を流用しない。',
 'r5kp':'本人・判断対象の正確な二対象列と固定基準から、同じ本人・事柄について通常の理由ある自己判断r5aaが成り立つ内容を返す。探究の目標に用い、目標への志向から達成を導かない。',
 'r5kq':'同じ規範・本人・立場・事柄・固定基準について、r5koの対象に向けた本人の学習・探究・検討h26fxを、同じ候補履歴の生存点で実行し、同じ本人と事柄のr5kpを同じ活動の目標とする。単なる目的の保持、他者の活動、能力の成功だけでは足りない。',
 'r5kr':'規範・本人・立場・選択・期間の正確な五対象列について、選択の固定基準点から始まる同じ有界期間内に、同じ本人の知るべき事柄へのr5kqの営みがあるという内容。期間は開始以上終了未満で、延期における負極性の方針の対象にする。',
 'r5ks':'r5krと同じ五対象列の有界期間について、その終了点以後の同じ全履歴に同じ本人のr5kqの営みがあるという内容。延期後に続けるという正極性の方針の対象であり、終点ちょうどで再開する場合も含める。実際の再開や成功は方針採用の外側で要求しない。',
 'r5kt':'同じ人の全義務項目の対応r5knと、固定選択点から始まる正の有界期間r5jdを保ち、その点で本人が実際に行う同じ選択で、期間内の営みr5krを負極性、終了以後の営みr5ksを正極性の方針として引き受ける。反対向きの同時採用と、同じ全未来の継続r5kuの拒否を認めず、本人の一時延期を単なる未達成や今後の放棄へ替えない。',
 'r5ku':'規範・本人・立場・選択の正確な四対象列から、同じ固定選択点以後の全履歴のどこかで、同じ本人の知るべき事柄へのr5kqの営みがあるという内容。終期や観測打切りで範囲を狭めず、放棄の負極性方針の対象にする。',
 'r5kv':'同じ全義務項目の対応と有効な履歴を保ち、本人が同じ基準点で実際に行う同じ選択で、今後の継続r5kuを負極性の方針として引き受ける。反対向きの同時採用と、いずれかの同じ期間後に続けるr5ksの同時採用を拒む。永久に実際の能力が失われることや、後に態度を撤回できないこと、権利が正当に消滅することは導かない。',
}
LIMITS=[
 'u0013第九文の本人の啓蒙延期と放棄を区別する依存群。知るべき事項を規範の正極性要求により固定し、その全事項と本人の自己判断領域の対応を保つ。規範の出所・立場は全文で固定するため引数に残し、今まさに全知識を達成済みであることや即時の期限は追加しない。',
 '啓蒙の営みを、知るべき事柄について本人が自分で理解し理由を吟味する学習・探究・検討を実行し、通常の理由ある自己判断を目指すことと読む。実際の認識成功や能力獲得と活動を区別する。義務事項全てを一度に完成する条件ではなく、その範囲における営みである。',
 '延期は、固定選択点からの有界期間には進めず、終了以後に続けるという実践的な選択を同じ応答行為で採用する読み。実際の選択は要求するが、将来の計画通りの再開・達成はこの選択の成立条件にしない。決めた期限に失敗した場合でも、当初の延期の選択を放棄へ書き換えない。期間の非空・連続性・一意の終了はr5jdを再利用する。',
 '放棄は、同じ本人の今後の継続全体を退ける実践上の方針を、同じ選択で取る読み。未達成・忘却・不能・一時的な不実行とは区別する。否定する対象が全未来の継続であることを明記するが、その方針が現実に永久に守られることや、正当な権利放棄の効力は含意しない。',
 '引用した目標や時間範囲付き内容を、目的・方針採用の判定時に実行しない。期間は延期の側では構成として検査するが、期間内の不実行や将来の成功をその外側で要求しない。未知の目的・規範・方針を偽で補わない。',
 'für seine Personはここでは対象となる啓蒙の本人を固定することとして構成する。他者に全く影響しないという追加条件にはしない。後世についての放棄、kannの規範的許容、nurの許容範囲、heiligな権利と侵害・踏みにじる見立て、zwar/aber/mehr noch・著者帰属・全文通読は残る。本文104主張と意味確認文字数は変えない。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def definitions():
    text='d r5kl[bindings j[a] reference d] e[b point['+bind(('person','item'),'k r5cl[v person v item v reference k h26ar[v reference] v point]')+']].\n'
    duty='k h237z[v source v person v role r b[p r5kl] l[a][v person v item] v reference '+TRUE+' v reference]'
    text+='d r5km[source a person a role a item a reference d] c['+both('k aa[v person]','k h26ad[v item v reference]',duty)+'].\n'
    owed='k r5km[v source v person v role v item v reference]'
    matched=both('k h226u[v person v reference v topic]','k h26fu[v topic v item v reference]')
    text+='d r5kn[source a person a role a reference d] c['+both('g item a['+owed+']','f item a[y['+owed+'][g topic a['+matched+']]]')+'].\n'
    text+='d r5ko[source a person a role a topic a reference d] c['+both('k h226u[v person v reference v topic]',
        'g item a['+both(owed,'k h26fu[v topic v item v reference]')+']')+'].\n'
    text+='d r5kp[bindings j[a] reference d] e[b point['+bind(('person','topic'),'k r5aa[v person v topic v reference v point]')+']].\n'
    inquiry=both('k r5ko[v source v person v role v topic v reference]','k h257z[v reference v candidate v point]',
        'k h256o[v person v candidate v point]','k h26fx[v person v activity v topic v reference]',
        't[k zzq[v person v activity]][v point]','k h26fv[v person v activity r[p r5kp] l[a][v person v topic] v reference v point]')
    text+='d r5kq[source a person a role a activity a topic a reference d candidate d point d] c['+inquiry+'].\n'
    acts='g activity a[g topic a[k r5kq[v source v person v role v activity v topic v reference v candidate v point]]]'
    bounded='k r5jd[v period v reference v candidate '+ANCHOR+' v end]'
    for name,where in (('r5kr','k h26e3[v period v reference v candidate v point]'),
        ('r5ks',both('k h257z[v reference v candidate v point]','x[e[v end][v point]][k ic[v end v point v candidate]]'))):
        body='g end d['+both(bounded,'g point d['+both(where,acts)+']')+']'
        text+='d '+name+'[bindings j[a] reference d] e[b candidate['+bind(NAMES,body)+']].\n'
    def policy(target,bindings,sign):return 'k h26ft[v person v response r[p '+target+'] '+bindings+' v reference '+sign+' '+ANCHOR+']'
    common=both('k r5kn[v source v person v role v reference]','t[k zzq[v person v response]]['+ANCHOR+']')
    deferred=both(common,'g end d['+bounded+']',policy('r5kr',FIVE,FALSE),policy('r5ks',FIVE,TRUE),
        'u['+policy('r5kr',FIVE,TRUE)+']','u['+policy('r5ks',FIVE,FALSE)+']','u['+policy('r5ku',FOUR,FALSE)+']')
    future=both('k h257z[v reference v candidate v point]','x[e['+ANCHOR+'][v point]][k ic['+ANCHOR+' v point v candidate]]',acts)
    text+='d r5ku[bindings j[a] reference d] e[b candidate['+bind(FOUR_NAMES,'g point d['+future+']')+']].\n'
    text+='d r5kt['+' '.join(n+' a' for n in NAMES)+' reference d candidate d] c['+deferred+'].\n'
    valid=both('k ta[i[at d][k h257z[v reference v candidate v at]] i[first d last d][k ic[v first v last v candidate]]]','k h257z[v reference v candidate '+ANCHOR+']')
    text+='d r5kv['+' '.join(n+' a' for n in FOUR_NAMES)+' reference d candidate d] c['+both(common,valid,policy('r5ku',FOUR,FALSE),'u['+policy('r5ku',FOUR,TRUE)+']',
        'f period a[u['+policy('r5ks',FIVE,TRUE)+']]')+'].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r5cl','r5aa','r5jd','zzq','h237z','h26ar','h226u','h26ad','h256o']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='personal_epistemic_duty_and_distinct_deferral_renunciation_choices',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
