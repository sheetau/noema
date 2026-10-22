"""Compose institutional self-misunderstanding and externally imposed hindrances."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,STATE,MODEL,ARGS
from scripts.compose_paired_influence import MATCH

PARENT='data/public-offers-sentence-basis-v1.json'
LIBRARY='examples/v016/government-self-misunderstanding.noema';BASIS='data/government-self-misunderstanding-basis-v1.json'
PROFILE=MODEL+' worlds h['+STATE+'] d matches '+MATCH+' evaluated h[d] c goal e'
PARGS=ARGS+' v worlds v matches v evaluated v goal'
PRIMITIVES={
 'h26pj':('[a a a d d] c',['judgment','organization','item','reference','point'],
   'この組織に帰属する判断のこの同じ内容項目において、対象となる組織が自分たち自身の制度的主体として捉えられている。外部組織についての判断対象が偶然自組織と一致するだけの場合、同じ判断の別の項目だけが自己言及である場合とは分ける。組織への帰属、内容と極性、正しさは別に結ぶ。個人用h242hを組織に代入せず、組織の自己位置付けを一般関係として指定する。'),
 'h26pk':('[a a a d] c',['item','organization','community','reference'],
   '同じ固定基準の内容項目は、この組織が同じ政治的共同体において担う役割・目的・任務又は権限のあり方についての理解を述べる。建物の色など偶然の属性や別組織の機能だけとは分ける。内容はh26aeのNoema命題で与え、この関係だけで受容・真理・正当な機能の特定説を断言しない。'),
 'h26pl':('[a a a d] c',['condition','government','community','reference'],
   'この条件・制度・作用要因は、同じ政府が同じ共同体への公的な権限において設け、維持し、又は実施するものに由来する。単に同じ国に存在する条件、政府の一職員の私的行為、別政府の規制とは分ける。現時点での適用、妨害効果、悪意、政府の自己理解の誤りが原因であることは別条件とする。'),
 'h26pm':('[a a d] c',['condition','person','reference'],
   'この条件は、同じ本人の理解・志向・判断そのものの構成要素ではなく、本人が活動する社会的・制度的環境に属する外部条件である。本人の恐れや理解不足だけとは区別し、本人が条件を知っていること、制御不能、物理的に遠方にあること、実際の阻害や本人の反抗を要求しない。'),
}
MEANINGS={
 'r56z':'同じ政府・共同体について、固定範囲の内容項目とその代表があり、その代表内容が同じ政府の自己役割を扱う。組織自身に帰属する同じ判断が、その同じ代表項目を自己のものとして捉え、h26aeの内容に指定極性を採用する。個人のfa・全員一致・発話の実行を代用しない。',
 'r562':'r56zの同じ制度的自己理解の採用極性が、同じ代表項目の実際の内容の同じ点での真偽と食い違う。偽の内容の肯定と真の内容の否定をともに扱い、単なる無知・考慮・不支持又は他者の誤った理解と分ける。',
 'r563':'同じ政府・共同体・固定基準・点について、r562の自己理解の誤りを持つ判断・内容項目・極性が存在する。全ての判断が誤り、政府が自分の存在を認めない、特定の誤説を採用するといった条件は加えない。',
 'r564':'同じ政府の公的条件h26plが同じ人に外的h26pmであり、その条件が同じ基準の現在点に存在又は適用されるh26kg。政府資格と本人の人間性を確認するが、これだけで妨害や自己誤解を認定しない。',
 'r565':'同じ目標命題を同じ割当てから候補状況への対応で評価し、左での達成が右での達成以上であるという二値の比較を作る。真は偽以上で、同値の二候補は同程度とする。比較側ごとに目標を変更しない。',
 'r566':'条件の有無とモデルの要因真偽が全介入解で一致し、r2wmの全解評価・両側の対応完備性・比較整合性の下、同じ背景の対応組で、その条件あり側だけ同じ目標が不成立となる例がある。未知・未評価・解なし・未対応を障害なしや妨害成立へ補わない。',
 'r567':'同じ政府にr563の自己理解の誤りがあり、その政府の同じ外的条件r564が現に適用され、その条件が同じ目標についてr566の潜在的妨害を持つ。別政府の自己誤解、別条件の現在の存在、別目標への悪化を寄せ集めない。自己誤解から妨害への因果、実際の敗北、障害克服の完了は追加しない。',
}
LIMITS=[
 'u0015第三文のsich selbst mißverstehenden Regierungを、政府が自分たちの公的役割・目的・任務・権限について制度上採用している理解に誤りがあるという読みで扱う。原文が述べない特定の誤説や心理的悪意は選ばず、その具体的内容はNoema命題として与える。',
 '組織判断の帰属は既存h247uを使い、個人の判断faや私的信念の多数決とは同一視しない。手続の個別実装・規則の正当性・全構成員の同意を新たな条件にしない。h26pjで同じ内容項目の制度的な自己位置付けを明示する。',
 '同じ代表項目のh26ae内容と採用極性を同じ時点で比較する。別名項目の置換だけで誤りを消さず、後の社会状態の変化や別組織の役割を真偽評価に流用しない。全ての自分に関する誤情報を、統治に関する自己理解の誤りとはしない。',
 'einer ... Regierungは障害の出所を同じ政府へ結ぶ。自己誤解と条件の由来は連言し、誤解が条件を生んだという因果や故意を原文にない必須条件として補わない。外的は態度保持者の内的な理解・志向とは別の制度的条件として読む。',
 '障害の一般構成は、同じ目標の達成を二値で比較する潜在的な阻害の読みである。同じ背景・初期条件・選択枝を対応させ、条件の有無だけを変える。現実の平均効果・頻度・全背景での阻害又は実際の達成不能を主張しない。指定モデルの現実への適合は意味規約の入力であり有限検査で実証しない。',
 '目標は一つのNoema命題として固定し、比較関数内で直接評価する。第三文では同じ自由の精神の国外への到達・保持へ具体的に接続する必要があり、この一般目標引数だけで全文の障害記述が済んだとはしない。複数の障害、格闘の活動と必要性、本文の固定設定・照応・auch/selbst・全文帰属と通読も残る。',
 '本文114主張、17全単位判断と追加二文763文字を保存する。第三文の意味確認文字数は増やさない。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    fields='government a community a judgment a item a reference d polarity c point d'
    args='v government v community v judgment v item v reference v polarity v point'
    canonical='k h26ag[v item v reference]'
    text='d r56z['+fields+'] c['+both('k r5zj[v government v community v point]',
        'k h26ad[v item v reference]','k h26ad['+canonical+' v reference]',
        'k h26pk['+canonical+' v government v community v reference]',
        'k h247u[v government v judgment v point]',
        'k h26pj[v judgment v government '+canonical+' v reference v point]',
        'k h245q[v judgment '+canonical+' r[p h26ae] v reference v polarity v point]')+'].\n'
    text+='d r562['+fields+'] c['+both('k r56z['+args+']',
        'u[e[t[k r5cc[v item v reference]][v point]][v polarity]]')+'].\n'
    text+='d r563[government a community a reference d point d] c[g judgment a[g item a[g polarity c[k r562['+args+']]]]].\n'
    source='government a community a person a condition a reference d point d'
    sourceargs='v government v community v person v condition v reference v point'
    text+='d r564['+source+'] c['+both('k r5zj[v government v community v point]','k aa[v person]',
        'k h26pl[v condition v government v community v reference]','k h26pm[v condition v person v reference]',
        'k h26kg[v condition v reference v point]')+'].\n'
    text+='d r565[goal e worlds h['+STATE+'] d] '+MATCH+'[i[left '+STATE+' right '+STATE+'][y[t[v goal][c[v worlds][v right]]][t[v goal][c[v worlds][v left]]]]].\n'
    align='k r2vc['+ARGS+' i[state '+STATE+'][z[c[v state][v factor]][k h26kg[v condition v reference c[v worlds][v state]]]]]'
    compared='k r2wm['+ARGS+' v matches i[state '+STATE+'][c[v evaluated][c[v worlds][v state]]] k r565[v goal v worlds]]'
    text+='d r566[condition a reference d '+PROFILE+'] c['+both(align,compared)+'].\n'
    text+='d r567['+source+' '+PROFILE+'] c['+both('k r563[v government v community v reference v point]',
        'k r564['+sourceargs+']','k r566[v condition v reference '+PARGS+']')+'].\n'
    return text
def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,
        ['r5zj','h26ad','h26ag','h26ae','h247u','h245q','r5cc','aa','h26kg','r2vc','r2wm']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='institutional_self_misunderstanding_and_external_hindrance_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
