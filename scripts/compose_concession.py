"""Separate prior conditions, contextual elapsed time and defeated expectations."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, definition, call, lam
from scripts.compose_persistence import generic_composed as persistence


def definitions():
    params = 'history h[d] c scope h[d] c before h[d d] c point d'
    text = definition('te', params, both(call('tb', v('history'), v('scope'), v('before')),
        app(v('history'), v('point')), quant('f', 'later', 'd', op('y', app(v('scope'), v('later')),
            app(v('before'), v('point'), v('later'))))))
    text += definition('tf', params + ' elapsed h[d d] c', both(
        call('te', *(v(n) for n in ('history', 'scope', 'before', 'point'))),
        quant('f', 'later', 'd', op('y', app(v('scope'), v('later')), app(v('elapsed'), v('point'), v('later'))))))
    params = 'person a premise e description i[h[a] e] conclusion e context d candidates h[a i[h[a] e] d d] c'
    selected = app(v('candidates'), v('person'), v('description'), v('context'), v('alternative'))
    text += definition('ja', params, both(quant('g', 'alternative', 'd', selected),
        quant('f', 'alternative', 'd', op('y', selected,
            both(op('t', v('premise'), v('alternative')), op('u', op('t', v('conclusion'), v('alternative'))))))))
    text += definition('jb', params, both(op('t', v('premise'), v('context')),
        op('t', v('conclusion'), v('context')),
        call('ja', *(v(n) for n in ('person', 'premise', 'description', 'conclusion', 'context', 'candidates')))))
    return text


def generic_composed():
    text, basis = persistence()
    text = format_graph(parse(text + definitions()), 'compact') + '\n'
    basis = deepcopy(basis)
    basis.update(version='concession-basis-v1', document='examples/v014/concession.noema')
    basis['definitions'].update({
        'te': '履歴内の指定状況が、空でなく間の抜けない評価範囲の全状況より先行する。別の履歴や範囲内の後の時点を先行条件に流用しない。',
        'tf': 'teを満たし、指定状況から全評価状況までの経過が、与えた文脈的な基準を満たす。数値の期間は固定しない。',
        'ja': '指定した人物・前提の記述・文脈に対応する通常予想の候補が空でなく、全候補で前提が成立し結論が成立しない。候補の妥当性を前提の真偽でも検査する。',
        'jb': '現在の文脈で前提と結論が共に成立する一方、jaの通常予想の候補では結論が成立しない。論理的矛盾や因果関係とは別の、期待に反する成立条件。'})
    basis['unresolved'] += ['通常予想の候補の選定根拠は解釈の前提である。全候補での不成立を要求する操作化であり、確率の高低や自然言語の譲歩全般を一意に定義したものではない。',
        '前提の内容と記述の対応は呼出側で保持する。候補の選定自体から前提の現実の真理は導かない。']
    audit_basis(parse(text), basis)
    return text, basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-lifelong-state.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + '\n' + definitions() + '''
r ka[a d] c.r kb[a a d] c.r kd[d d d] c.r ke[a a i[h[a] e] d d] c.
d kc[person a] e[b point[w[k aa[v person]][w[k ka[v person v point]][u[g other a[w[u[e[v other][v person]]][k kb[v person v other v point]]]]]]]].
'''
    history = lam('scene', 'd', call('ia', v('person'), v('context'), v('scene')))
    scope = lam('scene', 'd', call('ib', v('person'), v('context'), v('scene')))
    before = 'i[left d right d][' + call('ic', v('left'), v('right'), v('context')) + ']'
    elapsed = 'i[left d right d][' + call('kd', v('left'), v('right'), v('context')) + ']'
    prior = quant('g', 'point', 'd', both(call('tf', history, scope, before, v('point'), elapsed),
        op('t', call('kc', v('person')), v('point'))))
    text += 'd kf[person a] e[b context[' + prior + ']].\n'
    candidates = 'i[subject a description i[h[a] e] context d alternative d][' + call('ke', 'k wa[]',
        v('subject'), v('description'), v('context'), v('alternative')) + ']'
    concession = call('jb', v('person'), call('kf', v('person')), 'r[p kf]', call('ie', v('person')), v('context'), candidates)
    text += 'd kg[person a] e[b context[' + concession + ']].\n'
    text += 'd kh[population j[a]] e[k hq[v population p kg]].\n'
    text += definition('ki', 'population j[a] ratio b context d', call('hn', v('population'), 'p kg', v('ratio'), v('context')))
    doc = parse(text)
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '\n'
    basis = deepcopy(json.loads((ROOT / 'data/kant-lifelong-state-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-prior-concession-basis-v1', document='examples/v014/kant-prior-concession.noema')
    generic = generic_composed()[1]
    for name in ('te', 'tf', 'ja', 'jb'):
        basis['definitions'][name] = generic['definitions'][name]
    declarations = {d['name']: d for d in doc['declarations']}
    for symbol, labels, meaning in (
        ('ka', ['person', 'point'], 'その人が自然的な成長・成熟の意味で成人の段階に達している。法定年齢、現実の知的自立、他者の指導を受けていない事実とは区別する。自然的成熟の一般的な説明は残る。'),
        ('kb', ['person', 'other', 'point'], 'その人の自然的な発達上の依存が、その別人による指導を必要とする。実際に指導されていることや制度上の義務とは別の関係。'),
        ('kd', ['earlier', 'later', 'context'], '二状況間の経過が、この文脈で十分以前・とうの昔と扱う基準を満たす。一定の年数には固定せず、前後関係はteで別に要求する。'),
        ('ke', ['perspective', 'person', 'premise_description', 'context', 'alternative'], '指定した視点から、その人について記述された前提を認めたとき、通常予想する比較候補として採用する状況。現実の時間的履歴とは別の候補集合であり、原文の譲歩を読む際の明示的な解釈。')):
        basis['primitives'].append({'symbol': symbol, 'parameters': declarations[symbol]['parameters'],
            'result': 'truth', 'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'kc': '人であり自然的成人に達し、自然的な発達上の依存によって他者の指導が必要な状態ではない。知的自立bfの否定や実際の他者指導の不在を意味しない。',
        'kf': '同じ人物の履歴内に、生涯の評価範囲より十分前でkcを満たす状況がある。',
        'kg': 'kfの先行条件とieの持続が共に成立し、著者の視点でkfを認める通常予想の候補ではieが成立しない、という譲歩の読解候補。',
        'kh': 'kgを満たす人々が文脈上大きい割合を占めるという内容。先行条件と譲歩を同じ人々の性質へ接続する。',
        'ki': 'khの比率を明示した検査用条件。旧if・igも比較用に残す。'})
    basis['unresolved'] += generic['unresolved'][-2:] + [
        'kcは自然的成人という括弧内説明を手掛かりに、自然による解放を発達上の依存の不在で読む部分草案。自然の擬人化・宣告という比喩の働きや、自然的成熟の一般定義、ラテン語の語義の独立検証は残る。',
        'この版で先行条件・文脈的な経過・譲歩を割合の性質へ接続した。怠惰と臆病の原因説明、後見人の容易さ、段落の残部と原刊確認は未完。',
        'keの視点には既存の著者waを明示した。これは採用した読解の視点であり、全読者が同じ期待を持つとは主張しない。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    for compose, filename in ((generic_composed, 'data/concession-basis-v1.json'),
                              (source_composed, 'data/kant-prior-concession-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored concession differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Prior conditions and contextual expectations connected without equating maturity and ability')


if __name__ == '__main__':
    main()
