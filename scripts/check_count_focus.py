"""Check all attainable counts, weaker alternatives and fixed count background."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, SequenceValue
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_qualified_few import native_values, source_model as count_model
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import alignment as count_alignment
from scripts.compose_count_focus import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/count-focus-v1.json'
CRITERION_SORT = json.dumps({'kind': 'function', 'parameters': ['number'], 'result': 'truth'}, sort_keys=True, separators=(',', ':'))


def criteria(*predicates):
    return SequenceValue(tuple(FunctionValue(('number',), 'truth', predicate) for predicate in predicates), CRITERION_SORT)


def domain_checks():
    doc = parse(generic_composed()[0] + 'r za[] j[a].r zb[] j[b].q[e[k rcx[k za[]]][k zb[]]].')
    rows = {}
    for size in (0, 1, 2, 5, 16):
        population = tuple(range(size))
        expected = tuple(Fraction(i) for i in range(size + 1))
        result = values(doc, {'za': lambda: SequenceValue(population, '"individual"'),
            'zb': lambda: SequenceValue(expected, '"number"')}, tuple(range(max(1, size))), ('now',))
        if result != [True]:
            raise ValueError('Attainable counts were sampled or an endpoint omitted')
        rows[str(size)] = [int(item) for item in expected]
    return rows


def generic_checks():
    doc = parse(generic_composed()[0] + '''r za[] j[b].r zb[b] c.r zc[b] c.r zd[] j[h[b] c].r ze[] b.
q[k rcy[k za[] p zb p zc]].q[k rcz[k za[] p zb k zd[] k ze[]]].''')
    def run(selected, alternative, actual=1, counts=(0, 1, 2), repeats=1):
        return values(doc, {'za': lambda: SequenceValue(tuple(Fraction(n) for n in counts), '"number"'),
            'zb': selected, 'zc': alternative, 'zd': lambda: criteria(*([alternative] * repeats)),
            'ze': lambda: Fraction(actual)}, ('object',), ('now',))
    cases = 0
    for selected, alternative in product(product((False, True), repeat=3), repeat=2):
        implied = all(not p or q for p, q in zip(selected, alternative))
        for actual in range(3):
            got = run(lambda n: selected[int(n)], lambda n: alternative[int(n)], actual)
            if got != [implied, selected[actual] and (implied or not alternative[actual])]:
                raise ValueError('A weaker true alternative was excluded or a stronger true alternative allowed')
            cases += 1
    selected = lambda n: 0 < n < 3
    contrasts = {}
    for name, alternative, actual, counts, repeats, expected in (
        ('weaker_true', lambda n: n >= 1, 1, (0, 1, 2), 1, [True, True]),
        ('equivalent_true', lambda n: n in (1, 2), 1, (0, 1, 2), 1, [True, True]),
        ('overlapping_true', lambda n: n == 1, 1, (0, 1, 2), 1, [False, False]),
        ('overlapping_false', lambda n: n == 1, 2, (0, 1, 2), 1, [False, True]),
        ('incomplete_domain_hides_overlap', lambda n: n == 1, 1, (0, 1), 1, [True, True]),
        ('empty_domain', lambda n: n > 0, 1, (), 1, [True, False]),
        ('actual_outside_domain', lambda n: n >= 1, 2, (0, 1), 1, [True, False]),
        ('empty_alternatives', lambda n: n > 0, 1, (0, 1, 2), 0, [True, False]),
        ('duplicate_alternatives', lambda n: n >= 3, 1, (0, 1, 2), 2, [False, True]),
        ('impossible_alternative', lambda n: False, 1, (0, 1, 2), 1, [False, True])):
        got = run(selected, alternative, actual, counts, repeats)
        if got != expected:
            raise ValueError('Count focus contrast differs: ' + name)
        contrasts[name] = got
    return {'truth_table_cases': cases, 'contrasts': contrasts}


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.r zc[] d.r zd[] d.r zf[] j[a].
q[k h5o[k zf[] k zd[]]].q[k h5w[k zf[] k zd[]]].''')
    rows = {}
    for variant in ('baseline', 'weaker', 'equivalent', 'overlap', 'empty', 'wrong_context', 'wrong_size', 'all_of_small_scope'):
        model = count_model(doc)
        if variant == 'overlap':
            model['h4h'] = lambda size, context: Fraction(3)
        if variant == 'all_of_small_scope':
            model['zf'] = lambda: SequenceValue(('person',), '"individual"')
            model['h4i'] = lambda person, context: person == 'person'
        def family(size, context):
            if variant == 'empty' or context != ('expected' if variant == 'wrong_context' else 'now') or (
                    variant == 'wrong_size' and size != 3):
                return criteria()
            if variant == 'weaker':
                return criteria(lambda n: n > 0)
            if variant in ('equivalent', 'overlap'):
                return criteria(lambda n: n == 1)
            return criteria(lambda n: n >= 2)
        def no_expectation(*args):
            raise ValueError('Count focus must not read expectation alternatives')
        model.update(h5v=family, ke=no_expectation)
        actual = native_values(doc, model)
        expected = [True, variant not in ('overlap', 'empty', 'wrong_context', 'wrong_size')]
        if actual != expected:
            raise ValueError('Count background or family binding changed: ' + str((variant, actual)))
        rows[variant] = actual
    # The alternative is known at the actual count, but not at another attainable count.
    model = count_model(doc)
    model['h4h'] = lambda size, context: Fraction(3)
    def incomplete(n):
        if n == 2:
            raise ValueError('Unknown alternative at an attainable count')
        return n == 1
    model['h5v'] = lambda size, context: criteria(incomplete)
    try:
        native_values(doc, model)
    except ValueError as error:
        if str(error) != 'Unknown alternative at an attainable count':
            raise
    else:
        raise ValueError('Actual count alone substituted for implication across all attainable counts')
    return {'cases': rows, 'unknown_alternative_refused': True, 'expectation_primitives_guarded_against_execution': True}


def discourse_checks():
    doc = candidate(source_composed()[0], 'q[k h5z[]].')
    domain = ('author', 'condition', 'reason', 'conclusion', 'other')
    rows = {}
    for variant in ('baseline', 'old_content', 'wrong_node', 'wrong_author', 'omitted_premise', 'reversed_order'):
        model = guarded(doc)
        model.update(wa=lambda: 'author', wh=lambda: 'text', h3a=lambda: 'condition', h3s=lambda: 'reason', h5t=lambda: 'conclusion',
            uc=lambda node, author, description, context: (node, author, json.loads(description.syntax)['symbol'], context) == (
                'other' if variant == 'wrong_node' else 'conclusion', 'other' if variant == 'wrong_author' else 'author',
                'h5s' if variant == 'old_content' else 'h5y', 'text'),
            ud=lambda author, premises, conclusion, context: (author, conclusion, context) == ('author', 'conclusion', 'text') and
                {item for item in domain if premises(item)} == ({'condition'} if variant == 'omitted_premise' else {'condition', 'reason'}),
            ue=lambda first, last, context: (first, last, context) == (
                ('conclusion', 'reason', 'text') if variant == 'reversed_order' else ('reason', 'conclusion', 'text')))
        actual = values(doc, model, domain, ('text',))
        if actual != [variant == 'baseline']:
            raise ValueError('Focused conclusion attribution changed or executed the count')
        rows[variant] = actual
    return {'cases': rows, 'all_count_and_alternative_primitives_guarded_against_execution': True}


def alignment():
    row = count_alignment()
    row['definitions'] = ['h5w', 'h5x', 'h5y', 'h5z']
    row['remaining'] = ['selection and relevance of numeric alternatives', 'contextual upper bound and existential import',
        'presupposition versus assertion and full nur semantics', 'scope of Daher premises and source semantic equivalence']
    return row


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'count-focus'), (source_composed, 'kant-count-focus')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored count focus differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Count focus roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'][:-1] != parent['statements'][:-1]:
        raise ValueError('Earlier source changed outside the conclusion attribution')
    paths = list(documents) + [PARENT, 'data/count-focus-basis-v1.json', 'data/kant-count-focus-basis-v1.json',
        'scripts/compose_count_focus.py', 'scripts/check_count_focus.py', 'scripts/check_qualified_few.py',
        'scripts/check_achievement_exercise.py', 'scripts/check_scoped_counts.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_count_alternative_exclusion_not_counterexpectation',
        'documents': documents, 'count_domains': domain_checks(), 'generic': generic_checks(), 'source_cases': source_checks(),
        'discourse_cases': discourse_checks(), 'alignment': alignment(), 'roundtrips': True,
        'parent_declarations_preserved': True, 'source_assertions_replaced': 1, 'new_source_assertions': 0,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'background_reference': {'title': 'Mats Rooth, Alternative Semantics',
            'url': 'https://compling.cis.cornell.edu/mr249/papers/rooth-2016-alternative.pdf',
            'role': 'Alternative-based focus motivation, not evidence that this Kant reading is uniquely correct'},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Count focus report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('All attainable counts, weaker true alternatives and fixed count background checked')


if __name__ == '__main__':
    main()
