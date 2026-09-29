"""Bind an actual change process to ordered states and the affected person."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, definition, call, lam
from scripts.compose_concession import generic_composed as concession


def definitions():
    params = 'history h[d] c before h[d d] c process a earlier d later d transitions h[a d d] c'
    args = [v(n) for n in ('history', 'before', 'process', 'earlier', 'later', 'transitions')]
    text = definition('tg', params, both(call('ta', v('history'), v('before')),
        app(v('history'), v('earlier')), app(v('history'), v('later')),
        app(v('before'), v('earlier'), v('later')),
        app(v('transitions'), v('process'), v('earlier'), v('later'))))
    text += definition('th', params + ' state e', both(call('tg', *args),
        op('u', op('t', v('state'), v('earlier'))), op('t', v('state'), v('later'))))
    return text


def generic_composed():
    text, basis = concession()
    text = format_graph(parse(text + definitions()), 'compact') + '\n'
    basis = deepcopy(basis)
    basis.update(version='transitions-basis-v1', document='examples/v014/transitions.noema')
    basis['definitions'].update({
        'tg': '同じ順序付き履歴の二状況が厳密に前後し、指定した変化過程がその二状況を結ぶ。二状況の並置だけでは成立しない。',
        'th': 'tgを満たす同じ変化過程の前では内容が成立せず、後で成立する。後で成立するという状態条件だけとは区別する。'})
    basis['unresolved'] += ['過程の内部構造、連続性、唯一の発生時刻、因果機構はこの前後条件からは導かない。過程と影響される対象の結合は呼出側で保持する。']
    audit_basis(parse(text), basis)
    return text, basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-prior-concession.noema').read_text(encoding='utf-8'))
    base = deepcopy(doc)
    base['declarations'], base['statements'] = [], []
    history = lam('point', 'd', call('ia', v('person'), v('context'), v('point')))
    scope = lam('point', 'd', call('ib', v('person'), v('context'), v('point')))
    before = 'i[left d right d][' + call('ic', v('left'), v('right'), v('context')) + ']'
    elapsed = 'i[left d right d][' + call('kd', v('left'), v('right'), v('context')) + ']'
    witness = both(call('th', history, before, v('process'), v('earlier'), v('later'), 'p ag', call('kc', v('person'))),
        op('t', call('kl', v('person')), v('earlier')),
        call('la', v('person'), v('process'), v('earlier'), v('later')),
        call('tf', history, scope, before, v('later'), elapsed))
    for item in doc['declarations']:
        if item['name'] == 'kf':
            text = format_graph(base, 'compact') + '\n' + definitions() + '''
r la[a a d d] c.
d kl[person a] e[b point[g other a[w[u[e[v other][v person]]][k kb[v person v other v point]]]]].
'''
            text += definition('km', 'person a process a earlier d later d context d', witness)
            prior = quant('g', 'earlier', 'd', quant('g', 'later', 'd', quant('g', 'process', 'a',
                call('km', *(v(n) for n in ('person', 'process', 'earlier', 'later', 'context'))))))
            text += 'd kf[person a] e[b context[' + prior + ']].\n'
            base = parse(text)
        else:
            base['declarations'].append(deepcopy(item))
    base['statements'] = doc['statements']
    text = format_graph(base, 'compact') + '\n'
    basis = deepcopy(json.loads((ROOT / 'data/kant-prior-concession-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-release-transition-basis-v1', document='examples/v014/kant-release-transition.noema')
    generic = generic_composed()[1]
    for name in ('tg', 'th'):
        basis['definitions'][name] = generic['definitions'][name]
    declaration = next(d for d in base['declarations'] if d['name'] == 'la')
    basis['primitives'].append({'symbol': 'la', 'parameters': declaration['parameters'], 'result': 'truth',
        'arguments': ['person', 'process', 'earlier', 'later'],
        'meaning_ja': 'その人が、その前後状況を結ぶ変化過程において、状態変化を受ける対象である。同時に起きた別人の過程、単なる目撃、過程の原因であることとは区別する。'})
    basis['definitions'].update({
        'kl': 'その人の自然的な発達上の依存により、本人と異なる他者による指導が必要な状態。',
        'km': 'その人の同じ履歴内で、他者の指導を要する依存klかつkcでない状態から、kcが成立する状態へ、本人を対象とする過程ag・laが移す。その後状態は生涯の評価範囲より十分前である。',
        'kf': 'kmを満たす前後状況と変化過程が存在する。旧版の先行する状態だけという条件に代えて、依存から自然的成人への移行を先行条件として明示する。'})
    basis['unresolved'] += [generic['unresolved'][-1],
        'この版では解放を過去の依存からの移行として読む。前状態の依存を明示的に要求する読解候補であり、原文の唯一の分析とはしない。過程の具体的な機構と自然による宣告の比喩は未記述である。',
        '新kfは既存kg・kh・kiへ同じ定義参照で接続する。成熟・依存の一般的な説明、原因説明、後見人の容易さ、段落全体と原刊照合は残る。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    for compose, filename in ((generic_composed, 'data/transitions-basis-v1.json'),
                              (source_composed, 'data/kant-release-transition-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored transition document differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Release now requires a process, affected person and distinct before/after conditions')


if __name__ == '__main__':
    main()
