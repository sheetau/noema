"""Quantify retention configurations and every point of a common interval."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_gradual_self_departure import TIME,TARGS

PARENTS=('data/deliberate-retention-basis-v1.json','data/gradual-self-departure-basis-v1.json')
LIBRARY='examples/v016/noninterference-interval.noema';BASIS='data/noninterference-interval-basis-v1.json'
PRIMITIVES={
 'h26rp':('[a a a a d d] c',['actor','activity','target','configuration','reference','point'],
   '同じ行為者・活動・対象者・固定基準・活動点について、保持目的として記述できる関連する期間設定の全範囲に、この設定が属する。設定は履歴・順序・現在の始点・終点を閉じた記述で指定する。同じ状態の保持を目指す実際の目的があればそれを表す設定を必ず含み、目的の採用・成功・活動の実行に基づき事後選別しない。始点はこの活動点に一致し、少なくとも一つの設定を与える。完全性は解釈入力の条件である。'),
}
PROVIDERS={'history':('h26rq','i[h[d] c]'),'before':('h26rr','i[h[d d] c]'),'first':('h26rs','i[d]'),'last':('h26rt','i[d]')}
for role,(n,t) in PROVIDERS.items():
    PRIMITIVES[n]=('[a d] '+t,['configuration','reference'],
        '同じ保持目的の期間設定と固定基準が指定する'+role+'の閉じた記述。実際に達成された期間の選別ではなく、目的として目指す内容の構成要素である。四記述は同じ設定を共有し、真理や実現可能性は目的採用時に実行しない。別の活動点への呼称を同じ始点と扱わない。')
MEANINGS={
 'r6a5':'同じ行為者・活動・対象・基準・点の全設定h26rpの中に、同じ四記述をr6atへ渡して意図的な保持操作を満たす設定がある。目的を一つの選択された期間へ固定せず、別設定の失敗や不採用で実際の目的を消さない。',
 'r6a6':'同じ行為者・活動・対象・基準・点について、期間設定の範囲が非空で、その全設定の始点の呼称が同じ活動点を指す。目標達成・未来の履歴の真理・終点までの実現可能性は要求しない。設定欠落を非介入へ補わない。',
 'r6a7':'同じ非空の人間集団と有効な順序付き期間について、全区間の各点・全成員・全行為者・全活動のr6a6を要求し、期間中のどの点にもr6a5の意図的保持操作が存在しないとする。始終点だけの非介入、政府だけの非介入、一つの目的期間だけの不在へ狭めない。',
}
LIMITS=[
 'u0015第五文の非介入条件を全関連期間へ接続する依存群。活動点ごとの保持目的の全設定を量化し、そのどれかで意図的な操作があれば介入に数える。目的の成功や実現可能性は要求しない。',
 '設定の完全性は、実際の同じ保持目的を表す記述があれば必ず含めるというh26rpの意味規約である。有限試験が現実の全意図や全記述の探索を終えたことを意味しない。構文的に可能な目的は真理評価から分け、目的を採らない活動にも非空の候補設定を与える。',
 '設定欠落や他の活動点への始点の誤参照を非介入としない。目的の未来の保持を現在実行することなく、始点の呼称だけを活動点へ結ぶ。行為者・活動・対象・評価点を変えずに全設定を調べる。',
 '関連期間は固定された履歴の両端込み全区間で、結果を見て介入点を除かない。本文では自己からの離脱と同じ候補履歴・期間を共有する必要がある。終点以後の全未来や世界の全無関係な人への操作の不在は述べない。',
 'Die Menschenの範囲と本文の候補経過、wenn man nur nichtの条件・限定、同じ過程の後件、全文帰属は未接続。正本116主張と既存判断を保存し、新たな確認文字数は0。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)
def definitions():
    fields='actor a activity a target a reference d point d'
    scope='k h26rp[v actor v activity v target v configuration v reference v point]'
    providers=' '.join('k '+n+'[v configuration v reference]' for n,t in PROVIDERS.values())
    text='d r6a5['+fields+'] c[g configuration a['+both(scope,'k r6at[v actor v activity v target '+providers+' v reference v point]')+']].\n'
    text+='d r6a6['+fields+'] c['+both('g configuration a['+scope+']',
        'f configuration a[y['+scope+'][e[s[k h26rs[v configuration v reference]]][v point]]]')+'].\n'
    inside='c[k rlz['+TARGS+']][v point]'
    complete='f actor a[f activity a[f target a[f point d[y['+both('k h246c[v group v target v reference]',inside)+'][k r6a6[v actor v activity v target v reference v point]]]]]]'
    intervention='i[actor a activity a target a][g point d['+both(inside,'k r6a5[v actor v activity v target v reference v point]')+']]'
    text+='d r6a7[group a reference d '+TIME+'] c['+both('k ta[v history v before]','c[v history][v first]','c[v history][v last]',
        'c[v before][v first v last]',complete,'k r6av[v group v reference '+intervention+']')+'].\n'
    return text
def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for c,roots in zip(sources,(['r6at','r6av','h246c'],['ta','rlz'])):
        for d in closure(c.document,roots):
            n=d['name'];e=c.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not(set(MEANINGS)|set(PRIMITIVES))&set().union(*(set(c.entries) for c in sources))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(c.source_sha256) for c in sources))
    basis=dict(status='complete_retention_configurations_and_interval_noninterference_partial',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
