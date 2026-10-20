"""Integrate the same citizen's public opinion and civic noncontravention."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both
from scripts.compose_civic_example import NAMES, quantify

PARENT = 'examples/v016/kant-civic-example.noema'
PARENT_BASIS = 'data/civic-example-basis-v1.json'
DEPENDENCIES = ('data/levy-opinions-basis-v1.json', 'data/civic-noncontravention-basis-v1.json')
FULL = 'examples/v016/kant-public-civic-opinion.noema'
CORE = 'examples/v016/public-civic-opinion-core.noema'
BASIS = 'data/public-civic-opinion-basis-v1.json'
ANNOTATIONS = 'data/public-civic-opinion-identifiers-v1.json'
DETAILS = ('activity', 'scholar', 'audience')
FIELDS = ('person', 'role', 'activity', 'community', 'scholar', 'audience', 'levy')
PUBLIC = ('person', 'activity', 'scholar', 'audience', 'levy')
FAMILY = 'i b[h[a a a a a d] e]'
PRIMITIVES = {
    'h245u': ('[] a', [], '固定原文kant-1784:u0012[2771,2983)、Eben derselbeからseine Gedanken äußert.までの、同じ市民の公的見解と市民義務への不違反を述べる一文全体。'),
    'h245v': ('[a a a i d[e] a i d[e] i[h[a] e] d] c',
        ['node', 'presenter', 'first_node', 'first_content', 'second_node', 'second_content', 'dimension', 'context'],
        '同じ提示者が同じ文脈・共通観点で、先行内容をその限定を保ったまま認めても、後続内容を退ける理由にはならないとして譲歩的に提示する。h227uの譲歩関係を段階3の閉じた内容へ広げる。内容と箇所の順、条件・様相を保持し、前者の撤回、二内容の論理的矛盾、引用内容の現実の真理は含意しない。'),
    'h245w': ('[a a i d[e] ' + FAMILY + ' ' + FAMILY + ' d] c',
        ['node', 'presenter', 'outer_content', 'first_alternative', 'added_alternative', 'context'],
        '提示者がこの外側内容の条件内で、同じ本人・活動・立場・宛先・対象・基準へ適用する第一の代替に、第二の代替も取り上げて加える。二つの内容の選言は別に構成し、第一の現実の成立を前提化せず、両方必須や第二が第一を論理的に含むという内容へ変えない。追加の順と作用域を保持する。'),
}
MEANINGS = {
    'r35g': '同じ本人が同じ活動で学識者として同じ公衆へ同じ賦課について自分の見解を表すr347なら、その同じ評価点で同じ本人・市民の立場・活動・共同体についてr35fの不違反が成立する条件内容。市民の立場を学識者の立場へ置き換えず、実際の表出や許可を独立主張しない。',
    'r35h': '同じ本人・市民の立場・共同体・賦課・固定基準について、全活動・学識者の立場・公衆の組へr35gを適用する。都合よく義務に適合する発言だけで範囲を選び直さない。',
    'r35i': '第五段落の同じ固定基準h232vで、先行文と同じ八個体からなる全賦課事例r33wにr35hを適用する。Eben derselbeとsolcher Ausschreibungenを、同じ本人・市民役割・共同体・賦課への束縛として保持し、先行の実際の拒否・批判・処罰は前提にしない。',
    'r35j': 'r347と同じ本人・活動・学識者の立場・公衆・賦課・基準で、公的使用と不適切さr342についての本人の主張表出を結ぶ第一の代替。原文の条件内の一方として指定し、独立に現実の事実として断言しない。',
    'r35k': 'r35jと同じ引数で、不正義r343についての本人の主張表出を結ぶ第二の代替。不適切さと同義にせず、第一の表出の成立を必要条件にしない。',
    'r35l': '文全体r35iを著者waと提示h232oへ帰属し、先行文h245f/r34xとの同じ公私使用の観点r2zgでの対照と譲歩を結ぶ。条件内の二つの代替r35j/kの追加順と本文順序を保持し、引用内容を実行しない。',
}
LIMITS = [
    'Eben derselbeは先行する同じ賦課事例r33wの市民本人を強めて指す読みとする。本人・市民役割・共同体・賦課を同一の変数に保ち、全事例について条件付きで述べる。実在の唯一の市民や先行批判を実行した者だけに限定しない。',
    'wennは学識者としての同じ公的表出r347を前件、市民の立場での同じ活動への不違反r35fを後件とする。本人の全生活での義務履行、納付済み、現行法上の積極的許可や処罰の物理的不能へ読み替えない。',
    '不適切さと不正義は固定した適合条件と権利・権原・公平条件の不足として区別する。本人がその内容を自分の見解として示すことと、賦課が実際に不適切・不正であることを分ける。採用した語義は保存済みAdelungの補助資料に基づき、唯一の歴史的解釈とはしない。',
    'oder auchは第一の批判に第二も代替として加える提示と読む。二種の表出の少なくとも一方を許し、両方必須、排他的選言、第一の現実の表出を前提にしない。auchから数値的な強度差や意外性の順位までは補わない。',
    'öffentlichとals Gelehrterは、本人の同じ理性使用・立場・活動が本来の全読者世界に向けられる構成とする。seine Gedankenはその本人自身の判断内容の表出であり、他人の批判の中立的紹介では足りない。全読者の実際の受領・理解、書面という追加条件は置かない。',
    '不違反の評価規範源h245dは先行文と共有する。現在の三要求形式h7a/h7k/h237zについて、同じ活動への完全適用範囲と全型適合記述・全束縛列・段階1の全内容基準を保持する。実際の発令者の全指図や既知の有限リストをそのまま全義務へ置き換えない。',
    '適用範囲h245s/tは明示した解釈が完全に供給する入力であり、結果を見て不都合な要求を除けない。関係する他義務の妨害を評価する場合もその対象を含める。さらに高い段階の新たな要求形式を扱う場合は対応する適合構成の拡張が必要で、任意の段階を型を越えて一度に量化したとはしない。',
    'demohngeachtetは先行文の納付拒否禁止・条件付き処罰可能性を認めても、この同じ本人の学識者活動の不違反を退けないという譲歩対照と読む。先行制約の撤回や、全ての批判行為が無条件で市民義務に反しないとの主張にはしない。',
    '意味判断は原刊と定義群の通読による明示した解釈下の判断である。個別定義の実評価、型付き境界での条件・量化接続検査、引用の非事実性を区別し、同義性の自動証明や現実の全義務の網羅性の証明とはしない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT, PARENT_BASIS)


@lru_cache(None)
def dependencies(): return tuple(load_catalog(ROOT, p) for p in DEPENDENCIES)


def definitions():
    fields = ' '.join(n + ' a' for n in FIELDS) + ' reference d'
    antecedent = 't[k r347[' + ' '.join('v ' + n for n in PUBLIC) + ' v reference]][v point]'
    result = 't[k r35f[v person v role v activity v community v reference]][v point]'
    text = 'd r35g[' + fields + '] e[b point[y[' + antecedent + '][' + result + ']]].\n'
    args = ' '.join('v ' + n for n in FIELDS) + ' v reference'
    text += 'd r35h[person a role a community a levy a reference d] e[b point[' + quantify(DETAILS,
        't[k r35g[' + args + ']][v point]') + ']].\n'
    case = 'k r33w[' + ' '.join('v ' + n for n in NAMES) + ' k h232v[]]'
    result = 't[k r35h[v person v role v community v levy k h232v[]]][v point]'
    text += 'd r35i[] e[b point[' + quantify(NAMES, 'y[' + case + '][' + result + ']') + ']].\n'
    for name, message, content in [('r35j', 'r344', 'r342'), ('r35k', 'r345', 'r343')]:
        text += 'd ' + name + '[' + ' '.join(n + ' a' for n in PUBLIC) + ' reference d] e[b point[' + both(
            'k r2zi[v person v activity v scholar v reference]', 'k cc[v activity v audience v reference]',
            'k ce[v audience v reference]',
            't[k r346[v person v activity v audience v levy v reference r[p ' + message + '] r[p ' + content + ']]][v point]') + ']].\n'
    node, author, ctx = 'k h245u[]', 'k wa[]', 'k h232o[]'
    quote = 'r d[k r35i[]]'
    pair = node + ' ' + author + ' k h245f[] r d[k r34x[]] ' + node + ' ' + quote + ' r[p r2zg] ' + ctx
    text += 'd r35l[] c[' + both(
        'k h236i[' + node + ' ' + author + ' ' + quote + ' ' + ctx + ']',
        'k h236k[' + pair + ']', 'k h245v[' + pair + ']',
        'k h245w[' + node + ' ' + author + ' ' + quote + ' r b[p r35j] r b[p r35k] ' + ctx + ']',
        'k ue[k h245f[] ' + node + ' ' + ctx + ']', 'u[e[k h245f[]][' + node + ']]') + '].\n'
    return text


def build():
    old=parent();doc=deepcopy(old.document);statements,doc['statements']=doc['statements'],[];imported={}
    for lib in dependencies():
        for d in lib.document['declarations']:
            n=d['name'];previous=old.entries.get(n,imported.get(n))
            if previous:assert d==previous['declaration'] and lib.entries[n]['meaning_ja']==previous['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=lib.entries[n]
    assert not (set(PRIMITIVES)|set(MEANINGS)) & (set(old.entries)|set(imported))
    doc=parse(format_graph(doc,'compact')+''.join('r '+n+row[0]+'.' for n,row in PRIMITIVES.items())+definitions())
    added=doc['declarations'][len(old.document['declarations']):]
    new=dict(kind='assert',body=dict(kind='call',symbol='r35l',arguments=[]));doc['statements']=statements+[new]
    core=deepcopy(doc);core.update(declarations=closure(doc,list(MEANINGS)),statements=[new]);ds={d['name']:d for d in added}
    meanings={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS
    primitives={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja'])
        for n,e in imported.items() if e['kind']=='primitive'}
    primitives.update({n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=row[1],meaning_ja=row[2]) for n,row in PRIMITIVES.items()})
    sources=set().union(*(set(lib.source_sha256) for lib in dependencies()))
    basis=dict(status='public_levy_opinion_without_civic_duty_contravention',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        definitions=meanings,primitives=primitives,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(sources)},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/civic-example-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(annotations)}
