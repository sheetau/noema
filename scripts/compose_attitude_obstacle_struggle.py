"""Connect foreign acquisition, plural obstacles and necessary counteractivity."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,STATE as ASSIGNMENT
from scripts.compose_paired_influence import MATCH
from scripts.compose_social_attitude_paths import STATE,MAPS,REGIONS,REGION_FIELDS,REGION_ARGS

PARENTS=('data/social-attitude-paths-basis-v1.json','data/government-self-misunderstanding-basis-v1.json','data/public-offers-sentence-basis-v1.json')
LIBRARY='examples/v016/attitude-obstacle-struggle.noema';BASIS='data/attitude-obstacle-struggle-basis-v1.json'
WITNESSES=(('first','a'),('rest','j[a]'),('history','h[d] c'),('before','h[d d] c'),*((n,'h[a] '+t) for n,t in MAPS))
WITNESS_FIELDS=' '.join(n+' h[d] '+t for n,t in WITNESSES)
WITNESS_ARGS=' '.join('v '+n for n,t in WITNESSES)
GOAL_FIELDS=REGION_FIELDS+' origin a target a reference d '+WITNESS_FIELDS
GOAL_ARGS=REGION_ARGS+' v origin v target v reference '+WITNESS_ARGS
MODELS=(('variables','j[a]'),('equations','h[a '+ASSIGNMENT+'] c'),('factor','a'),('worlds','h['+ASSIGNMENT+'] d'),('matches',MATCH),('evaluated','h[d] c'))
MODEL_FIELDS=' '.join(n+' h[a] '+t for n,t in MODELS)
MODEL_ARGS=' '.join('v '+n for n,t in MODELS)
PRIMITIVES={
 'h26pn':('[a a a '+STATE+' d d] c',['activity','condition','beneficiary','state','reference','point'],
   'この活動は、同じ条件が同じ受け手による記述された状態の取得又は保持を損なう働きに対し、その働きを避け、抑え、又は乗り越えるように向けられている。状態は閉じた段階2人物性質で指定する。活動と条件の単なる併存、無関係な状態の防衛、条件を強める活動と区別する。回避・対抗の方向性であり、活動の生起・努力・実際の妨害・成功・条件の除去・特定の政治的手段は別に確認する。'),
 'h26po':('[a a d d] c',['person','activity','reference','point'],
   '本人が同じ活動において、固定した文脈の基準に照らして相応の精神的又は身体的な力を実際に投入して取り組む。単なる願望、偶然の参加、無関係な別活動の負担と区別する。仕事全般や最小限の動作だけから努力とせず、最大限の能力投入・疲労・苦痛・数値的な強度・継続時間の下限・成功は必須としない。'),
}
MEANINGS={
 'r57a':'同じ元と先の統治圏・元の人・国外の取得者・自由方針の基準を固定し、候補状況ごとの経路証人・履歴・順序・各段階の対応をr56xへ渡す国外到達と保持の目標内容。実際の一経路を全仮定状況へ固定せず、候補ごとに同じ態度の実取得と保持を評価する。',
 'r57b':'同じ目標と営みの実内容について、指定された関連経過の少なくとも一つで目標が達し、その目標が達する全経過で営みもある。r5nlの非空虚な目的相対的必要性を宗教目的から分けた一般構成。必要性から十分性・現実の達成・法的義務を導かない。',
 'r57c':'人である同じ当事者が同じ生起活動へ参加し、その活動に文脈上相応の力を投入するh26po。方法経路で努力が要るhzwzとは異なり、実際の努力活動を述べる。',
 'r57d':'同じ態度を実際に持つ当事者の活動が、その態度の表れr56qであり、実際の努力r57cを伴い、同じ受け手の同じ態度の取得・保持を妨げる条件の働きに対抗する方向h26pnを持つ。精神そのものを人や活動へ型変換せず、態度を担う人の営みとして構成する。',
 'r57e':'同じ自由方針への態度r56oを保ち、同じ受け手・条件・固定基準についてr57dの当事者と活動が存在する内容。当事者は受け手と同一でも別人でもよく、受け手本人だけの努力へ限定しない。',
 'r57f':'少なくとも二つの異なる条件を含む指定列について、同じ政府の自己誤解と、各条件の同じ人への外的性格・現在の公的適用を求める。条件ごとの妨害モデルは全て同じ一つの目標命題を比較し、重複一条件を複数と数えない。',
 'r57g':'指定された全ての条件について、同じ人の同じ自由への態度を対象とするr57eの対抗的な努力活動がある内容。一条件への努力だけで他条件を補わず、活動者と活動は条件ごとに存在量化して同一でも別でもよい。',
 'r57h':'関連経過範囲が非空で、その全経過において、指定全条件が同じ政府・共同体に由来し同じ人に外的な適用条件r564として残る。障害を先に取り去った別背景の達成から、障害下での必要性を否定又は証明しない。',
 'r57i':'同じ国外取得者について、実際の到達・保持r57a、同じ外国政府の自己誤解と複数の潜在的障害r57f、現にある対抗的努力r57g、同じ障害背景r57hの下でその目標に相対的な努力の必要性r57bを接続する。目標・受け手・外国政府・条件・固定基準を取り違えない。',
}
LIMITS=[
 'u0015第三文のerは同じ自由への態度を指し、ringenはその態度を担う人々による、当該態度の取得・保持に対する外的障害への努力を伴う対抗と読む。物体同士の格闘、政府の打倒、特定の政治活動、障害の消滅や克服完了は要求しない。',
 '態度保持者の同じ活動が態度の表れであり、努力と対抗の方向性を持つことを別々に確認する。受け手自身だけに努力を負わせず、他の保持者の同じ受け手への働きかけも許す。対抗の方向性だけで妨害や成功を認定しない。',
 'zu ringen hatはこの障害背景で同じ到達・保持に対抗的努力が要るという目的相対的必要性と読む。現実の努力も別に述べる。目的が達する可能経過があり、その全てに努力があることを要求し、目的達成不能から空虚に何でも必要としない。努力の十分性や規範源による義務にはしない。',
 'Hindernissenの複数を、文脈で指定する少なくとも二つの異なる条件がある読みで保持する。一規則の異なる適用条件は区別してよいが、同じ一条件の重複列だけを複数と数えない。全宇宙の障害の網羅や全条件への同一人物による抵抗は要求しない。',
 '各介入候補にはその候補に属する経路証人・履歴・順序を与える。現実の証人を全候補へ固定せず、同じ元と先の共同体・対象者・態度内容は固定する。証人を選び損ねたことを不可能性や妨害と同一視しないため、供給された経路束は候補内で到達が成立すればそれを示せるものとする。この十分性と比較モデル・可能経過範囲の現実適合は明示した解釈入力であり有限検査で実証しない。',
 '必要性の候補範囲は背景条件を固定した関連する全実践的経過とし、達成又は努力の有無から事後選別しない。各候補で同じ障害が適用されることをr57hで検査する。介入比較の条件なし側と、障害がある下での必要性の範囲は分ける。評価点は関連経過を含めて読むことができ、全活動の物理的同時発生を強制しない。',
 '本文の具体的な統治圏・経路・妨害モデル・関連経過の設定、先行自由例と同じ精神への照応、auch/selbst、全文帰属と通読は未接続。本文114主張、17全単位判断と追加二文763文字を保持し、第三文の意味確認文字数は増やさない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def app(n,arg):return 'c[v '+n+']['+arg+']'
def definitions():
    w=lambda n:app(n,'v candidate')
    path=REGION_ARGS+' '+w('first')+' '+w('rest')+' v origin v target v reference '+w('history')+' '+w('before')+' '+' '.join(w(n) for n,t in MAPS)+' v candidate'
    text='d r57a['+GOAL_FIELDS+'] e[b candidate[k r56x['+path+']]].\n'
    selected='c[v cases][v outcome]';goal='t[v goal][v outcome]'
    text+='d r57b[goal e undertaking e cases h[d] c] c['+both('g outcome d['+both(selected,goal)+']','f outcome d[y['+both(selected,goal)+'][t[v undertaking][v outcome]]]')+'].\n'
    text+='d r57c[actor a activity a reference d point d] c['+both('k aa[v actor]','k dg[v activity v point]','k df[v actor v activity v point]','k h26po[v actor v activity v reference v point]')+'].\n'
    text+='d r57d[actor a target a activity a condition a state '+STATE+' reference d point d] c['+both('k aa[v target]',
        'k r56q[v actor v activity v state v point]','k r57c[v actor v activity v reference v point]',
        'k h26pn[v activity v condition v target v state v reference v point]')+'].\n'
    text+='d r57e[target a condition a reference d] e[b point['+both('e[s[k h223h[v reference]]][v reference]',
        'g actor a[g activity a[k r57d[v actor v target v activity v condition k r56o[k h223h[v reference]] v reference v point]]]')+']].\n'
    member=lambda n:'k hg[v conditions v '+n+']'
    plural='g first a[g second a['+both(member('first'),member('second'),'u[e[v first][v second]]')+']]'
    model=' '.join(app(n,'v condition') for n,t in MODELS)
    per=both('k r564[v government v community v target v condition v reference v point]',
        'k r566[v condition v reference '+model+' v goal]')
    text+='d r57f[government a community a target a conditions j[a] reference d point d goal e '+MODEL_FIELDS+'] c['+both(plural,
        'k r563[v government v community v reference v point]','f condition a[y['+member('condition')+']['+per+']]')+'].\n'
    text+='d r57g[target a conditions j[a] reference d] e[b point[f condition a[y['+member('condition')+'][t[k r57e[v target v condition v reference]][v point]]]]].\n'
    context='k r564[v government v community v target v condition v reference v outcome]'
    text+='d r57h[government a community a target a conditions j[a] reference d cases h[d] c] c['+both('g outcome d['+selected+']',
        'f outcome d[y['+selected+'][f condition a[y['+member('condition')+']['+context+']]]]')+'].\n'
    targetgoal='k r57a['+GOAL_ARGS+']';undertaken='k r57g[v target v conditions v reference]'
    text+='d r57i['+GOAL_FIELDS+' conditions j[a] anchor d '+MODEL_FIELDS+' cases h[d] c] c['+both(
        't['+targetgoal+'][v anchor]',
        'k r57f[v government v foreigncommunity v target v conditions v reference v anchor '+targetgoal+' '+MODEL_ARGS+']',
        't['+undertaken+'][v anchor]',
        'k r57h[v government v foreigncommunity v target v conditions v reference v cases]',
        'k r57b['+targetgoal+' '+undertaken+' v cases]')+'].\n'
    return text
def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for c,roots in zip(sources,(['r56x','r56q','r56o','h223h','aa','dg','df'],['r563','r564','r566'],['hg'])):
        for d in closure(c.document,roots):
            n=d['name'];e=c.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(c.entries) for c in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in sources))
    basis=dict(status='foreign_attitude_plural_obstacles_and_necessary_counteractivity_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
