"""Keep a civic/intellectual comparison fixed inside nonfactive appearance."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both

PARENT='data/civic-intellectual-options-basis-v1.json';NAMES='data/whole-view-sentence-basis-v1.json'
OLD='examples/v016/kant-policy-recognition.noema';OLD_BASIS='data/policy-recognition-basis-v1.json'
LIBRARY='examples/v016/civic-advantage-appearance.noema';BASIS='data/civic-advantage-appearance-basis-v1.json'
CODE='i c[e]'
PRIMITIVES={
 'h26yy':('[a d d] d',['community','reference','view'],'同じ共同体・固定基準の二制度条件を比較するこの見方において、市民的自由が低い側の制度条件を評価する状況。同じ見方の高い側h26yzと対にし、本文の先の日時という意味にはしない。見かけの候補ごとに人物・活動・課題・規範的な役割を変更せず、同じ低い側の制度について評価する。'),
 'h26yz':('[a d d] d',['community','reference','view'],'同じ共同体・固定基準・見方で、市民的自由が高い側の制度条件を評価する状況。h26yyと同じ比較の相手であり、別の人口又は別の有利な課題への交換を許さない。高いという大小自体はr6hgで検査し、機会の増加や因果をこの状況名から推定しない。'),
 'h26y2':('[a d a '+CODE+' d d] c',['community','reference','observer','claim','anchor','candidate'],'同じ共同体・固定基準・人の観点で、この基準点から指定された同じ比較内容がどう見えるかを評価する、表面的な情報に沿う候補の全範囲。この観点は必ずしも著者個人の実際の確信ではなく、文章が示す一見の見通しである。現実の事実、全論理的可能性又は対象内容が真になる状況だけを選んだ集合とは分け、候補の非空性と同じ内容の全候補での成立をrroで確かめる。'),
}
MEANINGS={
 'r6ho':'同じ共同体・二法秩序・固定基準を保持し、各見方に対応する低い側と高い側の状況をr6hnへ渡す比較内容。人・活動・課題は固定基準へ留め、市民的許可と評価済みの精神的機会の厳密包含を同じ二点で評価する。',
 'r6hp':'r6hoと同じ共同体・二法秩序・固定基準・二点のうち、市民的許可の大小r6hgだけを取り出す内容。精神的利益の有無とは独立に、市民的自由が高い側という記述を確認する。',
 'r6hq':'同じ共同体・低い側の法秩序・高い側の法秩序・固定基準の閉じた呼称をr6hoへ適用し、段階2の閉じた比較内容を構成する。引用の作成時には法秩序・許可・能力を実行しない。',
 'r6hr':'h223g/h223hが返す共同体・二法秩序・固定基準の呼称が、それぞれ同じ対象を指すことを検査する。別の対象への呼称を、見かけの内容が成立しないという通常の判断へ紛れ込ませない。',
 'r6hs':'人の観点・同じ共同体・二法秩序・固定基準について、呼称の一致と、評価基準点での市民的自由の大小r6hpを要求し、同じ閉じたr6ho内容が非空の見かけの全候補で成立することをrroで構成する。実際の精神的優位は要求せず、実際に優位でもそれを排除しない。',
}
LIMITS=[
 'u0017第三文のscheint … vortheilhaftへ向けた、比較内容を保持する非事実的な見かけの依存群。精神的自由に有利という比較内容には、同じ成員・課題の達成機会の厳密包含拡大を用いる。二制度の共変動を原因の十分な説明とはせず、障壁や低い側の発展機会との因果的な接続は次に行う。',
 '見かけの全候補で同じ比較内容を評価する。市民的自由の大小は評価基準点でも確認するが、精神的機会が実際にも増えるとは推論しない。逆に、見かけは必ず誤りだという条件も加えない。空又は未知の見かけの範囲を成功させない。',
 '観点は一見の見通しを担う人の観点であり、著者の現実の心理的信念や読者全員の同意とはしない。何がその観点から見えているかはh26y2の明示した解釈入力とし、単なる肯定信念一般と区別する。視覚器官・知覚過程・確信度・根拠の正当化の一般理論は追加しない。',
 '低い側と高い側の制度・成員・課題・固定基準を候補間で保持する。候補は同じ制度の評価の見方であって、別のより有利な制度への交換ではない。時間的な前後、実在する二国家の比較、自由の程度の数値一単位の差は補わない。',
 '第三文全文の著者帰属・dochとhingegen・jener/diesem・越えがたい制限と全能力に応じた展開は未統合。第一・第二文の正本121主張、登録簿v205、意味確認範囲14,915文字を保持する。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in (PARENT,NAMES))
@lru_cache(None)
def legacy():
    ds=closure(parse((ROOT/OLD).read_text(encoding='utf-8')),('rro',))
    ms=json.loads((ROOT/OLD_BASIS).read_text(encoding='utf-8'))['definitions'];return ds,{d['name']:ms[d['name']] for d in ds}
def definitions():
    fields='community a lowerorder a higherorder a reference d';args='v community v lowerorder v higherorder v reference'
    points='k h26yy[v community v reference v view] k h26yz[v community v reference v view]'
    text=''.join('d '+n+'['+fields+'] e[b view[k '+target+'['+args+' '+points+']]].\n' for n,target in (('r6ho','r6hn'),('r6hp','r6hg')))
    names='community i[a] lowerorder i[a] higherorder i[a] reference i[d]'
    text+='d r6hq['+names+'] '+CODE+'[o a[r c[p r6ho]]['+args+']].\n'
    codes='k h223g[v community] k h223g[v lowerorder] k h223g[v higherorder] k h223h[v reference]'
    text+='d r6hr['+fields+'] c['+both(*['e[s[k '+('h223h' if n=='reference' else 'h223g')+'[v '+n+']]][v '+n+']' for n in ('community','lowerorder','higherorder','reference')])+'].\n'
    alternatives='i[observer a claim '+CODE+' anchor d candidate d][k h26y2[v community v reference v observer v claim v anchor v candidate]]'
    text+='d r6hs[observer a '+fields+'] e[b anchor['+both('k aa[v observer]','k r6hr['+args+']','t[k r6hp['+args+']][v anchor]',
      'k rro[v observer k r6hq['+codes+'] v anchor '+alternatives+']')+']].\n'
    return text
def build():
    p,names=parents();doc=deepcopy(p.document);doc['statements']=[];imported={n:e for n,e in p.entries.items()}
    for d in closure(names.document,('h223g','h223h')):
        n=d['name'];e=names.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
        else:doc['declarations'].append(d);imported[n]=e
    ds,means=legacy()
    for d in ds:
        if d['name'] in imported:assert d==imported[d['name']]['declaration'] and means[d['name']]==imported[d['name']]['meaning_ja']
        else:doc['declarations'].append(d)
    assert not(set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(p.entries) for p in parents()))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+r[0]+'.' for n,r in PRIMITIVES.items())+definitions());by={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=by[n]['parameters'],result=by[n]['result'],arguments=r[1],meaning_ja=r[2]) for n,r in PRIMITIVES.items()})
    paths=set().union(*(set(p.source_sha256) for p in parents()))|{OLD,OLD_BASIS}
    basis=dict(status='fixed_comparison_nonfactive_appearance_partial',document=LIBRARY,primitives=prims,
      definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|means|MEANINGS,
      imported_symbols={n:e['meaning_basis'] for n,e in imported.items()}|{n:OLD_BASIS for n in means},
      import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
