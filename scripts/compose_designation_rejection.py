"""Bind a designation's explicit reading to its subject's practical rejection."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,TRUE,FALSE
from scripts.compose_protected_remarks import bind
from scripts.compose_religious_freedom_policy import DUTY,DARGS,PARGS,POLICY_NAMES,TWO
from scripts.compose_self_report_dignity import FRAME,FRAME_NAMES,FARGS,name_args

PARENTS=('data/religious-freedom-policy-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/designation-rejection.noema';BASIS='data/designation-rejection-basis-v1.json'
PATTERN='i d[h[a] e]';USE_CODE='i[h[j[a]] e]'
PRIMITIVES={
 'h26nj':('[a a a '+TWO+' j[a] d c d] c',['source','person','role','target','bindings','reference','polarity','point'],
   '同じ規範出所が、同じ本人・立場について、段階2の閉じた内容族と同じ対象列・固定基準の内容の指定極性を積極的に許容する。h245cと同じ非事実的な許容を高い段階へ保つ。反対要求の不在、実行能力、現実の履行、規範の正当性、本人の自己評価とは別に与える。'),
 'h26nk':('[a '+PATTERN+' a d] c',['name','pattern','community','reference'],
   '同じ用法共同体と固定基準で、この名称に段階3の閉じた人物の性質記述を説明として結ぶ規約が採用されている。hw2の意味保持を高い段階へ保ち、原語の綴りで内容を代用しない。人物が実際にその性質を満たすこと、本人が名称を採用すること、全話者の合意、他の用法や別の基準の意味まで含意しない。'),
}
MEANINGS={
 'r5wr':'同じ規範出所・本人・立場・宗教的自由方針・対象列・固定基準で、実現と非実現の両方が許容され、双方に反対の要求がない。既存rnkの両方向の裁量を、今回の段階2の全宗教的自由方針へ接続する。',
 'r5ws':'r5wrの両方向の裁量と、その同じ本人が同じ集団全員へ残す宗教的自由方針r5v7の現実の成立。義務の履行だけや単なる介入不在とは分ける。',
 'r5wt':'同じ規範出所・公的立場・対象集団・共同体・主題・基準を固定した、r5wsを満たす人物の性質。自由を与えるかどうかを自分の裁量として扱う名称の説明候補。',
 'r5wu':'五個体と固定基準の閉じた名前をr5wtへ適用した段階3の性質記述。同じ真理値の別記述へ置換せず、名称の説明として引用できる。',
 'r5wv':'五個体と固定基準の各呼称の参照を確認し、同じ名称へ同じr5wuを同じ共同体・基準で結ぶ。名称の意味保持は内容の真理や名称拒否を要求しない。',
 'r5ww':'同じ生起活動で同じ提示者が同じ名称を同じ対象へ適用するrnhを、dg・f3・hzihへ接続する。名称への言及だけを適用にしない。',
 'r5wx':'固定した非空の名称使用者集団の誰かが、同じ本人へ同じ名称を適用する活動が評価点で生じるという内容。名称の表す性質の真理や本人の承認は含めない。',
 'r5wy':'固定基準を保ち、本人・名称・使用者集団の正確な三個体列をr5wxへ渡す内容族。短い列・余分な列を拒否し、引用対象を実際の人物と結ぶ。',
 'r5wz':'固定基準の閉じた名前だけをr5wyへ適用した段階0の内容族記述。本人・名称・使用者集団は同じ三個体列として別に渡す。',
 'r5w2':'同じ本人が同じ反応活動に参加し、その活動が生起し、非空の使用者集団で自分へその名称を適用するr5wyの内容を負極性の実践方針として明確に引き受ける。発言又は行動上の拒否であり、名称使用の不存在だけからは成立しない。',
 'r5w3':'本人・名称・使用者集団・基準を固定して、r5w2を満たす本人の反応活動があるという内容。既に名前を付けられた歴史的事件や相手の要求は前提にしない。',
 'r5w4':'同じ名称が同じr5wuの意味を保持することと、その同じ名称の自分への適用を本人が拒むr5w3を結ぶ。名称を人物自身と同一化せず、意味内容の偽・他者の遵守・現実の自由の不存在を導かない。',
 'r5w5':'同じ名称・使用者集団・意味設定を固定し、人物ごとにr5w4の名称拒否を返す。一般的な君主の条件へ後で接続するための性質であり、拒否する実在人物をここで断言しない。',
 'r5w6':'同じ自由方針を実現する義務r5wbがあれば、r5wrの両方向の裁量はないという条件内容。本人の判断・発言・名称拒否をこの定義上の関係から導かない。',
}
LIMITS=[
 'u0015第一文の名称Toleranzの自分への適用拒否に向けた依存群。本文112主張・全単位17判断を維持し、全文の意味確認を先取りしない。名称個体・使用者集団・用法共同体の具体的な本文束縛は統合時に行う。',
 '政治的なToleranzを、この箇所では宗教上の自由を本人の裁量による許容として与える側という名称の説明として読む。前段のPflichtとalsoの対照による明示的な文脈解釈であり、寛容一般の唯一の定義ではない。不賛同を抱くことや嫌悪を抑える心理を、この君主本人の事実として追加しない。DWBの宗教的許容と承認との区別を補助資料にする。',
 '名称の説明はNoemaの同じ自由方針と両方向の許容から構成する。規範出所は許容の評価源であり君主本人に自動同定しない。自称する内容を引用しただけでは、その裁量が正当に存在することも自由方針が現実に成立することも要求しない。',
 'ablehntは、自分へその名称を適用することに対して明確な負の実践的立場を取ると読む。既存の呼びかけだけの候補より広く、発言又は行動上の選択を許す。単なる名前の不使用、内心の予測、実行不能、名称の性質の否定とは分ける。DWBの提案・栄誉などを断る用法を参照する。',
 'von sichは名称の適用対象と拒否の主体を同じ本人へ束縛する。受け手が実際に従うこと、過去に名付けられた事件、未来永遠の不使用は要求しない。使用者集団を現在その名称を使う者だけに縮めず、固定した関連人物全員を供給する責任を残す。',
 '高慢という評価は、裁量の不成立だけとは同一視しない。AA6:465の他者への尊重を損なう優越要求という後年の説明は補助資料であり、1784年の一語に後年の全理論を読み込まない。高慢な呼称の評価、selbstの強調、alsoの帰結提示は次に構成する。',
 '有限モデルでは規範の16通りと実際の名前使用・拒否・意味内容の独立性、名前と列の一致を調べる。検査合格は採用読解の歴史的妥当性や一文全体の同義性を自動証明しない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    target='r c[p r5wa] l[a]['+' '.join('v '+n for n in POLICY_NAMES)+'] v reference'
    norm=lambda symbol,sign:'k '+symbol+'[v source v actor v office '+target+' '+sign+' v point]'
    text='d r5wr['+DUTY+'] e[b point['+both(*(norm('h26nj',s) for s in (TRUE,FALSE)),*('u['+norm('h26ne',s)+']' for s in (TRUE,FALSE)))+']].\n'
    text+='d r5ws['+DUTY+'] e[b point['+both('t[k r5wr['+DARGS+']][v point]','t[k r5v7['+PARGS+']][v point]')+']].\n'
    text+='d r5wt['+FRAME+'] h[a] e[i[actor a][k r5ws['+DARGS+']]].\n'
    text+='d r5wu['+' '.join(n+' i[a]' for n in FRAME_NAMES)+' reference i[d]] '+PATTERN+'[o a[r d[p r5wt]]['+' '.join('v '+n for n in (*FRAME_NAMES,'reference'))+']].\n'
    valid=both(*('e[s[k h223g[v '+n+']]][v '+n+']' for n in FRAME_NAMES),'e[s[k h223h[v reference]]][v reference]')
    text+='d r5wv[label a '+FRAME+'] c['+both(valid,'k h26nk[v label k r5wu['+name_args(FRAME_NAMES)+'] v community v reference]')+'].\n'
    text+='d r5ww[speaker a activity a label a subject a point d] c[k rnh[v speaker v activity v label v subject v point p dg p f3 p hzih]].\n'
    member='k h246c[v users v speaker v reference]'
    nonempty='g speaker a['+member+']'
    text+='d r5wx[actor a label a users a reference d] e[b point['+both(nonempty,'g speaker a[g activity a['+both(member,'k r5ww[v speaker v activity v label v actor v point]')+']]')+']].\n'
    text+='d r5wy[reference d] h[j[a]] e[i[bindings j[a]][b point['+bind(('actor','label','users'),'t[k r5wx[v actor v label v users v reference]][v point]')+']]].\n'
    text+='d r5wz[reference i[d]] '+USE_CODE+'[o a[r[p r5wy]][v reference]].\n'
    refusal=both(nonempty,'e[s[k h223h[v reference]]][v reference]','k dg[v response v point]','k df[v actor v response v point]',
        'k h244j[v actor v response k r5wz[k h223h[v reference]] l[a][v actor v label v users] '+FALSE+' v point]')
    text+='d r5w2[actor a response a label a users a reference d point d] c['+refusal+'].\n'
    text+='d r5w3[actor a label a users a reference d] e[b point[g response a[k r5w2[v actor v response v label v users v reference v point]]]].\n'
    text+='d r5w4[actor a label a users a '+FRAME+'] e[b point['+both('u[e[v actor][v label]]','k r5wv[v label '+FARGS+']','t[k r5w3[v actor v label v users v reference]][v point]')+']].\n'
    text+='d r5w5[label a users a '+FRAME+'] h[a] e[i[actor a][k r5w4[v actor v label v users '+FARGS+']]].\n'
    text+='d r5w6['+DUTY+'] e[b point[y[t[k r5wb['+DARGS+']][v point]][u[t[k r5wr['+DARGS+']][v point]]]]].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(['r5wb','r5v7','h223g','h223h','h246c','rdr'],['rnh','hzih','df','dg','f3','h244j'])):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(l.entries) for l in libs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='described_discretionary_policy_and_subjects_designation_rejection',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
