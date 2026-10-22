"""Compose self-initiated departure with qualitative, possibly nonmonotone progress."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/deliberate-retention-basis-v1.json','data/manifest-example-sentence-basis-v1.json')
LIBRARY='examples/v016/gradual-self-departure.noema';BASIS='data/gradual-self-departure-basis-v1.json'
TIME='history h[d] c before h[d d] c first d last d'
TARGS='v history v before v first v last'
PROFILE=TIME+' assessed h[d] c atleast h[d d] c'
PRIMITIVES={
 'h26rl':('[a d d d] c',['person','reference','left','right'],
   '同じ人・固定基準について、左点の思考や判断習慣の形成が右点以上に進んでいる。未陶冶h26rhで扱うのと同じ形成面を比較する。単一の知識の数や人格全体の道徳的価値、他人の成長との比較ではない。同程度を許す質的比較で、具体的な数値尺度・速度を原文に補わない。全関連点の評価・比較の整合性は合成側で検査する。'),
 'h26rm':('[a d d d] c',['person','reference','first','last'],
   '同じ人・固定基準の形成度について、第一点から第二点への正の増分が、この文脈で一段の漸進として扱う小ささの範囲内に収まる。零又は負の増分も許容範囲内とする。小ささの基準は結果を見て選び直さず、比較期間内で固定する。段階数・実時間の速度・数値上限・完全な連続性そのものではない。大きな区間の途中に小段階があるかは別に検査する。'),
 'h26rn':('[a a d d d] c',['person','process','reference','first','last'],
   '同じ人のこの期間の形成過程は、本人の関心・経験・検討に発する働きかけとして進み、外部の他者が個々の課題や方法を逐次決定してその人を動かすことを発生の条件としない。本人の関与だけ又は外的妨害がないだけとは区別する。von selbstを自己からの働きかけとして読む。助言・学習機会・教育・協力・他の原因を一律に排除せず、全活動の無意図性、単独の十分原因、努力不要、完全な自律能力を追加しない。'),
 'h26ro':('[a d d] c',['person','reference','point'],
   '同じ人・固定基準・点について、未陶冶の状態と、その同じ形成面を他の関連点と比較するための入力が評価済みである。高い形成度や状態からの離脱の成功を意味しない。欠測・未観測・未知を以前の未陶冶や進行なしへ補わない。比較関係自体は別に与える。'),
}
MEANINGS={
 'r6aw':'同じ厳密な順序付き履歴の異なる始終点を含む全区間で評価がそろい、形成度の比較が反射的・推移的・比較可能な前順序となる。同程度の異なる点を同一時点へ縮めず、実時間の間隔や数値差を要求しない。',
 'r6ax':'r6awの同じ区間・尺度で終点が始点より高く、その間に両端と厳密に異なる中間の形成度がある。小幅範囲を超える全ての正の増分には途中の厳密な中間値を要求し、隣接点の大きな跳躍も拒否する。零・負の増分は許容されることも確認し、途中の後退を禁止しない。',
 'r6ay':'同じ固定基準で人aaが未陶冶r6apから外れている状態。人でない対象の単なる否定を離脱成功とせず、全分野での完成や永続的な維持へ強めない。',
 'r6az':'同じ本人の同じ過程が、同じ履歴の前後で未陶冶からその不成立へ移すrcpを構成する。本人の能動的関与と精神的な部分への自己形成h4o、同じ非未陶冶の記述を生じさせるg3を結ぶ。単なる前後差や別人の仕事を成果にしない。',
 'r6a2':'r6azの同じ本人・過程・区間へ、本人の関心・経験・検討から進むh26rnを結ぶ。活動の実際の因果的成果と自己からの働きかけを分け、他者の助力の全面禁止や、妨害不在からの自動的な達成を加えない。',
 'r6a3':'同じ本人・基準・区間のどの二点でも、一方が未陶冶で他方がそこから外れていれば、後者の形成度が前者より厳密に高い。状態区分と段階比較を別の尺度にして混ぜない。未陶冶の内部にも、その外側にも複数の形成度を許す。',
 'r6a4':'同じ本人・過程・基準・全区間の自己からの離脱r6a2と、同じ形成面の質的な漸進r6ax、状態区分との整合r6a3を結ぶ。形成度の比較・小幅範囲・評価済みは全て同じ本人と基準へ固定する。',
}
LIMITS=[
 'u0015第五文arbeiten sich von selbst nach und nach aus der Rohigkeit herausへの依存群。未陶冶r6apから抜け出す変化を、本人の精神的な営みへの働きかけと、その人に同じ結果を生じさせる関係で構成する。未成熟bfや完全な自律能力upとは同一視しない。',
 'von selbstは本人の関心・経験・検討からの自己活動という読み。全ての活動が無意図、他人の助けがない、環境に依存しない、何も努力しなくても変わるという内容にはしない。先行の非介入条件はまだここに仮定していない。',
 'nach und nachは、同じ形成面に少なくとも二段階の厳密な進行があり、一段として大きい正の跳躍だけでは説明しない質的な読み。途中の停滞や後退を許す。数値尺度、障害件数、全区間単調増加、実時間当たりの速度、解析的連続性は原文に補わない。',
 '小幅の基準と時点範囲は固定された解釈入力で、結果に合わせた刻みの間引きや基準変更を許さない。大きな前後差には中間時点だけでなく厳密な中間の形成度を求める。有限検査が現実の全時点や尺度の正当性を証明したとはしない。',
 '既存rcpは同じ変化過程を本人の自己形成活動として扱い、その終端で生起・参加・作業・結果生成を結ぶ粒度である。瞬間的な活動だけには限定しない。形成の全ての部分活動・神経機構・唯一原因性・以後の永久的な保持を要求しない。',
 '過程は候補履歴の前後の達成内容として記述する。本文では非介入の条件の下でこの過程があるという作用域へ入れる必要があり、現在既に全員が未陶冶から出たことを主張しない。全関連時機・保持目的期間にわたる非介入、Die Menschenの範囲、条件とnur、本文設定・全文帰属は未接続。',
 '正本116主張、17全単位判断＋四文1033文字を保持し、第五文の意味確認文字数を増やさない。原刊seiの訂正記録v2を参照する。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def inside(n):return 'c[k rlz['+TARGS+']][v '+n+']'
def compare(a,b):return 'c[v atleast][v '+a+' v '+b+']'
def strict(a,b):return both(compare(a,b),'u['+compare(b,a)+']')
def every(names,body):
    for n in reversed(names):body='f '+n+' d[y['+inside(n)+']['+body+']]'
    return body
def definitions():
    order=both(every(('left',),compare('left','left')),
        every(('left','right'),'x['+compare('left','right')+']['+compare('right','left')+']'),
        every(('left','middle','right'),'y['+both(compare('left','middle'),compare('middle','right'))+']['+compare('left','right')+']'))
    text='d r6aw['+PROFILE+'] c['+both('k ta[v history v before]','c[v history][v first]','c[v history][v last]','c[v before][v first v last]',
        every(('point',),'c[v assessed][v point]'),order)+'].\n'
    intermediate=lambda a,b:'g middle d['+both(inside('middle'),'c[v before][v '+a+' v middle]','c[v before][v middle v '+b+']',strict('middle',a),strict(b,'middle'))+']'
    large=both('c[v before][v left v right]',strict('right','left'),'u[c[v small][v left v right]]')
    text+='d r6ax['+PROFILE+' small h[d d] c] c['+both('k r6aw['+TARGS+' v assessed v atleast]',strict('last','first'),intermediate('first','last'),
        every(('left','right'),'y['+compare('left','right')+'][c[v small][v left v right]]'),
        every(('left','right'),'y['+large+']['+intermediate('left','right')+']'))+'].\n'
    text+='d r6ay[reference d] h[a] e[i[person a][b point['+both('k aa[v person]','u[t[c[k r6ap[v reference]][v person]][v point]]')+']]].\n'
    fields='person a process a reference d '+TIME
    text+='d r6az['+fields+'] c['+both('k aa[v person]','e[s[k h223h[v reference]]][v reference]',
        'k rcp[v history v before v person v process v first v last c[k r6ap[v reference]][v person] c[k r6ay[v reference]][v person] o a[r[p r6ay]][k h223h[v reference]] p ag p la p dg p df p h4o p g3]')+'].\n'
    text+='d r6a2['+fields+'] c['+both('k r6az[v person v process v reference '+TARGS+']','k h26rn[v person v process v reference v first v last]')+'].\n'
    classified=both('t[c[k r6ap[v reference]][v person]][v left]','t[c[k r6ay[v reference]][v person]][v right]')
    higher=both('k h26rl[v person v reference v right v left]','u[k h26rl[v person v reference v left v right]]')
    text+='d r6a3[person a reference d '+TIME+'] c['+every(('left','right'),'y['+classified+']['+higher+']')+'].\n'
    text+='d r6a4['+fields+'] c['+both('k r6a2[v person v process v reference '+TARGS+']',
        'k r6ax['+TARGS+' i[point d][k h26ro[v person v reference v point]] i[left d right d][k h26rl[v person v reference v left v right]] i[left d right d][k h26rm[v person v reference v left v right]]]',
        'k r6a3[v person v reference '+TARGS+']')+'].\n'
    return text
def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for c,roots in zip(sources,(['r6ap','h223h','aa'],['rcp','ag','la','dg','df','h4o','g3','ta','rlz'])):
        for d in closure(c.document,roots):
            n=d['name'];e=c.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(c.entries) for c in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in sources))
    basis=dict(status='gradual_self_initiated_departure_from_uncultivated_state_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
