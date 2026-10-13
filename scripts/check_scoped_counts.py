"""Check exact populations, strict upper bounds and explicit existence separately."""
import argparse
from fractions import Fraction
import hashlib
from itertools import permutations, product
import json

from noema.finite_semantics import Content, SequenceValue
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.compose_scoped_counts import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/scoped-counts-v1.json'


def arithmetic(bad_indicator=False):
    return {'ha': lambda a, b: a + b, 'hb': lambda a, b: a * b, 'hc': lambda a, b: a < b,
        'hd': lambda truth: Fraction(2 if bad_indicator and truth else int(truth))}


def finite_checks():
    doc = parse(generic_composed()[0] + '''r za[] j[a].r zb[a] c.r zc[a] c.r zd[] b.
q[k rcm[k za[] p zb]].q[k rcn[k za[] p zb p zc k zd[]]].q[k rco[k za[] p zb p zc k zd[]]].''')
    domain = ('one', 'two', 'three')
    def run(population, scope, selected, upper, bad_indicator=False, unknown=False):
        def property(person):
            if unknown:
                raise ValueError('Unknown property is not false')
            return person in selected
        model = {**arithmetic(bad_indicator), 'za': lambda: SequenceValue(tuple(population), '"individual"'),
            'zb': lambda x: x in scope, 'zc': property, 'zd': lambda: Fraction(upper)}
        return values(doc, model, domain, ('now',))
    scopes, thresholds = 0, 0
    for length in range(4):
        for population in product(domain, repeat=length):
            for membership in product((False, True), repeat=3):
                scope = {x for x, yes in zip(domain, membership) if yes}
                complete = bool(population) and len(population) == len(set(population)) and set(population) == scope
                count = population.count('one')
                actual = run(population, scope, {'one'}, 2)
                if actual != [complete, complete and count < 2, complete and 0 < count < 2]:
                    raise ValueError('Incomplete, duplicated or empty population accepted')
                scopes += 1
    for size in (1, 2, 3):
        scope = set(domain[:size])
        for population in permutations(domain[:size]):
            for membership in product((False, True), repeat=3):
                selected = {x for x, yes in zip(domain, membership) if yes}
                count = len(scope & selected)
                for upper in (-1, 0, Fraction(1, 2), 1, Fraction(3, 2), 2, 3, 4):
                    actual = run(population, scope, selected, upper)
                    if actual != [True, upper > 0 and count < upper, 0 < count < upper]:
                        raise ValueError('Ordering, fractional bound or existential count differs')
                    thresholds += 1
    contrasts = {}
    for name, population, scope, selected, upper, expected in (
        ('omitted_eligible_person', ('one', 'two'), set(domain), {'one'}, 2, [False] * 3),
        ('selected_only_sample', ('one',), set(domain), {'one'}, 2, [False] * 3),
        ('out_of_scope_person', domain, {'one', 'two'}, {'one'}, 2, [False] * 3),
        ('duplicate', ('one', 'one', 'two'), {'one', 'two'}, {'one'}, 3, [False] * 3),
        ('zero_qualifiers', domain, set(domain), set(), 1, [True, True, False]),
        ('at_upper_boundary', domain, set(domain), {'one', 'two'}, 2, [True, False, False]),
        ('all_of_small_scope', ('one',), {'one'}, {'one'}, 2, [True, True, True])):
        actual = run(population, scope, selected, upper)
        if actual != expected:
            raise ValueError('Count contrast failed: ' + name)
        contrasts[name] = actual
    bad = run(domain, set(domain), {'one'}, 2, bad_indicator=True)
    if bad != [False] * 3:
        raise ValueError('Invalid indicator was accepted')
    contrasts['bad_indicator'] = bad
    try:
        run(domain, set(domain), {'one'}, 2, unknown=True)
    except ValueError as exc:
        if str(exc) != 'Unknown property is not false':
            raise
    else:
        raise ValueError('Missing evaluation lowered the count')
    return {'scope_cases': scopes, 'threshold_and_permutation_cases': thresholds,
        'contrasts': contrasts, 'unknown_property_refused': True}


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] j[a].r zb[a] e.r zc[] d.
q[k h4j[k za[] p zb k zc[]]].q[k h4k[k za[] p zb k zc[]]].''')
    domain, scenes = ('one', 'two', 'three', 'object'), ('text', 'other')
    rows = {}
    cases = {'baseline': [True, True], 'zero': [True, False], 'boundary': [False, False],
        'missing_person': [False, False], 'duplicate': [False, False], 'not_human': [False, False],
        'wrong_scope_context': [False, False], 'wrong_property_context': [True, False],
        'wrong_threshold_context': [False, False], 'nonpositive_threshold': [False, False],
        'population_size_bound': [True, True]}
    for variant, expected in cases.items():
        population = ('one', 'two') if variant == 'missing_person' else ('one', 'one', 'two', 'three') if variant == 'duplicate' else domain[:3]
        def property(person):
            qualifies = person == 'one' or variant == 'boundary' and person == 'two'
            if variant == 'zero':
                qualifies = False
            return Content(scenes, (False, qualifies) if variant == 'wrong_property_context' else (qualifies, False))
        model = guarded(doc)
        model.update(arithmetic())
        model.update(za=lambda: SequenceValue(population, '"individual"'), zb=property, zc=lambda: 'text',
            aa=lambda who: who in domain[:3] and not (variant == 'not_human' and who == 'three'),
            h4i=lambda who, context: who in domain[:3] and context == ('other' if variant == 'wrong_scope_context' else 'text'),
            h4h=lambda size, context: Fraction(0) if variant == 'nonpositive_threshold' or context !=
                ('other' if variant == 'wrong_threshold_context' else 'text') else size / 2 if variant == 'population_size_bound' else Fraction(2))
        actual = values(doc, model, domain, scenes)
        if actual != expected:
            raise ValueError('Contextual source count differs: ' + str((variant, actual)))
        rows[variant] = actual
    return rows


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0010')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source unit changed')
    start = text.index('nur Wenige')
    end = start + len('nur Wenige')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': end, 'source': text[start:end],
        'definitions': ['h4j', 'h4k'], 'status': 'partial_explicit_reading', 'full_semantic_equivalence': False,
        'remaining': ['existential import and contextual bound', 'nur focus and expectations', 'Daher inference',
            'successful independent work on the mind and secure gait as the counted property']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'scoped-counts'), (source_composed, 'kant-scoped-counts')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored scoped count differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Count roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/scoped-counts-basis-v1.json', 'data/kant-scoped-counts-basis-v1.json',
        'scripts/compose_scoped_counts.py', 'scripts/check_scoped_counts.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_contextual_few_with_explicit_finite_scope', 'documents': documents,
        'finite_counts': finite_checks(), 'source_cases': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0,
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
            raise ValueError('Scoped counts report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Complete populations, strict count bounds and separate existence checked')


if __name__ == '__main__':
    main()
