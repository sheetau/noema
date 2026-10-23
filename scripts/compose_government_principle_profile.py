"""Track adopted government rules by content while preserving opaque adoption."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/civic-spirit-sentence-basis-v1.json'
OLD='examples/v016/kant-governing-principles.noema';OLD_BASIS='data/governing-principles-basis-v1.json'
LIBRARY='examples/v016/government-principle-profile.noema';BASIS='data/government-principle-profile-basis-v1.json'
CODE='i[h[j[a]] e]';FIELDS='government a community a reference d';ARGS='v government v community v reference'
TRUE='e[n p a b][n p a b]'
PRIMITIVES={
 'h27c6':('[a d] a',['community','reference'],'同じ民衆の共同体と固定基準で、その公的運営・執行を担う政府の参照。評価点や原則の成否ごとに別政府へ交換しない。政府としての資格はr5zjで別に確認する。'),
 'h27c7':('[a a d] a',['government','community','reference'],'同じ政府が、自らの公的な統治方針について規範の名宛人となる制度上の立場。個々の職員の私的な立場や人格とは分け、h27dfで同じ政府の立場であることを確認する。'),
 'h27da':('[a a d] j[a]',['government','community','reference'],'この比較で扱う一般的な統治行動規則の全候補列。採用済みか否かによらず固定し、前後又は因果比較の片側で候補を増減させない。非空・重複なし・h27dbとの完全一致を検査する。'),
 'h27db':('[a a d a] c',['government','community','reference','rule'],'同じ比較で一般的な統治行動規則の候補として検討する全範囲。個別の一回の命令、事実の報告、規則の名前だけを内容の代わりにせず、候補ごとの具体的な規則内容をh27dcに保持する。採用の有無そのものではない。'),
 'h27dc':('[a a d a] '+CODE,['government','community','reference','rule'],'同じ規則候補の具体的なNoema内容を持つ閉じた記述。空の外側引数列から状況ごとの内容を返し、同じ政府の一般的な行動方針を表す。比較点・結果によって記述を交換しない。名前だけの未記述条件を完成した尊厳規則として扱わず、原文統合ではその具体的本体を指定する。'),
 'h27dd':('[a a d a d] c',['government','community','reference','rule','point'],'同じ政府・制度上の立場・規則の採用状態について、この評価点で判断に必要な情報が整っている。無記録を不採用にせず、採用したことや実際の履行そのものは含めない。'),
 'h27de':('[a a d d] c',['government','community','reference','probe'],'規則の内容を比較する全状況の固定範囲。前後の採用状態や有利な差に応じて選び直さず、候補内容の違いを調べる基準を明示する。現実に政府が経験した状況だけに限らず、この有限の範囲での同値を全可能状況での同義証明へ拡張しない。'),
 'h27df':('[a a a d] c',['government','office','community','reference'],'同じ共同体の公的運営を担うこの政府が、指定の制度上の立場を持つ。名宛人が政府であることと、人間の職員が個別活動でその資格を行使することを区別する。道徳的正当性、全員の同意、規則の実際の履行は含まない。'),
}
MEANINGS={
 'r6k3':'同じ民衆の共同体と基準で参照された政府が、既存r5zjの公的運営・管轄の資格を持ち、指定した制度上の立場もその政府のものである。政府を人間一人へ置換しない。',
 'r6k4':'同じ政府が出所かつ名宛人となり、同じ制度上の立場で候補規則の具体的記述を満たすよう要求している。既存rxx/h7kへの接続であり、統治上の自己規律としての採用を表す。内容を脱引用せず、履行・正当性・採択行為の生起を加えない。',
 'r6k5':'同じ全比較状況が非空で、その全てにおいて二つの候補規則を空の引数列で適用した内容が同じ真偽になる。この明示範囲に相対的な内容の同値であり、名前の一致でも無条件の同義証明でもない。',
 'r6k6':'同じ比較範囲で指定候補と内容が同値な規則が、同じ点に少なくとも一つ採用されている。特定の記述への規範を別名へ転用する操作ではなく、採用集合を内容の同値類ごとに観察するプロフィール。',
 'r6k7':'同じ政府と公的立場、非空で完全な全候補列、非空の固定した全比較状況を確認し、その点で全候補の採用状態が評価できることを要求する。採用済みの候補だけへ範囲を縮めない。',
 'r6la':'前後の同じ政府・基準でr6k7が成立し、少なくとも一つの規則内容の同値類について採用の有無が異なる。追加だけ又は撤回だけでもよく、全原則の変更や旧規則の廃止と新規則の採用の同時成立を要求しない。時系列と因果は外側で別に接続する。',
 'r6lb':'同じ政府・共同体・固定基準・開始点を保ち、終点ごとのr6laの原則内容の変化を返す。政府への最終的な因果作用、自己利益判断、尊厳規則そのものをこの内容だけで完成させない。',
}
LIMITS=[
 'Grundsätze der Regierungを、この政府が自らの統治を方向付ける一般的な行動規則として採用する原則と読む。Adelungの行動の規則という用法を比較資料とし、数学的公理・事実認識・政府の全信念まで義務へ還元する定義とはしない。',
 '採用は同じ政府を出所と名宛人にした統治上の自己規律としてh7k/rxxで表す。明文の法律、議決、全職員の賛成、実際の履行、道徳的正当性を追加しない。具体的な政府の判断主体の構成は利益判断の接続時にも保持する。',
 '同じ比較状況で同内容の規則への改名だけを、内容の変化に数えない。規範そのものは記述を区別しており、別名の規則を要求したことにはしない。内容の同値類の採用状態だけを比較する。',
 '前後で固定した全候補と全比較状況を使い、全候補の採用状態を評価する。比較範囲内で一致した規則が、その外でも同じ意味だとは証明しない。範囲の妥当性は公開した解釈の一部である。',
 '原則への作用を内容の変化として接続する準備であり、原則の追加・撤回を許す。旧rx3の必ず両方を行う置換を必須にしない。因果的寄与、同じ民衆との関係、endlichの先後、auch/sogarの提示は後続で統合する。',
 '具体的な尊厳に即した扱い、機械以上の人間、政府自身への利益判断、Wenn/soと全文帰属は未完。候補内容h27dcに未記述の名前だけを与えて完了扱いにしない。正本と意味確認文字数は維持する。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
@lru_cache(None)
def legacy():
    ds=closure(parse((ROOT/OLD).read_text(encoding='utf-8')),('rxx',))
    meanings=json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions']
    return ds,{d['name']:meanings[d['name']] for d in ds}

def definitions():
    office='k h27c7['+ARGS+']'
    selected=lambda rule:'k h27db['+ARGS+' v '+rule+']'
    code=lambda rule:'k h27dc['+ARGS+' v '+rule+']'
    probes='k h27de['+ARGS+' v probe]'
    actual=lambda rule:'t[c[s['+code(rule)+']][l[a][]]][v probe]'
    text='d r6k3['+FIELDS+'] c['+both('e[v government][k h27c6[v community v reference]]','k r5zj['+ARGS+']','k h27df[v government '+office+' v community v reference]')+'].\n'
    text+='d r6k4['+FIELDS+' rule a point d] c['+both(selected('rule'),'k rxx[v government v government '+office+' '+code('rule')+' v point p h7k]')+'].\n'
    text+='d r6k5['+FIELDS+' first a second a] c['+both(selected('first'),selected('second'),'g probe d['+probes+']',
        'f probe d[y['+probes+'][z['+actual('first')+']['+actual('second')+']]]')+'].\n'
    text+='d r6k6['+FIELDS+' candidate a point d] c['+both(selected('candidate'),
        'g rule a['+both(selected('rule'),'k r6k4['+ARGS+' v rule v point]','k r6k5['+ARGS+' v candidate v rule]')+']')+'].\n'
    text+='d r6k7['+FIELDS+' point d] c['+both('k r6k3['+ARGS+']','k rcm[k h27da['+ARGS+'] i[rule a]['+selected('rule')+']]',
        'g probe d['+probes+']','f rule a[y['+selected('rule')+'][k h27dd['+ARGS+' v rule v point]]]')+'].\n'
    text+='d r6la['+FIELDS+' start d end d] c['+both('k r6k7['+ARGS+' v start]','k r6k7['+ARGS+' v end]',
        'g candidate a['+both(selected('candidate'),'u[z[k r6k6['+ARGS+' v candidate v start]][k r6k6['+ARGS+' v candidate v end]]]')+']')+'].\n'
    text+='d r6lb['+FIELDS+' start d] e[b end[k r6la['+ARGS+' v start v end]]].\n'
    return text

def build():
    p=parent();doc=deepcopy(p.document);doc.update(declarations=closure(p.document,('r5zj','rcm','h7k')),statements=[])
    imports={d['name']:p.entries[d['name']] for d in doc['declarations']};ds,means=legacy();doc['declarations'].extend(ds)
    assert not(set(PRIMITIVES)|set(MEANINGS))&set(p.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imports.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set(p.source_sha256)|{OLD,OLD_BASIS}
    basis=dict(status='government_practical_rule_content_profile_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imports.items() if e['kind']=='definition'}|means|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imports.items()}|{n:OLD_BASIS for n in means},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
