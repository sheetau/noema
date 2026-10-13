"""Describe norms about parameterized policies without erasing their targets."""
from copy import deepcopy
import json

from noema.grammar import format_graph, number_word, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, quant, call, definition

PARENT = 'examples/v014/kant-described-norms.noema'
DESCRIPTION = 'i[h[j[a]] e]'
RULE = 'h[a a a ' + DESCRIPTION + ' j[a] c d] c'
PARAMS = ('source a person a role a description ' + DESCRIPTION + ' bindings j[a] polarity c context d '
    'valid h[j[a]] c required ' + RULE + ' allowed ' + RULE)
TRUE = 'e[n p a b][n p a b]'


def definitions():
    fields = [v(n) for n in ('source', 'person', 'role', 'description', 'bindings')]
    rule = lambda name, sign: app(v(name), *fields, sign, v('context'))
    sign = v('polarity')
    requested, permitted, opposed = rule('required', sign), rule('allowed', sign), rule('required', op('u', sign))
    valid = app(v('valid'), v('bindings'))
    actual = op('t', app('s[v description]', v('bindings')), v('context'))
    text = definition('rdr', 'bindings j[a] size b', op('e', 'd[v bindings]', v('size')))
    return text + ''.join(definition(name, PARAMS, both(valid, body)) for name, body in (
        ('rds', requested), ('rdt', permitted), ('rdu', both(permitted, op('u', opposed))),
        ('rdv', both(requested, opposed)), ('rdw', both(requested, op('u', op('e', actual, sign))))))


MEANINGS = {
    'rdr': '個体を並べた引数列の長さが指定値に等しい。負数や非整数の長さには一致しない。',
    'rds': '対象記述に渡す引数列が指定条件に適合し、同じ出所・名宛人・立場・記述・引数列・極性・文脈について要求がある。',
    'rdt': 'rdsと同じ対象の固定方法で積極的な許可がある。反対要求との衝突はこの条件だけでは除かない。',
    'rdu': '同じ指定対象への許可rdtがあり、その反対極性への要求がない。',
    'rdv': '適合する同じ引数列と記述について、指定極性と反対極性が共に要求される。',
    'rdw': '指定対象への要求があり、その記述に同じ引数列を適用した現在の真偽が、要求された極性に一致しない。',
}
LIMITS = [
    '記述は個体の有限列から内容へのNoemaの関数を指す。引数の順序と数を保持し、本文を引用文字列で代用しない。数・状況など個体以外の引数をこの列へ暗黙に変換しない。',
    'validは同じ対象記述の引数規約に対応する条件として渡す。一般形だけではその組合せの正しさを自動証明せず、原文接続では記述と長さ規約を固定する。',
    '外側の規範の出所・名宛人・立場と、対象政策の規範の出所・対象者・立場は別の束縛である。引数を偶然同じにした場合も両者を同一視する規則は加えない。',
    'rdwだけが対象内容を脱引用して評価する。要求・許可を述べることから対象の成立や、規範の正当性・実現能力を補わない。',
    'この一般形は任意長の個体列を渡せるが、原文用の具体的なアダプターは二引数と三引数である。無限の列全体を有限候補へ置き換えて量化しない。',
]


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'policy-norms-basis-v1', 'document': 'examples/v014/policy-norms.noema',
        'primitives': [], 'definitions': MEANINGS, 'unresolved': LIMITS}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def adapter(symbol, target, names, shape):
    positions = ['a[v bindings][n p ' + number_word(i) + ' b][v ' + name + ']' for i, name in enumerate(names)]
    body = both(call(shape, v('bindings')), *positions, op('t', call(target, *(v(n) for n in names)), v('context')))
    for name in reversed(names):
        body = quant('g', name, 'a', body)
    return 'd ' + symbol + '[bindings j[a]] e[b context[' + body + ']].\n'


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-described-norms-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    dc = basis['role_linkage']['symbols']['roles']['dc']
    extra = 'd h7f[bindings j[a]] c[k rdr[v bindings n p c b]].\nd h7g[bindings j[a]] c[k rdr[v bindings n p d b]].\n'
    extra += adapter('h7h', dc, ('actor', 'activity'), 'h7f')
    extra += adapter('h7i', 'h7d', ('regime', 'actor', 'role'), 'h7g')
    extra += adapter('h7j', 'h7e', ('regime', 'actor', 'role'), 'h7g')
    extra += 'r h7k[a a a ' + DESCRIPTION + ' j[a] c d] c.r h7l[a a a ' + DESCRIPTION + ' j[a] c d] c.\n'
    params = 'assessor a regulator a office a regime a person a role a context d'
    bindings = 'l[a][v regime v person v role]'
    for symbol, relation, target in (('h7m', 'rds', 'h7i'), ('h7n', 'rdt', 'h7j'), ('h7o', 'rdw', 'h7i')):
        extra += definition(symbol, params, call(relation, v('assessor'), v('regulator'), v('office'), 'r[p ' + target + ']',
            bindings, TRUE, v('context'), 'p h7g', 'p h7k', 'p h7l'))
    extra += definition('h7p', 'source a person a role a activity a context d', call('rdu', v('source'), v('person'), v('role'),
        'r[p h7h]', 'l[a][v person v activity]', TRUE, v('context'), 'p h7f', 'p h7k', 'p h7l'))
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis.update(version='kant-policy-norms-basis-v1', document='examples/v014/kant-policy-norms.noema')
    for name, meaning in (
        ('h7k', '指定の規範の出所が、名宛人にその立場で、記述へ同じ順序の引数列を渡した対象内容の指定極性を満たすよう要求する。対象内容が別の規範状態でもよく、その現実の成立とは分ける。'),
        ('h7l', '指定の規範の出所が、名宛人にその立場で、同じ記述・引数列で指定された内容の極性を積極的に許可する。許可された内容の実行や、義務との同一視を含まない。')):
        row = next(row for row in doc['declarations'] if row['name'] == name)
        basis['primitives'].append({'symbol': name, 'parameters': row['parameters'], 'result': row['result'],
            'arguments': ['source', 'addressee', 'role', 'target_description', 'bindings', 'polarity', 'context'], 'meaning_ja': meaning})
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h7f': '行為実行アダプター用の二つの個体引数という長さ規約。',
        'h7g': '政策状態アダプター用の三つの個体引数という長さ規約。',
        'h7h': '引数列の順に本人・活動を取り、既存の同じ実行内容を返す。列長が二でない場合には成立せず、規範を呼ぶ側でもh7fを検査する。',
        'h7i': '引数列の順に規範の出所・本人・立場を取り、公的活動の記述付き許可h7dを返す。余分な引数を切り捨てない。',
        'h7j': '同じ三つの引数順で、私的活動の記述付き禁止の存在h7eを返す。',
        'h7m': '評価側の出所が規制者にその職務で、指定した規範の出所・本人・立場に対してh7iの許可状態を実現するよう要求する。外側と内側の出所・人・立場を分け、許可状態を実行評価しない。',
        'h7n': '評価側の出所が規制者にその職務で、指定した内側の出所・本人・立場についてh7jの制限状態を許可する。実際の制限や、制限せよという要求は含まない。',
        'h7o': 'h7mの要求があり、同じ内側の出所・本人・立場に対するh7iの許可状態が現在成立していない。',
        'h7p': '同じ列を取る規範関係で、二引数の行為実行記述h7hへの、反対要求と衝突しない許可を表す。引数の個数ごとに基本関係を増やす必要がないことを示す接続。'})
    basis['unresolved'] += LIMITS + [
        '旧df/dgに相当する著者側の要求と制限への許可を、記述と束縛を保持するh7m/h7nへ接続した。評価側の出所や規制者の具体的な人物・制度は原文から補っていない。',
        'h7i/h7jは空・過不足のある列を成立させない。順序を誤った同じ長さの列は別の政策対象であり、意味上の役割の正当性は対象の規約と解釈に依存する。',
        'h7dの全称条件は該当する活動がない場合も成立する。外側の要求h7mだけから公的活動の実例の存在は導かない。',
        '常に・しばしば・非常に狭く・啓蒙を特に妨げずにという時間・頻度・程度・留保、権利保障や基本概念、原文全体の意味一致は未完。',
        'h7pと以前の行為別規範は対応する解釈を与えれば比較できるが、原始関係h7k/h7lをh7a/h7bへ自動同一化する規則は追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'policy-norms'), (source_composed, 'kant-policy-norms')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored policy norms differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Parameterized action and policy norms share one target representation')


if __name__ == '__main__':
    main()
