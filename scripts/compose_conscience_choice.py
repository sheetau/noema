"""Compose each person's freedom of their own reasoning on conscience matters."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind

PARENTS=('data/religious-freedom-policy-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/conscience-choice.noema';BASIS='data/conscience-choice-basis-v1.json'
GOAL='i[h[a] e]'
NAMES=('actor','person','community','matter','judgment')
FIELDS=' '.join(n+' a' for n in NAMES)+' reference d'
ARGS=' '.join('v '+n for n in NAMES)+' v reference'
ROLE='k h26ny[v person v community v reference]'
THREE='l[a][v person v matter v judgment]'
FIVE='l[a][v person v community v matter v judgment '+ROLE+']'
PRIMITIVES={
 'h26nw':('[a a d d] c',['person','matter','reference','candidate'],
  '固定基準の同じ本人・事柄の道徳的自己判断への関わりを分類するために考慮する事例状況の全範囲。この候補はその範囲に属する。事柄や本人を別の対象にすり替えず、肯定的な分類結果だけを選ばない。現実に判断した履歴、本人の現有能力で実現できる経路、許可された行為だけには限定しない。候補内の判断主体・対象・自己評価の内容はfa/fb/seで別に構成する。'),
 'h26nx':('[a a a d] c',['person','matter','judgment','reference'],
  '同じ固定基準で、同じ本人が同じ事柄について自身の理性で判断する活動の全候補を記述する個体索引。この判断索引が範囲に入る。成功例、正しい結論、許可済み又は現に実行できる活動だけに狭めない。実行時の条件は別のNoema式で構成し、索引への所属から実際の判断・能力・自由を導かない。'),
 'h26ny':('[a a d] a',['person','community','reference'],
  '同じ共同体・固定基準で、本人が自身に関わる道徳上・信仰上の事柄を自身の責任で吟味・判断する側の立場。宗教的信仰を持つ人だけ又は救済に必要と考える営みだけに限定しない。他人に委ねられた公的職務の遂行とは次元を分けるが、この別立場を名目として同じ自己判断への強制を自由と呼ばない。実行・能力・許可をこの立場参照だけでは主張しない。'),
 'h26nz':('[a a a a a d d] c',list(NAMES)+['reference','point'],
  '同じ統治側・本人・共同体・事柄・判断候補・固定基準・点について、本人の道徳的自己判断の立場に対する両極性の要求と許可、統治側が関与する権威的・強制的介入の有無が評価されている。自由や能力そのものと分け、未知を介入又は要求の不在へ変えない。候補範囲は結果を見る前に固定する。'),
}
MEANINGS={
 'r5y3':'同じ人・事柄・固定基準について、完全な分類用候補範囲h26nwをhzgqへ渡し、その同じ本人による同じ事柄への道徳的自己評価の事例がある。現実に自責した事柄だけ、宗教に属する事柄だけへ縮めない。',
 'r5y4':'同じ人・事柄・判断について、本人の理解力の所有と使用、同じ事柄の判断、用いた理由、他者によるその判断の指導の不在を要求する。rcrの支持条件だけを恒真関係に置き換え、誤った推論や支持のない理由の判断を自由の対象から除かない。',
 'r5y5':'r5y3の良心に関わる同じ事柄とh26nxの全判断候補索引を結ぶ。本人が現在行った判断や許可された判断だけで全称範囲を作らない。',
 'r5y6':'本人・事柄・判断の正確な三対象列を同じr5y5候補とr5y4の実行内容へ結ぶ。何らかの事柄への一つの判断で別の候補を代用しない。',
 'r5y7':'本人・共同体・事柄・判断・立場の正確な五対象列を、同じh26nyの自己判断の立場とr5y6へ結ぶ。内容に明示した立場を介入判定へ渡す。',
 'r5za':'同じ統治側から同じ本人・立場・事柄・判断候補・基準・点へ、実行要求も不実行要求もない。規範の沈黙だけでは積極的許容や非介入としない。',
 'r5zb':'r5zaと同じ候補内容の実行と不実行の双方が積極的に許容される。反対の要求との衝突も除く。',
 'r5zc':'同じ活動の生起と同じ統治側の参加を、同じ本人のr5y7の自己判断へのh26hoの権威的・強制的介入へ結ぶ。別人・別活動の条件を寄せ集めない。',
 'r5zd':'同じ良心事項・本人の判断候補について、r5zbの両方向の許容と、その統治側が関与するr5zcの介入の不在を合わせる。実際の判断・能力・全主体からの自由は導かない。',
 'r5ze':'同じ本人の全良心事項について、各事柄の判断候補が非空であり、全候補の規範・介入評価が揃う。本人は人であることを要求するが、良心事項のない人を集団から除外しない。',
 'r5zf':'同じ統治側・共同体・基準について、各人のr5zeの評価と全良心事項の全判断候補のr5zdを求める人物性質。受益者を自由にされる同じ本人へ直接適用できる。',
 'r5zg':'r5tyの非空で人だけから成る固定集団の全成員へ、同じr5zfを適用する。全人類又は現在人口との完全一致は本文側の範囲条件と結ぶ必要があり、この関数だけで対象集団を認定しない。',
 'r5zh':'統治側・共同体・固定基準の閉じた呼称をr5zfへ適用して、受益者を引数とする自由の状態記述を作る。規範内容の引用を構築するだけで判断実行を要求せず、基本関係g3へ渡す段階0の状態記述として型検査する。',
 'r5zi':'r5zhへ渡す統治側・共同体・基準の閉じた呼称を元の三対象へ照合する。後続の功績・恩恵の接続で別の統治側や基準へすり替えない。',
}
LIMITS=[
 'u0015第一文末のJedem ... in allem, was Gewissensangelegenheit ist, seiner eigenen Vernunft zu bedienenへ向けた具体的な自由内容。政府側からの解放の出来事、最初の達成、称揚・恩恵との同一出来事への束縛、一文全体はまだ完成ではない。',
 '良心事項は同じ本人の行為・選択の道徳的自己評価に関わる事柄として読む。信仰上の事柄を含めうるが、宗教だけ、現に罪悪感を持つ事柄だけ、既に正しく判断できる事柄だけにしない。DWBのGewissenssacheを補助とし、カントの後年の良心論全体を1784年へ移さない。',
 '分類用事例は現実の履歴や本人の実行能力とは別で、h26nwで全候補範囲を固定する。その範囲の完全な供給は解釈の責任であり、有限検査で現実世界の全事柄の列挙を証明しない。',
 '自身の理性使用は、本人の理解力を用い理由を伴って同じ対象を自分で判断する読みとする。今その判断を他人に指導してもらうこととは区別するが、過去に学んだこと・助言・議論一般を禁じない。判断の正しさ・理由の正当な支持・確実さ・上手さを自由の必要条件にしない。',
 'freiは同じ統治側に相対的な両方向の許容、両方向の指図の不在、その統治側が関与する権威的・強制的介入の不在とする。他の独立主体からの全自由、実際の理性使用、実行能力、新しい立法行為をこの状態内容からは推論しない。',
 '各人・各事柄の全判断候補を量化する。一人につき一つだけ、正しい又は現に可能な候補だけの許容にしない。該当する良心事項がない本人も人々から除かず、その人への全称は空範囲でよいが、該当事柄があるなら判断候補と評価の欠落を拒否する。',
 '本文で固定する全人間範囲・君主と政府側の関係、自由を生じさせた変化と出来事・zuerst・wenigstens・解放の意味、規範的称揚の基準・著者帰属は次の統合に残る。112主張、v196、17単位判断と確認済み文字数は据え置く。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def definitions():
    text='d r5y3[person a matter a reference d] c['+both('k aa[v person]',
        'c[k hzgq[i[candidate d][k h26nw[v person v matter v reference v candidate]]]][v person v matter]')+'].\n'
    judging='k rcr[v person v judgment v point p ab p ac p fa p fb p fc i[reason a decision a at d]['+TRUE+'] p ad]'
    text+='d r5y4[person a matter a judgment a] e[b point['+both('k aa[v person]',judging,'k fb[v judgment v matter v point]')+']].\n'
    candidate='k r5y5[v person v matter v judgment v reference]'
    text+='d r5y5[person a matter a judgment a reference d] c['+both('k r5y3[v person v matter v reference]','k h26nx[v person v matter v judgment v reference]')+'].\n'
    text+='d r5y6[bindings j[a] reference d] e[b point['+bind(('person','matter','judgment'),both(candidate,'t[k r5y4[v person v matter v judgment]][v point]'))+']].\n'
    text+='d r5y7[bindings j[a] reference d] e[b point['+bind(('person','community','matter','judgment','role'),both('e[v role]['+ROLE+']','t[k r5y6['+THREE+' v reference]][v point]'))+']].\n'
    target='v actor v person '+ROLE+' r b[p r5y6] '+THREE+' v reference '
    norm=lambda sign:'k h237z['+target+sign+' v point]'
    permit=lambda sign:'k h245c['+target+sign+' v point]'
    text+='d r5za['+FIELDS+' point d] c['+both('u['+norm(TRUE)+']','u['+norm(FALSE)+']')+'].\n'
    text+='d r5zb['+FIELDS+' point d] c['+both('k r5za['+ARGS+' v point]',permit(TRUE),permit(FALSE))+'].\n'
    text+='d r5zc['+FIELDS+' activity a point d] c['+both('k dg[v activity v point]','k df[v actor v activity v point]',
        'k h26ho[v activity v person r b[p r5y7] '+FIVE+' v reference v point]')+'].\n'
    text+='d r5zd['+FIELDS+' point d] c['+both(candidate,'k r5zb['+ARGS+' v point]','u[g activity a[k r5zc['+ARGS+' v activity v point]]]')+'].\n'
    scoped='k r5y3[v person v matter v reference]'
    checked=both('g judgment a['+candidate+']','f judgment a[y['+candidate+'][k h26nz['+ARGS+' v point]]]')
    text+='d r5ze[actor a person a community a reference d point d] c['+both('k aa[v person]','f matter a[y['+scoped+']['+checked+']]')+'].\n'
    text+='d r5zf[actor a community a reference d] h[a] e[i[person a][b point['+both('k r5ze[v actor v person v community v reference v point]',
        'f matter a[f judgment a[y['+candidate+'][k r5zd['+ARGS+' v point]]]]')+']]].\n'
    text+='d r5zg[actor a group a community a reference d] e[b point['+both('k r5ty[v group v reference]',
        'f person a[y[k h246c[v group v person v reference]][t[c[k r5zf[v actor v community v reference]][v person]][v point]]]')+']].\n'
    text+='d r5zh[actor i[a] community i[a] reference i[d]] '+GOAL+'[o a[r[p r5zf]][v actor v community v reference]].\n'
    text+='d r5zi[actor a community a reference d] c['+both('e[s[k h223g[v actor]]][v actor]','e[s[k h223g[v community]]][v community]','e[s[k h223h[v reference]]][v reference]')+'].\n'
    return text
def build():
    doc=deepcopy(parents()[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(parents(),(['h237z','h245c','h26ho','dg','df','r5ty','h246c','h223g','h223h'],['aa','hzgq','rcr','ab','ac','fa','fb','fc','ad'])):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(p.entries) for p in parents()))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(p.source_sha256) for p in parents()))
    basis=dict(status='each_person_all_conscience_matters_and_government_relative_choice',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
