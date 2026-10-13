"""Keep temporal scope inside versus outside a normative requirement explicit."""
from copy import deepcopy
import json

from noema.grammar import format_graph, number_word, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, call, definition
from scripts.compose_policy_norms import TRUE

PARENT = 'examples/v014/kant-policy-norms.noema'


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = 'r h7q[a d d] c.r h7r[a d d] c.\nd h7s[bindings j[a]] c[k rdr[v bindings n p e b]].\n'
    history = 'i[point d][k h7q[v frame v anchor v point]]'
    scope = 'i[point d][k h7r[v frame v anchor v point]]'
    before = 'i[first d last d][k ic[v first v last v anchor]]'
    valid = call('tb', history, scope, before)
    fields = ('regime', 'person', 'role', 'frame')
    positions = ['a[v bindings][n p ' + number_word(i) + ' b][v ' + name + ']' for i, name in enumerate(fields)]
    target = both(call('h7s', v('bindings')), *positions, valid,
        call('tc', scope, call('h7d', v('regime'), v('person'), v('role'))))
    for name in reversed(fields):
        target = quant('g', name, 'a', target)
    extra += 'd h7t[bindings j[a]] e[b anchor[' + target + ']].\n'
    params = 'assessor a regulator a office a regime a person a role a frame a anchor d'
    bindings = 'l[a][v regime v person v role v frame]'
    args = [v('assessor'), v('regulator'), v('office'), 'r[p h7t]', bindings, TRUE, v('anchor'), 'p h7s', 'p h7k', 'p h7l']
    extra += definition('h7u', params, call('rds', *args))
    required_at_point = 'b point[' + call('h7m', *(v(n) for n in ('assessor', 'regulator', 'office', 'regime', 'person', 'role')), v('point')) + ']'
    extra += definition('h7v', params, both(valid, call('tc', scope, required_at_point)))
    extra += definition('h7w', 'regime a person a role a frame a anchor d', op('t', call('h7t', bindings), v('anchor')))
    extra += definition('h7x', params, call('rdw', *args))
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-policy-norms-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-temporal-norms-basis-v1', document='examples/v014/kant-temporal-norms.noema')
    for name, meaning in (
        ('h7q', '指定した期間枠をこの評価状況で解釈するときの、一つの時間的経過に属する状況。反事実的な別経過を同じ並びへ混ぜない。既存icの先行関係をこの経過に制限して使う。'),
        ('h7r', '同じ期間枠・評価状況で、常時の規範や許可状態を評価する対象時点の範囲。期間枠の同一性を保持し、各時点で都合のよい範囲へ選び直さない。非空性・履歴内の所属・間の欠落をtbで検査する。')):
        row = next(row for row in doc['declarations'] if row['name'] == name)
        basis['primitives'].append({'symbol': name, 'parameters': row['parameters'], 'result': row['result'],
            'arguments': ['temporal_frame', 'evaluation_context', 'point'], 'meaning_ja': meaning})
    basis['definitions'].update({
        'h7s': '規範の出所・本人・立場・期間枠を順に渡す四引数の長さ規約。',
        'h7t': '四引数から同じ期間枠を取り、その評価状況で非空・同一の時間的経過内・間の抜けない対象範囲の全点で、公的活動の許可状態h7dが成立する内容。始点と終点だけでは足りない。',
        'h7u': '指定した一つの評価文脈で、評価側の出所が規制者に、同じ内側の出所・本人・立場・期間枠についてh7tの全期間の許可状態を実現するよう要求する。期間や内側の許可の真偽はここでは実行評価しない。',
        'h7v': '指定した期間枠の非空で間の抜けない対象範囲の全点で、同じ評価側の出所が同じ規制者・職務にh7mの許可要求をしている。時間量化は規範の外にある。各点で内側の許可が現に成立することは要求しない。',
        'h7w': '同じ内側の出所・本人・立場・期間枠に対するh7tが、指定評価状況で現に成立する。規範の要求とは別の条件。',
        'h7x': 'h7uの全期間の許可を求める要求があるが、その同じ対象内容が現在の評価状況では成立していない。規範の正当性や責任までは判定しない。'})
    basis['unresolved'] += [
        'jederzeitの時間量化が規範の対象内容の中にある読みh7uと、各対象時点で規範が成立する読みh7vを区別する。両者を無条件に入れ替える法則を採用せず、原文の唯一の作用範囲を確定したとはしない。',
        'h7tには非空で間の抜けない一つの時間的範囲を採用する。生涯・永遠・過去だけといった期間を原文から補わない。時点ごとの公的活動の種類が変わっても、同じ内側の出所・人・立場を固定して評価する。',
        '期間枠とその各評価状況での時間的解釈を分ける。履歴と範囲の完全性、実際の連続時間に対する評価点の粒度、反事実的な期間の対応は意味規約であり、有限検査だけでは証明しない。',
        'h7uは対象が現在不成立でも要求を記述できる。空・不整合な期間でh7tが不成立になる場合も、要求そのものを自動的に消去しない。知識が欠けて期間を評価できない場合とは区別する。',
        'h7vを判定するには期間と各時点の要求を評価するが、各時点の実際の許可は評価しない。h7wとh7xは内側の許可を評価する。',
        '頻度・制限の程度・啓蒙への影響、権利保障、基本概念と全文の意味一致は未完。既存の定義・主張を保持し、現実の許可や要求を本文主張へ追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = source_composed()
    for path, body in ((ROOT / basis['document'], text), (ROOT / 'data/kant-temporal-norms-basis-v1.json',
            json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored temporal norms differ')
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Temporal scope kept inside and outside normative requirements explicitly')


if __name__ == '__main__':
    main()
