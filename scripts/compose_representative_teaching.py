"""Separate delegated business, actual teaching and speaking for a principal."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_confessional_teaching import NAMES,FIELDS,ARGS,MESSAGE

PARENT='data/clerical-conscience-basis-v1.json'
LIBRARY='examples/v016/representative-teaching.noema'
BASIS='data/representative-teaching-basis-v1.json'
TASK_FIELDS=FIELDS+' occasion a activity a message '+MESSAGE
TASK_ARGS=ARGS+' v occasion v activity v message'
PRIMITIVES={
    'h247n':('[a a a a d] c',['person','role','principal','subject','point'],
        '同じ本人に委ねられたこの職務の任務には、この主題について同じ委託元の業務をその委託元に代わって取り扱うことが含まれる。単に利益を与えること、同じ組織に所属すること、自分の仕事だけを行うこととは区別する。職務保持・奉仕・活動の職務上の位置付けはcf/h246k/cbで別に結ぶ。個々の発話の実行・規定適合や私的な信念、あらゆる内容を自由に決める権限、現代の特定の法的代理制度を含意しない。'),
    'h247o':('[a a a '+MESSAGE+' d] c',['activity','principal','subject','message','point'],
        'この活動で同じ主題について伝えられる同じ閉じたNoema発話記述は、指定した委託元の立場で、その委託元に代わって行う発言として提示される。活動の話者・職務委任・業務担当・実際の伝達は別に結ぶ。委託元の名を含むだけの発話や他人の見解の中立的引用とは区別する。委託元または話者の内心の確信、内容の真理、各発言への無制限の権限・法的有効性は含意しない。発話記述を真偽が同じ別記述へ置き換えない。'),
}
MEANINGS={
    'r37z':'同じ本人が同じ職務を委ねられ、本人と異なる同じ委託元にその職務で仕え、同じ主題について委託元の業務を代わって扱う任務h247nを持つ。職務保持や奉仕だけで業務代理を補わず、実際の発話もまだ要求しない。',
    'r372':'同じ聖職者事例・担当機会・活動・主題・発話の実際の教示r357に、同じ評価点のr37zの業務担当とcbの職務としての活動位置付けを結ぶ。少なくとも一人の担当宛先への実際の伝達を保ち、規定適合や教会の名による提示は別に扱う。',
    'r373':'同じ職務上の業務担当者による教示r372に、同じ活動・教会・主題・発話・評価点について教会の名による提示h247oを結ぶ。本人の独立した見解の表明や、教会の名を言及しただけの引用と区別する。',
    'r374':'r373の教会の名による同じ実際の教示と、r356の同じ担当機会・全担当宛先・採用された同じ条件列への適合を合わせる。代表して語ることと規定を満たすことを独立に要求し、片方だけからもう片方を導かない。',
}
LIMITS=[
    'u0012[3528,3793)の職務上の教示、Geschäftträger、im Namen eines andern、nach Vorschriftに向けた依存群。任用された目的の一般方針、本人の裁量の否定、同じ教示内容をそのようなものとして提示する外側の構成、sondernとDenn、文全体の著者帰属は未統合。確認文字数を増やさない。',
    'Geschäftträgerを同じ教会の業務を委託された立場で扱う者と読む。現代の外交官の役職、特定の法人格・法的代理制度・儀礼、全会員の信念を補わない。h247nの業務担当とh247oの発言上の代表を別の基本関係として明示する。',
    'eines andernの委託元には先行の同じ教会を渡し、本人との非同一性をr37zで明示する。個人の上司名を原文外から補わない。具体的な任用過去の構成は既存r35y/r36gにあり、この群で代理任務からその存在を推論しない。',
    'r373は実際に少なくとも一人の担当宛先へ教示したことを扱い、まだ全担当宛先への履行や規定適合を保証しない。r374では既存r356による全担当宛先への提示と同じ基準列への適合も要求する。受け手全員の理解・賛同は要求しない。',
    '閉じた発話記述はそのまま伝達と代表提示と基準評価へ渡す。引用時には発話の真理や本人の確信を実行せず、これらを条件とする基準が明示された場合だけ基準側で評価する。',
    '局所検査はr35t/r357/r356を含む既存の教示構成を通常評価し、新定義を型付き境界へ置換しない。教会の業務や代表という基本関係の一般理論、原文と唯一の意味同値性を有限モデルで証明しない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def definitions():
    text='d r37z[person a role a principal a subject a point d] c['+both(
        'k aa[v person]','u[e[v person][v principal]]','k cf[v person v role v point]',
        'k h246k[v person v principal v role v point]',
        'k h247n[v person v role v principal v subject v point]')+'].\n'
    text+='d r372['+TASK_FIELDS+'] e[b point['+both('t[k r357['+TASK_ARGS+']][v point]',
        'k r37z[v person v role v church v subject v point]',
        'k cb[v person v activity v role v point]')+']].\n'
    text+='d r373['+TASK_FIELDS+'] e[b point['+both('t[k r372['+TASK_ARGS+']][v point]',
        'k h247o[v activity v church v subject v message v point]')+']].\n'
    text+='d r374['+TASK_FIELDS+'] e[b point['+both('t[k r373['+TASK_ARGS+']][v point]',
        't[k r356['+TASK_ARGS+']][v point]')+']].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['aa','cf','cb','h246k','r357','r356']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    prims.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    basis=dict(status='delegated_business_representative_exposition_and_conformity',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
