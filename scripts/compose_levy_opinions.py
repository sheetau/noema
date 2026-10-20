"""Compose a scholar's own public criticism of the same levy."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both, TRUE

PARENT = 'data/civic-example-basis-v1.json'
LIBRARY = 'examples/v016/levy-opinions.noema'
BASIS = 'data/levy-opinions-basis-v1.json'
PRIMITIVES = {
    'h245n': ('[a d] j[h[a] e]', ['subject', 'reference'],
        '同じ対象と固定基準で採用する、対象とその事情への適合条件の有限列。対象・目的・時機・事情に即した適切さを評価する条件関数を明示する。単なる効率や社交上の作法だけに限定せず、条件の成否を見て事後選択しない。各関数へ同じ対象を渡し、評価点で充足を調べる。'),
    'h245o': ('[a d] j[h[a] e]', ['subject', 'reference'],
        '同じ対象と固定基準で採用する、権利・権原・公平に関する条件の有限列。誰のどの権利や公平の条件かをNoemaの条件関数として明示する。現行法令への適合だけや本人の好悪へ狭めず、条件の成否を見て事後選択しない。各関数へ同じ対象を渡し、評価点で充足を調べる。'),
    'h245p': ('[a a a i[h[a d] f] d d] c',
        ['activity', 'recipient', 'subject', 'message_family', 'reference', 'point'],
        '同じ提示活動で、この受け手へ、同じ対象と固定基準を閉じた発話関数へ渡した発話を示す。h244oの対象束縛を一対象と基準にした関係。提示者・活動の生起・発話の力は別に構成し、内容の真理、受け手の受領・理解・賛同は含意しない。'),
    'h245q': ('[a a i[h[a d] e] d c d] c',
        ['judgment', 'subject', 'content_family', 'reference', 'polarity', 'point'],
        'この判断が同じ対象・固定基準を閉じた内容関数へ渡した内容について、指定極性の見解を持つことを、同じ評価点で表す。肯定ならその内容を是とする判断であり、単にその命題を考慮しただけではない。判断する本人はfaで別に結ぶ。判断内容の客観的真理は含意しない。'),
    'h245r': ('[a a d] c', ['activity', 'judgment', 'point'],
        '同じ活動が同じ評価点で、この判断を表出する。判断しただけ、他人の判断の引用、実際の提示とは別の内的活動で代用しない。判断者・提示者・提示内容は別に同じ引数で結ぶ。'),
}
MEANINGS = {
    'r342': '同じ賦課と固定基準の適合条件h245nを既存retへ渡し、評価点で少なくとも一条件が不充足という内容を構成する。不適切さの採用した読みであり、空列や未評価から不適切さを補わない。',
    'r343': '同じ賦課と固定基準の権利・権原・公平の条件h245oをretへ渡し、評価点で少なくとも一条件が不充足という内容を構成する。不正義の採用した読みであり、r342と同義にせず、空列や未評価から不正義を補わない。',
    'r344': '同じ賦課・固定基準の不適切さr342を主張する発話。発話の力と内容の真理は別である。',
    'r345': '同じ賦課・固定基準の不正義r343を主張する発話。発話の力と内容の真理は別である。',
    'r346': '同じ本人による同じ生起する提示活動が、同じ固定した非空の宛先範囲の全員へ、同じ賦課・基準の発話を示す。その本人自身が同じ評価点で持つ肯定極性の判断内容を同じ活動が表し、同じ賦課への否定的な評価の立場を示す。判断・発話の関数はr347で対応させる。内容の真理や受け手の理解は要求しない。',
    'r347': '同じ本人・活動・学識者としての立場による公的理性使用r2ziと、その同じ活動の宛先が本来の全読者世界であるcc/ceを結ぶ。その活動で、不適切さr342を自分の見解として主張するか、不正義r343を自分の見解として主張するかの少なくとも一方を要求する。二種の発言を区別した選言であり、選言命題一つの表出や両方必須へ変えない。',
}
LIMITS = [
    'u0012[2771,2983)の公に自分の見解を表す前件に向けた依存群。市民の義務への不違反、先行文との譲歩対照、oder auchの追加焦点、全文帰属は未統合。新規意味確認文字数は加算しない。',
    '不適切さと不正義は保存したAdelungの語義に基づき別々の条件不足として読む。具体的な評価条件は明示した解釈の入力であり、原文が条件列を列挙したという主張や、Kantの正義論全体の定義ではない。',
    '条件関数は固定基準で選び、対象と評価点を保持する。発言に帰属する内容を構成できることと、その内容を事実として評価できることは別である。発言の検査では引用内容を実行せず、不正義が実在するとの著者主張を補わない。',
    'Gedankenはここで示す評価上の見解として読む。発言の全文や心理内容を一命題へ尽くす主張ではない。自分の見解の表出と他人の見解の中立的な紹介を区別する。',
    '全読者世界に向けた公的使用を要求するが、全員の実際の受領・理解は要求しない。この文単独から書面という追加要件や、先行の納付拒否・出過ぎた批判の実行を加えない。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT)


def definitions():
    text = 'd r342[levy a reference d] e[k ret[v levy k h245n[v levy v reference]]].\n'
    text += 'd r343[levy a reference d] e[k ret[v levy k h245o[v levy v reference]]].\n'
    text += 'd r344[levy a reference d] f[j s[k r342[v levy v reference]]].\n'
    text += 'd r345[levy a reference d] f[j s[k r343[v levy v reference]]].\n'
    text += 'd r346[person a activity a audience a levy a reference d message i[h[a d] f] content i[h[a d] e]] e[b point[' + both(
        'k dg[v activity v point]', 'k f3[v person v activity v point]',
        'g recipient a[k h6t[v audience v recipient v reference]]',
        'f recipient a[y[k h6t[v audience v recipient v reference]][k h245p[v activity v recipient v levy v message v reference v point]]]',
        'g judgment a[' + both('k fa[v person v judgment v point]',
            'k h245q[v judgment v levy v content v reference ' + TRUE + ' v point]',
            'k h245r[v activity v judgment v point]') + ']',
        'k h244n[v person v activity v levy v point]') + ']].\n'
    text += 'd r347[person a activity a scholar a audience a levy a reference d] e[b point[' + both(
        'k r2zi[v person v activity v scholar v reference]',
        'k cc[v activity v audience v reference]', 'k ce[v audience v reference]',
        'x[t[k r346[v person v activity v audience v levy v reference r[p r344] r[p r342]]][v point]]'
        '[t[k r346[v person v activity v audience v levy v reference r[p r345] r[p r343]]][v point]]') + ']].\n'
    return text


def build():
    old = parent(); doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['ret', 'dg', 'f3', 'h6t', 'fa', 'h244n', 'r2zi', 'cc', 'ce']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    ds = {d['name']: d for d in doc['declarations']}
    primitives = {n: dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'],
        arguments=e['arguments'], meaning_ja=e['meaning_ja']) for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2])
        for n, row in PRIMITIVES.items()})
    basis = dict(status='own_public_levy_opinions_candidate', document=LIBRARY, primitives=primitives,
        definitions={n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS,
        imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
        import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(old.source_sha256)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
