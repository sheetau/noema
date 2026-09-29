"""Compose ordered temporal scope, persistence and favorable attitude separately."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, definition, call, lam


def definitions():
    member = lambda n: app(v('history'), v(n))
    selected = lambda n: app(v('scope'), v(n))
    before = lambda a, b: app(v('before'), v(a), v(b))
    order = both(
        quant('g', 'point', 'd', member('point')),
        quant('f', 'left', 'd', op('y', member('left'), op('u', before('left', 'left')))),
        quant('f', 'left', 'd', quant('f', 'right', 'd', op('y', both(member('left'), member('right'),
            op('u', op('e', v('left'), v('right')))), op('x', before('left', 'right'), before('right', 'left'))))),
        quant('f', 'left', 'd', quant('f', 'middle', 'd', quant('f', 'right', 'd', op('y',
            both(member('left'), member('middle'), member('right'), before('left', 'middle'), before('middle', 'right')),
            before('left', 'right'))))))
    text = definition('ta', 'history h[d] c before h[d d] c', order)
    scope = both(call('ta', v('history'), v('before')),
        quant('g', 'point', 'd', selected('point')),
        quant('f', 'point', 'd', op('y', selected('point'), member('point'))),
        quant('f', 'left', 'd', quant('f', 'middle', 'd', quant('f', 'right', 'd', op('y',
            both(selected('left'), selected('right'), member('middle'), before('left', 'middle'), before('middle', 'right')),
            selected('middle'))))))
    text += definition('tb', 'history h[d] c scope h[d] c before h[d d] c', scope)
    text += definition('tc', 'scope h[d] c state e', both(
        quant('g', 'point', 'd', selected('point')),
        quant('f', 'point', 'd', op('y', selected('point'), op('t', v('state'), v('point'))))))
    text += definition('td', 'person a description i[h[a] e] scope h[d] c favor h[a i[h[a] e] d] c', both(
        quant('g', 'point', 'd', selected('point')),
        quant('f', 'point', 'd', op('y', selected('point'),
            app(v('favor'), v('person'), v('description'), v('point'))))))
    return text


def generic_composed():
    text = format_graph(parse('n:\n' + definitions()), 'compact') + '\n'
    basis = {'version': 'persistence-basis-v1', 'document': 'examples/v014/persistence.noema',
        'primitives': [], 'definitions': {
            'ta': '空でない履歴の状況について、先行関係が非反射的・推移的であり、異なる二状況が比較できる。履歴内の厳密な全順序を要求する。',
            'tb': 'taを満たす履歴の中で、評価範囲が空でない部分集合であり、選択した二状況の間にある履歴内の状況を全て含む。',
            'tc': '空でない評価範囲の全状況で、指定した内容が成立する。初期と終期だけの一致ではない。',
            'td': '空でない評価範囲の全状況で、その人物が、指定した性質の記述に該当する自分の状態へ肯定的な態度を持つ。態度の関係は引数であり、状態の成立や自由な選択をこの条件からは導かない。'},
        'unresolved': ['履歴が一つの時間的経過を過不足なく表すこと、状況の粒度、評価範囲の選定は解釈の前提である。有限の観測点だけで現実の全時間を検証しない。',
            'tcとtdは別々の条件であり、成立する内容と態度の対象記述が対応することは呼出側で保持する。',
            '瞬間的な気分と一般的な傾向、強制の不在、意図的な選択、因果的な動機付けの理論は含まない。']}
    audit_basis(parse(text), basis)
    return text, basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-large-share.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + '\n' + definitions() + '''
r ia[a d d] c.r ib[a d d] c.r ic[d d d] c.r id[a i[h[a] e] d] c.
'''
    history = lam('point', 'd', call('ia', v('person'), v('context'), v('point')))
    scope = lam('point', 'd', call('ib', v('person'), v('context'), v('point')))
    before = 'i[left d right d][' + call('ic', v('left'), v('right'), v('context')) + ']'
    body = both(call('tb', history, scope, before), call('tc', scope, call('bf', v('person'))),
                call('td', v('person'), 'r[p bf]', scope, 'p id'))
    text += 'd ie[person a] e[b context[' + body + ']].\n'
    text += 'd if[population j[a]] e[k hq[v population p ie]].\n'
    text += definition('ig', 'population j[a] ratio b context d', call('hn', v('population'), 'p ie', v('ratio'), v('context')))
    doc = parse(text)
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '\n'
    basis = deepcopy(json.loads((ROOT / 'data/kant-large-share-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-lifelong-state-basis-v1', document='examples/v014/kant-lifelong-state.noema')
    generic = generic_composed()[1]
    basis['definitions'].update(generic['definitions'])
    declarations = {d['name']: d for d in doc['declarations']}
    for symbol, labels, meaning in (
        ('ia', ['person', 'context', 'point'], 'その人について、この文脈で採用した一つの時間的履歴に属する状況。反事実的な別の履歴の状況と混ぜないという解釈上の前提を持つ。'),
        ('ib', ['person', 'context', 'point'], 'この文脈で、その人の生涯にわたる継続を評価する範囲に属する状況。履歴内の非空で間の抜けない範囲であることをtbで検査する。出生から死亡までの全瞬間か、文脈上の残る生涯かはこの関係の解釈で明示する。'),
        ('ic', ['earlier', 'later', 'context'], 'この文脈の時間的履歴で第一の状況が第二より先行する。taによって履歴内の順序条件を検査する。'),
        ('id', ['person', 'property_description', 'point'], 'その状況で、その人が記述された性質に該当する自分の状態を好ましく受け入れている。状態の成立、能力、強制の不在、意図的な選択は別の条件である。')):
        basis['primitives'].append({'symbol': symbol, 'parameters': declarations[symbol]['parameters'],
            'result': 'truth', 'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'ie': 'その人の生涯として評価する時間範囲が履歴内の非空の区間であり、その全範囲で既存の未成熟bfが成立し、その同じbfの記述に該当する状態を好ましく受け入れている。',
        'if': '生涯の評価範囲で好んで未成熟に留まるieに該当する人々の比率が、文脈上の大きさの基準を満たすという内容。既存hqへ性質を接続する。',
        'ig': 'ifの量化する比率を明示した検査用の条件。母集団、文脈、同じ人物についての時間・状態・態度の対応を保持する。'})
    basis['unresolved'] += generic['unresolved'] + [
        '以前の未接続記録に対し、この版でhqの性質をieへ接続した。u0009の原因、自然による先行する解放、dennochの譲歩、後半の後見人の容易さはまだ接続していない。',
        'gerne Zeitlebensという表現を、文脈上評価する生涯の範囲における持続的な状態と肯定的態度で読む候補である。全瞬間の気分や出生直後の判断を原文が主張すると決めつけない。範囲・粒度の確定と一般的な傾向の理論は残る。',
        '自由な選択の結果だから継続したという因果関係は追加していない。原文の全文やこの読解の唯一性を検証済みとはしない。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    for compose, filename in ((generic_composed, 'data/persistence-basis-v1.json'),
                              (source_composed, 'data/kant-lifelong-state-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored persistence document differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Ordered persistence and favorable attitude connected to the population quantifier')


if __name__ == '__main__':
    main()
