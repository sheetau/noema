"""Keep a directed reformulation separate from truth and Boolean negation."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-prescription-mentions.noema'
DESCRIPTION = 'i[h[a a a] e]'


def definitions():
    return '''
r rbf[a a DESC DESC d] c.
d rbg[node a author a earlier DESC replacement DESC context d] c[
 w[u[e[v earlier][v replacement]]][k rbf[v node v author v earlier v replacement v context]]
].
'''.replace('DESC', DESCRIPTION)


def generic_composed():
    doc = parse('n:\n' + definitions())
    declaration = doc['declarations'][0]
    basis = {'version': 'reformulations-basis-v1', 'document': 'examples/v014/reformulations.noema',
        'primitives': [{'symbol': 'rbf', 'parameters': declaration['parameters'], 'result': declaration['result'],
            'arguments': ['node', 'author', 'earlier_description', 'replacement_description', 'context'],
            'meaning_ja': '著者がこの談話箇所・文脈で、先の三項関係の記述を言い直し、後の記述をより適切な表現として採る。両記述の三つの引数位置は同じ対象を保つ。先の内容の偽、後の内容の現実の真、論理的な否定関係、第三者による同意は含まない。'}],
        'definitions': {'rbg': '二つの三項関係の記述が異なり、先の記述から後の記述へ向きのある言い直しがある。同じ記述の反復、選言、両内容の同時成立とは区別する。'},
        'unresolved': [
            '言い直しを採用する談話関係は意味規約として与える。より適切であること自体を客観的に証明した関係ではない。',
            'ここでは三つの対象の位置を持つ性質記述を扱う。同じ型の別の話題にも使えるが、任意の引数型・個数を一つの多相関係として扱う構文は追加していない。',
            '記述の違いは正規化した構文に基づく。意味上の同義性や、訂正・限定・強調の全ての語用論を判定する処理ではない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions() + '''
r hh2[a a d] c.r hi2[a a a d] c.r hj2[a c d] c.r hk2[] a.
d hm2[person a faculty a act a] e[b context[w[k hh2[v faculty v person v context]][w[
 k hi2[v person v faculty v act v context]
][k hj2[v act e[v act][v act] v context]]]]].
d hn2[person a faculty a act a] e[b context[w[k hh2[v faculty v person v context]][w[
 k hi2[v person v faculty v act v context]
][k hj2[v act u[e[v act][v act]] v context]]]]].
d ho2[] c[k rbg[k hk2[] k wa[] r[p hm2] r[p hn2] k wh[]]].
''')
    doc['statements'] = statements + [{'kind': 'assert', 'body': {'kind': 'call', 'symbol': 'ho2', 'arguments': []}}]
    basis = deepcopy(json.loads((ROOT / 'data/kant-prescription-mentions-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-reformulations-basis-v1', document='examples/v014/kant-reformulations.noema')
    generic = generic_composed()[1]
    basis['primitives'] += generic['primitives']
    basis['definitions'].update(generic['definitions'])
    declarations = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('hh2', ['faculty', 'person', 'context'], 'この能力が、この人自身に自然に備わる能力として文脈で位置付けられる。理解力だけへ限定せず、後天的な技能の全てや、遺伝的な決定性とも同一視しない。自然的な資質の基礎説明は未完。'),
        ('hi2', ['person', 'faculty', 'act', 'context'], '本人がこの同じ能力を、この同じ行為において使用する。所有や能力の有無だけでは成立せず、別の能力の使用を混ぜない。使用の合理性や適切さは別の条件である。'),
        ('hj2', ['act', 'positive', 'context'], '同じ使用行為に対するこの文脈の評価。positiveが真なら合理的な使用として、偽なら誤用として評価される。二分類は互いの論理的否定ではなく、それぞれ明示的な評価を要する。合理性・適切な用途・誤用の基礎説明は未完。'),
        ('hk2', [], '第三段落で能力の使用を誤用と言い直す談話箇所。実際の使用行為そのものとは区別する。'),
    ):
        d = declarations[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update({
        'hm2': '同じ本人に自然に備わる同じ能力を同じ行為で使い、その行為が合理的な使用として評価されるという三項の内容。',
        'hn2': '同じ本人・能力・行為を保ち、その使用が誤用として評価されるという三項の内容。hm2の単純な否定ではなく、能力の帰属と使用を積極的に要求する。',
        'ho2': '著者がこの箇所でhm2の記述をhn2へ言い直す。両内容を実行せず、使用行為や資質の実在をこの主張だけから確定しない。'})
    basis['unresolved'] += generic['unresolved'] + [
        'oder vielmehrを、先の言い方から後の言い方への方向を持つ表現修正として読む。先の内容が必ず偽で、後がその否定であるという読みは加えない。',
        'Naturgabenを理解力だけへ縮めず、自然的な能力の帰属をhh2で分ける。ただし生得・発達・学習・自然の語義全体を説明し終えたとはしない。',
        '合理的使用と誤用は文脈の評価としてhj2に分けた。使用目的・評価基準の構成と根拠、道具としての働き、機械的な適用、足枷と持続への接続は残る。',
        '追加主張は著者による言い直しの帰属一件だけであり、hm2やhn2の実際の成立を断言する主張ではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, name in ((generic_composed, 'reformulations'), (source_composed, 'kant-reformulations')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + name + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored reformulation differs')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Directed reformulation preserves actor, faculty and use-event positions')


if __name__ == '__main__':
    main()
