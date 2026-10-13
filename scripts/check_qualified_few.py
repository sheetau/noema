"""Check guarded actual counts, independent concession and attributed inference."""
import argparse
from fractions import Fraction
import hashlib
from itertools import permutations, product
import json

from noema.finite_semantics import SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_achievement_exercise import source_model as achievement_model, DOMAIN, SCENES
from scripts.check_conditional_release import values
from scripts.check_controlled_gait import alignment as gait_alignment
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.compose_qualified_few import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/qualified-few-v1.json'
NATIVE_STEP_LIMIT = 32_000_000


def native_values(doc, model):
    return [row['value'] for row in evaluate_document(doc, individuals=DOMAIN + ('author',), situations=SCENES,
        primitives=model, max_steps=NATIVE_STEP_LIMIT, memoize_definitions=True, memoize_expressions=True)]


def generic_checks():
    doc = parse(generic_composed()[0] + '''r za[] j[a].r zb[a] c.r zc[a] c.r zd[a] c.r ze[] b.
q[k rcu[k za[] p zc p zd]].q[k rcv[k za[] p zb p zc p zd k ze[]]].q[k rcw[k za[] p zb p zc p zd k ze[]]].''')
    domain = ('one', 'two', 'three')
    def run(qualified, complete, upper, population=domain):
        model = {**arithmetic(), 'za': lambda: SequenceValue(population, '"individual"'),
            'zb': lambda person: person in domain, 'zc': lambda person: qualified[domain.index(person)],
            'zd': lambda person: complete[domain.index(person)], 'ze': lambda: Fraction(upper)}
        return values(doc, model, domain, ('now',))
    cases = 0
    for flags in product((False, True), repeat=6):
        qualified, complete = flags[:3], flags[3:]
        guard = all(q or c for q, c in zip(qualified, complete))
        count = sum(qualified)
        for upper in (0, 1, 2, 4):
            actual = run(qualified, complete, upper)
            expected = [guard, guard and 0 < upper and count < upper, guard and 0 < count < upper]
            if actual != expected:
                raise ValueError('Unknown negative or expectation changed actual count')
            cases += 1
    contrasts = {}
    for name, qualified, complete, upper, population, expected in (
        ('unassessed_positive', (True, False, False), (False, True, True), 2, domain, [True] * 3),
        ('unassessed_negative', (True, False, False), (True, False, True), 2, domain, [False] * 3),
        ('zero_qualifiers', (False,) * 3, (True,) * 3, 2, domain, [True, True, False]),
        ('omitted_nonqualifier', (True, False, False), (True,) * 3, 2, domain[:2], [True, False, False]),
        ('duplicate', (True, False, False), (True,) * 3, 2, ('one', 'one', 'two', 'three'), [True, False, False]),
        ('empty_scope_list', (False,) * 3, (True,) * 3, 2, (), [True, False, False]),
        ('at_upper_boundary', (True, True, False), (True,) * 3, 2, domain, [True, False, False])):
        actual = run(qualified, complete, upper, population)
        if actual != expected:
            raise ValueError('Qualified count contrast failed: ' + name)
        contrasts[name] = actual
    for population in permutations(domain):
        if run((True, False, False), (False, True, True), 2, population) != [True] * 3:
            raise ValueError('Order changed the count or its guard')
    return {'truth_and_threshold_cases': cases, 'permutation_cases': 6, 'contrasts': contrasts}


def source_model(doc, variant='baseline'):
    original = 'exercise_before_achievement' if variant == 'known_achievement_unassessed_earlier' else variant
    if variant in ('unassessed_after_positive', 'unknown_expectations', 'unknown_reason', 'omitted_person'):
        original = 'baseline'
    model = achievement_model(doc, original)
    model.update(arithmetic())
    population = ('person',) if variant == 'omitted_person' else ('person', 'other')
    model.update(zf=lambda: SequenceValue(population, '"individual"'),
        h4i=lambda person, context: person in ('person', 'other'), h4h=lambda size, context: Fraction(2))
    if variant in ('known_achievement_unassessed_earlier', 'unassessed_after_positive'):
        old_available, old_outcomes = model['ae'], model['af']
        model['ae'] = lambda person, plan, point: old_available(person, plan, point) or (person, plan, point) == ('person', 'plan', 'finish')
        model['af'] = lambda person, plan, first, last: old_outcomes(person, plan, first, last) or (
            person, plan, first, last) == ('person', 'plan', 'finish', 'exit')
        # ap deliberately retains the original selection: the added method has no assessed outcome.
    if variant == 'unknown_expectations':
        def unknown(*args):
            raise ValueError('Unknown expectations cannot alter actual counts')
        model['ke'] = unknown
    if variant == 'unknown_reason':
        def unknown(*args):
            raise ValueError('Unknown support is not false')
        model['fd'] = unknown
    return model


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.r zc[] d.r zd[] d.r zf[] j[a].
q[x[t[k h4q[k za[]]][k zd[]]][k h4t[k za[] k zd[]]]].
q[k h5m[k zf[] k zd[]]].q[k h5n[k zf[] k zd[]]].q[k h5o[k zf[] k zd[]]].''')
    cases = {'baseline': [True] * 4, 'no_exercise': [True, True, True, False],
        'exercise_before_achievement': [True, True, True, False],
        'unassessed_achievement': [False] * 4, 'known_achievement_unassessed_earlier': [True, False, False, False],
        'unassessed_after_positive': [True] * 4, 'unknown_expectations': [True] * 4,
        'omitted_person': [True, True, False, False]}
    rows = {}
    for variant, expected in cases.items():
        actual = native_values(doc, source_model(doc, variant))
        if actual != expected:
            raise ValueError('Native qualifying count failed: ' + str((variant, actual, expected)))
        rows[variant] = actual
    try:
        native_values(doc, source_model(doc, 'unknown_reason'))
    except ValueError as error:
        if str(error) != 'Unknown support is not false':
            raise
    else:
        raise ValueError('Unknown judgment support lowered the count')
    return {'query_order': ['prior_person_guard', 'new_population_guard', 'zero_permitting_upper_count', 'positive_upper_count'],
        'cases': rows, 'unknown_support_refused': True, 'unknown_expectations_do_not_change_count': True}


def concession_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.r zc[] d.r zd[] d.r zf[] j[a].
q[k h5o[k zf[] k zd[]]].q[k h5p[k zf[] k zd[]]].''')
    rows = {}
    for variant in ('baseline', 'no_expectations', 'expected_also_exercises'):
        actual = native_values(doc, source_model(doc, variant))
        expected = [True, variant == 'baseline']
        if actual != expected:
            raise ValueError('Concession filtered an actual successful person: ' + str((variant, actual)))
        rows[variant] = actual
    return rows


def discourse_checks():
    doc = candidate(source_composed()[0], 'q[k h5u[]].')
    domain = ('author', 'condition', 'reason', 'conclusion', 'other')
    rows = {}
    for variant in ('baseline', 'claim_node', 'author', 'content', 'context', 'omitted_premise',
            'conclusion_as_premise', 'inference_conclusion', 'reverse_order'):
        model = guarded(doc)
        def claimed(node, author, description, context):
            return (node, author, json.loads(description.syntax)['symbol'], context) == (
                'other' if variant == 'claim_node' else 'conclusion',
                'other' if variant == 'author' else 'author', 'h5q' if variant == 'content' else 'h5s',
                'elsewhere' if variant == 'context' else 'text')
        def inferred(author, premises, conclusion, context):
            expected = {'condition'} if variant == 'omitted_premise' else {'conclusion'} if variant == 'conclusion_as_premise' else {'condition', 'reason'}
            return {item for item in domain if premises(item)} == expected and (author, conclusion, context) == (
                'author', 'reason' if variant == 'inference_conclusion' else 'conclusion', 'text')
        model.update(wa=lambda: 'author', wh=lambda: 'text', h3a=lambda: 'condition', h3s=lambda: 'reason',
            h5t=lambda: 'conclusion', uc=claimed, ud=inferred,
            ue=lambda first, last, context: (first, last, context) == (
                ('conclusion', 'reason', 'text') if variant == 'reverse_order' else ('reason', 'conclusion', 'text')))
        actual = values(doc, model, domain, ('text', 'elsewhere'))
        if actual != [variant == 'baseline']:
            raise ValueError('Attributed inference or source order differs')
        rows[variant] = actual
    return {'cases': rows, 'all_count_and_content_primitives_guarded_against_execution': True}


def unbounded_refusal():
    doc = candidate(source_composed()[0], 'r zz[] d.q[t[k h5s[]][k zz[]]].')
    model = guarded(doc)
    model['zz'] = lambda: 'text'
    try:
        values(doc, model, ('person',), ('text',))
    except ValueError as error:
        if str(error) != 'Cannot finitely quantify the unbounded sequence domain':
            raise
        return {'refused': True, 'reason': str(error)}
    raise ValueError('One listed population substituted for all finite sequences')


def alignment():
    row = gait_alignment()
    units = json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
    text = next(unit['text'] for unit in units if unit['id'] == row['unit'])
    row['start'] = text.index('Daher giebt es nur Wenige')
    row['end'] += 1
    row['source'] = text[row['start']:row['end']]
    row['definitions'] = ['h5m', 'h5n', 'h5o', 'h5p', 'h5q', 'h5r', 'h5s', 'h5u']
    row['remaining'] = ['existential import and nur focus', 'contextual threshold and complete interpretation of predicates',
        'full semantics of self-cultivation and intellectual stability', 'concession distribution and Daher premise scope',
        'source equivalence and arbitrary finite sequence proof']
    return row


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'qualified-few'), (source_composed, 'kant-qualified-few')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored qualified few differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Qualified few roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'][:-1] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/qualified-few-basis-v1.json', 'data/kant-qualified-few-basis-v1.json',
        'scripts/compose_qualified_few.py', 'scripts/check_qualified_few.py', 'scripts/check_achievement_exercise.py',
        'scripts/check_scoped_counts.py', 'scripts/check_controlled_gait.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_actual_few_with_separate_concession_and_inference_attribution',
        'documents': documents, 'generic': generic_checks(), 'source_cases': source_checks(),
        'concession_cases': concession_checks(), 'discourse_cases': discourse_checks(),
        'unbounded_sequence': unbounded_refusal(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 1, 'native_step_limit': NATIVE_STEP_LIMIT,
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
            raise ValueError('Qualified few report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Actual counts, adequate negative assessment, separate concession and Daher attribution checked')


if __name__ == '__main__':
    main()
