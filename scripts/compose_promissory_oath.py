"""Bind solemn assurance and religious invocation to the same reciprocal act."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT
from scripts.compose_qualitative_influence import both

PARENT='data/irrevisable-confession-basis-v1.json'
LIBRARY='examples/v016/promissory-oath.noema'
BASIS='data/promissory-oath-basis-v1.json'
TERMS='i[h[j[a]] e]'
AUTHORITY='i[h[a] e]'
PRIMITIVES={
    'h255e':('[a d] c',['entity','point'],
        '宗教的な描写の中で、この対象は人間世界の制度や裁判の設定に従属せず、人の誠実さと道徳的な違反を知り裁く上位の人格的な存在として位置づけられる。この採用読解で神的な権威を指す性質。対象がこの性質を実際に持つかは入力を必要とし、性質を引用するだけでは該当個体の実在、神学説の真理、特定の宗派・固有名を断言しない。'),
    'h255f':('[a a d] c',['person','activity','point'],
        '本人はこの行為を、通常の会話・私的な心づもりと区別した、慣習的に特別の重みを持つ厳粛な表明として行っている。真剣な気分だけでは足りず、そのような表明としての言葉または儀礼上の形式がある。具体的な句、身振り、証人の人数、国家による認証、本人の誠実さ、法的効力はこの関係から決めない。'),
    'h255g':('[a a '+AUTHORITY+' '+TERMS+' j[a] d] c',['person','activity','authority','terms','bindings','point'],
        '本人は同じ表明行為で、閉じた性質記述により指す権威を、自分が同じ閉じた条項関数と順序付き引数の内容を誠実に引き受けることの証人として呼びかける。単に権威の名前を挙げること、条項内容の真理や現在の履行済みを証明することとは別。誠実さは呼びかけの対象であり、本人が実際に誠実か、権威が存在・受領するかは含意しない。'),
    'h255h':('[a a '+AUTHORITY+' '+TERMS+' j[a] d] c',['person','activity','authority','terms','bindings','point'],
        '本人は同じ表明行為で、閉じた記述で指す権威に、同じ条項と引数への自分の引受けが意図的な偽りや裏切りであれば、自分をその責任に応じて裁く側として呼びかける。条件付きの自己への責任の承認を含む呼びかけであり、罰の種類・量、故意のない履行失敗への処罰、実際の違反・裁き・正当性を追加しない。'),
}
MEANINGS={
    'r46w':'神的な道徳上の証人・裁き手h255eの性質を閉じたNoema記述として呼びかけへ渡すための関数。性質の本文を引用し、該当個体の存在量化や真理評価をしない。',
    'r46x':'同じ本人・行為・時点について、厳粛な表明h255fと、同じ閉じた条項・引数・権威記述r46wへの証人の呼びかけh255g、意図的な偽りや裏切りへの裁き手の呼びかけh255hを結ぶ。呼びかけ内容の誠実さや履行は脱引用しない。',
    'r46y':'同じ本人の引受けh255b、同じ行為で他の全当事者に対する引受けh255d、同じ行為へのr46xの宗教的な宣誓修飾を結ぶ。別行為の約束・儀礼・相互性を継ぎ合わせない。行為の実行者・生起・形成履歴は外側のhzcgで確認する。',
    'r46z':'r46vと同じ団体・合意・信条・主題・固定基準・全所属者・五引数条項r46uに、r46yで強化した宣言関係を適用する。二人以上の全当事者の同じ引受け行為が宣誓条件を満たす。目的、権限、信条や呼びかけ内容の真理、契約の有効性は要求しない。',
}
LIMITS=[
    'eidlichをこの教会団体の文脈に即して宗教的な宣誓として読む。厳粛な引受け、神的な権威への誠実さの証人の呼びかけ、故意の偽り・裏切りへの自己の責任を結ぶ。全文化・全時代の宣誓の必要十分条件とはしない。',
    '呼びかけ先は共通の性質記述r46wで指定する。原文にない固有名・特定の祈祷文・罰・実際の宗教的信念を足さず、別々の語句による表明も同じ意味の呼びかけとして許す。権威の実在や応答も断言しない。',
    '旧rinの単なる対象不成立なら応答という構成をそのまま故意の違反に代用しない。h255hは意図的な偽りや裏切りについて本人が裁きに服するという呼びかけ関係を入力として受け、実際の処罰や条件文の真理を述べない。',
    'h255f/g/hは一般的な表明の様式と呼びかけの関係である。原文一文をそのまま一基本記号へ置き換えず、宣誓を同じ相互引受けの本人・行為・時点・条項・引数へ合成する。慣習・呼びかけの認定は明示解釈の責任で、記録が未知なら推測しない。',
    '後見の目的・例示・自己呼称・権限の問い・次の否定回答は未統合。主文96主張と確認済み文字数は変更しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    text='d r46w[entity a] e[b point[k h255e[v entity v point]]].\n'
    fields='person a activity a terms '+TERMS+' bindings j[a] point d'
    target='v person v activity r[p r46w] v terms v bindings v point'
    text+='d r46x['+fields+'] c['+both('k h255f[v person v activity v point]',
        'k h255g['+target+']','k h255h['+target+']')+'].\n'
    fields='body a reference d person a activity a agreement a terms '+TERMS+' bindings j[a] point d'
    text+='d r46y['+fields+'] c['+both('k h255b[v person v activity v agreement v terms v bindings v point]',
        'f other a[y['+both('k h246c[v body v other v reference]','u[e[v person][v other]]')+']['+
        'k h255d[v person v other v activity v agreement v terms v bindings v point]]]',
        'k r46x[v person v activity v terms v bindings v point]')+'].\n'
    declares='i[person a activity a agreement a terms '+TERMS+' bindings j[a] point d]['+(
        'k r46y[v body v reference v person v activity v agreement v terms v bindings v point]]')
    text+='d r46z[body a agreement a creed a subject a reference d] c['+both('e[k h254z[v agreement]][v reference]',
        'k hzcg[v agreement r[p r46u] v reference k r46a[v body v reference p h246c] '+
        'i[person a][l[a][v person v agreement v body v creed v subject]] '+
        'i[at d][k h255c[v agreement v reference v at]] p h255a '+declares+']')+'].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);doc['statements']=[]
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    primitives={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in old.entries.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='same_reciprocal_undertaking_with_religious_promissory_oath',document=LIBRARY,primitives=primitives,
        definitions={n:e['meaning_ja'] for n,e in old.entries.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in old.entries.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
