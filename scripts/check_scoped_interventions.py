"""Compare scoped causal solutions with independent Boolean enumeration."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from noema.semantics import SemanticError
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_scoped_groups import PEOPLE, source_model as group_model
from scripts.compose_scoped_interventions import ROOT, generic_composed, source_composed, FALSE, TRUE

REPORT = ROOT / 'reports/scoped-interventions-v1.json'
STATE = {'kind': 'function', 'parameters': ['individual'], 'result': 'truth'}
DOMAIN = (*PEOPLE, 'restriction', 'attempt', 'unrelated')


def values(doc, model, people, scenes=('actual',), memoize=True, budget=5_000_000):
    return [r['value'] for r in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=budget, memoize_definitions=memoize)]


def query_document():
    return parse(generic_composed()[0] + '''
r za[] j[a].r zb[a h[a] c] c.r zc[] a.r zd[] c.r ze[] a.
q[k rv[k za[] p zb i[var a][e[v var][k zc[]]] i[var a][k zd[]] i[state h[a] c][c[v state][k ze[]]]]].
q[k rv[k za[] p zb i[var a][e[v var][k zc[]]] i[var a][k zd[]] i[state h[a] c][u[c[v state][k ze[]]]]]].
q[k rw[k za[] p zb i[var a][e[v var][k zc[]]] i[var a][k zd[]] i[state h[a] c][c[v state][k ze[]]]]].
q[k rx[k za[] p zb k zc[] i[state h[a] c][c[v state][k ze[]]]]].
''')


def exhaustive_checks():
    doc, digest = query_document(), hashlib.sha256()
    assignments = [dict(zip(('x', 'y'), bits)) for bits in product((False, True), repeat=2)]
    count = 0
    for bits in product((False, True), repeat=8):
        tables = {'x': bits[:4], 'y': bits[4:]}
        def equation(variable, state):
            return tables[variable][2*int(state('x'))+int(state('y'))]
        for factor, fixed in product(('x', 'y'), (False, True)):
            target = 'y' if factor == 'x' else 'x'
            def solutions(setting):
                return [s for s in assignments if s[factor] == setting and
                        s[target] == equation(target, lambda name: s[name])]
            states, on, off = solutions(fixed), solutions(True), solutions(False)
            expected = [any(s[target] for s in states), any(not s[target] for s in states),
                bool(states) and all(s[target] for s in states),
                any(s[target] for s in off) and bool(on) and all(not s[target] for s in on)]
            model = {'za': lambda: SequenceValue(('x', 'y'), '"individual"'), 'zb': equation,
                     'zc': lambda: factor, 'zd': lambda: fixed, 'ze': lambda: target}
            result = values(doc, model, ('x', 'y', 'unrelated'))
            if result != expected:
                raise ValueError('Scoped solutions differ from independent enumeration: ' + repr((bits, factor, fixed, result, expected)))
            digest.update(json.dumps([list(bits), factor, fixed, result], separators=(',', ':')).encode('utf-8'))
            count += 1
    return {'binary_models': 256, 'intervention_cases': count,
            'both_target_truth_values_and_guarantee_match': True, 'prevention_matches': True,
            'results_sha256': digest.hexdigest()}


def scope_checks():
    text = generic_composed()[0] + '''
r za[] j[a].r zb[] b.r zc[a h[a] c] c.r zd[a] c.r ze[] a.
q[k rt[k za[]]].q[e[d[k rs[k za[]]]][k zb[]]].
q[k ru[k za[] p zc i[var a][FALSE] i[var a][FALSE] p zd]].
q[k rv[k za[] p zc i[var a][FALSE] i[var a][FALSE] i[state h[a] c][TRUE]]].
q[k rx[k za[] p zc k ze[] i[state h[a] c][FALSE]]].
'''.replace('FALSE', FALSE).replace('TRUE', TRUE)
    doc, rows = parse(text), {}
    people = ('x', 'y', *('other'+str(i) for i in range(14)))
    for name, variables, dirty in (('two_variables', ('x', 'y'), False), ('empty', (), False),
                                  ('duplicate', ('x', 'x'), False),
                                  ('nonadjacent_duplicate', ('x', 'y', 'x'), False),
                                  ('three_variables', ('x', 'y', 'other0'), False),
                                  ('outside_true', ('x', 'y'), True)):
        model = {'za': lambda: SequenceValue(variables, '"individual"'), 'zb': lambda: Fraction(2**len(variables)),
                 'zc': lambda *args: False, 'zd': lambda var: dirty and var == 'other0', 'ze': lambda: 'other0'}
        result = values(doc, model, people)
        repeated = name in ('duplicate', 'nonadjacent_duplicate')
        expected = [not repeated, True, not repeated and name != 'outside_true', not repeated, False]
        if result != expected:
            raise ValueError('Declared-variable scope differs: ' + name + repr(result))
        rows[name] = {'results': result, 'individuals': len(people), 'variables': len(variables),
                      'assignments': 2**len(variables)}
    legacy = parse((ROOT / 'examples/v012/binary-interventions.noema').read_text(encoding='utf-8') + '''
r za[a h[a] c] c.q[k sb[p za i[var a][FALSE] i[var a][FALSE]]].
'''.replace('FALSE', FALSE))
    try:
        values(legacy, {'za': lambda *args: False}, people)
    except SemanticError as error:
        if 'Finite function domain exceeds 4096 tables' not in str(error):
            raise
        rows['legacy_large_domain'] = {'refused': True, 'reason': str(error)}
    else:
        raise ValueError('Legacy whole-domain comparison unexpectedly evaluated')
    return rows


def contrast_checks():
    doc, rows = query_document(), {}
    for name, fn in (
        ('prevents', lambda x, y: not x), ('promotes', lambda x, y: x),
        ('never', lambda x, y: False), ('always', lambda x, y: True),
        ('multiple', lambda x, y: y), ('no_solution', lambda x, y: not y)):
        model = {'za': lambda: SequenceValue(('x', 'y'), '"individual"'),
            'zb': lambda var, state: True if var == 'x' else fn(state('x'), state('y')),
            'zc': lambda: 'x', 'zd': lambda: True, 'ze': lambda: 'y'}
        result = values(doc, model, ('x', 'y'))
        expected = {'prevents': [False, True, False, True], 'promotes': [True, False, True, False],
            'never': [False, True, False, False], 'always': [True, False, True, False],
            'multiple': [True, True, False, False], 'no_solution': [False, False, False, False]}[name]
        if result != expected:
            raise ValueError('Prevention conflated with nonoccurrence: ' + name)
        rows[name] = result
    return rows


def source_model(doc, variant):
    model = group_model(doc)
    def equations(group, person, context):
        def rule(variable, state):
            if variable == 'restriction':
                return variant != 'inconsistent_observation'
            x, y = state('restriction'), state('attempt')
            if variant == 'spontaneous_nonattempt':
                return False
            if variant == 'multiple_solutions':
                return y
            if variant == 'no_solution':
                return not y
            if (group, person, context) != (
                'population' if variant == 'wrong_group_model' else 'guards',
                'other' if variant == 'wrong_person_model' else 'person',
                'belief' if variant == 'wrong_model_context' else 'actual'):
                return False
            return not x
        return FunctionValue(('individual', STATE), 'truth', rule)
    model.update(ee=lambda: 'restriction', ef=lambda: 'restriction' if variant == 'same_variable' else 'attempt',
        eh=equations,
        ei=lambda person, description, context: variant == 'actually_attempts'
            and (person, symbol(description), context) == ('person', 'bb', 'actual'),
        ep=lambda act, person, context: variant != 'no_restriction' and (act, person, context) == (
            'activitytwo' if variant == 'different_act' else 'activity',
            'other' if variant == 'wrong_restriction_target' else 'person', 'actual'),
        za=lambda: 'person', zb=lambda: 'actual')
    if variant == 'different_participant':
        model['df'] = lambda actor, act, context: (actor, act, context) == ('guardone', 'activity', 'actual')
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: value for name, value in model.items() if name in required}


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.
q[k ek[k db[] k za[] k zb[]]].q[t[k eq[k db[] k za[]]][k zb[]]].
q[t[k ej[k za[]]][k zb[]]].q[t[k er[k db[] k za[]]][k zb[]]].
''')
    rows = {}
    expected = {
        'baseline': [True, True, False, True], 'spontaneous_nonattempt': [False, True, False, False],
        'actually_attempts': [True, True, True, False], 'no_restriction': [True, False, False, False],
        'inconsistent_observation': [True, True, False, False], 'multiple_solutions': [False, True, False, False],
        'no_solution': [False, True, False, False], 'same_variable': [False, True, False, False],
        'wrong_group_model': [False, True, False, False], 'wrong_person_model': [False, True, False, False],
        'wrong_model_context': [False, True, False, False], 'different_act': [True, False, False, False],
        'wrong_restriction_target': [True, False, False, False], 'different_participant': [True, False, False, False],
    }
    for name, target in expected.items():
        result = values(doc, source_model(doc, name), DOMAIN)
        if result != target:
            raise ValueError('Factual prevention differs: ' + name + repr(result))
        rows[name] = dict(zip(('model_prevention', 'actual_restriction', 'actual_attempt', 'factual_prevention'), result))
    ordinary = values(doc, source_model(doc, 'baseline'), DOMAIN, memoize=False, budget=20_000_000)
    if ordinary != expected['baseline']:
        raise ValueError('Ordinary and memoized prevention differ')
    return {'cases': rows, 'ordinary_baseline_agrees': True, 'individuals': len(DOMAIN),
            'model_variables': 2, 'enumerated_assignments': 4, 'definitions_replaced_by_primitives': False}


def population_checks():
    doc = candidate(source_composed()[0], '''
r za[] d.q[t[k es[k db[]]][k za[]]].
''')
    rows = {}
    for variant in ('all_targets', 'unaffected_target', 'unrestricted_target', 'empty_scope'):
        model = source_model(doc, 'baseline')
        def equations(group, person, context):
            return FunctionValue(('individual', STATE), 'truth', lambda variable, state:
                True if variable == 'restriction' else False if (
                    variant == 'unaffected_target' and person == 'other') else not state('restriction'))
        model.update(za=lambda: 'actual', eh=equations,
            ep=lambda act, person, context: (act, context) == ('activity', 'actual')
                and person in ('person', 'other', 'third')
                and not (variant == 'unrestricted_target' and person == 'other'))
        if variant == 'empty_scope':
            model['u3'] = lambda *args: False
        result = values(doc, model, DOMAIN, ('actual', 'belief', 'loss'))
        if result != [variant == 'all_targets']:
            raise ValueError('Prevention was not scoped over the same affected population: ' + variant + repr(result))
        rows[variant] = result[0]
    return rows


def alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
                if u['id'] == 'kant-1784:u0009')
    text = unit['text']
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Pinned source differs')
    start = text.index('und sorgfältig verhüteten')
    end = text.index('; so zeigen', start)
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'segments': [
        {'start': start, 'end': end, 'source': text[start:end], 'definitions': ['ej', 'ek', 'eq', 'er', 'es'],
         'status': 'explicit_interpretive_annotation'}],
        'full_semantic_equivalence': False,
        'remaining': ['cognitive change before prevention', 'carefulness and emphasis', 'permission opportunity and courage',
            'livestock and walking-frame depictions', 'subsequent danger demonstration', 'empirical model grounding', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored scoped intervention differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Scoped intervention roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/scoped-interventions-basis-v1.json', 'data/kant-scoped-interventions-basis-v1.json',
        'examples/v014/kant-scoped-groups.noema', 'data/kant-scoped-groups-basis-v1.json',
        'examples/v012/binary-interventions.noema', 'scripts/compose_scoped_interventions.py',
        'scripts/check_scoped_interventions.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'scoped_causal_models_and_explicit_prevention_reading', 'documents': documents,
        'exhaustive': exhaustive_checks(), 'scope': scope_checks(), 'contrasts': contrast_checks(),
        'source': source_checks(), 'population': population_checks(), 'alignment': alignment(), 'roundtrips': True,
        'inherited_statements_unchanged': parse(source_composed()[0])['statements'] == parse(
            (ROOT / 'examples/v014/kant-scoped-groups.noema').read_text(encoding='utf-8'))['statements'],
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Scoped intervention report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('256 models / 1024 interventions, 14 factual-prevention and 4 population cases verified')


if __name__ == '__main__':
    main()
