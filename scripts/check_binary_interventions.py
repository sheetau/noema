"""Compare Noema intervention definitions to exhaustive Boolean model solutions."""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'examples/v012/binary-interventions.noema'
REPORT = ROOT / 'reports/binary-interventions-v1.json'
STATE = {'kind': 'function', 'parameters': ['individual'], 'result': 'truth'}


def query_document():
    text = LIBRARY.read_text(encoding='utf-8') + '''
r ta[] h[a h[a] c] c.r tb[] a.r tc[] c.r td[] h[h[a] c] c.
q[j v[k se[k ta[] k tb[] k tc[]]]].
q[k sf[k ta[] k tb[] k tc[] k td[]]].
q[k sg[k ta[] k tb[] k tc[] k td[]]].
q[k sk[k ta[] k tb[] k tc[]]].
q[k sh[k ta[] k tb[] k td[]]].
q[k si[k ta[] k tb[] k td[]]].
q[k sj[k ta[] k tb[] k td[]]].
'''
    return parse(text)


def check_model(equations, variables, factor, value, target, *, document=None):
    """equations[var](plain dict) is the independent, extensional model input."""
    assignments = [dict(zip(variables, flags)) for flags in product((False, True), repeat=len(variables))]
    def solutions(setting):
        return [s for s in assignments if s[factor] == setting
                and all(s[x] == equations[x](s) for x in variables if x != factor)]
    def guarantees(setting, outcome):
        states = solutions(setting)
        return bool(states) and all(s[target] == outcome for s in states)
    states = solutions(value)
    expected = {
        'solutions': [[s[x] for x in variables] for s in states],
        'possible': any(s[target] for s in states),
        'guaranteed': bool(states) and all(s[target] for s in states),
        'unique': len(states) == 1,
        'positive': guarantees(True, True) and guarantees(False, False),
        'negative': guarantees(True, False) and guarantees(False, True),
        'unchanged': ((guarantees(True, True) and guarantees(False, True))
                      or (guarantees(True, False) and guarantees(False, False))),
    }
    predicates = {
        'ta': lambda: FunctionValue(('individual', STATE), 'truth',
                                    lambda x, state: equations[x]({k: state(k) for k in variables})),
        'tb': lambda: factor, 'tc': lambda: value,
        'td': lambda: FunctionValue((STATE,), 'truth', lambda state: state(target)),
    }
    actual = evaluate_document(document or query_document(), individuals=variables, situations=('context',),
                               primitives=predicates, max_steps=1000000)
    observed = {'solutions': [[row[0](x) for x in variables] for row in actual[0]['answers']]}
    observed.update({key: row['value'] for key, row in zip(list(expected)[1:], actual[1:], strict=True)})
    if observed != expected:
        raise ValueError('Intervention definitions disagree with explicit solutions: ' + repr((expected, observed)))
    return observed


def exhaustive_checks():
    variables = ('x', 'y')
    assignments = list(product((False, True), repeat=2))
    document, digest, count = query_document(), hashlib.sha256(), 0
    for flags in product((False, True), repeat=8):
        tables = {x: dict(zip(assignments, flags[i * 4:(i + 1) * 4])) for i, x in enumerate(variables)}
        equations = {x: (lambda s, table=table: table[s['x'], s['y']]) for x, table in tables.items()}
        for factor, value in product(variables, (False, True)):
            result = check_model(equations, variables, factor, value, 'y', document=document)
            digest.update(json.dumps(result, sort_keys=True, separators=(',', ':')).encode('utf-8'))
            count += 1
    return {'binary_models': 256, 'intervention_cases': count, 'all_solution_sets_and_six_properties_match': True,
            'results_sha256': digest.hexdigest()}


def named_checks():
    cases, document = {}, query_document()
    for label, y in [('positive', lambda s: s['x']), ('negative', lambda s: not s['x']),
                     ('unchanged_true', lambda s: True), ('unchanged_false', lambda s: False),
                     ('multiple_solutions', lambda s: s['y']), ('no_solution', lambda s: not s['y'])]:
        cases[label] = check_model({'x': lambda s: False, 'y': y}, ('x', 'y'), 'x', True, 'y', document=document)
    observations = {}
    for background in (False, True):
        direct = {'x': lambda s: background, 'y': lambda s: s['x'], 'z': lambda s: background}
        confounded = {'x': lambda s: s['z'], 'y': lambda s: s['z'], 'z': lambda s: background}
        observations[str(background).lower()] = {}
        for label, equations in [('direct', direct), ('common_cause', confounded)]:
            # Enumerate the observational fixed points independently of do(x).
            points = [flags for flags in product((False, True), repeat=3)
                      if all(flags[i] == equations[x](dict(zip(('x', 'y', 'z'), flags)))
                             for i, x in enumerate(('x', 'y', 'z')))]
            observations[str(background).lower()][label] = [list(p) for p in points]
            cases[label + '_background_' + str(background).lower()] = check_model(
                equations, ('x', 'y', 'z'), 'x', not background, 'y', document=document)
        if observations[str(background).lower()]['direct'] != observations[str(background).lower()]['common_cause']:
            raise ValueError('Confounding example must have the same observations')
    return {'cases': cases, 'identical_observations_different_interventions': observations}


def ordered_checks():
    doc = parse(LIBRARY.read_text(encoding='utf-8') + '''
r ta[] h[a h[a] c] c.r tb[] a.r te[] h[h[a] c h[a] c] c.
q[k sl[k ta[] k tb[] k te[]]].
q[k sm[k ta[] k tb[] k te[]]].
q[k sn[k ta[] k tb[] k te[]]].
''')
    cases = {}
    for label, equation, score, expected in [
        ('progress_one_to_two', lambda x, s: False if x == 'x' else not s('x') if x == 'y' else s('x'),
         lambda s: int(s('y')) + 2 * int(s('z')), [True, False, True]),
        ('same_change_reverse_criterion', lambda x, s: False if x == 'x' else not s('x') if x == 'y' else s('x'),
         lambda s: -int(s('y')) - 2 * int(s('z')), [False, True, False]),
        ('possible_improvement_not_guaranteed', lambda x, s: False if x == 'x' else s('y') if x == 'y' else s('x'),
         lambda s: int(s('y')) + int(s('z')), [False, False, True]),
        ('no_solution_is_not_improvement', lambda x, s: not s('y') if x == 'y' else False,
         lambda s: int(s('y')), [False, False, False]),
    ]:
        actual = evaluate_document(doc, individuals=('x', 'y', 'z'), situations=('context',), primitives={
            'ta': lambda: FunctionValue(('individual', STATE), 'truth', equation), 'tb': lambda: 'x',
            'te': lambda: FunctionValue((STATE, STATE), 'truth', lambda left, right: score(left) < score(right))},
            max_steps=1000000)
        observed = [r['value'] for r in actual]
        if observed != expected:
            raise ValueError('Ordered intervention comparison differs: ' + label)
        cases[label] = {'expected': expected, 'actual': observed}
    return cases


def build_report():
    doc = parse(LIBRARY.read_text(encoding='utf-8'))
    basis = json.loads((ROOT / 'data/binary-interventions-basis-v1.json').read_text(encoding='utf-8'))
    for notation in ('compact', 'full'):
        text = format_graph(doc, notation)
        if parse(text) != doc or parse(decode(encode(text, 'v2'))) != doc:
            raise ValueError('Intervention library round trip differs')
    from scripts.compose_kant_interventions import composed
    kant_text, kant_basis = composed()
    if (ROOT / kant_basis['document']).read_text(encoding='utf-8') != kant_text:
        raise ValueError('Stored Kant reading differs')
    if json.loads((ROOT / 'data/kant-intervention-basis-v1.json').read_text(encoding='utf-8')) != kant_basis:
        raise ValueError('Stored Kant reading basis differs')
    kant_doc = parse(kant_text)
    for notation in ('compact', 'full'):
        canonical = format_graph(kant_doc, notation)
        if parse(canonical) != kant_doc or parse(decode(encode(canonical, 'v2'))) != kant_doc:
            raise ValueError('Kant intervention reading round trip differs')
    files = ['examples/v012/binary-interventions.noema', 'data/binary-interventions-basis-v1.json',
             'scripts/check_binary_interventions.py', 'noema/discourse.py', 'noema/finite_semantics.py',
             'noema/grammar.py', 'noema/semantics.py', 'noema/meaning_basis.py', 'noema/script.py',
             'scripts/compose_kant_interventions.py', 'examples/v012/kant-questions.noema',
             'data/kant-question-basis-v1.json', 'examples/v012/kant-interventions.noema', 'data/kant-intervention-basis-v1.json']
    return {'status': 'verified_binary_model_definitions_not_general_causal_language_completion',
            'basis_audit': audit_basis(doc, basis), 'roundtrips': True, 'exhaustive': exhaustive_checks(),
            'countermodels': named_checks(), 'ordered_outcomes': ordered_checks(), 'verified_full_source_units': 0,
            'kant_reading': {'status': 'explicit_model_relative_strong_reading_only',
                             'basis_audit': audit_basis(kant_doc, kant_basis), 'roundtrips': True,
                             'original_general_question_draft_preserved': True},
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    result = build_report()
    if args.verify_only:
        if json.loads(REPORT.read_text(encoding='utf-8')) != result:
            raise ValueError('Binary intervention report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('256 binary models / 1024 intervention cases matched; no full paper unit claimed')


if __name__ == '__main__':
    main()
