"""Compose further independent judging across persons and future generations."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENT='data/covenant-question-basis-v1.json'
LIBRARY='examples/v016/human-enlightenment-block.noema'
BASIS='data/human-enlightenment-block-basis-v1.json'
PRIMITIVES={
 'h256m':('[] a',[],'この議論でいうMenschengeschlecht、人類という通時的な全体。特定国の人民・教区・現在の読者・生物学的な人種へ限定しない。各時点の対象者はaaとh256oから別に構成する。'),
 'h256n':('[d d] c',['candidate','point'],'人類の将来を考える同じ候補の経過に、この時点が含まれる。基準以後の経過全体を供給し、観測した有限区間や都合のよい点だけで代用しない。候補の現実性や個人の不死は含意しない。順序・基準の包含・終点の不在は別に構成する。'),
 'h256o':('[a d d] c',['individual','candidate','point'],'同じ候補の経過のこの時点で、この個体が生存している。現在生存する者だけを将来の母集団へ固定せず、後の出生と以前の死を区別する。人類への分類はaaで別に指定する。'),
}
MEANINGS={
 'r5aa':'同じ人・判断対象・固定領域・評価点について、既存r2gvで通常の評価場面におけるr2qlの理由ある自己判断を述べる。本人の基盤保持、外的機会、全対応活動、通常性を既存と同じ引数で保ち、偶然の単発成功や知識量だけで代用しない。',
 'r5ab':'同じ人と固定領域の前後の評価がともに有効で、少なくとも一つの判断対象で以前は通常の理由ある自己判断がなく、後にある。全領域の完成や他の全対象での無損失を要求せず、一部の改善を取り逃がさない。',
 'r5ac':'同じ候補・時点の生存する人aaの範囲が非空で、その全員に同じ固定領域でのr2qmの有効な判断評価がある。出生・死亡を許し、空の人類や未知の評価を進歩なしとして扱わない。',
 'r5ad':'同じ候補の前後にr5acがあり、後の生存者に、同じ本人の一判断対象での新たな自立、または以前の全生存者にはなかった判断対象での通常の自立がある。個人の部分的な進展と世代をまたいだ範囲の拡大を含む。既存の自立の保持や同じ水準の世代交代だけでは進展にしない。時間配置はr5aeで指定する。',
 'r5ae':'同じ全履歴に属する、固定起点以後の開始点とそれより後の終了点についてr5adの進展がある。起点以前だけの進展を今後の進展へ算入しない。',
 'r5af':'同じ候補の固定起点以後の全経過で人類の非空性と評価の有効性を保ち、どの前後点にもr5aeの新たな進展がない内容。既に得た自立の喪失は要求しない。',
 'r5ag':'r5afに加えて同じ全将来に終点がないrbzを要求する。短期停滞や終期不明、個人の不死、数値時間の非有界性を同一視しない。',
 'r5ah':'人類h256mのみからなる正確な一個体列と固定起点から、第六段落の固定領域h255oにおけるr5agを作る。国の共同体や現在の当事者を対象へ置換しない。',
 'r5ai':'同じ団体・合意・形成基準について、制度的な実施・維持が同じ人類へのr5ahの進展の永久的不在を成立・維持させるh255kと、その結果r5agを結ぶ。単なる停滞の併存では妨害の成功としない。',
 'r5aj':'団体・合意の正確な二個体列と形成基準からr5aiの妨害結果を目的内容にする。',
 'r5ak':'先のr47hの同じ種類の団体・信条の候補について、同じr47dの目的付き相互宣誓形成と、人類の今後の啓蒙を永久に妨げるr5ajの共同目的採用を結ぶ。形成者がその共同目的に参加する同じ宣誓行為はr47d内のh255mで保つ。目的の成功は形成の外側で要求しない。',
 'r5al':'団体・合意・信条・主題・政治的共同体の正確な五個体列を、同じ合意の形成基準h254zにおけるr5akへ結ぶ。仮定の前件として引用でき、これ自体では契約の実在や正当性を主張しない。',
}
LIMITS=[
 'alle weitere Aufklärungは、同じ判断領域で理由ある自己判断ができる対象の新たな獲得・広がりという読みを採る。既存の通常評価r2ql/r2gvを再利用し、一人の部分的改善も新しい世代による範囲の拡大も含める。議論の回数、服従、情報項目の単なる増加で代用しない。',
 '判断対象はh226uで固定し、成功した対象だけを選ばない。対象の細かさは解釈入力であり、同じ対象での速度向上や、通常の自己判断の成立条件を変えない微小な熟練差を別の進展として数える尺度ではない。全ての可能な哲学的な啓蒙観を網羅した定義とはしない。後続文が独立に述べる知識の拡大と誤りの修正も別に構成する。',
 '人類は通時的な全体。aaと各候補時点の生存から対象者を構成し、特定国・現在の当事者・固定読者一覧へ限定しない。同じ水準の世代交代は維持、新しい判断対象での自立は進展として区別する。',
 '進展がないことだけでは、人類が絶えた場合や未評価の場合を区別できない。全将来の人類の非空性と評価の有効性を要求し、絶滅を目標の達成としない。これは人類の継続する議論という採用読解の範囲条件であり、個人の無限寿命を要求しない。',
 'auf immerは終点のない将来全体、abhaltenは同じ合意の制度的実施がその不進展を成立・維持させる働きとして読む。結果が以前は偽だったこと、唯一原因性、数値的な無限大は追加しない。有限の全履歴では終点なしの条件が偽になり、有限検査の成功を永久の実現と扱わない。',
 'solcherは先の種類・信条・相互宣誓・後見目的を持つ合意を受ける。人類への妨害はこの合意に新たに説明される共同目的であり、全員の私的な内心の一致や成功は要求しない。原文のwould形と無効性への条件・諸制度の承認・談話帰属は本文統合で残る。',
]

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)

def living(person,point):return both('k aa[v '+person+']','k h256o[v '+person+' v candidate v '+point+']')

def definitions():
    cases='i[scene d][k h226v[v person v topic v scope v point v scene]]'
    held='i[scene d]['+both('k h226w[v person v topic v scope v point v scene]','g judgment a[k h226y[v person v topic v scope v point v scene v judgment]]')+']'
    opportunity='i[scene d][k hzzzv[v person v topic v scene]]'
    preferred='i[first d last d][k h226x[v person v topic v scope v point v first v last]]'
    response='i[scene d][k r2ql[v person v topic v scope v point v scene]]'
    text='d r5aa[person a topic a scope d point d] c[k r2gv['+' '.join((cases,held,opportunity,preferred,response))+']].\n'
    gain='g topic a['+both('k h226u[v person v scope v topic]','u[k r5aa[v person v topic v scope v first]]','k r5aa[v person v topic v scope v last]')+']'
    text+='d r5ab[person a scope d first d last d] c['+both('k r2qm[v person v scope v first]','k r2qm[v person v scope v last]',gain)+'].\n'
    text+='d r5ac[scope d candidate d point d] c['+both('g person a['+living('person','point')+']',
        'f person a[y['+living('person','point')+'][k r2qm[v person v scope v point]]]')+'].\n'
    earlier='g other a['+both(living('other','first'),'k h226u[v other v scope v topic]','k r5aa[v other v topic v scope v first]')+']'
    collective='g topic a['+both('k h226u[v person v scope v topic]','k r5aa[v person v topic v scope v last]','u['+earlier+']')+']'
    individual=both(living('person','first'),'k r5ab[v person v scope v first v last]')
    gained='g person a['+both(living('person','last'),'x['+individual+']['+collective+']')+']'
    text+='d r5ad[scope d candidate d first d last d] c['+both('k r5ac[v scope v candidate v first]','k r5ac[v scope v candidate v last]',gained)+'].\n'
    text+='d r5ae[scope d anchor d candidate d first d last d] c['+both('k h256n[v candidate v first]','k h256n[v candidate v last]',
        'x[e[v first][v anchor]][k ic[v anchor v first v candidate]]','k ic[v first v last v candidate]',
        'k r5ad[v scope v candidate v first v last]')+'].\n'
    timeline='i[at d][k h256n[v candidate v at]] i[first d last d][k ic[v first v last v candidate]] v anchor'
    stable='k rca['+timeline+' i[at d][k r5ac[v scope v candidate v at]]]'
    no_gain='u[g first d[g last d[k r5ae[v scope v anchor v candidate v first v last]]]]'
    text+='d r5af[scope d anchor d] e[b candidate['+both(stable,no_gain)+']].\n'
    text+='d r5ag[scope d anchor d] e[b candidate['+both('t[k r5af[v scope v anchor]][v candidate]','k rbz['+timeline+']')+']].\n'
    text+='d r5ah[bindings j[a] reference d] e[b candidate['+both('e[v bindings][l[a][k h256m[]]]','t[k r5ag[k h255o[] v reference]][v candidate]')+']].\n'
    text+='d r5ai[body a agreement a reference d] e[b candidate['+both(
        'k h255k[v agreement v body r[p r5ah] l[a][k h256m[]] v reference v candidate]',
        't[k r5ag[k h255o[] v reference]][v candidate]')+']].\n'
    text+='d r5aj[bindings j[a] reference d] e[b candidate['+bind(('body','agreement'),'t[k r5ai[v body v agreement v reference]][v candidate]')+']].\n'
    fields='body a agreement a creed a subject a community a reference d';args='v body v agreement v creed v subject v community'
    text+='d r5ak['+fields+'] c['+both('k r47h['+args+' k h255o[]]','k r47d['+args+' v reference]',
        'k h255l[v body v agreement r[p r5aj] l[a][v body v agreement] v reference]')+'].\n'
    text+='d r5al[bindings j[a]] e[b point['+bind(('body','agreement','creed','subject','community'),
        'k r5ak['+args+' k h254z[v agreement]]')+']].\n'
    return text

def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r2gv','r2ql','r2qm','rca','rbz','r47h','r47d','h255p','h255r','h255o']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+v[0]+'.' for n,v in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=v[1],meaning_ja=v[2]) for n,v in PRIMITIVES.items()})
    basis=dict(status='humanity_further_independent_judging_and_purposive_block',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
