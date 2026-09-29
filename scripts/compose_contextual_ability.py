"""Separate possible success, guaranteed success and explicit assessment standards."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, call, app, op, both, quant, definition

AVAILABLE = 'h[a a d] c'
OUTCOMES = 'h[a a d d] c'


def definitions():
    option = [('actor', 'a'), ('plan', 'a'), ('start', 'd')]
    selected = app(v('selected'), *(v(n) for n, _ in option), v('end'))
    outcome = app(v('outcomes'), *(v(n) for n, _ in option), v('end'))
    available = app(v('available'), *(v(n) for n, _ in option))
    success = op('t', v('goal'), v('end'))
    params = 'actor a goal e start d available ' + AVAILABLE + ' outcomes ' + OUTCOMES
    contextual = params + ' selected ' + OUTCOMES
    args = [v(n) for n in ('actor', 'goal', 'start', 'available', 'outcomes', 'selected')]
    valid = call('xa', *(v(n) for n, _ in option), v('outcomes'), v('selected'))
    text = definition('xa', 'actor a plan a start d outcomes ' + OUTCOMES + ' selected ' + OUTCOMES,
        both(quant('g', 'end', 'd', selected), quant('f', 'end', 'd', op('y', selected, outcome))))
    text += definition('xb', params, quant('g', 'plan', 'a', both(available,
        quant('g', 'end', 'd', both(outcome, success)))))
    text += definition('xc', params, quant('g', 'plan', 'a', both(available,
        quant('g', 'end', 'd', outcome), quant('f', 'end', 'd', op('y', outcome, success)))))
    text += definition('xd', contextual, quant('g', 'plan', 'a', both(available, valid,
        quant('f', 'end', 'd', op('y', selected, success)))))
    assessment_args = [v(n) for n in ('actor', 'start', 'available', 'outcomes', 'selected')]
    text += definition('xe', 'actor a start d available ' + AVAILABLE + ' outcomes ' + OUTCOMES + ' selected ' + OUTCOMES,
        quant('f', 'plan', 'a', op('y', available, valid)))
    text += definition('xf', contextual, op('x', call('xe', *assessment_args), call('xd', *args)))
    text += definition('xg', contextual, both(call('xe', *assessment_args), op('u', call('xd', *args))))
    return text


def generic_composed():
    text = format_graph(parse('m:\n' + definitions()), 'compact') + '\n'
    basis = {'version': 'contextual-ability-basis-v1', 'document': 'examples/v013/contextual-ability.noema',
             'primitives': [], 'definitions': {
        'xa': '指定した人・方法・開始状況について、評価対象の結果が空でなく、全て想定結果に含まれる。',
        'xb': '実行できる方法があり、その想定結果の少なくとも一つで目的が成立する。成功の可能性であり保証ではない。',
        'xc': '実行できる方法があり、その想定結果が空でなく、全結果で目的が成立する。',
        'xd': '実行できる方法のうち、xaを満たす評価対象の全結果で目的が成立する方法がある。他の方法の評価範囲が妥当であることまでは含まない。',
        'xe': '実行できる全方法について評価対象が空でなく想定結果の部分集合である。実行できる方法がなければこの整合条件は成立する。',
        'xf': 'xdの達成方法を一つ確認できるか、xeにより全方法の評価範囲が整合する。能力の有無をこの解釈内で判定できる条件。',
        'xg': 'xeによって全方法の評価範囲の整合性を確認した上で、xdの達成方法がない。単なるxdの否定とは区別し、未評価の方法を不可能扱いしない。'},
        'unresolved': ['評価対象の選択基準は引数で明示する。自然言語の能力一般を一つの基準に還元した定義ではない。',
                       '結果の選択関数は目的内容を引数に取らないが、選択基準を恣意的に設定できないという社会的・認識的保証は、この形式だけでは与えない。']}
    audit_basis(parse(text), basis)
    return text, basis


def source_composed():
    doc = parse((ROOT / 'examples/v013/kant-opening-discourse.noema').read_text(encoding='utf-8'))
    base = deepcopy(doc)
    base['statements'], base['declarations'] = [], []
    for item in doc['declarations']:
        if item['name'] == 'bc':
            prefix = format_graph(base, 'compact') + '\nr ap[a a d d] c.\n' + definitions()
            prefix += 'd bc[person a scene d] c[w[k aa[v person]][k xg[v person k bb[v person] v scene p ae p af p ap]]].\n'
            base = parse(prefix)
        elif item['name'] == 'be':
            prefix = format_graph(base, 'compact') + '\nd be[person a change a before d after d] c['
            prefix += 'w[k ag[v change v before v after]][w[k bd[v person v before]][k xd[v person k bb[v person] v after p ae p af p ap]]]].\n'
            base = parse(prefix)
        else:
            base['declarations'].append(deepcopy(item))
    base['statements'] = doc['statements']
    text = format_graph(base, 'compact') + '\n'
    basis = deepcopy(json.loads((ROOT / 'data/kant-opening-discourse-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-contextual-ability-basis-v1', document='examples/v013/kant-contextual-ability.noema')
    declaration = next(d for d in parse(text)['declarations'] if d['name'] == 'ap')
    basis['primitives'].append({'symbol': 'ap', 'parameters': declaration['parameters'], 'result': 'truth',
        'arguments': ['person', 'plan', 'start', 'outcome'],
        'meaning_ja': 'その人・方法・開始状況について、この読解で能力の評価対象に採った結果。全ての可能な結果を含むとは限らない。採用基準は文脈の前提であり、原文が一意に指定した基準とは扱わない。'})
    basis['definitions'].update(generic_composed()[1]['definitions'])
    basis['definitions'].update({
        'bc': '人であり、明示した評価範囲が整合し、その範囲の全結果で自立的使用bbを達成する方法がない。旧草案の全想定結果での保証の否定から区別する。',
        'be': '実際の変化過程で、bdの状態から、評価範囲が整合し自立的使用を達成する方法がある状態へ移る。評価範囲の欠落を離脱の達成とは扱わない。'})
    basis['unresolved'] += [
        'この文書では全結果での達成保証だけを能力と扱う旧草案を改め、評価範囲を引数と基本関係apで明示した。baは旧条件との比較用に保持する。',
        'apの具体的な採用基準は原文で列挙されていない。今回の文脈的な操作化をUnvermögen一般の唯一の語義とはしない。',
        '因果・決意と勇気の不足の範囲・Ausgangの全容・ラテン語の独立した意味確認は残る。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    for compose, filename in ((generic_composed, 'data/contextual-ability-basis-v1.json'),
                              (source_composed, 'data/kant-contextual-ability-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored contextual ability differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Contextual assessment separated from possible and guaranteed success')


if __name__ == '__main__':
    main()
