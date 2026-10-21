"""Fix the implicit personal-endorsement supposition to the same doctrines."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_personal_conviction import CONTENT,PREMISE
from scripts.compose_responsible_exposition import FIELDS,ARGS

PARENTS=('data/clerical-report-forecast-basis-v1.json','data/doctrinal-statutes-basis-v1.json','data/responsible-exposition-basis-v1.json')
LIBRARY='examples/v016/personal-endorsement-case.noema'
BASIS='data/personal-endorsement-case-basis-v1.json'
NAMES='personname i[a] bundlename i[a] referencename i[d]'
NAME_ARGS='v personname v bundlename v referencename'
STATUTE_FIELDS='person a church a creed a subject a standard a bundle a reference d'
STATUTE_ARGS='v person v church v creed v subject v standard v bundle v reference'
PRIMITIVES={
    'h252o':('[a a '+CONTENT+' d d] c',['person','target','content','reference','point'],
        'この場面で検討の対象となっているのは、指定対象の同じ閉じた内容関数を固定基準の下で本人が自分自身の見解として肯定できるか、ということである。組織の採用見解を代わりに述べることの可否とは区別する。肯定・否定・確信の結果、実際の発問者や署名文書、外的な判断機会の存在はこの関係から導かない。内容を実行せず、本人の立場からの賛同が問題となる位置付けを表す。'),
}
MEANINGS={
    'r422':'同じ本人・対象の判断への外的機会hzzzvがあり、同じ閉じた内容・固定基準への本人自身の肯定が問題となるh252oを結ぶ。本人が肯定済みであることや実際の判断を要求しない、仮定の前提内容。',
    'r423':'本人・対象・固定基準の閉じた呼称と同じ閉じた内容関数から、r422を各候補で評価する閉じた段階0の前提関数を構成する。呼称と内容は構築した式に保持し、内容の真理・前提の実現はここで実行しない。',
    'r424':'同じ本人・教会・規定群・固定列のr42mに、r423の本人自身の賛同を問う仮定を渡す。三呼称が同じ本人・規定群・基準を指すことを要求し、r42iの同じ教義連言内容を前提と帰結の判断へ渡す。候補ごとに内容を交換せず、十分な賛同の否定を各候補の内側に保持する。',
    'r425':'同じ十個体と固定基準で、本人の十分な賛同の仮定的否定r424と、同じ規定の説明を責任をもって引き受けられるr42sを合わせる。仮定判断と実践可能性の候補範囲を交換せず、否定的確信だけから許容や可能性を導かない。gleichwohlの談話提示そのものは別に接続する。',
}
LIMITS=[
    'u0012[3899,4278)の本人自身の賛同と引受け可能性の併存へ向けた依存群。本文と確認文字数は据え置く。gleichwohlの譲歩提示、weil以下との理由関係、全実益、alsdann、文全体の帰属は未統合。',
    'würdeの省略された仮定を、同じ内容への本人自身の賛同を問う機会がある場合、と補う明示した読み。実際の署名要求、圧力、別職への移行、訓練、現実の前提の偽を追加しない。前後の本人の確信と教会の名での教示の区別を参照するが、唯一の文法的・歴史的復元とはしない。',
    '検討対象の位置付けh252oと外的機会hzzzvは別入力。仮定の全候補で両方を満たし、空範囲や前提を欠く候補は仮定的否定の成功にしない。比較候補hzkoの選択理由と妥当性は明示解釈の条件を継承する。',
    'r423は対象・基準への閉じた呼称を受け取る構成。r424は呼称の指示先との一致を確認する。呼称を持たない任意の個体へ暗黙にコードを捏造せず、全文への統合では同じ呼称の供給・束縛を明示する。',
    '同じ規定群の固定列h252g・内容連言r42iは前提と帰結で共通。列の完全性はr42jで確認する。十分な確信の不在を全教義の偽、各項の否定、現実の不賛同へ強めない。',
    'r425は同じ評価点の二条件の連言で、二種類の候補世界が同一という条件ではない。判断の場面と引受けの候補をそれぞれ保持し、教示目標の履行、教義の真理、良心上の許容を相互に推定しない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    args='v person v target v content v reference v point'
    text='d r422[person a target a content '+CONTENT+' reference d point d] c['+both(
        'k hzzzv[v person v target v point]','k h252o['+args+']')+'].\n'
    template='r[i[person a target a content '+CONTENT+' reference d][i[point d][k r422['+args+']]]]'
    text+='d r423[person i[a] target i[a] content '+CONTENT+' reference i[d]] '+PREMISE+'[o a['+template+'][v person v target o r[v content] v reference]].\n'
    rules='k h252g[v bundle v reference]';content='k r42i['+rules+' v reference]'
    premise='k r423[v personname v bundlename '+content+' v referencename]'
    text+='d r424['+STATUTE_FIELDS+' '+NAMES+' actual d] c['+both(
        'e[v person][s[v personname]]','e[v bundle][s[v bundlename]]','e[v reference][s[v referencename]]',
        'k r42m[v person v church v creed v subject v standard v bundle '+rules+' v reference '+premise+' v actual]')+'].\n'
    text+='d r425['+FIELDS+' '+NAMES+' actual d] c['+both(
        'k r424['+STATUTE_ARGS+' '+NAME_ARGS+' v actual]',
        'k r42s['+ARGS+' v actual]')+'].\n'
    return text


def build():
    catalogs=parents();doc=deepcopy(catalogs[0].document);doc.update(declarations=[],statements=[]);imported={}
    for old,roots in zip(catalogs,(('hzzzv',),('r42m',),('r42s',))):
        for d in closure(old.document,list(roots)):
            n=d['name'];e=old.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not (set(PRIMITIVES)|set(MEANINGS))&set().union(*(set(c.entries) for c in catalogs))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(c.source_sha256) for c in catalogs))
    basis=dict(status='same_doctrines_personal_endorsement_supposition_and_responsible_exposition',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
