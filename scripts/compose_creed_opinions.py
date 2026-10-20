"""Bind qualified thoughts about a creed's shortcomings to public expression."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both

PARENTS = ('data/clerical-obligation-basis-v1.json','data/reviewed-thoughts-basis-v1.json')
LIBRARY = 'examples/v016/creed-opinions.noema'
BASIS = 'data/creed-opinions-basis-v1.json'
NAMES = ('person','activity','scholar','audience','thought','creed','judgment','beneficiary')
FIELDS = ' '.join(n+' a' for n in NAMES)+' reference d'
ARGS = ' '.join('v '+n for n in NAMES)+' v reference'
PRIMITIVES = {}
MEANINGS = {
    'r36u':'同じ見解を表す所見が、同じ信条について備えるべき条件の不充足r326を論点として扱う。h243xを明示した評価条件へ結び、見解全体を欠点があるという一命題に狭めない。欠点の実在・信条の真理・所見への賛同は要求しない。',
    'r36v':'同じ本人・見解・判断・受益者・基準点の慎重な吟味と善意r36sに、同じ信条の欠点への論点r36uを結ぶ。別人の吟味や別見解の善意、別の信条の欠点を借りない。',
    'r36w':'同じ本人による同じ提示活動の生起に、固定した非空の宛先範囲の全員への同じ見解内容の提示を結ぶ。r36mの本人の肯定判断とh245rによるその判断の表出を同じ評価点で要求し、h224y/h224zからrsbで構成した同じ発話をf2へ渡す。受領・理解・賛同や内容の真理は要求しない。',
    'r36x':'基準点の同じ資格r36vを、同じ本人・活動・学識者の立場r2ziと、その同じ活動が本来の全読者世界cc/ceへ向けられることに結ぶ。公的な活動の候補であり、提示の実行を基準点に要求しない。',
    'r36y':'同じ候補r36xと、その同じ本人・活動・公衆・見解・判断によるr36wの実際の伝達を結ぶ内容。資格・宛先の基準点を固定し、伝達の評価点を別に扱う。自由や使命の対象として引用でき、引用しただけで実行を要求しない。',
}
LIMITS = [
    'u0012[3186,3452)の同じ信条の欠点についての資格ある見解と、その公的な伝達の依存群。改善提案・全範囲の自由・追加される使命・文間対照と著者帰属は未統合で、意味確認文字数は加算しない。',
    '見解が扱う欠点は、固定した評価条件を備えないというr326の内容を論点とする読み。原文が具体的な欠点や判断条件を列挙したとはしない。欠点が客観的に存在するという著者の別主張へ変えない。',
    'h243xの所見は見解の言語的な内容を対象とする。r36mの肯定判断は見解全体への本人の立場であり、欠点があるという単純命題への無条件の賛同と同一化しない。',
    '発話は同じ見解の肯定的な伝達として構成する。相手の賛同、全員の受領、書面の現存を加えない。r2ziの公的理性使用の分類は既存の意味を保持する。',
    'r36xは活動を分類する資格、r36yは実行内容。自由や使命はこの群から推論せず別に構成する。職務内の教示や信条の真理を公的批判の条件にしない。',
]


@lru_cache(None)
def parents(): return tuple(load_catalog(ROOT,p) for p in PARENTS)


def definitions():
    text='d r36u[thought a creed a reference d] c[g criterion a[k h243x[v thought v creed v criterion r[p r326] v reference]]].\n'
    text+='d r36v[person a thought a judgment a beneficiary a creed a reference d] c['+both(
        'k r36s[v person v thought v judgment v beneficiary v reference]', 'k r36u[v thought v creed v reference]')+'].\n'
    message='k rsb[k h224y[v thought] r[e[n p a b][n p a b]]]'
    text+='d r36w[person a activity a audience a thought a judgment a reference d] e[b point['+both(
        'k dg[v activity v point]', 'k f3[v person v activity v point]',
        'g recipient a[k h6t[v audience v recipient v reference]]',
        'f recipient a[y[k h6t[v audience v recipient v reference]][k f2[v activity v recipient k h224z[v thought] '+message+' v point]]]',
        'k r36m[v person v thought v judgment v point]', 'k h245r[v activity v judgment v point]')+']].\n'
    text+='d r36x['+FIELDS+'] c['+both(
        'k r36v[v person v thought v judgment v beneficiary v creed v reference]',
        'k r2zi[v person v activity v scholar v reference]',
        'k cc[v activity v audience v reference]', 'k ce[v audience v reference]')+'].\n'
    text+='d r36y['+FIELDS+'] e[b point['+both('k r36x['+ARGS+']',
        't[k r36w[v person v activity v audience v thought v judgment v reference]][v point]')+']].\n'
    return text


def build():
    old,review=parents(); doc=deepcopy(old.document)
    doc.update(declarations=closure(doc,['r326','h243x','dg','f3','f2','h6t','h245r','r2zi','cc','ce']),statements=[])
    imported={d['name']:old.entries[d['name']] for d in doc['declarations']}
    for d in closure(review.document,['r36s','rsb']):
        n=d['name']; entry=review.entries[n]
        if n in imported: assert d==imported[n]['declaration'] and entry['meaning_ja']==imported[n]['meaning_ja']
        else: doc['declarations'].append(d); imported[n]=entry
    assert not set(MEANINGS)&set().union(*(set(p.entries) for p in parents()))
    doc=parse(format_graph(doc,'compact')+definitions())
    basis=dict(status='qualified_thoughts_about_creed_shortcomings_and_public_expression',document=LIBRARY,
        primitives={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
            for n,e in imported.items() if e['kind']=='primitive'},
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(set().union(*(set(c.source_sha256) for c in parents())))},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n', BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
