"""Describe assessed multi-step declines on a fixed catalogue and time interval."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params, args

PARENT = 'examples/v014/kant-free-pursuit.noema'
STATE = 'h[a] c'
EQUATIONS = 'h[a ' + STATE + '] c'
TIME = [('history', 'h[d] c'), ('before', 'h[d d] c'), ('start', 'd'), ('end', 'd')]
CHECKED = TIME + [('obstacles', 'j[a]'), ('scope', 'h[a] c'), ('assessed', 'h[a d] c')]
DECLINE = CHECKED + [('hindering', 'h[a d] c')]
GRADUAL = DECLINE + [('bound', 'b')]
CAUSAL = [('variables', 'h[a] j[a]'), ('equations', 'h[a d] ' + EQUATIONS), ('factors', 'h[a] a'),
    ('worlds', 'h[a d ' + STATE + '] d'), ('population', 'j[a]'), ('people', 'h[a] c'),
    ('property', 'h[a] e'), ('evaluated', 'h[a] e')]
SOURCE_CAUSAL = CAUSAL[:-2]
SOURCE = [(n, t) for n, t in GRADUAL if n not in ('assessed', 'hindering')] + SOURCE_CAUSAL
ROOTS = ['rly', 'rlz', 'rl2', 'rl3', 'rl4', 'rl5', 'rl6', 'rl7', 'rma']
TRUE = 'e[n p a b][n p a b]'


def interval(point): return app(k('rlz', *args(TIME)), v(point))
def count(point): return k('rly', v('obstacles'), v('hindering'), v(point))


def definitions():
    text = definition('rly', 'obstacles j[a] hindering h[a d] c point d',
        k('hf', v('obstacles'), 'i[obstacle a][' + app(v('hindering'), v('obstacle'), v('point')) + ']'), 'b')
    inside = both(app(v('history'), v('point')),
        op('x', op('e', v('start'), v('point')), app(v('before'), v('start'), v('point'))),
        op('x', op('e', v('point'), v('end')), app(v('before'), v('point'), v('end'))))
    text += definition('rlz', params(TIME), 'i[point d][' + inside + ']', 'h[d] c')
    checked = quant('f', 'point', 'd', op('y', interval('point'), quant('f', 'obstacle', 'a', op('y',
        app(v('scope'), v('obstacle')), app(v('assessed'), v('obstacle'), v('point'))))))
    text += definition('rl2', params(CHECKED), both(k('ta', v('history'), v('before')),
        app(v('history'), v('start')), app(v('history'), v('end')), app(v('before'), v('start'), v('end')),
        k('rcm', v('obstacles'), v('scope')), checked))
    ordered = both(interval('first'), interval('last'), app(v('before'), v('first'), v('last')))
    nonincrease = quant('f', 'first', 'd', quant('f', 'last', 'd', op('y', ordered,
        op('u', k('hc', count('first'), count('last'))))))
    text += definition('rl3', params(DECLINE), both(k('rl2', *args(CHECKED)), nonincrease, k('hc', count('end'), count('start'))))
    between = quant('g', 'middle', 'd', both(app(v('history'), v('middle')),
        app(v('before'), v('first'), v('middle')), app(v('before'), v('middle'), v('last'))))
    text += definition('rl5', 'history h[d] c before h[d d] c first d last d', both(
        app(v('history'), v('first')), app(v('history'), v('last')), app(v('before'), v('first'), v('last')), op('u', between)))
    adjacent = both(interval('first'), interval('last'), k('rl5', v('history'), v('before'), v('first'), v('last')))
    limited = quant('f', 'first', 'd', quant('f', 'last', 'd', op('y', adjacent,
        op('u', k('hc', k('ha', count('last'), v('bound')), count('first'))))))
    intermediate = quant('g', 'middle', 'd', both(interval('middle'),
        app(v('before'), v('first'), v('middle')), app(v('before'), v('middle'), v('last')),
        k('hc', count('middle'), count('first')), k('hc', count('last'), count('middle'))))
    resolved = quant('f', 'first', 'd', quant('f', 'last', 'd', op('y', both(ordered,
        k('hc', k('ha', count('last'), v('bound')), count('first'))), intermediate)))
    middle = quant('g', 'middle', 'd', both(interval('middle'), app(v('before'), v('start'), v('middle')),
        app(v('before'), v('middle'), v('end')), k('hc', count('middle'), count('start')), k('hc', count('end'), count('middle'))))
    text += definition('rl4', params(GRADUAL), both(k('rl3', *args(DECLINE)), k('hc', 'n p a b', v('bound')), limited, resolved, middle))
    retained = quant('f', 'first', 'd', quant('f', 'last', 'd', op('y', ordered, quant('f', 'obstacle', 'a', op('y',
        both(app(v('scope'), v('obstacle')), app(v('hindering'), v('obstacle'), v('last'))),
        app(v('hindering'), v('obstacle'), v('first')))))))
    text += definition('rl6', params(GRADUAL), both(k('rl4', *args(GRADUAL)), retained))
    variables = app(v('variables'), v('obstacle')); equations = app(v('equations'), v('obstacle'), v('point'))
    factor = app(v('factors'), v('obstacle')); world = app(v('worlds'), v('obstacle'), v('point'), v('state'))
    all_assessed = quant('f', 'person', 'a', op('y', app(v('people'), v('person')),
        op('t', app(v('evaluated'), v('person')), world)))
    side = lambda sign: k('rw', variables, equations, 'i[item a][' + op('e', v('item'), factor) + ']',
        'i[item a][' + sign + ']', 'i[state ' + STATE + '][' + all_assessed + ']')
    text += definition('rl7', params([('obstacle', 'a'), ('point', 'd')] + CAUSAL), both(
        k('rcm', v('population'), v('people')), k('ree', variables, equations, factor), side(TRUE), side(op('u', TRUE))))
    score = 'i[state ' + STATE + '][' + k('hf', v('population'), 'i[person a][' +
        op('t', app(v('property'), v('person')), world) + ']') + ']'
    text += definition('rma', params([('obstacle', 'a'), ('point', 'd')] + CAUSAL), k('reg', variables, equations, factor, score, 'n p a b'))
    return text


MEANINGS = {
    'rly': '固定した障害候補列で、その時点に妨害条件を満たす個体の数。完全列挙や評価整合は別のrl2で確認する。',
    'rlz': '同じ履歴で始点から終点までを両端込みで選ぶ。中間点を結果に応じて除外しない。',
    'rl2': '履歴が厳密な全順序で両端が所属し前後する。非空で重複のない障害候補列が範囲を完全に列挙し、区間内の全候補・全時点が評価済みである。',
    'rl3': 'rl2の同じ範囲・尺度で妨害条件を満たす数がどの前後でも増加せず、終点では始点より厳密に少ない。',
    'rl5': '指定履歴の前後二点の間に、同じ履歴の中間点がない。順序の妥当性は呼出側のrl2で確認する。',
    'rl4': 'rl3に加え、隣接点ごとの減少が指定した正の上限以内であり、始点と終点の間に両端と異なる中間値がある。任意の前後の差が上限を超えるなら、その間に両端と異なる件数の中間点も要求する。隣接点がないだけで大きな跳躍を許さず、二回以上の減少を持つ件数尺度の強い候補。',
    'rl6': 'rl4に加え、後の妨害条件を満たす候補は必ず前にも満たす。同じ候補の単調な除去を要求し、件数だけの減少と候補の入替えを区別する。',
    'rl7': '同じ候補・時点で要因の有無の双方に介入解があり、完全に列挙した同じ人々の能力評価が両側の全解で整合する。',
    'rma': '同じ候補・時点・構造モデルで、要因ありの独立使用能力人数が要因なしより少ない介入解の組がある。潜在的な妨害であり、実際の生起や全組での妨害保証とは別。',
    'hze5': 'rl7の能力評価を既存foへ接続し、同じ非空の対象範囲が全て人aaであることを要求する候補別・時点別の評価条件。',
    'hze6': 'rmaの人数尺度を、評価済みで指導なしに自分の理解力を使える既存h4lへ接続する。時点や介入側によって対象者・能力内容を交換しない。',
    'hze7': 'hze5の全評価とhze6の妨害条件を、同じ障害候補列・期間・順序・一段階の上限を持つrl4の漸減へ接続する。',
}
LIMITS = [
    '件数による有限段階の候補であり、原文の障害一般を個数へ還元しない。各障害の強さや分布、連続的な変化、時間の長さに対する速度、確率的な傾向は別に必要である。',
    'rl4は全区間で非増加かつ二回以上の減少を要求する強い読み。日常的な漸減が局所的な増加を許す場合の意味まで同一視しない。上限や履歴の刻みは原文が指定した数値ではない。',
    '有限の履歴の全点を比較する。標本の間に未記述の時点がないことや、現実の全障害・全人類を列挙したことは証明しない。rl6だけが障害候補自体の入替えも排除する。',
    '各時点の同一モデル内で要因の有無を比較する。時点間で方程式の背景が変わる場合もあるが、対象者・能力内容・要因の対応は固定する。介入モデルの現実的妥当性、障害が変化した原因や実際の除去行為は未完。',
    'rmaとhze6は生の妨害判定であり、評価欠落を除外するrl7・hze5と全区間のrl2なしに、確認済みの障害数の減少とは扱わない。解なし・未知・能力評価の欠落を障害なしへ補わない。',
    'u0014の一般的啓蒙を妨げる障害の漸減への部分注記。自己責任による未成熟からの離脱との言い換え、明瞭な徴候、自由な取り組みとの接続、著者帰属、段落全体の意味確認は残る。',
]


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8')); statements, doc['statements'] = doc['statements'], []
    text = definitions()
    fields = [('obstacle', 'a'), ('point', 'd')] + CAUSAL
    for name, target in (('hze5', 'rl7'), ('hze6', 'rma')):
        body = k(target, *args(fields, property='p h4l', evaluated='p fo'))
        if name == 'hze5':
            body = both(quant('f', 'person', 'a', op('y', app(v('people'), v('person')), k('aa', v('person')))), body)
        text += definition(name, params(SOURCE_CAUSAL), 'i[obstacle a point d][' + body + ']', 'h[a d] c')
    text += definition('hze7', params(SOURCE), k('rl4', *args(GRADUAL,
        assessed=k('hze5', *args(SOURCE_CAUSAL)), hindering=k('hze6', *args(SOURCE_CAUSAL)))))
    doc = parse(format_graph(doc, 'compact') + text); doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-free-pursuit-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-declining-hindrances-basis-v1', document='examples/v014/kant-declining-hindrances.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def projected(roots, stem):
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=roots, statement_indices=[])
    result = extract_basis(doc, basis, selected, version=stem + '-basis-v1', document_path='examples/v014/' + stem + '.noema')
    return format_graph(selected.document, 'compact') + '\n', result


def generic_composed(): return projected(ROOTS, 'declining-hindrances')
def core_composed(): return projected(ROOTS + ['hze5', 'hze6', 'hze7'], 'declining-hindrances-core')
BUILDERS = ((generic_composed, 'declining-hindrances'), (source_composed, 'kant-declining-hindrances'), (core_composed, 'declining-hindrances-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored declining hindrances differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
