"""Separate competence, choice of criterion, and the absence of free discretion."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_confessional_teaching import NAMES,FIELDS,ARGS,MESSAGE

PARENT='data/representative-policy-basis-v1.json'
LIBRARY='examples/v016/teaching-discretion.noema'
BASIS='data/teaching-discretion-basis-v1.json'
OPEN_FIELDS='source a person a role a subject a message '+MESSAGE+' reference d'
OPEN_ARGS='v source v person v role v subject v message v reference'
PRIMITIVES={
    'h247p':('[a a a a '+MESSAGE+' d d] c',['source','person','role','subject','message','reference','point'],
        'この制度的・規範的な出所の下で、この本人はこの立場において、固定基準の同じ主題・閉じた発話記述に関する教示の内容と扱いを決める職務上の権限を持つ。単に発話を伝える許可、事実上の支配力、発言能力、実際の決定行為、私的な確信とは区別する。裁量の範囲に課される基準や他者の指示、決定の実行・正当性、現代法上の特定の権利変動はこの関係だけでは定めない。'),
    'h247q':('[a a a a '+MESSAGE+' d d] c',['source','person','role','subject','message','reference','point'],
        '同じ出所・本人・立場・固定基準の同じ主題と閉じた発話記述に関する教示の内容と扱いを決める際、本人の判断を最終的かつ十分な決定基準としてよい。他者が指定した内容・規定に合わせるという条件でその裁量を制限されない。本人の判断が現にあったこと、正しいこと、決定権限そのもの、思考能力や全ての局所的判断の自由は含意しない。実務上の個々の判断が許されるだけの場合とは区別する。'),
}
MEANINGS={
    'r4d':'同じ出所・本人・職務・主題・閉じた発話記述・内容基準・評価点について、教示内容を決める職務上の権限h247pと、本人の判断を他者の規定で制限されない最終的な基準にできるh247qを結ぶ。freie Gewalt nach eigenem Gutdünkenの採用解釈。実際の独断的発言は要求しない。',
    'r4e':'同じr4dの自由な教示内容決定の権限を否定する。権限はあるが判断基準が指定されている場合も含め、全ての実務判断の禁止、全権限の欠如、教示不能や教示の不実行へ強めない。未知の権限や基準を否定の根拠に補わない。',
    'r4f':'同じ教会を制度上の出所とする、同じ本人・職務・主題・発話についてのr4eと、同じ九個体・内容基準・評価点の代表教示への現任用r4cを合わせる。一般方針と当該発話への裁量の否定を別々に保持し、任用から否定を導かず、否定から任用を補わない。',
}
LIMITS=[
    'u0012[3528,3793)のnicht freie Gewalt ... nach eigenem Gutdünken zu lehrenと任用の対置に向けた依存群。本文のwas/das/dessenが受ける同じ発話と、そのようなものとして提示する外側の内容、sondern、Denn、全文帰属は未統合。文字数を増やさない。',
    'Gewaltはここでは職務上の内容決定権限、Gutdünkenは本人の判断・裁量を基準にすることと読む。AdelungのGewalt項とDRWのgutdenken/Gutdenken項を補助資料として保存するが、辞書の全用法や唯一の作者意図を主張しない。',
    '既存h237bは独立に方針を決め直す立場の実際の行使、rnkは同じ政策の肯否への許可を扱う。今回の職務上の内容決定権限を、単なる行使の不在や伝達への許可の有無へ同一化せず、それらの意味も変更しない。',
    '二つの基本関係は決定権限と許容される決定基準を分ける一般的な意味規約。教示の実行・教義の真理・本人の判断の実在や正しさを付けず、否定はその組合せだけへかける。権限の全哲学・法理論や正当化手続の完成ではない。',
    '同じ閉じたNoema発話記述を引数として保持し、同じ真偽を返す別記述へ置き換えない。制度上の出所はr4fでは同じ教会であり、学識者としての別の立場の公的自由を否定しない。',
    'r4fは両内容を同じ点で構成するが、原文の提示関係へ接続するときは引用する。外側の著者や本人が提示しただけで、権限の不存在・任用・教示の現実の成立を導かない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    text='d r4d['+OPEN_FIELDS+'] e[b point['+both('k h247p['+OPEN_ARGS+' v point]',
        'k h247q['+OPEN_ARGS+' v point]')+']].\n'
    text+='d r4e['+OPEN_FIELDS+'] e[b point[u[t[k r4d['+OPEN_ARGS+']][v point]]]].\n'
    text+='d r4f['+FIELDS+' message '+MESSAGE+'] e[b point['+both(
        't[k r4e[v church v person v role v subject v message v reference]][v point]',
        't[k r4c['+ARGS+']][v point]')+']].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);doc.update(declarations=closure(doc,['r4c']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='free_teaching_discretion_and_same_representative_appointment',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
