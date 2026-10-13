"""Check tolerable losses against independently enumerated intervention solutions."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, SequenceValue
from noema.description_templates import apply_description
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.policy_descriptions import close_policy_description
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.compose_bounded_hindrance import ROOT, PARENT, LIBRARY, EQUATIONS, SCORE, generic_composed, source_composed

REPORT = ROOT / 'reports/bounded-hindrance-v1.json'
STATE_SORT = {'kind': 'function', 'parameters': ['individual'], 'result': 'truth'}
VARIABLES = ('x', 'y')
ASSIGNMENTS = tuple(product((False, True), repeat=2))
SCENES = ('offlow', 'offhigh', 'onlow', 'onhigh')


def state_index(state):
    return 2 * int(state('x')) + int(state('y'))


def primitives(table, scores, tolerance):
    return {**arithmetic(),
        'za': lambda: FunctionValue(('individual', STATE_SORT), 'truth',
            lambda variable, state: False if variable == 'x' else table[state_index(state)]),
        'zb': lambda: 'x',
        'zc': lambda: FunctionValue((STATE_SORT,), 'number', lambda state: Fraction(scores[state_index(state)])),
        'zd': lambda: Fraction(tolerance), 'zxv': lambda: SequenceValue(VARIABLES, '"individual"')}


def finite_checks():
    extra = 'r za[] ' + EQUATIONS + '.r zb[] a.r zc[] ' + SCORE + '.r zd[] b.r zxv[] j[a].\n'
    extra += 'q[k ree[k zxv[] k za[] k zb[]]].' + ''.join('q[k ' + name + '[k zxv[] k za[] k zb[] k zc[] k zd[]]].' for name in ('ref', 'reg', 'reh'))
    doc = parse(generic_composed()[0] + extra)
    def run(table, scores=(0, 1, 0, 1), tolerance=0, variables=VARIABLES, domain=VARIABLES):
        model = primitives(table, scores, tolerance)
        model['zxv'] = lambda: SequenceValue(tuple(variables), '"individual"')
        return values(doc, model, domain, SCENES)
    count = 0
    for table in product((False, True), repeat=4):
        off = [i for i, (x, y) in enumerate(ASSIGNMENTS) if not x and y == table[i]]
        on = [i for i, (x, y) in enumerate(ASSIGNMENTS) if x and y == table[i]]
        for scores in ((0, 1, 0, 1), (0, 0, 0, 0), (0, 0, -1, -1), (10, 20, 10, 20)):
            for tolerance in (-1, 0, Fraction(1, 2), 1, 10):
                both = bool(on and off)
                possible = tolerance >= 0 and any(scores[a] + tolerance >= scores[b] for a in on for b in off)
                harmful = tolerance >= 0 and any(scores[a] + tolerance < scores[b] for a in on for b in off)
                expected = [both, possible, harmful, tolerance >= 0 and both and not harmful]
                observed = run(table, scores, tolerance)
                if observed != expected:
                    raise ValueError('Noema and independent outcome comparison differ')
                count += 1
    negative = (True, True, False, False)
    contrasts = {}
    for name, table, scores, tolerance, expected in (
        ('large_loss', negative, (0, 1, 0, 1), 0, [True, False, True, False]),
        ('exact_boundary', negative, (0, 1, 0, 1), 1, [True, True, False, True]),
        ('below_boundary', negative, (0, 1, 0, 1), Fraction(1, 2), [True, False, True, False]),
        ('small_loss_while_both_progress', negative, (9, 10, 9, 10), 2, [True, True, False, True]),
        ('no_progress_on_either_side', (False,) * 4, (0, 1, 0, 1), 0, [True, True, False, True]),
        ('regression_but_bounded', negative, (-2, -1, -2, -1), 2, [True, True, False, True]),
        ('improvement', (False, False, True, True), (0, 1, 0, 1), 0, [True, True, False, True]),
        ('multiple_mixed', (False, True, False, True), (0, 1, 0, 1), 0, [True, True, True, False]),
        ('no_solutions', (True, False, True, False), (0, 1, 0, 1), 1, [False] * 4),
        ('no_on_solutions', (False, False, True, False), (0, 1, 0, 1), 1, [False] * 4),
        ('no_off_solutions', (True, False, False, False), (0, 1, 0, 1), 1, [False] * 4),
        ('negative_tolerance', negative, (0, 1, 0, 1), -1, [True, False, False, False]),
        ('shifted_origin', negative, (100, 101, 100, 101), 1, [True, True, False, True]),
        ('scaled_with_tolerance', negative, (0, 10, 0, 10), 10, [True, True, False, True]),
        ('scaled_without_tolerance', negative, (0, 10, 0, 10), 1, [True, False, True, False]),
    ):
        actual = run(table, scores, tolerance)
        if actual != expected:
            raise ValueError('Bounded effect contrast differs: ' + str((name, actual)))
        contrasts[name] = actual
    scope_cases = {}
    for name, variables, domain, expected in (
        ('empty', (), VARIABLES, [False] * 4),
        ('factor_absent', ('y',), VARIABLES, [False] * 4),
        ('duplicate', ('x', 'y', 'x'), VARIABLES, [False] * 4),
        ('sixteen_individuals_two_variables', VARIABLES, (*VARIABLES, *(str(i) for i in range(14))), [True, True, False, True]),
    ):
        actual = run(negative, tolerance=1, variables=variables, domain=domain)
        if actual != expected:
            raise ValueError('Causal variable scope differs: ' + str((name, actual)))
        scope_cases[name] = actual
    return {'binary_table_score_tolerance_cases': count, 'contrasts': contrasts, 'scope_cases': scope_cases}


def quoted(name, reference=False):
    body = {'kind': 'function_ref' if reference else 'call', 'symbol': name}
    if not reference:
        body['arguments'] = []
    return {'kind': 'quote', 'body': body}


def source_checks():
    text, basis = source_composed()
    extra = ('r za[] ' + EQUATIONS + '.r zb[] a.r zc[] ' + SCORE + '.r zd[] b.'
        'r zxv[] j[a].r ze[] h[h[a] c] d.r zf[] d.r zq[d] c.d zp[] e[b point[k zq[v point]]].'
        'r zxa[] a.r zxb[] a.r zxc[] a.r zxd[] a.r zxe[d] j[a].r zxf[d] b.r zxg[b] c.'
        'r zxh[] j[d].r zxi[d] b.r zxj[] b.r zxk[b] c.')
    base = candidate(text, extra)
    target = close_policy_description(base, quoted('hzf', True), [quoted(name) for name in ('zp', 'zxv', 'za', 'zb', 'ze', 'zc', 'zd')])
    syntax = json.dumps(target['body'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    expressions = candidate(text, extra + 'q[k hze[k zp[] k zxv[] k za[] k zb[] k ze[]]].q[t[k hzf[k zp[] k zxv[] k za[] k zb[] k ze[] k zc[] k zd[]]][k zf[]]].')['statements']
    permission = {'kind': 'ask', 'body': {'kind': 'call', 'symbol': 'hza',
        'arguments': [quoted('zb')['body']] * 3 + [target, quoted('zf')['body']]}}
    doc = {**base, 'statements': [*expressions, permission]}
    def run(variant='baseline', only_permission=False):
        selected = {**doc, 'statements': [permission]} if only_permission else doc
        model = guarded(selected)
        model.update(zb=lambda: 'x', zf=lambda: 'offlow' if variant == 'not_actual' else 'onlow',
            h7l=lambda source, person, role, desc, bindings, sign, context: variant != 'not_permitted'
                and (source, person, role, desc.syntax, bindings.items, sign) == ('x', 'x', 'x', syntax, (), True))
        if not only_permission:
            table = (False,) * 4 if variant == 'no_progress' else (True, False, True, False) if variant == 'no_solution' else (True, True, False, False)
            model.update(primitives(table, (0, 1, 0, 1), 0 if variant == 'large_harm' else 1))
            model['ze'] = lambda: FunctionValue((STATE_SORT,), 'situation', lambda state:
                'offlow' if variant == 'wrong_worlds' else SCENES[state_index(state)])
            model['zq'] = lambda point: point.startswith('off') if variant == 'opposite_policy' else (
                point.endswith('high') if variant == 'unrelated_policy' else point.startswith('on'))
            if variant == 'unknown_score':
                model['zc'] = guarded(selected)['zc']
            if variant == 'unknown_policy':
                model['zq'] = guarded(selected)['zq']
        return values(selected, model, VARIABLES, SCENES)
    contrasts = {}
    for name, expected in (
        ('baseline', [True, True, True]), ('large_harm', [True, False, True]),
        ('not_actual', [True, False, True]), ('not_permitted', [True, True, False]),
        ('no_progress', [True, True, True]), ('no_solution', [False, False, True]),
        ('wrong_worlds', [False, False, True]), ('opposite_policy', [False, False, True]),
        ('unrelated_policy', [False, False, True]),
    ):
        actual = run(name)
        if actual != expected:
            raise ValueError('Policy/model correspondence differs: ' + str((name, actual)))
        contrasts[name] = actual
    if run(only_permission=True) != [True]:
        raise ValueError('Describing conditional permission evaluated its target')
    for variant in ('unknown_score', 'unknown_policy'):
        try:
            run(variant)
        except ValueError as exc:
            if 'Unrelated primitive' not in str(exc):
                raise
        else:
            raise ValueError('Unknown comparison became no harm')
    # Nest the actual frequency template, not only the smaller test policy.
    # The hypothetical model's individual domain is deliberately not used to
    # claim finite verification of every full social-policy counterfactual.
    frequency = apply_description(base, quoted('h77', True), [quoted(name, reference) for name, reference in (
        ('zxa', False), ('zxb', False), ('zxc', False), ('zxd', False), ('zxe', True), ('zxf', True),
        ('zxg', True), ('zxh', False), ('zxi', True), ('zxj', False), ('zxk', True))])
    qualified = close_policy_description(base, quoted('hzf', True),
        [frequency, *[quoted(name) for name in ('zxv', 'za', 'zb', 'ze', 'zc', 'zd')]])
    nested_permission = {**permission, 'body': {**permission['body'],
        'arguments': permission['body']['arguments'][:3] + [qualified, quoted('zf')['body']]}}
    nested_doc = {**base, 'statements': [nested_permission]}
    nested_model = guarded(nested_doc)
    expected_syntax = json.dumps(qualified['body'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    nested_model.update(zb=lambda: 'x', zf=lambda: 'onlow',
        h7l=lambda source, person, role, desc, bindings, sign, context:
            desc.syntax == expected_syntax and bindings.items == () and sign)
    if values(nested_doc, nested_model, VARIABLES, SCENES) != [True]:
        raise ValueError('Actual frequency target could not be nested under its hindrance condition')
    normalized = parse(format_graph(doc))
    for notation in ('full', 'compact'):
        form = format_graph(normalized, notation)
        if parse(form) != normalized or parse(decode(encode(form, 'v2'))) != normalized:
            raise ValueError('Qualified permission description roundtrip differs')
    return {'contrasts': contrasts, 'permission_does_not_evaluate_policy_or_comparison': True,
        'unknown_score_and_policy_refused': True, 'qualified_policy_description_roundtrips': True,
        'nested_frequency_target_typechecked_without_evaluation': True,
        'progress_measure_grounding_complete': False}


def alignment():
    old = json.loads((ROOT / 'reports/closed-policies-v1.json').read_text(encoding='utf-8'))['alignment']
    row = dict(old['segments'][0])
    row['definitions'] = ['hze', 'hzf', 'red', 'reh']
    row['review_ja'] = '同じ政策と介入要因の対応を検査し、制限の有無による全解の尺度低下に許容上限を設けた候補。進歩の実現とは区別する。尺度の啓蒙への接続、原文の適切な許容基準と意味一致は未完。'
    return {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'bounded-hindrance'), (source_composed, 'kant-bounded-hindrance')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored bounded hindrance differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Bounded hindrance roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    declarations = {row['name']: row for row in doc['declarations']}
    if any(declarations.get(row['name']) != row for row in parse((ROOT / LIBRARY).read_text(encoding='utf-8'))['declarations']):
        raise ValueError('Existing scoped intervention library changed')
    paths = [*documents, PARENT, LIBRARY, 'data/bounded-hindrance-basis-v1.json', 'data/kant-bounded-hindrance-basis-v1.json',
        'scripts/compose_bounded_hindrance.py', 'scripts/check_bounded_hindrance.py', 'reports/closed-policies-v1.json',
        'noema/policy_descriptions.py', 'noema/finite_semantics.py', 'noema/discourse.py']
    return json.loads(json.dumps({'status': 'partial_model_relative_bounded_hindrance_not_complete_progress_clause',
        'documents': documents, 'finite': finite_checks(), 'source': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_and_scoped_library_preserved': True, 'new_source_assertions': 0, 'new_primitives': 0,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Bounded hindrance report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Intervention losses, solution existence and qualified policy targets checked')


if __name__ == '__main__':
    main()
