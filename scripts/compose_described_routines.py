"""Keep a repeatable formulation, its instance, use and examination distinct."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-use-standards.noema'
PATTERN = 'i[h[a] e]'
BASE_PARAMS = f'person a form a act a pattern {PATTERN} argument i[a] instance i[e] context d'
FUNCTIONS = f'stored h[a {PATTERN} d] c use h[a a a d] c applied h[a i[e] a d] c'
REVIEW = 'judgments h[a a d] c matters h[a a d] c reviews h[a a d] c'
ARGS = 'v person v form v act v pattern v argument v instance v context'


def definitions():
    return f'''
r rbo[{PATTERN} i[a] i[e]] c.
d rbp[form a pattern {PATTERN} argument i[a] instance i[e] context d stored h[a {PATTERN} d] c] c[
 w[c[v stored][v form v pattern v context]][k rbo[v pattern v argument v instance]]
].
d rbq[{BASE_PARAMS} {FUNCTIONS}] c[w[
 k rbp[v form v pattern v argument v instance v context v stored]
][w[c[v use][v person v form v act v context]][c[v applied][v person v instance v act v context]]]].
d rbr[{BASE_PARAMS} {FUNCTIONS} {REVIEW}] c[w[
 k rbq[{ARGS} v stored v use v applied]
][u[g judgment a[w[c[v judgments][v person v judgment v context]][w[
 c[v matters][v judgment v form v context]
][c[v reviews][v judgment v act v context]]]]]]].
d rbs[form a context d stored h[a {PATTERN} d] c] c[g pattern {PATTERN}[c[v stored][v form v pattern v context]]].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    decl = doc['declarations'][0]
    basis = {'version': 'described-routines-basis-v1', 'document': 'examples/v014/described-routines.noema',
        'primitives': [{'symbol': 'rbo', 'parameters': decl['parameters'], 'result': decl['result'],
            'arguments': ['pattern_description', 'argument_description', 'instance_description'],
            'meaning_ja': '同じNoema文書の閉じた記述について、instanceがpatternの関数式をargumentの個体式へ適用した式の引用と構文上等しい。束縛変数名は正規化するが、別名展開・ベータ簡約・評価結果の一致による置換はしない。description_templates.is_description_instanceで検査できる構造関係。'}],
        'definitions': {
            'rbp': 'その定型表現が保持する同じ一項の型へ、同じ引数記述を適用して得た式の記述である。型・引数・適用例を評価せず、真偽や成功は要求しない。',
            'rbq': 'rbpの型と適用例を保ち、同じ人が同じ表現を同じ活動で使い、その具体化された記述をその活動を進めるために採っている。実際の使用は内容の真理や正当性を保証しない。',
            'rbr': 'rbqがあり、その人が同じ表現の同じ活動への適用を吟味する判断は、その文脈にはない。別の人・別の表現・別の活動についての判断を本人の吟味に数えない。',
            'rbs': '人物・事柄など一つの個体を入れる位置を持つ内容の記述を、固定した再利用可能な表現として保持するもの。全ての定型句・全ての型や引数数を尽くす分類ではない。'},
        'unresolved': [
            'rboは同じ文書の式の構造関係である。自然言語の全ての定型句をこの一項の型へ自動変換する規則ではない。',
            '表現が型を保持すること、その使用、活動への採用、適用を吟味する判断の対象関係は意味規約として引数で与える。媒体や慣習の成立、判断一般の基礎説明は残る。',
            'rbrはその活動・文脈に吟味がない条件であり、過去にも未来にも考えないこと、判断能力の欠如、無意識、自動機械、非合理性や誤用を含意しない。',
            '判断関係は確定した解釈の事実として使う。判断記録が見つからないだけで存在の否定を与えることはできない。',
            'rbsは全ての式記述に存在量化する。有限評価器で少数の式だけを候補として代用せず、評価不能を明示する。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    statements, doc['statements'] = doc['statements'], []
    extra = f'''
r hw2[a {PATTERN} d] c.r hx2[a a a d] c.r hy2[a i[e] a d] c.r hz2[a a d] c.
d h22[form a] e[b context[k rbs[v form v context p hw2]]].
d h23[{BASE_PARAMS}] c[k rbq[{ARGS} p hw2 p hx2 p hy2]].
d h24[{BASE_PARAMS}] c[k rbr[{ARGS} p hw2 p hx2 p hy2 p fa p fb p hz2]].
d h25[faculty a {BASE_PARAMS}] c[w[k hh2[v faculty v person v context]][w[
 k hi2[v person v faculty v act v context]
][k h24[{ARGS}]]]].
'''
    doc = parse(format_graph(doc, 'compact') + definitions() + extra)
    doc['statements'] = statements
    basis = deepcopy(json.loads((ROOT / 'data/kant-use-standards-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-described-routines-basis-v1', document='examples/v014/kant-described-routines.noema')
    generic = generic_composed()[1]
    basis['primitives'] += generic['primitives']
    basis['definitions'].update(generic['definitions'])
    declarations = {d['name']: d for d in doc['declarations']}
    for name, arguments, meaning in (
        ('hw2', ['form', 'pattern_description', 'context'], 'その表現は、同じ式の型として繰り返し参照して使える、固定した内容の構成を保持する。ここでは個体一つを入れる位置を持つ型を用いる。実際の反復回数や物理的な媒体を要求しない。'),
        ('hx2', ['person', 'form', 'act', 'context'], '同じ人が、この表現を同じ活動の用に供している。表現を所有・参照できるだけでは成立せず、本人の能力そのものを表現と同一視しない。'),
        ('hy2', ['person', 'instance_description', 'act', 'context'], '同じ人がその具体化された記述を、同じ活動を進めるための言い方・定め方として採っている。内容の真理、本人の同意・信念、評価の正当性や目的達成とは別に扱う。'),
        ('hz2', ['judgment', 'act', 'context'], 'この判断は、対象の表現を同じ活動に適用してよいかを吟味する判断である。何かを考えたことや、別の活動の吟味で代用しない。')):
        d = declarations[name]
        basis['primitives'].append({'symbol': name, 'parameters': d['parameters'], 'result': d['result'],
            'arguments': arguments, 'meaning_ja': meaning})
    basis['definitions'].update({
        'h22': 'Formelnについて、固定した一項の表現の型を保持するものという部分的な構成を与える。数式に限定せず、慣習的な定型句全体の語義を確定したとはしない。',
        'h23': '同じ型・引数・具体化された記述について、本人がその定型表現を同じ活動で使う。',
        'h24': 'h23の使用があり、その表現の同じ活動への適用を本人が吟味する判断はこの文脈にはない。',
        'h25': '同じ本人に自然に備わる同じ能力を同じ活動で使用し、h24の表現使用がその同じ活動にある。mechanischen Werkzeugeの一つの部分的な読みとして接続する。'})
    basis['unresolved'] += generic['unresolved'] + [
        'mechanischenを、その都度の適用の吟味なしに型を使うという部分的な読みで構成した。原文の唯一の読み、自動機械の物理、あらゆる習慣的活動の必要十分条件とはしない。',
        '規定hd2と定型表現h22の全てがこのように使われるという主張はまだない。二つの名詞の列挙、これらという指示、道具としての一般化、足枷と持続の比喩への接続は残る。',
        'h25から合理的使用hm2や誤用hn2は導かない。本文の主張は親文書のまま保持し、特定の型や具体化された活動を原文へ補わない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for builder, stem in ((generic_composed, 'described-routines'), (source_composed, 'kant-described-routines')):
        text, basis = builder()
        for path, body in ((ROOT / basis['document'], text), (ROOT / ('data/' + stem + '-basis-v1.json'),
                json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored described routines differ')
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Typed formulation instances and same-use examination composed')


if __name__ == '__main__':
    main()
