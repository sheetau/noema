"""Retain the described factors of an explanation without equating truth profiles."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
r ea[a i[h[a] e] a i[h[a] e] d] c.
d eb[factorobject a factor i[h[a] e] effectobject a effect i[h[a] e] scene d] c[
  w[t[c[s[v factor]][v factorobject]][v scene]][t[c[s[v effect]][v effectobject]][v scene]]
].
d ec[factorobject a factor i[h[a] e] effectobject a effect i[h[a] e] scene d] c[
  w[k ea[v factorobject v factor v effectobject v effect v scene]][k eb[v factorobject v factor v effectobject v effect v scene]]
].
d ed[person a selected i[h[a] e] excluded i[h[a] e] effect i[h[a] e] scene d] c[
  w[k ea[v person v selected v person v effect v scene]][u[k ea[v person v excluded v person v effect v scene]]]
].
'''


def generic_composed():
    doc = parse('m:\n' + definitions())
    primitive = next(d for d in doc['declarations'] if d['name'] == 'ea')
    basis = {'version': 'described-explanations-basis-v1', 'document': 'examples/v013/described-explanations.noema',
        'primitives': [{'symbol': 'ea', 'parameters': primitive['parameters'], 'result': 'truth',
            'arguments': ['factor_subject', 'factor_description', 'effect_subject', 'effect_description', 'context'],
            'meaning_ja': '指定した文脈の説明で、第一対象についての要因の記述を、第二対象についての結果の記述の原因として採用する関係。記述はNoemaの性質定義を指す。両内容が同時に真であることや現実の因果関係の成立は、この関係だけからは従わない。'}],
        'definitions': {
            'eb': '二つの性質記述をそれぞれの対象へ適用し、両内容が指定状況で成立する。原因としての採用は含まない。',
            'ec': 'eaによる原因説明への採用とebによる両内容の成立をともに要求する。それでも介入効果や因果機構の証明ではない。',
            'ed': '同じ対象と結果記述について、選択した要因記述は原因説明に採用し、除外した要因記述は採用しない。内容の成立を評価しない。'},
        'unresolved': ['基本関係eaは原因説明への採用の意味規約であり、原因を発見するアルゴリズムや実在の因果関係の一般理論ではない。',
            '記述の同一性は既存の正規化した構文の同一性である。異なる別名が同じ因果機構を指すかを自動判定しない。',
            'ebとecは脱引用を含むので、現行0.13の制約ではこれらを参照した式をさらに引用できない。edにはこの制約を持ち込まない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v013/kant-contextual-ability.noema').read_text(encoding='utf-8'))
    base = deepcopy(doc)
    base['statements'], base['declarations'] = [], []
    for declaration in doc['declarations']:
        if declaration['name'] == 'bd':
            text = format_graph(base, 'compact') + '\n' + definitions() + '''
d bj[person a] e[b scene[u[k ak[v person v scene]]]].
d bq[person a] e[b scene[u[k ai[v person v scene]]]].
d br[person a] e[b scene[u[k aj[v person v scene]]]].
d bs[person a] e[b scene[w[t[k bq[v person]][v scene]][t[k br[v person]][v scene]]]].
d bd[person a scene d] c[w[k bc[v person v scene]][k ed[v person r[p bs] r[p bj] r[p bf] v scene]]].
'''
            base = parse(text)
        else:
            base['declarations'].append(deepcopy(declaration))
    base['statements'] = doc['statements']
    text = format_graph(base, 'compact') + '\n'
    basis = deepcopy(json.loads((ROOT / 'data/kant-contextual-ability-basis-v1.json').read_text(encoding='utf-8')))
    generic = generic_composed()[1]
    basis.update(version='kant-described-explanations-basis-v1', document='examples/v013/kant-described-explanations.noema')
    basis['primitives'] += generic['primitives']
    basis['definitions'].update(generic['definitions'])
    basis['definitions'].update({
        'bj': 'その人について、問題となる行為に必要な理解能力が十分でないという内容。',
        'bq': 'その人について、問題となる行為への決意が十分でないという内容。',
        'br': 'その人について、問題となる行為への勇気が十分でないという内容。',
        'bs': 'bqとbrがともに成立する内容。先行草案の論理積による読みを保持し、要因の記述を一つの定義として参照できるようにした。',
        'bd': 'bcの未成熟にあり、原因説明では決意と勇気の不足bsを採用し、理解能力の不足bjを採用しない。真偽が同じでも二つの要因記述を同一化しない。'})
    basis['unresolved'] += generic['unresolved'] + [
        'この文書のbdは旧ahの内容値による説明からeaの記述参照へ移した。旧宣言ahは以前の条件との比較のため保持するが、bdからは使わない。',
        'bsは決意不足と勇気不足の論理積という先行草案の読みを保持する。原文の不足の作用範囲の解釈は未確定。',
        '原因を説明に採用することと、原因の発見・実在・責任の規範的判定を区別する。今回の記述参照だけでは後者を確立しない。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    for compose, filename in ((generic_composed, 'data/described-explanations-basis-v1.json'),
                              (source_composed, 'data/kant-described-explanations-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored described explanation differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Explanation factors retain descriptions independently of truth values')


if __name__ == '__main__':
    main()
