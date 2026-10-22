"""Compose deliberate contrivance aimed at keeping people uncultivated."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/manifest-example-sentence-basis-v1.json'
LIBRARY='examples/v016/deliberate-retention.noema';BASIS='data/deliberate-retention-basis-v1.json'
HISTORY='i[h[d] c]';BEFORE='i[h[d d] c]';STATE='i[h[a] e]'
TIMES='history '+HISTORY+' before '+BEFORE+' first i[d] last i[d]'
TARGS='v history v before v first v last'
PRIMITIVES={
 'h26rh':('[a d d] c',['person','reference','point'],
   'この人について、経験・学習・考察による思考や判断習慣の形成が未発達で、事柄や他者の見方を区別して吟味する素養が乏しい状態がある。Rohigkeitをこの論述における未陶冶として読む基本概念。単独の知識項目の不知、礼儀違反、暴力性、人種・階級・民族の属性とはしない。生得的な固定性、本人の責任、他者の指導なしに理解力を使えないこと、全道徳的欠陥は含意しない。判断基準はreferenceに固定し、未知を未陶冶やその不在へ補わない。'),
 'h26ri':('[a a '+STATE+' d d] c',['activity','target','state','reference','point'],
   'この活動は、同じ本人が記述された状態から移っていくことに関わる条件・情報・機会・依存の配置へ、人為的に手を加えて組み替え又は保つ操作である。künstelnをこの文脈での作為的な介入として読む。単なる同席、自然な状態の持続、無関係な人工物の制作、状態移行への介入を伴わない理由の提示と区別する。妨害又は保持という目的、実行、成功、秘密性・虚偽・悪意・政府の権限は別条件であり、この関係だけから補わない。'),
 'h26rj':('[a a d d] c',['actor','activity','reference','point'],
   '同じ活動への本人の関与が、自分が何をするかの把握に基づく選択・制御に結び付いている。反射的な反応、偶然の作用、単に結果を予想したことと区別する。手段を意図的に扱うことを表し、全副作用の予見、特別に長い熟慮、道徳的な悪さの自覚は要求しない。実際の能動的参加と特定の目的内容は別に結ぶ。'),
 'h26rk':('[a a i b[e] d] c',['actor','activity','goal','point'],
   '本人が同じ活動の計画・遂行で目指す目的内容を、閉じた段階1の記述として指定する。既存hzuと同じ目的関係を、引用の評価を含む保持・因果内容の段階に適用する。単なる予測・好み・他人の目的とは区別し、活動の実行、目的の真理・達成・実現可能性をこの関係だけから要求しない。引用内容をこの関係で実行しない。'),
}
MEANINGS={
 'r6ap':'同じ固定基準の下で、人aaにh26rhの未陶冶があるという人物状態。知的未成熟bfや自由の不在と同じ定義へ置き換えない。',
 'r6aq':'同じ活動の始点生起r2mjが、同じ本人の同じ状態の期間全体の保持r2mkへ因果的に寄与し、実際に両内容が成立するというrqquの達成内容。保持には順序付き履歴、異なる両端、全中間点が要る。これは目的として引用する内容であり、現在の目的採用時には実行しない。',
 'r6ar':'活動・対象者の閉じた呼称と、同じ履歴・順序・始終点・状態の閉じた記述をr6aqへ構文として適用し、段階1の保持目的を作る。記述をデータとして引用し直して渡すため、目標を構成するだけで未来の保持や寄与を評価しない。',
 'r6as':'同じ人の行為者と対象者について、同じ活動の生起・能動的参加、作為的介入、意図的な選択・制御を結び、その同じ活動による同じ対象者の保持r6arを目的とする。始点は現在の活動点で、同じ状態が対象者に現在成立する。目的を持つだけの未実行、別人への目標、別活動による寄与、未来の成功の追加を避ける。',
 'r6at':'同じ固定基準のr6apを閉じた状態記述としてr6asへ渡す。未陶冶の実際の現在状態と、その状態へ働く操作と、その保持を目指す内容を同じものにする。基準と個体の呼称が指す対象も検査する。',
 'r6au':'指定された非空の対象範囲について、そのどの対象にも、指定された介入関係を満たす行為者・活動の組が存在しない。無関係な対象への活動を混ぜず、候補関係を全ての行為者・活動について渡す。対象が空なだけで非介入としない。',
 'r6av':'同じ固定集団が非空で全員人間r5tyであることを保ち、その全成員h246cをr6auの対象範囲にする。介入述語は本人・活動・対象の三引数を保ち、特定の政府だけや成功した活動だけへ範囲を狭めない。',
}
LIMITS=[
 'u0015第五文[1210,1354)のabsichtlich künstelt, um sie darin zu erhaltenへの依存群。思考・判断の未陶冶をRohigkeitの採用解釈とし、同じ人をその状態に保つための意図的な作為的介入を構成する。原文の全語義や人間集団の生得的属性の理論とはしない。',
 '現在その状態にある同じ対象への実際の介入と、未来を含む保持を目指す目的を分ける。目的の保持期間は閉じた履歴と始終点で指定する。期間の完全性は解釈入力の条件で、達成内容では全中間点の保持と同じ行為の因果的寄与を確認する。',
 '保持の目的は達成内容の段階1引用で、目指す時点に成功を要求しない。失敗する妨害も介入条件に入りうる。逆に、目的も作為的介入もない偶然の停滞を意図的保持にはしない。',
 '介入する人を政府・君主だけに限定せず、対象者本人との同一性も相違も強制しない。自由な助言や教育一般を一律に妨害とせず、操作の性格、意図的関与、同じ保持目的の三条件を別に検査する。',
 '非介入の一般構成r6au/r6avは、対象全員に対する行為者・活動の完全な関係を引数として受ける。本文への接続では、行為の全関連時機と目的期間をどう選ぶかを明示し、特定時点又は特定期間への目的だけを調べて全非介入へ強めない。',
 '人々の自発的な活動、徐々に抜け出す過程、同じ状態の解消、wenn man nur nichtの条件・限定、本文設定と全文帰属は未接続。正本116主張、17全単位判断＋四文1033文字を保存し、新しい確認文字数は0。原刊末尾seiの訂正記録v2を参照する。',
]
@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)
def definitions():
    text='d r6ap[reference d] h[a] e[i[person a][b point['+both('k aa[v person]','k h26rh[v person v reference v point]')+']]].\n'
    fields='activity a target a '+TIMES+' state '+STATE
    text+='d r6aq['+fields+'] e[b outcome[k rqqu[v activity o a[r[p r2mj]][v first] v target o a[r[p r2mk]][v history v before v first v last v state] v outcome]]].\n'
    text+='d r6ar[activity i[a] target i[a] '+TIMES+' state '+STATE+'] i b[e][o a[r b[p r6aq]][v activity v target o r[v history] o r[v before] o r[v first] o r[v last] o r[v state]]].\n'
    text+='d r6as[actor a '+fields+' reference d point d] c['+both(
        'k aa[v actor]','k aa[v target]','k dg[v activity v point]','k df[v actor v activity v point]',
        'e[s[v first]][v point]','t[c[s[v state]][v target]][v point]',
        'e[s[k h223g[v activity]]][v activity]','e[s[k h223g[v target]]][v target]',
        'k h26ri[v activity v target v state v reference v point]','k h26rj[v actor v activity v reference v point]',
        'k h26rk[v actor v activity k r6ar[k h223g[v activity] k h223g[v target] '+TARGS+' v state] v point]')+'].\n'
    state='o a[r[p r6ap]][k h223h[v reference]]'
    text+='d r6at[actor a activity a target a '+TIMES+' reference d point d] c['+both(
        'e[s[k h223h[v reference]]][v reference]',
        'k r6as[v actor v activity v target '+TARGS+' '+state+' v reference v point]')+'].\n'
    text+='d r6au[targets h[a] c interventions h[a a a] c] c['+both('g target a[c[v targets][v target]]',
        'u[g actor a[g activity a[g target a['+both('c[v targets][v target]','c[v interventions][v actor v activity v target]')+']]]]')+'].\n'
    text+='d r6av[group a reference d interventions h[a a a] c] c['+both('k r5ty[v group v reference]',
        'k r6au[i[target a][k h246c[v group v target v reference]] v interventions]')+'].\n'
    return text
def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(old.document,['aa','dg','df','r2mj','r2mk','rqqu','h223g','h223h','r5ty','h246c']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not(set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    basis=dict(status='deliberate_contrivance_for_same_state_retention_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
