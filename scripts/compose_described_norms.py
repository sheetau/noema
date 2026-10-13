"""Keep action and description identity in normative targets."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, app, op, both, call, definition

PARENT = 'examples/v014/kant-public-use-link.noema'
DESCRIPTION = 'i[h[a a] e]'
RULE = 'h[a a a a ' + DESCRIPTION + ' c d] c'
PARAMS = 'source a person a role a activity a description ' + DESCRIPTION + ' polarity c context d required ' + RULE + ' allowed ' + RULE
TRUE = 'e[n p a b][n p a b]'


def definitions():
    fields = [v(n) for n in ('source', 'person', 'role', 'activity', 'description')]
    rule = lambda name, polarity: app(v(name), *fields, polarity, v('context'))
    sign = v('polarity')
    positive = rule('required', sign)
    opposed = rule('required', op('u', sign))
    permitted = rule('allowed', sign)
    actual = op('t', app('s[v description]', v('person'), v('activity')), v('context'))
    return ''.join(definition(name, PARAMS, body) for name, body in (
        ('rdm', both(permitted, op('u', opposed))),
        ('rdn', both(positive, opposed)),
        ('rdo', both(permitted, opposed)),
        ('rdp', op('u', opposed)),
        ('rdq', both(positive, op('u', op('e', actual, sign))))))


MEANINGS = {
    'rdm': '同じ出所・人・立場・行為・記述・評価文脈について、指定極性を積極的に許可し、反対極性を要求しない。真は記述された実行、偽はその不実行を対象にする。',
    'rdn': '同じ指定対象と文脈について、実行と不実行の両方を要求する規範上の衝突。別の行為や記述の要求を混ぜない。',
    'rdo': '指定極性への許可と、同じ対象の反対極性への要求が併存する。',
    'rdp': '指定極性と反対の要求がない。指定極性への積極的な許可や実行を意味しない。',
    'rdq': '指定極性への要求があり、同じ記述を同じ人・行為へ適用した現在の実行状態がその極性と一致しない。未履行の判定であり責任や制裁は含まない。',
}
LIMITS = [
    '記述はNoemaで定義した人・行為から内容への関数を指し、原語文字列を保存しない。行為と記述の両方を固定し、真偽が同じだけの別対象へ規範を移さない。',
    '極性は真ならその記述の成立、偽なら不成立である。許可しないことと不実行を要求することを同一視しない。反対極性の許可は矛盾ではなく、両方を選べる場合を許す。',
    '同じ記述に対する規範を判定する操作的な関係であり、別の記述間の含意に沿った規範推論、優先順位、例外、規範の正当性は未記述。別名の同義性も自動判定しない。',
    'rdm〜rdpは記述された内容を実行評価しない。rdqだけは未履行を判定するため脱引用を行うので、現行の引用制約によりrdqを含む式を引用の内部へ入れられない。',
]


def generic_composed():
    doc = parse('n:\n' + definitions())
    basis = {'version': 'described-norms-basis-v1', 'document': 'examples/v014/described-norms.noema',
        'primitives': [], 'definitions': MEANINGS, 'unresolved': LIMITS}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-public-use-link-basis-v1.json').read_text(encoding='utf-8')))
    mapping = basis['role_linkage']['symbols']['roles']
    statements, doc['statements'] = doc['statements'], []
    extra = 'r h7a[a a a a ' + DESCRIPTION + ' c d] c.r h7b[a a a a ' + DESCRIPTION + ' c d] c.\n'
    desc = 'r[p ' + mapping['dc'] + ']'
    names = ('person', 'activity', 'role', 'audience', 'channel', 'subject', 'description', 'context')
    params = 'person a activity a role a audience a channel a subject a description i[h[a] f] context d authority a'
    extra += definition('h7c', params, both(call('h6v', *(v(n) for n in names)),
        call('rdm', v('authority'), v('person'), v('role'), v('activity'), desc, TRUE, v('context'), 'p h7a', 'p h7b')))
    extra += '''d h7d[source a person a role a] e[b context[f activity a[y[
 k ''' + mapping['da'] + '''[v person v activity v role v context]
][k rdm[v source v person v role v activity ''' + desc + ' ' + TRUE + ''' v context p h7a p h7b]]]]].
d h7e[source a person a role a] e[b context[g activity a[w[
 k ''' + mapping['db'] + '''[v person v activity v role v context]
][k h7a[v source v person v role v activity ''' + desc + ' u[' + TRUE + '''] v context]]]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis.update(version='kant-described-norms-basis-v1', document='examples/v014/kant-described-norms.noema')
    for name, meaning in (
        ('h7a', '指定の出所が、その人・立場・行為について、同じ実行記述の指定極性を満たすよう要求する。真は実行、偽はその不実行への要求。現実の実行や正当性とは区別する。'),
        ('h7b', '指定の出所が、その人・立場・行為について、同じ実行記述の指定極性を積極的に許可する。要求の不在や実行可能性とは区別する。')):
        row = next(row for row in doc['declarations'] if row['name'] == name)
        basis['primitives'].append({'symbol': name, 'parameters': row['parameters'], 'result': row['result'],
            'arguments': ['source', 'person', 'role', 'activity', 'execution_description', 'polarity', 'context'], 'meaning_ja': meaning})
    basis['definitions'].update(MEANINGS)
    basis['definitions'].update({
        'h7c': 'h6vで同じ公的活動・宛先・提供内容を固定し、本人・立場・活動と旧dcの実行記述に対して、rdmによる積極的な実行許可がある。旧h6yの内容値による許可に代わる、記述と行為を保持した接続。',
        'h7d': 'その人・立場で公的使用に分類される全活動について、同じ活動と実行記述への積極的な許可があり、不実行の要求と衝突しないという内容。該当する活動がない場合は全称として成立し、自由の実例の存在を補わない。',
        'h7e': 'その人・立場で私的使用に分類される活動のうち、同じ活動と実行記述について不実行を要求されるものがあるという内容。公的活動の禁止や、許可の単なる不在を代用しない。'})
    basis['unresolved'] += LIMITS + [
        '旧h6yおよび旧dd/deに相当する内容値方式は比較用に保持し、新しい接続にはh7c/h7d/h7eを用いる。既存の宣言と主張を黙って置き換えない。',
        '実行を指す同じ記述と極性を使うことで、同じ状況真偽を持つ別の行為を区別する。別名で記述された同じ現実の活動に規範がどう適用されるかは未解決。',
        '公的使用の自由を実現せよという著者側の要求、制限することへの許可、常に・しばしば・程度・留保を新しい記述方式へ移す作業は残る。今回のh7d/h7eをその全意味と同一視しない。',
        '公衆・学識者・職務の分類と読者範囲の規約、原文との意味一致は未完。新たな実際の許可・禁止を本文主張へ追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'described-norms'), (source_composed, 'kant-described-norms')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored described norms differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Normative targets retain action, description and polarity')


if __name__ == '__main__':
    main()
