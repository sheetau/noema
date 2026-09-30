"""Evaluate low burden while remaining in a state, separately from preference."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_easy_roles import generic_composed as easy_roles
from scripts.compose_limits import ROOT, v, call, app, op, both, quant, definition


def definitions():
    params = 'person a state e goal e context d available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c cost h[a a d] b standard h[b] c'
    joint_goal = 'b scene[' + both(op('t', v('state'), v('scene')), op('t', v('goal'), v('scene'))) + ']'
    text = definition('rj', params, both(op('t', v('state'), v('context')),
        call('nd', v('person'), joint_goal, *(v(name) for name in ('context', 'available', 'outcomes', 'selected', 'cost', 'standard')))))
    params = 'person a state h[a] e goal h[a] e context d cases h[a d d] c available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c cost h[a a d] b standard h[b d] c'
    selected = app(v('cases'), v('person'), v('context'), v('scene'))
    criterion = 'i[value b][' + app(v('standard'), v('value'), v('context')) + ']'
    evaluated = call('rj', v('person'), app(v('state'), v('person')), app(v('goal'), v('person')), v('scene'),
        *(v(name) for name in ('available', 'outcomes', 'selected', 'cost')), criterion)
    text += definition('rk', params, both(quant('g', 'scene', 'd', selected),
        quant('f', 'scene', 'd', op('y', selected, evaluated))))
    return text


def generic_composed():
    text, basis = easy_roles()
    doc = parse(text + definitions())
    basis = deepcopy(basis)
    basis.update(version='state-convenience-basis-v1', document='examples/v014/state-convenience.noema')
    basis['definitions'].update({
        'rj': '開始時点で状態が成立し、同じ本人が選択できる一つの方法について、非空で整合した全評価結果でその状態と実用上の目的が共に成立し、その方法の負担が指定基準を満たす。状態に入る容易さや、好むこととは分ける。',
        'rk': '本人と文脈に対応する仮定状況の範囲が非空で、全ての選択状況でrjが成立する。負担の判定基準は元の評価文脈に固定し、方法の利用可能性や負担は各状況で調べる。'})
    basis['unresolved'] += [
        '状態に留まりつつ実用上の目的を低負担で満たせるという、便宜さの一つの操作的な説明である。便利さの全語義、継続経路全体での状態の保持、習慣的な一般化を一意に定義するものではない。',
        '状態への好意、状態を選んだという行為、自由な選択、道徳的な望ましさは条件に含めない。評価結果での状態の保持と、現実にその方法を実行したことも別である。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v014/kant-payment-expectation.noema').read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    text = format_graph(doc, 'compact') + definitions() + '''
r uj[a d d] c.r uk[b d] c.r um[a d] c.r uo[] a.
d ul[person a] e[b context[k rk[v person p bf p sw v context p uj p ae p af p ap p oc p uk]]].
d un[] e[b context[
 w[g person a[k um[v person v context]]][f person a[y[k um[v person v context]][w[k aa[v person]][t[k ul[v person]][v context]]]]]
]].
'''
    doc = parse(text)
    doc['statements'] = statements
    text = format_graph(doc, 'compact') + '''
s[w[k uc[k uo[] k wa[] r[k un[]] k wh[]]][w[k ue[k mw[] k uo[] k wh[]]][k ue[k uo[] k s3[] k wh[]]]]].
'''
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / 'data/kant-payment-expectation-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-state-convenience-basis-v1', document='examples/v014/kant-state-convenience.noema')
    # Preserve the old basis on disk, but do not carry its obsolete claim that
    # the convenience and payment sentences are absent into this new document.
    basis['unresolved'] = [note for note in basis['unresolved'] if not note.startswith('Es ist so bequem')]
    generic = generic_composed()[1]
    basis['definitions'].update({name: generic['definitions'][name] for name in ('rj', 'rk')})
    decls = {d['name']: d for d in doc['declarations']}
    for name, labels, meaning in (
        ('uj', ['person', 'context', 'case'], '未成熟の状態にある場合の便宜さを評価するため、その本人と文脈について採用する仮定状況。現実の履歴や、前後の文の評価範囲を自動的に同一視しない。'),
        ('uk', ['burden', 'context'], 'この文脈で、本人の負担が「これほど便利」と評価する水準に収まるという基準。特定の数値、単位、別の状態との優劣を原文へ補わない。'),
        ('um', ['person', 'context'], '便宜さについての一般的な評価をこの文脈で適用する人物の範囲。全人類を無条件に全称化せず、評価する範囲は明示した解釈の前提とする。'),
        ('uo', [], '未成熟でいる便宜さを述べる文の談話箇所。原因説明の後、三つの代行例の前に位置する。')):
        d = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'], 'arguments': labels, 'meaning_ja': meaning})
    basis['definitions'].update({
        'ul': '本人について選んだ仮定状況で、既存の未成熟bfにあるまま実用上の目的swを低負担で満たせる方法がある。便宜さの基準ukは元の文脈へ固定する。',
        'un': '評価する人物の範囲umが非空で、その全員が人でありulを満たす内容。著者の主張の記述として帰属し、読者が実際に未成熟であるとか著者が未成熟を推奨しているとはしない。'})
    basis['unresolved'] += generic['unresolved'][-2:] + [
        '便宜さの読みを、未成熟の状態にある場合の低負担な目的達成として明示した。未成熟の一般的な定義、目的・負担・適用人物と場面の範囲、soの程度や皮肉の効果は未確定である。',
        '既存のidによる状態への好意やmeによる行為の理由を、この便宜さの条件へ追加しない。低負担であることだけから好意・実行・推奨・自由な選択を推論しない。',
        '第二段落冒頭四文の全てに部分草案が接続した。これは原文区間の草案化の範囲であり、語義や原文との同義性の確認、原刊照合、段落残部と全文完成ではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, filename in ((generic_composed, 'data/state-convenience-basis-v1.json'),
                              (source_composed, 'data/kant-state-convenience-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored state convenience differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Convenience of remaining in a state connected without inferring preference or actual choice')


if __name__ == '__main__':
    main()
