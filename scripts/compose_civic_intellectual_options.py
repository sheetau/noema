"""Ground civic permissions and intellectual opportunities in fixed scopes."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/whole-view-sentence-basis-v1.json'
OLD='examples/v016/option-inclusion.noema';OLD_BASIS='data/apparent-liberty-basis-v1.json'
LIBRARY='examples/v016/civic-intellectual-options.noema';BASIS='data/civic-intellectual-options-basis-v1.json'
ACTION='i[h[a a] e]';TRUE='e[n p a b][n p a b]'
PRIMITIVES={
 'h26yo':('[a a a d] c',['community','person','activity','reference'],'同じ政治的共同体の成員について、市民として外的な共同生活の中で行えることを比較する全関連行為の範囲。移動・交流・生活上の選択などの実行内容をh26yrの閉じた記述で明らかにし、現在許される行為、成功者又は官職の職務だけを選ばない。比較する制度条件と評価候補を通じて同じ本人・行為の区切りを保持する。'),
 'h26yp':('[a a d d] a',['order','community','reference','point'],'同じ共同体・法秩序・固定基準について、その評価点で市民の行為を拘束又は許容する、公的な法秩序の規範的出所。個人の好み、教会の内部規則又は別の共同体の許可を借りず、対応する秩序とその運用はr6frで別に確かめる。規範的な権限・出所の指定であり、現に全ての法が守られることではない。'),
 'h26yq':('[a a d] a',['community','person','reference'],'同じ固定基準で同じ共同体の成員である当人が、市民的な共同生活の中で行為する立場。個別の官職の受託職務や学識者としての書面発表の立場に限定しない。比較両側で同じ立場への自由を比べる。'),
 'h26yr':('[a d] '+ACTION,['activity','reference'],'固定した行為と基準について、誰がその行為を実行するかを二引数の閉じたNoema内容で指定する記述。原語名や任意の真偽ラベルを実行内容とせず、対象行為の内容を明らかにする。許可を問うときに記述された実行を先に要求せず、本人・行為は規範側と同じ引数へ束縛する。'),
 'h26ys':('[a a a d] c',['community','person','task','reference'],'同じ政治的共同体の成員について、思考の自由を比較する全関連判断課題の範囲。ここでは民衆の精神の自由を、成員の自分の理解力と理由による判断活動の機会として読む。課題内容はh26ytの全事項とr6hhで構成し、実際に達成された課題だけを選ばない。市民的行為h26yoの範囲とは区別し、両者が重なる場合も同一とは推定しない。'),
 'h26yt':('[a a d] c',['task','matter','reference'],'同じ判断課題と固定基準で、その課題が問う全事項にこの事柄が含まれる。事柄は問い・判断の対象であり、支持理由や判断行為そのものとは分ける。課題の成功に合わせて事項を削らず、課題の非空性と全事項に対応する本人の判断を合成側で検査する。'),
 'h26yu':('[a a a d d] c',['person','task','judgment','reference','point'],'同じ本人のこの判断行為が、この固定基準・点で指定された課題の遂行に属する。別課題での判断の成功を流用せず、どの事柄についての判断か、自分の理解力の使用、理由の支持と他者の指導の不在は既存rcrとfbで別に構成する。'),
 'h26yv':('[a a d a a d] c',['community','task','reference','actor','method','point'],'同じ共同体・判断課題・固定基準の機会を評価する際、この行為者がこの点で実行できる方法。現在の法的許可だけや本人の既有の能力だけと同一視せず、当の制度条件における実効的な機会として指定する。実行済みとはしない。'),
 'h26yw':('[a a d a a d d] c',['community','task','reference','actor','method','point','outcome'],'同じ共同体・判断課題・固定基準・行為者・方法・起点の下で、その方法を実行したときの候補となる結果状況。別の制度・課題・本人へ替えず、方法を採る前の同じ条件を保つ。結果を現在の実行と同一視しない。'),
 'h26yx':('[a a d a a d d] c',['community','task','reference','actor','method','point','outcome'],'同じ方法・起点の候補のうち、明示した能力評価で考慮する全結果状況。目的を達成する結果だけを事後に選ばず、xa/xe/xfが非空性と候補との整合を検査する。未評価又は未知入力を不能へ置換しない。'),
}
MEANINGS={
 'r6hd':'同じ固定基準で、その政治的共同体の成員である人。単なる所在地、書面の読者、官職保持者又は実行済みの行為者だけへ範囲を替えない。',
 'r6he':'同じ人間の成員r6hdと、h26yoで固定するその人の全関連市民的行為の組。許可の大小に応じて比較対象者や活動を替えない。',
 'r6hf':'同じ市民的行為の組について、指定した法秩序を出所とする同じ本人・市民の立場・行為・閉じた実行内容への積極的な正極性許可と、負極性の要求の不在を既存rdmで確認する。行為の現実の実行・実行可能性・不実行への許可までは含意しない。',
 'r6hg':'同じ共同体・固定基準で、二つの指定された法秩序が対応する点で運用されることをr6frで確認し、全成員・全関連行為の市民的自由r6hfが低い側から高い側へ厳密に包含拡大することを既存rwvで構成する。数値一単位の差、時間的な先後又は別人口への交換とはしない。',
 'r6hh':'同じ人・判断課題・固定基準について、その課題の全事項が非空であり、各事項についてその同じ人の課題遂行に属する判断がある内容。各判断は本人の理解力を使い、用いた理由に支持され、他人の指導によらない既存rcrを満たす。異なる事項ごとに別の判断でもよく、一つの判断で全事項を同時に済ませることは要求しない。',
 'r6hi':'同じ成員と固定された精神的課題について、この点の方法・候補・評価結果を既存xdに渡し、r6hhの課題目標に達する方法があるという機会。思想の現実の実行又はその法的許可と分け、本人側だけの安定した既有能力へ読み替えない。',
 'r6hj':'r6hiと同じ成員・課題・基準・方法範囲について、達成方法を確認できるか全方法の評価範囲が整合する既存xfを要求する。課題目標の全事項が非空であることも別に要求し、対象のない課題を評価済みの不能へ通さない。',
 'r6hk':'同じ成員・非空の課題内容・固定基準・方法範囲について、既存xgによる評価済みの達成不能。xdの単なる否定、未評価、全世界・未来全体での不可能とは区別する。',
 'r6hl':'同じ成員・精神的課題の比較範囲が非空であり、その全組について比較する二点のr6hjがともに成立する。可能な課題だけを選ばず、一方で評価できない対象を除外しない。',
 'r6hm':'r6hlの両側の評価が整った同じ全範囲において、精神的課題の達成機会r6hiが低い側から高い側へ厳密に包含拡大する。件数だけの増加、別人の成功又は既存機会の喪失を伴う交換とは区別する。',
 'r6hn':'同じ共同体・二法秩序・固定基準・二評価点について、市民的許可の拡大r6hgと精神的課題の機会の拡大r6hmを連言する。市民的自由から精神の自由への含意・因果又は現実の利益を自動追加せず、後続の見かけの利益の内容としても使う比較構成。',
}
LIMITS=[
 'u0017第三文の市民的自由の程度と民衆の精神の自由への依存群。同じ成員と課題の固定範囲で、市民的自由は公的法秩序からの積極的許可、精神の自由は本人の理解力と支持理由による自立的な判断課題の達成機会として読む。二種類の自由を同じ許可又は同じ能力へ還元しない。',
 '民衆の精神はこの群では共同体成員に分布する判断の営みとして扱い、人と別に存在する一つの超個人的な心を実体化しない。各人が既に全てを判断したという主張も、全員が必ず改善するという条件も補わない。選択肢の比較は人と課題の組を保持し、一人の成功を他人の機会にしない。',
 '精神的課題は非空の全事項について、同じ本人が課題に属する判断を行い、その判断がrcrと同じ事項へのfbを満たすことから構成する。理由の正当化や理解力の所有という既存基本関係を使う。全知・全専門技能・芸術的想像・感情の全側面を一律にこの判断課題へ含めたという一般定義は主張しない。',
 '程度の比較には、固定した人・活動範囲における厳密包含を採る。一部を失って別の重要な機会を得る比較はこの順序では比較不能になる。大小を数値差や時間順序へ変換せず、法的許可に物理的実行を要求しない。規範が未知の場合と、既知だが積極的許可がない場合も分ける。',
 '精神的機会の比較では両側の全対象の能力評価を確かめる。今の方法と条件に相対的な機会であり、通常機会下の本人の既有能力、訓練後の永久的な能力又は未評価の方法の不存在ではない。全課題の一斉遂行や、全成員で共有する一つの方法を要求しない。',
 'r6hnだけでは因果的な利益、scheintの見え方、dochの対照、越えがたい障壁、低い側が与える展開の余地、全能力、jener/diesemの照応と全文帰属を記述し終えない。次に同じ二制度条件を見かけの候補・障壁・発展機会へ接続する。旧apparent-liberty等の草案と確認済み本文121主張・19全単位判断は変更しない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def legacy():
    doc=parse((ROOT/OLD).read_text(encoding='utf-8'));means=json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions']
    return closure(doc,('rwv',)),{n:means[n] for n in ('rwu','rwv')}
def definitions():
    text='d r6hd[person a community a reference d] c['+both('k aa[v person]','k h237c[v person v community v reference]')+'].\n'
    text+='d r6he[community a person a activity a reference d] c['+both('k r6hd[v person v community v reference]','k h26yo[v community v person v activity v reference]')+'].\n'
    text+='d r6hf[community a order a person a activity a reference d point d] c['+both('k r6he[v community v person v activity v reference]',
      'k rdm[k h26yp[v order v community v reference v point] v person k h26yq[v community v person v reference] v activity k h26yr[v activity v reference] '+TRUE+' v point p h7a p h7b]')+'].\n'
    fields='community a lowerorder a higherorder a reference d lower d higher d'
    people='i[person a][k r6hd[v person v community v reference]]';civil='i[person a activity a][k h26yo[v community v person v activity v reference]]'
    sides=['i[person a activity a outer d][k r6hf[v community v '+side+'order v person v activity v reference v '+side+']]' for side in ('lower','higher')]
    text+='d r6hg['+fields+'] c['+both('k r6fr[v community v lowerorder v reference v lower]','k r6fr[v community v higherorder v reference v higher]',
      'k rwv['+people+' '+civil+' '+' '.join(sides)+' v reference]')+'].\n'
    matters='k h26yt[v task v matter v reference]'
    judgment=both('k h26yu[v person v task v judgment v reference v point]','k fb[v judgment v matter v point]',
      'k rcr[v person v judgment v point p ab p ac p fa p fb p fc p fd p ad]')
    text+='d r6hh[person a task a reference d] e[b point['+both('k aa[v person]','g matter a['+matters+']',
      'f matter a[y['+matters+'][g judgment a['+judgment+']]]')+']].\n'
    mental=both('k r6hd[v person v community v reference]','k h26ys[v community v person v task v reference]','g matter a['+matters+']')
    providers=' '.join(('i[actor a method a point d][k h26yv[v community v task v reference v actor v method v point]]',
      'i[actor a method a point d outcome d][k h26yw[v community v task v reference v actor v method v point v outcome]]',
      'i[actor a method a point d outcome d][k h26yx[v community v task v reference v actor v method v point v outcome]]'))
    for n,target in (('r6hi','xd'),('r6hj','xf'),('r6hk','xg')):
        text+='d '+n+'[community a person a task a reference d point d] c['+both(mental,'k '+target+'[v person k r6hh[v person v task v reference] v point '+providers+']')+'].\n'
    chosen=both('k r6hd[v person v community v reference]','k h26ys[v community v person v task v reference]')
    text+='d r6hl[community a reference d lower d higher d] c['+both('g person a[g task a['+chosen+']]',
      'f person a[f task a[y['+chosen+']['+both('k r6hj[v community v person v task v reference v lower]','k r6hj[v community v person v task v reference v higher]')+']]]')+'].\n'
    sides=['i[person a task a outer d][k r6hi[v community v person v task v reference v '+side+']]' for side in ('lower','higher')]
    text+='d r6hm[community a reference d lower d higher d] c['+both('k r6hl[v community v reference v lower v higher]',
      'k rwv['+people+' i[person a task a][k h26ys[v community v person v task v reference]] '+' '.join(sides)+' v reference]')+'].\n'
    text+='d r6hn['+fields+'] c['+both('k r6hg[v community v lowerorder v higherorder v reference v lower v higher]',
      'k r6hm[v community v reference v lower v higher]')+'].\n'
    return text
def build():
    p=parent();doc=deepcopy(p.document);doc.update(declarations=closure(p.document,('r6fr','rdm','h7a','h7b','rcr','xd','xf','xg','ab','ac','fa','fb','fc','fd','ad','h237c')),statements=[])
    imported={d['name']:p.entries[d['name']] for d in doc['declarations']};ds,means=legacy()
    for d in ds:
        if d['name'] in imported:assert d==imported[d['name']]['declaration'] and means[d['name']]==imported[d['name']]['meaning_ja']
        else:doc['declarations'].append(d)
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(p.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(p.source_sha256)|{OLD,OLD_BASIS}
    basis=dict(status='fixed_civic_permissions_and_intellectual_opportunities_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|means|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|{n:OLD_BASIS for n in means},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
