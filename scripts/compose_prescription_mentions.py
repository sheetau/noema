"""Derive quotable instances of existing prescription evaluators."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.specialization import specialize_definition
from scripts.compose_limits import ROOT

PARENT = 'examples/v014/kant-described-prescriptions.noema'
TARGETS = {'rbb': 'he2', 'rbc': 'hf2', 'rbd': 'hg2'}


def composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-described-prescriptions-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-prescription-mentions-basis-v1', document='examples/v014/kant-prescription-mentions.noema')
    bindings = {4: {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': 'bf'}},
                5: {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': 'bm'}}}
    traces = []
    for source, target in TARGETS.items():
        result = specialize_definition(doc, source, target, bindings)
        doc = result.document
        traces.append({'source': source, 'target': target, 'bound_positions': result.bound_positions,
            'condition': 'bf', 'goal': 'bm', 'expanded_definitions': result.expanded_definitions,
            'disquotations_removed': result.disquotations_removed})
    basis['definitions'].update({
        'he2': 'rbbの条件記述をbf、目標記述をbmに固定した適用条件。出所・規則・本人・立場・肯否・文脈・立場への該当関係は引数のまま保つ。そうした規定が存在するという断言ではない。',
        'hf2': '同じ固定された条件と目標についてrbcと同じ遵守条件を、既知の脱引用を展開して表す。記述として引用できるが、元の式と構文同一とは扱わない。',
        'hg2': '同じ固定された条件と目標についてrbdと同じ違反条件を表す。条件や目標が未確定の任意の規則へ適用する定義ではない。'})
    basis['specialization'] = {'derivations': traces, 'existing_quotation_rule_unchanged': True,
        'example_rule_not_attributed_to_kant': True, 'new_assertions': 0}
    basis['unresolved'] += [
        'この条件・目標の組は、引用できる規則評価を記述するために既存の性質を使った構成例である。カントがこの規定を採用した・要求したという原文対応を追加しない。',
        '特殊化は、閉じた型付き引数の代入、変数捕獲を避ける展開、既知の引用の評価を行う。基本関係の解釈は実行せず、未知の式は推測しない。',
        '任意の評価を含む式の引用、式記述全体の量化、使用・誤用や足枷の比喩、規範の社会的な基礎説明は未完のままである。',
        '値の一致は全域で純粋な解釈についての展開規則に基づく。評価順序、計算量、部分的または副作用を持つ外部関数の実行挙動まで一致させる機能ではない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = composed()
    for path, body in ((ROOT / basis['document'], text), (ROOT / 'data/kant-prescription-mentions-basis-v1.json',
            json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored prescription mention differs')
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Fixed prescription evaluators derived as quotable definitions')


if __name__ == '__main__':
    main()
