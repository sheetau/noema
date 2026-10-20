"""General civic resistance and its possible induction by the same criticism."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENTS=('data/protected-remarks-basis-v1.json','data/civic-levy-refusal-basis-v1.json')
LIBRARY='examples/v016/general-resistance.noema'
BASIS='data/general-resistance-basis-v1.json'
CODE='i[h[j[a]] e]'
FIELDS='issuer a person a role a response a community a description '+CODE+' bindings j[a] sign c reference d'
ARGS='v issuer v person v role v response v community v description v bindings v sign v reference'
PRIMITIVES={
    'h244p':('[a a d] c',['issuer','community','reference'],
        'この出所は同じ政治的共同体の公的な共同事務・規律について人々への指図を発する制度上の側である。私人の助言や希望だけとは区別する。個別の要求、道徳的正当性・適法性・受諾・履行は別である。'),
    'h244q':('[a d] j[a]',['community','reference'],
        '同じ固定基準でこの政治的共同体に属する人々の有限列。標本や既に反抗した人々だけの列に差し替えない。過不足の不在はr34gで成員関係との同値を全個体について検査し、重複・空列は割合の定義で拒否する。無限共同体の測度はこの有限の読みの対象外である。'),
    'h244r':('[a d b] c',['community','reference','ratio'],
        '同じ共同体・固定基準の下で、この成員割合を局所的・孤立的でない一般的な広がりとする比較基準。成功した候補だけを見て変えず、文脈に即した単調な基準として明示する。原文にない過半数・全員・特定の数値を固定しない。ゼロ割合の排除はr34hでも要求する。'),
    'h244s':('[a a i b[h[a d] e] d d] c',['activity','community','effect_family','reference','outcome'],
        'この同じ候補状況で、活動が同じ共同体と固定基準を閉じた内容関数へ渡した結果の成立を誘発する因果関係にある。単なる共起・後続・相関とは区別する。既存g3を対象と明示基準および段階1記述へ広げる。活動生起と結果の実際の成立は別に検査し、現実での発生や規範的許可を含めない。'),
    'h244t':('[a a d d] c',['activity','community','evaluation','outcome'],
        '同じ批判活動と共同体について、この評価状況から見た事情に適合する可能な結果状況である。成功結果だけを事後選別しない。認識者の単なる無知、空想上の無制約な想像、処罰の許可、現実の結果とは分ける。'),
}
MEANINGS={
    'r34e':'同じ市民・共同体に公的指図をする出所からの、同じ内容記述・引数列・極性の要求が評価点で適用される。その要求への応答として本人が同じ反応活動を実行し、同じ内容の反対極性を実践的方針とする。納付以外の要求と禁止への反抗も扱い、未履行だけを反抗にしない。',
    'r34f':'同じ人・共同体・固定基準に対して、r34eを満たす出所・市民の立場・反応・型付き内容記述・引数列・要求極性の組があるという内容。全ての適合する記述・有限列を量化し、既知の納付記述や検査用の有限候補だけに限定しない。',
    'r34g':'固定された成員列h244qについて、列への出現と同じ基準で人かつ共同体成員であることの同値を全個体に要求する。反抗した者だけの列、欠落・余分のある列を、母集団全体として扱わない。',
    'r34h':'r34gの母集団の完全性と、既存rflの重複なし・非空・正確な割合を結び、同じ評価点の個人の実践的反抗r34fが正の割合で文脈的広がりh244rに達するという内容。孤立的な一事例や全員の一致へ一般性を固定しない。',
    'r34i':'既存rfjで、同じ批判・共同体に関する評価点からの候補が少なくとも一つあり、その同じ候補で批判が起き、r34hの同じ共同体・固定基準の一般的反抗を誘発し、その結果も成立することを要求する内容。別候補の生起・因果・結果を合成せず、現実の反抗や全候補での発生を主張しない。',
}
LIMITS=[
    'u0012[2513,2770)の挿入説明das allgemeine Widersetzlichkeiten veranlassen könnteに向けた依存群。原刊486頁とAA8/37の該当文を再読した。本文への統合・Skandal評価・処罰可能性・sogar・全文帰属は残り、新規意味確認を加算しない。',
    'Widersetzlichkeitenは公的な指図への実践的な反抗の諸事例と読む。単に思想上の異論、誤解、不能、未払いだけを数えず、実際の暴力や組織化、命令違反の成功は要件にしない。個別の課税拒否だけでなく、共同体の他の公的な指図への反抗も範囲に保つ。',
    'allgemeineは同じ政治的共同体における人々への広がりとする明示した読み。万人の全称でも、別々の命令の種類数でもない。有限な共同体の全成員を固定して扱い、標本率・候補ごとの母集団変更では代用しない。個別人数・広がりの閾値は原文が指定していない。',
    'r34fは記述と有限列の全領域を量化する。有限評価器は拒否し、列挙可能な既知の少数の要求で置き換えない。局所検査ではr34eを実定義で評価し、広がり・候補の接続検査ではr34fを型付き境界として別に扱う。',
    '因果h244sと候補h244tは明示したモデル入力であり、共起から因果を推定するアルゴリズムではない。ここで社会的因果の現実の同定を証明したとはしない。könnteの可能性を確率閾値・必然・実際の結果へ変えない。',
    '引用するr34hは段階1の閉じた内容関数であり、対象共同体と固定基準を因果関係にも結果成立にも同じく渡す。結果内容を脱引用するrfkを無理に引用せず、同じ結果の実定義を直接適用する。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    text='d r34e['+FIELDS+'] e[b point['+both(
        'k r33s[v person v role v community v reference]','k h244p[v issuer v community v reference]',
        'k h7k[v issuer v person v role v description v bindings v sign v point]',
        'k h244k[v response v issuer v person v role v description v bindings v sign v reference]',
        't[k zzq[v person v response]][v point]',
        'k h244j[v person v response v description v bindings u[v sign] v point]')+']].\n'
    body='t[k r34e['+ARGS+']][v point]'
    for name,sort in reversed((('issuer','a'),('role','a'),('response','a'),('description',CODE),('bindings','j[a]'),('sign','c'))):
        body='g '+name+' '+sort+'['+body+']'
    text+='d r34f[person a community a reference d] e[b point['+body+']].\n'
    text+='d r34g[community a reference d] c[f person a[z[k hg[k h244q[v community v reference] v person]]['+both(
        'k aa[v person]','k h237c[v person v community v reference]')+']]].\n'
    text+='d r34h[community a reference d] e[b point['+both('k r34g[v community v reference]',
        't[k rfl[v community i[group a][k h244q[v group v reference]] p aa '
        'i[person a][k r34f[v person v community v reference]] '
        'i[ratio b]['+both('k hc[n p a b v ratio]','k h244r[v community v reference v ratio]')+']]][v point]')+']].\n'
    text+='d r34i[criticism a community a reference d] e[b point[k rfj[v criticism v point '
    text+='i[activity a evaluation d outcome d][k h244t[v activity v community v evaluation v outcome]] '
    text+='i[outcome d]['+both('k dg[v criticism v outcome]',
        'k h244s[v criticism v community r b[p r34h] v reference v outcome]',
        't[k r34h[v community v reference]][v outcome]')+']]]].\n'
    return text


def build():
    old,civic=parents();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['rfj','rfl','hg','dg']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(civic.document,['r33s','zzq','h7k','h244j','h244k']):
        n=d['name']
        if n in imported:assert d==imported[n]['declaration'] and civic.entries[n]['meaning_ja']==imported[n]['meaning_ja']
        else:doc['declarations'].append(d);imported[n]=civic.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS)) & (set(old.entries)|set(civic.entries))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    primitives={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(c.source_sha256) for c in parents()))
    basis=dict(status='general_civic_resistance_and_possible_induction',document=LIBRARY,primitives=primitives,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
