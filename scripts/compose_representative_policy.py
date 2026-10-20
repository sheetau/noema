"""Lift representative teaching across all tasks and bind it to appointment."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_confessional_teaching import NAMES,FIELDS,ARGS,MESSAGE

PARENTS=('data/clerical-conscience-basis-v1.json','data/representative-teaching-basis-v1.json')
LIBRARY='examples/v016/representative-policy.noema'
BASIS='data/representative-policy-basis-v1.json'
MEANINGS={
    'r375':'同じ担当機会について全活動・全型適合発話記述を量化し、実際の教示r357があれば同じ活動・発話の規定適合r36aと、同じ教会の名による教示r373を要求する。適合した一活動だけを選ばず、追加の教示にも両条件が及ぶ。各追加活動が全担当宛先へ届いたことまでは要求しない。',
    'r376':'同じ担当機会について、既存r36cの非空で整合した期間・実行存在・全期間内の全実行を扱う構造を保持し、存在側を全担当宛先へ規定に沿い教会の名で教えるr374、全称側をr375へ置き換える。任意の一時機・一方法での履行を許し、不実行・期間外・追加の非代表発言を適合例で隠さない。',
    'r377':'同じ聖職者事例について、非空の全担当機会、元の生徒・会衆全員の担当割当て、全機会のr376を結ぶ。既存r36dの機会・宛先網羅を保持し、生徒と会衆への別機会の教示や宛先の重複を許す。',
    'r4a':'本人・職務・教会・会衆・生徒範囲・会衆成員範囲・信条・主題・基準の正確な九個体列と固定基準を、教会の名による全機会の教示方針r377へ渡す閉じた段階1のアダプター。単一の発話や任意の一活動へ目標を縮めない。',
    'r4b':'同じ教会が同じ本人へ同じ職務を過去に任用した一つの行為に、r4aの一般方針へ正確な九個体列と同じ内容基準を渡した内容を満たすことが条件として付されていた。既存r35yの履歴・時点・行為・条件の結合をそのまま使い、教示を実行しない。',
    'r4c':'同じ本人が現在点で、本人と異なる同じ教会の同じ主題を扱う業務担当r37zを担い、同じ職務への過去任用に同じ一般方針を付されたr4bがある。過去の任用だけから現在も職務を保持することを導かず、任用や現在の委任から教示の実行を導かない。',
}
LIMITS=[
    'u0012[3528,3793)のnach Vorschrift und im Namen eines andern vorzutragen angestellt istに向けた一般方針と任用の依存群。原文の全文提示、本人のGutdünkenによる裁量の否定、sondern、Dennは未統合で、本文や確認文字数は更新しない。',
    '既存r36c/d/e/gの担当機会・期間・宛先・束縛・任用構造を複製して新しい目標へ接続する。旧定義の意味や本文を変えず、全発話記述域を有限の見本へ縮めない。',
    '各担当機会に一つ以上の全担当宛先への適合した代表教示を求め、期間内の追加の実際の教示には規定適合と同じ教会の名での提示を要求する。全方法・全時点の実行、追加発言ごとの全宛先への到達は補わない。',
    'r4bは同じ過去任用の条件、r4cはそれに現在の委任・奉仕・業務担当を合わせる。現在の別個の規範要求h237z、本人の承諾、過去から現在までの連続勤務、法的有効性を任用事実から推論しない。',
    '任用条件の内容基準と過去の任用時点を区別し、記述・順序付き束縛・基準・正極性を保持する。教会の名による提示と基準適合は目的内容内にあり、現実の発言、教義の真理、本人の確信を外側の任用条件へ移さない。',
    '有限診断では個別教示の型付き境界と二発話の診断用展開を明示する。原定義は全記述域の有限評価を拒否する。個別教示はrepresentative-teachingの通常評価を根拠として引き継ぎ、有限例を全現実事例の網羅や意味同値性の自動証明としない。',
]


@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)


def renamed(node,mapping):
    if isinstance(node,dict):return {k:(mapping.get(v,v) if k=='symbol' else renamed(v,mapping)) for k,v in node.items()}
    if isinstance(node,list):return [renamed(v,mapping) for v in node]
    return node


def build():
    old,teaching=parents();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['r36c','r36d','r36e','r36g']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(teaching.document,['r373','r374']):
        n=d['name'];e=teaching.entries[n]
        if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
        else:doc['declarations'].append(d);imported[n]=e
    assert not set(MEANINGS)&set().union(*(set(p.entries) for p in parents()))
    fields=FIELDS+' occasion a';args=ARGS+' v occasion v activity v message'
    text='d r375['+fields+'] e[b point[f activity a[f message '+MESSAGE+'[y[t[k r357['+args+']][v point]]['+both(
        't[k r36a['+ARGS+' v activity v message]][v point]','t[k r373['+args+']][v point]')+']]]]].'
    doc=parse(format_graph(doc,'compact')+text)
    for source,target,mapping in [('r36c','r376',{'r356':'r374','r36b':'r375'}),
        ('r36d','r377',{'r36c':'r376'}),('r36e','r4a',{'r36d':'r377'}),('r36g','r4b',{'r36e':'r4a'})]:
        d=deepcopy(old.entries[source]['declaration']);d['name']=target;d['body']=renamed(d['body'],mapping);doc['declarations'].append(d)
    text='d r4c['+FIELDS+'] e[b point['+both('k r37z[v person v role v church v subject v point]',
        't[k r4b['+ARGS+']][v point]')+']].'
    doc=parse(format_graph(doc,'compact')+text)
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    sources=set().union(*(set(p.source_sha256) for p in parents()))
    basis=dict(status='complete_representative_teaching_policy_and_current_appointment',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
