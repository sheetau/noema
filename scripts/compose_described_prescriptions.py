"""Retain a conditional prescription's syntax independently of its truth."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-linked-draft.noema'
PARAMS = 'rule a source a person a role a condition i[h[a] e] goal i[h[a] e] positive c context d holding h[a a d] c'
ARGS = 'v rule v source v person v role v condition v goal v positive v context v holding'


def definitions():
    return '''
r rba[a a a i[h[a] e] i[h[a] e] c d] c.
d rbb[PARAMS] c[w[k rba[v rule v source v role v condition v goal v positive v context]][w[
 c[v holding][v person v role v context]
 ][
 t[c[s[v condition]][v person]][v context]
]]].
d rbc[PARAMS] c[w[k rbb[ARGS]][z[t[c[s[v goal]][v person]][v context]][v positive]]].
d rbd[PARAMS] c[w[k rbb[ARGS]][u[z[t[c[s[v goal]][v person]][v context]][v positive]]]].
d rbe[rule a] e[b context[g source a[g role a[g condition i[h[a] e][g goal i[h[a] e][g positive c[
 k rba[v rule v source v role v condition v goal v positive v context]
]]]]]]].
'''.replace('PARAMS', PARAMS).replace('ARGS', ARGS)


def generic_composed():
    doc = parse('n:\n' + definitions())
    primitive = doc['declarations'][0]
    basis = {'version': 'described-prescriptions-basis-v1', 'document': 'examples/v014/described-prescriptions.noema',
        'primitives': [{'symbol': 'rba', 'parameters': primitive['parameters'], 'result': primitive['result'],
            'arguments': ['rule', 'source', 'role', 'condition_description', 'goal_description', 'positive', 'context'],
            'meaning_ja': 'この出所が、この規則を、この立場で条件に該当する人に記述された目標を満たすよう求める規定として、この文脈で採用している。positiveが偽なら同じ目標の不成立を求める。条件と目標は人から命題内容への式の記述で保持する。採用・要求の存在は、正当性、能力、実現、普遍的な道徳的義務を意味しない。'}],
        'definitions': {
            'rbb': '同じ規則・出所・立場・条件記述・目標記述・肯否の規定があり、本人が評価する同じ立場にあり、その条件が本人について現在成立する。規則の存在、立場、条件の成立を別々に要求する。',
            'rbc': 'rbbが成立し、その同じ本人について目標の真偽が規定の肯否と一致する。現在状況での遵守条件であり、将来の期限や達成過程を補わない。',
            'rbd': 'rbbが成立し、その同じ本人について目標の真偽が規定の肯否と一致しない。未適用・未記録・責任や罰の認定とは区別する。',
            'rbe': '出所・立場・人についての条件と目標の記述・肯否を持ち、それらを結ぶ規定として採用されているもの。採用された条件付き規則の構造を表し、条件に合う人や実現した目標の存在は要求しない。'},
        'unresolved': [
            '規範的な採用・要求は基本関係rbaの意味規約であり、その社会的な成立過程や正当性を一般理論から定義したものではない。',
            '記述を同じ真理値の別記述へ置き換えない。採用された規則があることと、条件が成立して適用されることを分ける。',
            '違反は確定した真偽に基づく評価であり、証拠の不在を目標の偽へ変換しない。期限・例外・優先順位・制裁・能力・責任は別途記述する。',
            'rbbからrbdは脱引用を含むため、現行版ではその定義をさらに記述として引用できない。rbaとrbeは内容を実行せず参照できる。',
            'rbeは式記述の全領域に存在量化する。有限検査器はこの領域を列挙できず、既知の少数の式だけで代用しない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions() + 'd hd2[rule a] e[k rbe[v rule]].')
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-linked-draft-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-described-prescriptions-basis-v1', document='examples/v014/kant-described-prescriptions.noema')
    generic = generic_composed()[1]
    basis['primitives'] += generic['primitives']
    basis['definitions'].update(generic['definitions'])
    basis['definitions']['hd2'] = '第三段落のSatzungenについて、採用された条件付きの規定というrbeの構造を与える読解候補。文言の固定性・制定の機構・一般的な拘束性を説明し終えたものではない。Formelnや機械的使用、足枷の比喩とはまだ結ばない。'
    basis['unresolved'] += generic['unresolved'] + [
        'Satzungenへの接続は規定としての構造だけを与える部分的な読解候補であり、名詞全体の意味確認ではない。特定の出所・役割・条件・目標を原文へ補わない。',
        'Formeln、mechanischen Werkzeuge、自然的な能力の使用と誤用、足枷の比喩と持続への因果は未記述。今回これらの句を対応済み範囲として追加しない。',
        '新しい本文の主張は追加しない。hd2を対象とする集団・比喩・前後の推論は次の接続課題である。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, name in ((generic_composed, 'described-prescriptions'), (source_composed, 'kant-described-prescriptions')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + name + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored described prescription differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Prescribed condition and goal descriptions retained independently of truth')


if __name__ == '__main__':
    main()
