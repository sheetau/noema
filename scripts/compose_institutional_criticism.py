"""Keep a religious order and every citizen's public written criticism together."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE

PARENT='data/legislative-touchstone-basis-v1.json'
LIBRARY='examples/v016/institutional-criticism.noema'
BASIS='data/institutional-criticism-basis-v1.json'
CHOICES=('making','presenting','scholar','notes','audience','field')
NAMES=('community','regime','person',*CHOICES)
FIELDS=' '.join(n+' a' for n in NAMES)+' reference d candidate d point d'
ARGS=' '.join('v '+n for n in NAMES)+' v reference v candidate v point'
FRAME='community a regime a reference d candidate d point d'
FRAME_ARGS='v community v regime v reference v candidate v point'
PRIMITIVES={
 'h26cs':('[a a d] c',['regime','community','reference'],'この制度配置は、同じ政治的共同体における宗教上の教え・礼拝・奉仕の共同行為を、規則や役割と運営の仕組みによって組織するものとして位置付く。宗教組織という人々の集団、単独の信条文書、個人の内心だけとは区別する。特定教派・現実の採用・真理・正当性は要求せず、配置の現在の存続は別に結ぶ。'),
 'h26ct':('[a a d] c',['field','regime','reference'],'同じ制度配置における宗教上の教え・実践・組織運営のあり方を扱う検討領域。今批評が許される話題だけへ縮めず、別制度・一人の無関係な私事や軍事組織の活動へ取り替えない。どの欠点を指摘するか、その真偽や是認は別に記述する。'),
 'h26cu':('[a a d d d] c',['person','community','reference','candidate','point'],'同じ固定基準と候補経過のこの点で、この人が同じ政治的共同体の市民に属する。各点での完全な成員範囲を指定し、批評済み・許可済み・学識者の肩書・聖職者・賛成者だけに限らない。選挙権、現代の国籍法、血統を補わず、時点間の加入・離脱も排除しない。人であることは利用側でも確認する。'),
 'h26cv':('[a a d d d] c',['regime','community','reference','candidate','point'],'この同じ候補経過のこの点に、指定された同じ宗教上の制度配置が、その政治的共同体で共同行為を組織する秩序として運用・維持されている。法案の検討、過去の一度の採用、別制度の存続、全成員の賛同や服従、正当性とは区別する。いつ導入されたかと存続する期間全体は別に構成する。'),
 'h26cw':('[a a d] a',['regime','community','reference'],'指定された制度配置の下で同じ共同体の市民に公的な批評の許否を与える制度上の規範の出所。固定基準で同じ出所を追跡し、各人・各時点の許可が得られるよう事後に出所を選び替えない。特定の統治者名・規制担当者やその道徳的正当性を補わず、許可と反対要求はh7l/h7kで同じ内容へ与える。'),
}
MEANINGS={
 'r5e5':'同じ政治的共同体・宗教上の制度・評価点の市民について、その制度の同じ検討領域への非空の欠点所見r33a、自分の作成活動h243yと学識者の使用r2zi、同じ作品を同じ本来の公衆へ書面で提供するr3z/h243zを結ぶ候補。制作済み・許可・欠点の真理・読者判断の達成や目的を選別条件にしない。',
 'r5e6':'同じ市民の同じ学識者の立場に、同じ制度の規範出所h26cwから、所見の作成r33g、同じ公衆への提出r33h、両方r33iのそれぞれについてrduの衝突のない積極的許可がある。全てに同じ点・本人・作品・活動を使い、両実行の許可だけで片方の禁止を見落とさない。実行は引用したまま扱う。',
 'r5e7':'同じ市民・制度・共同体・基準・候補点について、公的な批評の候補r5e5が少なくとも一つあり、その全候補に同じr5e6の自由がある。既に書けた所見や許可された活動だけへ範囲を絞らず、空の候補範囲を自由としない。',
 'r5fa':'同じ制度がh26csの宗教上の配置であり、その点の全市民h26cuについて、人であることと、その本人のr5e7の批評の自由を要求する。市民の帰属を固定基準の一時点の名簿に凍結せず、同じ候補の各評価点で追う。市民が一人もいない場合の普遍条件から市民の存在を追加しない。',
 'r5fb':'同じ共同体・制度・固定基準・候補経過・評価点で、その制度がh26cvにより存続し、全市民への批評の自由r5faがある。別制度や別時点の存続と自由を合算しない。導入や期間全体はこの一点の条件とは別である。',
 'r5fc':'同じ共同体・制度・固定基準・候補経過を固定したr5fbの時間内容。後続の期間・到達条件の構成へ渡せるが、この内容を作るだけで全期間の成立、最初の到達点、改正や廃止を主張しない。',
}
LIMITS=[
 'u0013第七文[1437,2309)の全体へ向けた、市民の公的な書面批評と同じ制度の存続の依存群。自由と存続を同じ点で結び、期間と仮定上の自己賦課への接続は残す。確認済み文字数は増やさない。',
 'Anmerkungenは同じ制度の欠点を論点として分析・説明・指摘する非空の所見と読む。以前のr33a、r326と書面による公的使用r3zを再利用するが、将校の軍務領域h244aと、zur Beurtheilungに対応した読者の判断を目的とするhztl/r327はこの文に追加しない。',
 '同じ所見の作成・公衆への提供を認める内容とする。自由はrduの積極的許可と反対要求の不在であり、単なる禁止不在・無妨害・物理的能力・実際の刊行とは区別する。制度下で自由を与えた規範状態を仮定の内側で記述するための部品であり、現実の自由の存在を新しく断言しない。',
 'jedem der Bürgerは同じ共同体の各評価点での全市民であり、聖職者だけや肩書を既に持つ者だけへ狭めない。学識者の立場は公的な理性使用の分類として各候補へ結ぶ。vornehmlichの聖職者への取り立ては全文で別に接続する。',
 '非空の全批評候補は、制作完了・内容の真理・現在の許可で選別しない。候補の完全な供給は解釈入力の責任であり、有限モデルの例を全ての発言候補と同一化しない。',
 'dermaligen Einrichtungと導入されたOrdnungの同一性は、全経過で同じ制度変数を共有する接続に用いる。導入行為・法の全条項と制度の対応、一定の短い期間、期待と目的、洞察・共同提案・保護・非妨害、談話帰属と全文通読は未完である。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def quantify(names,body,op):
    for n in reversed(names):body=op+' '+n+' a['+body+']'
    return body
def definitions():
    text='d r5e5['+FIELDS+'] c['+both('k h26cs[v regime v community v reference]',
        'k h26ct[v field v regime v reference]','k h26cu[v person v community v reference v candidate v point]',
        'k r33a[v notes v field v reference]','k r2zi[v person v making v scholar v reference]',
        'k cc[v making v audience v reference]',
        'k r3z[v person v presenting v scholar v notes v audience v reference]',
        'k h243y[v person v making v notes v reference]','k h243z[v presenting v notes v audience v reference]')+'].\n'
    clauses=[]
    for target,names in (('r33g',('person','making','notes')),('r33h',('person','presenting','notes','audience')),('r33i',('person','making','presenting','notes','audience'))):
        seq='l[a]['+' '.join('v '+n for n in names)+']'
        clauses.append('k rdu[k h26cw[v regime v community v reference] v person v scholar r[p '+target+'] '+seq+' '+TRUE+' v point i[items j[a]][e[v items]['+seq+']] p h7k p h7l]')
    text+='d r5e6['+FIELDS+'] c['+both(*clauses)+'].\n'
    candidate='k r5e5['+ARGS+']'
    personfields='person a '+FRAME
    text+='d r5e7['+personfields+'] c['+both(quantify(CHOICES,candidate,'g'),quantify(CHOICES,'y['+candidate+'][k r5e6['+ARGS+']]','f'))+'].\n'
    citizen='k h26cu[v person v community v reference v candidate v point]'
    text+='d r5fa['+FRAME+'] c['+both('k h26cs[v regime v community v reference]',
        'f person a[y['+citizen+']['+both('k aa[v person]','k r5e7[v person '+FRAME_ARGS+']')+']]')+'].\n'
    text+='d r5fb['+FRAME+'] c['+both('k h26cv[v regime v community v reference v candidate v point]','k r5fa['+FRAME_ARGS+']')+'].\n'
    text+='d r5fc[community a regime a reference d candidate d] e[b point[k r5fb['+FRAME_ARGS+']]].\n'
    return text
def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,['r33a','r2zi','r3z','h243y','h243z','r33g','r33h','r33i','rdu','h7k','h7l']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='public_written_criticism_by_all_citizens_under_continuing_religious_order',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
