"""Distinguish topical independent judgment from the possibility of enabling it."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args

PARENT = 'examples/v014/kant-personal-criteria.noema'
JUDGMENT = [('owned', 'h[a a d] c'), ('use', 'h[a a a d] c'), ('judgments', 'h[a a d] c'),
    ('matters', 'h[a a d] c'), ('reasons', 'h[a a d] c'), ('support', 'h[a a d] c'), ('guidance', 'h[a a a d] c')]
METHODS = [('relevant', 'h[a a] c'), ('available', 'h[a a a d] c'),
    ('outcomes', 'h[a a a d d] c'), ('selected', 'h[a a a d d] c')]
CHECKED = [('person', 'a'), ('context', 'd')] + METHODS
CAPABLE = CHECKED + [('goals', 'h[a a] e')]
ENABLING = [('enabler', 'a'), ('person', 'a'), ('context', 'd'),
    ('enabling', 'h[a a a d] c'), ('effects', 'h[a a a d d] c')]
POSSIBLE = ENABLING + METHODS + [('goals', 'h[a a] e')]
COLLECTIVE = [('population', 'j[a]'), ('scope', 'h[a] c'), ('context', 'd'),
    ('assessed', 'h[a] e'), ('capable', 'h[a] e'), ('enableassessed', 'h[a] e'), ('enableable', 'h[a] e'),
    ('currentupper', 'b'), ('enableupper', 'b')]
SOURCE = [('topic', 'a'), ('anchor', 'd'), ('topics', 'h[a a a d] c')] + METHODS[1:]
ENABLE_SOURCE = SOURCE + [(n, t) for n, t in ENABLING if n not in ('person', 'context')]
GROUP_SOURCE = [(n, t) for n, t in COLLECTIVE if n not in ('assessed', 'capable', 'enableassessed', 'enableable')] + ENABLE_SOURCE
ROOTS = ['rlk', 'rll', 'rlm', 'rln', 'rlo', 'rlp']


def method(name):
    tail = [('actor', 'a'), ('plan', 'a'), ('start', 'd')] + ([] if name == 'available' else [('end', 'd')])
    return 'i[' + params(tail) + '][' + app(v(name), v('actor'), v('matter'), v('plan'), v('start'),
        *([] if name == 'available' else [v('end')])) + ']'


def enabling(name):
    tail = [('actor', 'a'), ('plan', 'a'), ('start', 'd')] + ([] if name == 'enabling' else [('end', 'd')])
    return 'i[' + params(tail) + '][' + app(v(name), v('actor'), v('person'), v('plan'), v('start'),
        *([] if name == 'enabling' else [v('end')])) + ']'


def definitions():
    witness = both(k('rcr', v('person'), v('judgment'), v('point'), *args(JUDGMENT)),
        app(v('matters'), v('judgment'), v('matter'), v('point')))
    text = definition('rlk', params([('person', 'a'), ('matter', 'a')] + JUDGMENT),
        'b point[' + quant('g', 'judgment', 'a', witness) + ']', 'e')
    relevant = app(v('relevant'), v('person'), v('matter'))
    checked = k('xe', v('person'), v('context'), *(method(n) for n in ('available', 'outcomes', 'selected')))
    text += definition('rll', params(CHECKED), both(quant('g', 'matter', 'a', relevant),
        quant('f', 'matter', 'a', op('y', relevant, checked))))
    capable = k('xd', v('person'), app(v('goals'), v('person'), v('matter')), v('context'),
        *(method(n) for n in ('available', 'outcomes', 'selected')))
    text += definition('rlm', params(CAPABLE), both(k('rll', *args(CHECKED)),
        quant('f', 'matter', 'a', op('y', relevant, capable))))
    text += definition('rln', params(ENABLING), k('xe', v('enabler'), v('context'), enabling('enabling'), enabling('effects'), enabling('effects')))
    future = 'b future[' + k('rlm', *args(CAPABLE, context=v('future'))) + ']'
    text += definition('rlo', params(POSSIBLE), both(k('rln', *args(ENABLING)),
        k('xb', v('enabler'), future, v('context'), enabling('enabling'), enabling('effects'))))
    counts = [op('u', k('hc', 'd[v population]', v(bound))) for bound in ('currentupper', 'enableupper')]
    for field, upper in (('capable', 'currentupper'), ('enableable', 'enableupper')):
        predicate = 'i[person a][' + op('t', app(v(field), v('person')), v('context')) + ']'
        counts.append(k('rcn', v('population'), v('scope'), predicate, v(upper)))
    assessed = quant('f', 'person', 'a', op('y', app(v('scope'), v('person')), both(
        op('t', app(v('assessed'), v('person')), v('context')),
        op('t', app(v('enableassessed'), v('person')), v('context')))))
    text += definition('rlp', params(COLLECTIVE), both(assessed, *counts))
    return text


MEANINGS = {
    'rlk': '本人がその事柄について、自分の理解力を使い、同じ判断で用いた理由に支えられ、他者の指導なしで判断するという内容。rcrの判断対象を、同じ指定事柄へ固定する。',
    'rll': '本人の固定された事柄の範囲が非空で、各事柄について利用可能な全方法の評価対象が非空かつ想定結果の部分集合である。方法がない場合と、ある方法の評価が欠ける場合を分ける。',
    'rlm': 'rllを満たし、固定範囲の全事柄について、同じ本人と事柄の目標を指定評価結果の全てで達成する方法xdがある。事柄ごとに方法を変えてよいが、別の本人・事柄の結果で代用しない。',
    'rln': '同じ実施者・対象者・開始時点について、利用可能な全支援方法に非空の想定結果がある。対象者本人に支援方法が利用可能であることとは区別する。',
    'rlo': 'rlnを満たし、同じ実施者が対象者をrlmの能力状態にする方法と成功する想定結果が少なくとも一つある。目標・対象者・事柄の範囲を結果時点で選び直さない。現在の能力や支援の実施済み、成功保証は要求しない。',
    'rlp': '同じ非空の対象範囲を重複なく完全に列挙し、全対象の現在能力と支援可能性の評価が整合する。その両方の該当人数が、それぞれ指定した正の上限より少ない。上限は母集団の人数以下に制限し、全員が該当する場合を不足としない。',
    'hzeq': '人aaについて、同じ主題・本人・基準時点で固定した事柄の範囲にrllの評価条件を要求する性質。',
    'hzer': 'hzeqと同じ事柄と方法にrlmを適用し、目標を既存の理解力の所有・使用、理由に支えられた指導なしの判断へ接続する。',
    'hzes': '人aaに対する同じ実施者の支援についてrlnの評価条件を要求する性質。',
    'hzet': 'hzerと同じ事柄・目標の能力に、その人を置く可能性rloを述べる性質。基準時点での事柄の範囲を支援の結果でも保持する。',
    'hzeu': '同じ人々・主題・基準時点・実施者について、現在の自立的判断能力と、その能力に置く可能性の不足をrlpで比較する。評価不足を該当人数0として数えない。',
}
LIMITS = [
    '事柄の範囲は主題・本人・基準時点で固定する。宗教という主題の具体的な内容や、その範囲の完全性を名前や型だけで定義し終えたとはしない。',
    'rlkとxdの組合せは、根拠のある自立的判断を選んだ結果範囲で達成する能力の候補である。sicher und gutの習熟、確信、あらゆる外乱への頑健性を網羅する意味確認は残る。',
    '支援する実施者と対象者は別の引数である。実施者が本人と同じ場合も許すが、本人ができる方法を別の実施者の方法として流用しない。何もしない方法や現在の能力から将来の能力への保持は自動追加しない。',
    'rloは成功結果が一つあるという可能性であり、全結果での成功保証ではない。各支援結果の中では、同じ対象者が範囲内の全事柄について能力を持つ必要があり、別々の結果に部分能力を分散させても成立しない。',
    '人数上限は、その母集団について不足の程度を読むために指定する文脈的な基準であり、原文が与えた数値ではない。人数尺度と上限で「まだ非常に不足」の全語義を確定せず、能力の程度や分布の全てを一つの人数へ還元しない。',
    '仮定した有限範囲の完全な列挙と評価を検査する。現実の全人類・全ての宗教的事柄・全ての可能な方法を有限例で確認したとはしない。未知の所属、評価、使用、支持は偽で補わず拒否する。',
    'u0014の能力と、それが可能になる状態に置くことの不足に関する一文への部分候補である。時代を問う冒頭の問答、進行中の啓蒙、障害の漸減と徴候、フリードリヒの世紀、著者帰属と全文の意味確認は未接続。原始記号と著者主張は追加しない。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    relevant = 'i[person a matter a][' + app(v('topics'), v('person'), v('topic'), v('matter'), v('anchor')) + ']'
    goal = 'i[person a matter a][' + k('rlk', v('person'), v('matter'), *['p ' + n for n in ('ab', 'ac', 'fa', 'fb', 'fc', 'fd', 'ad')]) + ']'
    for name, target, fields, arguments in (
        ('hzeq', 'rll', SOURCE, CHECKED), ('hzer', 'rlm', SOURCE, CAPABLE),
        ('hzes', 'rln', ENABLE_SOURCE, ENABLING), ('hzet', 'rlo', ENABLE_SOURCE, POSSIBLE)):
        body = k(target, *args(arguments, relevant=relevant, goals=goal))
        text += definition(name, params(fields), 'i[person a][b context[' + both(k('aa', v('person')), body) + ']]', 'h[a] e')
    data = {name: k(symbol, *args(fields)) for name, symbol, fields in (
        ('assessed', 'hzeq', SOURCE), ('capable', 'hzer', SOURCE), ('enableassessed', 'hzes', ENABLE_SOURCE), ('enableable', 'hzet', ENABLE_SOURCE))}
    humans = quant('f', 'person', 'a', op('y', app(v('scope'), v('person')), k('aa', v('person'))))
    text += definition('hzeu', params(GROUP_SOURCE), both(humans, k('rlp', *args(COLLECTIVE, **data))))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-personal-criteria-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-topical-enablement-basis-v1', document='examples/v014/kant-topical-enablement.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'topical-enablement')
def core_composed(): return projected(ROOTS + ['hzeq', 'hzer', 'hzes', 'hzet', 'hzeu'], 'topical-enablement-core')
BUILDERS = ((generic_composed, 'topical-enablement'), (source_composed, 'kant-topical-enablement'), (core_composed, 'topical-enablement-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored topical enablement differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
