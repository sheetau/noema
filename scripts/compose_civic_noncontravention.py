"""Preserve all descriptions in action-scoped civic duty conformity."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_qualitative_influence import both, TRUE, FALSE

PARENT = 'data/civic-example-basis-v1.json'
LIBRARY = 'examples/v016/civic-noncontravention.noema'
BASIS = 'data/civic-noncontravention-basis-v1.json'
ZERO = 'i[h[j[a]] e]'
ONE = 'i b[h[j[a] d] e]'
PRIMITIVES = {
    'h245s': ('[a a a ' + ZERO + ' j[a] d] c',
        ['person', 'role', 'activity', 'target', 'bindings', 'reference'],
        '指定の本人・立場で同じ活動を評価するとき、同じ段階0の内容関数と順序付き個体列で特定する規範対象が、その活動についての義務適合の判断に関係する。採用した解釈の固定基準に従う適用範囲であり、現在の要求・許可・実行・適合の成否とは別に、関係する対象を全て含める。関係する不都合な要求を除外せず、本人の別の活動についてだけの要求は含めない。単に引数列に活動名が現れることとも区別する。'),
    'h245t': ('[a a a ' + ONE + ' j[a] d d] c',
        ['person', 'role', 'activity', 'target', 'bindings', 'target_reference', 'reference'],
        'h245sと同じ、活動についての義務適合を評価する完全な適用範囲を、段階1の内容関数・順序付き個体列・内容の基準引数で特定する。最後の基準は範囲を固定し、内容へ渡す基準とは分ける。対象内容の真理や適合の成否で範囲を選び直さず、別活動にだけ課された義務を本人の生活全体の履行として要求しない。'),
}
MEANINGS = {
    'r35a': '同じ出所・本人・立場・段階0の対象記述・順序付き束縛・評価点について、h7kの正極性要求ならその内容の真、負極性要求なら偽を求める。要求がなければこの対象については不違反だが、積極的許可を意味しない。相反要求は両方を満たせず、未知の内容を都合よく補わない。',
    'r35b': 'r35aと同じ極性別の適合をh237zの段階1の対象へ広げる。要求に使う記述・束縛・内容基準と、実行評価するものを同一に保つ。範囲を固定する基準や要求の評価点を内容基準へ取り違えない。',
    'r35c': '同じ本人・立場・活動の固定した適用範囲h245sについて、全段階0記述と全有限個体列を量化し、r35aの適合を求める。既知の記述列や試験で使う束縛列だけで全域を代用しない。',
    'r35d': '同じ本人・立場・活動の固定した適用範囲h245tについて、全段階1記述・全有限個体列・全内容基準を量化し、r35bの適合を求める。同じ場面で無関係な他の活動の履行を要求せず、関係する対象の漏れも許さない。',
    'r35e': '同じ活動へ直接課されたh7aの要求について、既存rfgの全記述域・全出所量化を保持し、指定の規範出所からの要求に範囲を固定する。別の実際の命令者の要求を採用した市民義務の規範と自動で同一視しない。',
    'r35f': '同じ共同体・本人・市民の立場r33sと、著者が採る市民規範の出所h245dを保持し、同じ評価点で直接行為型r35e、束縛付き段階0型r35c、束縛付き段階1型r35dの不違反を合わせる。同じ発言についての市民義務の不違反候補であり、発言の実行、支払済み、積極的許可、全生活の無過失は含意しない。',
}
LIMITS = [
    'u0012[2771,2983)の市民の義務への不違反を構成する依存群。本人の公的見解r347との条件接続、demohngeachtet、oder auch、全文帰属は未統合。本文・意味確認文字数は更新しない。',
    '不違反は、その発言について市民の立場で評価すべき全要求への適合と読む。h245s/tは完全な適用範囲の明示入力であり、試験データから現実の網羅性を認定しない。発言に伴う別義務の妨害が関係する解釈なら、それを評価する対象も範囲から除外してはならない。',
    '現在の本文が用いるh7a、h7k、h237zの三つの要求形式を全て扱う。各型の記述域・束縛列域・内容基準域を量化するが、任意の引用段階を型を越えて一度に量化する演算ではない。将来さらに高い段階の要求形式を導入する場合、その要求への適合も追加する必要がある。',
    'h245dは先行文と同じ規範上の出所であり、実在の全発令者の全要求を自動で正当化しない。対立する正負の要求は両立できないものとして検査し、優先順位や免除を暗黙に追加しない。',
    '既存rfe/rfgの意味は保持する。旧版では引用できなかった脱引用を、v016の段階2の引用へ収める。引用可能であることと、全記述域で不違反が成立することは別である。有限評価器は全記述域・全束縛列域の列挙を拒否する。',
]


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT)


def definitions():
    text = ''
    for name, sort, relation in [('r35a', ZERO, 'h7k'), ('r35b', ONE, 'h237z')]:
        fields = 'source a person a role a target ' + sort + ' bindings j[a] '
        args = 'v source v person v role v target v bindings '
        application = 'c[s[v target]][v bindings'
        if name == 'r35b':
            fields += 'targetreference d '; args += 'v targetreference '; application += ' v targetreference'
        fields += 'point d'; application += ']'
        actual = 't[' + application + '][v point]'
        text += 'd ' + name + '[' + fields + '] c[' + both(
            'y[k ' + relation + '[' + args + TRUE + ' v point]][' + actual + ']',
            'y[k ' + relation + '[' + args + FALSE + ' v point]][u[' + actual + ']]') + '].\n'
    fields = 'source a person a role a activity a reference d'
    text += 'd r35c[' + fields + '] e[b point[f target ' + ZERO + '[f bindings j[a][y[' + (
        'k h245s[v person v role v activity v target v bindings v reference]') + '][' + (
        'k r35a[v source v person v role v target v bindings v point]') + ']]]]].\n'
    text += 'd r35d[' + fields + '] e[b point[f target ' + ONE + '[f bindings j[a][f targetreference d[y[' + (
        'k h245t[v person v role v activity v target v bindings v targetreference v reference]') + '][' + (
        'k r35b[v source v person v role v target v bindings v targetreference v point]') + ']]]]]].\n'
    text += 'd r35e[source a person a role a activity a point d] c[k rfg[v person v role v activity v point '
    text += 'i[origin a recipient a office a act a target i[h[a a] e] sign c at d][' + both(
        'e[v origin][v source]', 'k h7a[v origin v recipient v office v act v target v sign v at]') + ']]].\n'
    source = 'k h245d[v community v reference]'
    text += 'd r35f[person a role a activity a community a reference d] e[b point[' + both(
        'k r33s[v person v role v community v reference]',
        'k r35e[' + source + ' v person v role v activity v point]',
        't[k r35c[' + source + ' v person v role v activity v reference]][v point]',
        't[k r35d[' + source + ' v person v role v activity v reference]][v point]') + ']].\n'
    return text


def build():
    old = parent(); doc = deepcopy(old.document)
    doc.update(declarations=closure(doc, ['rfg', 'h7a', 'h7k', 'h237z', 'r33s', 'h245d']), statements=[])
    imported = {d['name']: old.entries[d['name']] for d in doc['declarations']}
    assert not (set(PRIMITIVES) | set(MEANINGS)) & set(old.entries)
    doc = parse(format_graph(doc, 'compact') + ''.join('r ' + n + row[0] + '.' for n, row in PRIMITIVES.items()) + definitions())
    ds = {d['name']: d for d in doc['declarations']}
    primitives = {n: dict(parameters=e['declaration']['parameters'], result=e['declaration']['result'],
        arguments=e['arguments'], meaning_ja=e['meaning_ja']) for n, e in imported.items() if e['kind'] == 'primitive'}
    primitives.update({n: dict(parameters=ds[n]['parameters'], result=ds[n]['result'], arguments=row[1], meaning_ja=row[2])
        for n, row in PRIMITIVES.items()})
    basis = dict(status='ranked_action_scoped_civic_noncontravention_candidate', document=LIBRARY, primitives=primitives,
        definitions={n: e['meaning_ja'] for n, e in imported.items() if e['kind'] == 'definition'} | MEANINGS,
        imported_symbols={n: e['meaning_basis'] for n, e in imported.items()},
        import_source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(old.source_sha256)}, limitations=LIMITS)
    return {LIBRARY: format_graph(doc, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
