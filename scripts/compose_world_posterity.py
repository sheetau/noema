"""Bind complete present/posterity scopes to nonfactive grateful praise."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_qualified_prince_frame import FIELDS as PRINCE,ARGS as PARGS

PARENTS=('data/grateful-regard-basis-v1.json','data/merit-praise-basis-v1.json','data/named-epoch-sentence-basis-v1.json')
LIBRARY='examples/v016/world-posterity.noema';BASIS='data/world-posterity-basis-v1.json'
GOAL='i[h[a] e]';RESPONSE='i b[h[a a a] e]';STANDARD='h[a '+RESPONSE+' '+GOAL+'] e'
FRAME='firstgroup a lastgroup a firstepoch a lastepoch a reference d candidate d anchor d'
FARGS='v firstgroup v lastgroup v firstepoch v lastepoch v reference v candidate v anchor'
SCOPE='group a epoch a hearers a benefaction a beneficiary a reference d candidate d anchor d benefit '+GOAL+' ground '+GOAL
SARGS='v group v epoch v hearers v benefaction v beneficiary v reference v candidate v anchor v benefit v ground'
NAMES=('group','epoch','hearers','benefaction','beneficiary','reference','candidate','anchor')
MERIT='firstgroup a lastgroup a firstepoch a lastepoch a hearers a benefaction a beneficiary a candidate d anchor d benefit '+GOAL+' ground '+GOAL+' firststandards j['+STANDARD+'] laststandards j['+STANDARD+']'
MARGS='v firstgroup v lastgroup v firstepoch v lastepoch v hearers v benefaction v beneficiary v candidate v anchor v benefit v ground v firststandards v laststandards'
HISTORY='i[at d][k h257z[v reference v candidate v at]]'
BEFORE='i[first d last d][k ic[v first v last v candidate]]'
PERIODS='i[era a at d][k h26ab[v era v reference v candidate v at]]'
MEANINGS={
 'r5yq':'同じ固定基準・履歴候補で、二時代がrjdの非空で順序づけられた区間であり、後続時代が現在時代の全点より後にある履歴内の全点とちょうど一致する。後続期間を都合よい一部分・直後の一世代だけへ縮めない。',
 'r5yr':'同じ後続時代についてrjgを使い、固定集団がその期間のどこかで生存する全人間と一致し非空である。現在まで生存した者だけ、称賛や感謝をする者だけの標本にしない。',
 'r5ys':'現在集団はr5sbの現在点で生存する全人間、後代集団はr5yrの現在時代より後の全期間で生存する人間とする。二集団は区別するが成員の重複は禁じず、血縁の子孫や一斉の世代交代へ限定しない。',
 'r5yt':'固定集団に属し、その応答点に生存する話者が、同じ時代内かつ基準現在以降でr5ypの感謝の態度を持って同じ対象者を称える。恩恵の行為、受益者、称揚行為、聴衆と対象者を保持し、現在より前の発話や死後の本人の発話を混ぜない。',
 'r5yu':'r5ytの全設定の閉じた呼称と、恩恵・功績記述そのものの引用から作る段階1の応答記述。感謝の判断内容が持つ状態の脱引用への依存を保ち、段階0へ落とさない。',
 'r5yv':'同じ応答に渡す五個体・三状況の閉じた呼称を元の設定へ照合する。恩恵と功績の記述の引用はそれぞれo rで同じ値から構成し、入れ替えない。',
 'r5yw':'既存ro5と同じ真の功績内容・非空の全適用基準の構造を、段階1の応答記述へ型を保って移した内容。応答の実行や義務、未来の心情を要求しない。新しい値する判定器は追加しない。',
 'r5yx':'r5yvの全参照一致の下で、同じ集団・時代の感謝を伴う応答記述r5yuに対しr5ywの値する評価を行う人物性質。応答における感謝を実際の集団全体の心情として外へ出さない。',
 'r5yy':'r5ysの現在と後代の完全な二範囲を、同じ現在点・同じ対象・恩恵・功績・聴衆における二つのr5yxの連言へ結ぶ。一方だけからの適合で済ませず、感謝する者だけに母集団を縮めない。',
 'r5yz':'同じ現在点の人物の宗教的判断の到達状態r5xvと、r5yyの現在・後代双方からの感謝を伴う称揚に値する評価を連言する。',
 'r5y2':'r5xjの同じ君主の前件を満たす者へr5yzを結ぶ一般条件。功績・恩恵・全適合基準は後半の解放内容と同じ設定へ閉じる必要があり、この依存群だけで文全体を完成扱いにしない。',
}
LIMITS=[
 'Welt und Nachweltは、現在の人々と、その現在時代より後に生存する人々として読む。DWB Nachweltの未来の人類とWelt/Mitweltとの対照を補助とする。物理的な地球、王の血縁の子孫、特定国民だけへ限定しない。',
 '現在世界の成員は基準現在に生存する全人間であり、現在時代の過去部分にだけ生存した者は含めない。後代は現在時代の全点より後の履歴全体を採り、直後の一世代だけに制限しない。現在時代の区切りは明示的な解釈基準で、原文に特定の年を追加しない。',
 '同じ人が現在と後代の両方で生存する場合を排除しない。世代を厳密な出生年別の互いに素な集団へ分割する読みは採らない。有限例の履歴は規則の反例検査であり、未来の全人類や無限の歴史の経験的な確認ではない。',
 'dankbarenは値する応答の記述内で、各応答の話者が感謝の態度を持つという読みを採る。世界と後代は固定された全人間範囲であり、感謝する人物だけの集団を最初から選ばない。現在又は未来の全員が実際に感謝するという独立した全称主張や、任意の人数閾値を原文へ補わない。',
 '集団全体の心情を別に統計的に述べる読みや形容詞を独立に投射する読みもありうるが、今回は不定詞句の応答の特徴として明示する。感謝の内容を落とさず、値する評価から実際の心情や発話を推論しない。',
 '感謝を含む応答は状態内容の脱引用への依存を含むため段階1を用いる。ro5の定義を上書きせず、構造を同一に保って応答記述の型だけを段階1へ移す。前回の感謝なしの段階0の応答が適切だったことは変更しない。',
 '二つの集団・時代・恩恵と功績・適合基準の本文での固定、最初の政府側の解放と良心事項の自由、名称評価の独立した著者帰属、sondern、一文全体と後続の意味判断は残る。本文112主張・v196・17単位判断を維持する。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def upgrade_merit():
    old=parents()[1].entries['ro5']['declaration'];oldtype=old['parameters'][1]['sort']
    newtype=deepcopy(oldtype);newtype['rank']=1
    def walk(x):
        if x==oldtype:return deepcopy(newtype)
        if isinstance(x,list):return [walk(y) for y in x]
        if isinstance(x,dict):return {k:walk(v) for k,v in x.items()}
        return x
    result=walk(old);result['name']='r5yw';return result

def definitions():
    period='k h26ab[v lastepoch v reference v candidate v at]'
    tail=both('k h257z[v reference v candidate v at]',
        'f earlier d[y[k h26ab[v firstepoch v reference v candidate v earlier]][k ic[v earlier v at v candidate]]]')
    text='d r5yq[firstepoch a lastepoch a reference d candidate d] c['+both(
        'k h26aa[v firstepoch v reference]','k h26aa[v lastepoch v reference]',
        'k rjd[v firstepoch v lastepoch '+HISTORY+' '+BEFORE+' '+PERIODS+']','f at d[z['+period+']['+tail+']]')+'].\n'
    text+='d r5yr[group a epoch a reference d candidate d] c[k rjg[v group v epoch v reference p aa p aa i[person a at d][k h256o[v person v candidate v at]] p h246c '+HISTORY+' '+BEFORE+' '+PERIODS+']].\n'
    text+='d r5ys['+FRAME+'] c['+both('u[e[v firstgroup][v lastgroup]]',
        'k r5sb[v firstgroup v firstepoch v reference v candidate v anchor]',
        'k r5yq[v firstepoch v lastepoch v reference v candidate]',
        'k r5yr[v lastgroup v lastepoch v reference v candidate]')+'].\n'
    audience='i[recipient a][k h246c[v hearers v recipient v reference]]'
    response='t[c[k r5yp[v benefaction v beneficiary v benefit v reference v candidate '+audience+' v ground]][v holder v response v actor]][v point]'
    text+='d r5yt['+SCOPE+'] h[a a a] e[i[holder a response a actor a][b point['+both(
        'k h246c[v group v holder v reference]','k h256o[v holder v candidate v point]',
        'k h26ab[v epoch v reference v candidate v point]','x[e[v anchor][v point]][k ic[v anchor v point v candidate]]',response)+']]].\n'
    named=' '.join(n+' '+('i[d]' if n in ('reference','candidate','anchor') else 'i[a]') for n in NAMES)+' benefit i['+GOAL+'] ground i['+GOAL+']'
    text+='d r5yu['+named+'] '+RESPONSE+'[o a[r b[p r5yt]]['+' '.join('v '+n for n in (*NAMES,'benefit','ground'))+']].\n'
    names=['k '+('h223h' if n in ('reference','candidate','anchor') else 'h223g')+'[v '+n+']' for n in NAMES]
    text+='d r5yv['+SCOPE+'] c['+both(*('e[s['+c+']][v '+n+']' for n,c in zip(NAMES,names)))+'].\n'
    code='k r5yu['+' '.join(names)+' o r[v benefit] o r[v ground]]'
    text+='d r5yx['+SCOPE+' standards j['+STANDARD+']] h[a] e[i[actor a][b point['+both(
        'k r5yv['+SARGS+']','t[k r5yw[v actor '+code+' v ground v standards]][v point]')+']]].\n'
    def side(which):return 't[c[k r5yx[v '+which+'group v '+which+'epoch v hearers v benefaction v beneficiary v reference v candidate v anchor v benefit v ground v '+which+'standards]][v actor]][v point]'
    text+='d r5yy[reference d '+MERIT+'] h[a] e[i[actor a][b point['+both('e[v point][v anchor]','k r5ys['+FARGS+']',side('first'),side('last'))+']]].\n'
    text+='d r5yz[topic a reference d '+MERIT+'] h[a] e[i[actor a][b point['+both(
        't[c[k r5xv[v topic v reference]][v actor]][v point]','t[c[k r5yy[v reference '+MARGS+']][v actor]][v point]')+']]].\n'
    text+='d r5y2['+PRINCE+' '+MERIT+'] e[k r5xk['+PARGS+' k r5yz[v topic v reference '+MARGS+']]].\n'
    return text

def build():
    libs=parents();doc=deepcopy(libs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for lib,roots in zip(libs,(['r5yp','h223g','h223h'],['r5xv','r5xk','ro5'],['r5sb','rjd','rjg','aa','h256o','h257z','h26aa','h26ab','h246c','ic'])):
        for d in closure(lib.document,roots):
            n=d['name'];e=lib.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not set(MEANINGS)&set().union(*(set(l.entries) for l in libs))
    doc['declarations'].append(upgrade_merit());doc=parse(format_graph(doc,'compact')+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    paths=set().union(*(set(l.source_sha256) for l in libs))
    basis=dict(status='complete_present_and_posterity_scopes_for_grateful_deserved_praise',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
