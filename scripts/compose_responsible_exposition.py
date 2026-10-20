"""Construct the exposition undertaken and distinguish practical admissibility."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_confessional_teaching import NAMES,MESSAGE
from scripts.compose_protected_remarks import bind

PARENTS=('data/clerical-report-forecast-basis-v1.json','data/doctrinal-statutes-basis-v1.json')
LIBRARY='examples/v016/responsible-exposition.noema'
BASIS='data/responsible-exposition-basis-v1.json'
TARGETS=(*NAMES,'bundle')
FIELDS=' '.join(n+' a' for n in TARGETS)+' reference d'
ARGS=' '.join('v '+n for n in TARGETS)+' v reference'
SEQ='l[a]['+' '.join('v '+n for n in TARGETS)+']'
GOAL='i b[h[j[a] d] e]'
PRIMITIVES={
    'h252g':('[a d] j[a]',['scope','reference'],
        '同じ範囲について固定基準で採用した個体の完全な有限列。順序もこの参照で固定し、評価の成否や後の候補状況に合わせて列を選び直さない。具体的な所属との一致・非空性・重複の不在はrcm等で別に要求する。未知の列を空列で補わない。'),
    'h252h':('[a a '+GOAL+' j[a] d d] c',['person','act','goal','bindings','reference','point'],
        '同じ本人がこの行為によって、指定した閉じた段階1の目標関数へ同じ個体列と固定基準を渡す遂行を、自分の責任で果たすべき事柄として引き受ける。単なる希望・予測・他者の発言の紹介、他者による一方的な任用、遂行を試みただけの場合とは分ける。行為の生起と行為者は別に結ぶ。履行・成功・客観的な義務の正当性・有効な契約・他者の受領をこの関係だけから導かない。'),
    'h252i':('[a '+GOAL+' j[a] d d d] c',['person','goal','bindings','reference','actual','candidate'],
        '同じ本人が同じ閉じた目標・対象列・固定基準の遂行を引き受けることについて、評価点の関連する事情と利用可能な手段・立場を保持して考慮する実践的な候補状況。実際に引受けが成功した状況だけで選別せず、無関係な再訓練や別職への移行で評価点の事情を取り替えない。引受けの成立・良心上の許容・目標の履行は別に評価し、現実の履歴や将来の必然性とはしない。'),
    'h252j':('[a a d d] c',['person','act','reference','point'],
        '同じ本人による同じ行為は、固定基準で適用する良心に照らした実践上の基準により、自分の責任で行ってよいものとして許容される。罪悪感がないこと・禁止が見つからないこと・教会が任用したこと・実行できることとは区別する。行為の具体的な引受け内容と生起は別に結ぶ。あらゆる倫理的正当化の一般理論や原文にない法制度を補わない。'),
}
MEANINGS={
    'r42n':'同じ固定列h252gからr42hで作る教義全体の内容を主張する、閉じた段階0の発話族記述。内容の真理を評価せず、実際の伝達・本人の信念・教会の代表としての発言は別に結ぶ。',
    'r42o':'同じ聖職者事例・規定群r42jを保ち、同じ本人・担当機会・活動について、その同じ規定内容r42nを教会の名で基準に沿って全担当宛先へ説明するr374を結ぶ。教義の真理や本人の確信は要求しない。',
    'r42p':'正確な十個体列を九個体の聖職者事例と同じ規定群へ束縛し、同じ基準のr42oを満たす担当機会・説明活動が存在するという遂行内容。引受けの対象として引用し、引受け自体から実行しない。活動は一回の短い発話に限定しない。',
    'r42q':'同じ本人を先頭とする対象列・目標記述・固定基準へのh252hの責任ある引受けと、同じ行為の生起dg・行為者dfを結ぶ。履行内容を実行せず、良心上の許容や実際の任用とは別に扱う。',
    'r42r':'同じ本人・目標・対象列・固定基準と評価点の実践候補h252iのどれかに、r42qの引受けがあり、その同じ行為が同じ本人にとってh252jにより許容される。可能な引受けと許容される引受けを別の候補や行為から寄せ集めない。空範囲では偽で、現在の引受け済みや履行を含意しない。',
    'r42s':'同じ教会・信条・主題・採用基準・規定群と固定列をr42jで保持し、同じ本人と十個体列についてr42pの説明を引き受けられるr42rを結ぶ。単に誰かが何かを引き受けられることへ弱めず、確信の不足だけから許容や可能性を導かない。',
}
LIMITS=[
    'u0012[3899,4278)のzu deren Vortrag er sich ... anheischig machen kannに向けた依存群。先行の同じ本人の確信の否定との結合、仮定の補充、gleichwohlとweil、全実益と後続条件・全文帰属は未統合。確認文字数を増やさない。',
    'Adelungのanheischig machenを責任ある引受けとして読み、単なる試行wagen、他者の任命、履行済みや契約の全法的効力と区別する。kannは当該事情で可能な、良心上許容できる引受けという明示した読み。前後の良心と辞職条件を参照するが、許容を教義の真理や欠けた確信だけから導かない。',
    '引受け目標は同じ規定群の内容を実際にNoemaで構成した説明。r374の担当機会・宛先範囲を用い、教会の全教義を一度に全会員へ伝えることに一般化しない。説明する活動には複合的な活動も代入でき、特定の期日・一回の講義・受け手の理解を補わない。',
    'r42pは全個体域で担当機会と活動を存在量化する。有限診断の範囲は明示し、引用の成功を現実の目標実現や全記述域の評価成功としない。',
    'h252iの実践候補とh252jの良心上の許容は別の解釈入力。個人の罪悪感・能力の高さ・一般的な契約自由を自動補完しない。これらの基本関係で実践的可能性や良心の全哲学を完成したとはしない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    rules='k h252g[v bundle v reference]'
    text='d r42n[bundle a reference d] '+MESSAGE+'[o a[r[i[body e][i[subject a][j s[v body]]]]][k r42h['+rules+' v reference]]].\n'
    case='k r42j[v church v creed v subject v standard v bundle '+rules+' v reference]'
    teaching='t[k r374['+' '.join('v '+n for n in NAMES)+' v reference v occasion v activity k r42n[v bundle v reference]]][v point]'
    text+='d r42o['+FIELDS+' occasion a activity a] e[b point['+both(case,teaching)+']].\n'
    goal='g occasion a[g activity a[t[k r42o['+ARGS+' v occasion v activity]][v point]]]'
    text+='d r42p[bindings j[a] reference d] e[b point['+bind(TARGETS,goal)+']].\n'
    shared='v person v act v goal v bindings v reference v point'
    text+='d r42q[person a act a goal '+GOAL+' bindings j[a] reference d point d] c['+both(
        'a[v bindings][n p a b][v person]','k dg[v act v point]',
        'k df[v person v act v point]','k h252h['+shared+']')+'].\n'
    text+='d r42r[person a goal '+GOAL+' bindings j[a] reference d actual d] c[g point d['+both(
        'k h252i[v person v goal v bindings v reference v actual v point]',
        'g act a['+both('k r42q['+shared+']','k h252j[v person v act v reference v point]')+']')+']].\n'
    text+='d r42s['+FIELDS+' actual d] c['+both(case,
        'k r42r[v person r b[p r42p] '+SEQ+' v reference v actual]')+'].\n'
    return text


def build():
    old,statutes=parents();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r374','df','dg']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(statutes.document,['r42j','r42h']):
        n=d['name'];e=statutes.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(c.entries) for c in parents()))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='same_doctrinal_exposition_and_admissible_responsible_undertaking',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
