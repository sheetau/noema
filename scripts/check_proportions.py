"""Exact finite counts and countermodels for population scope and proportions."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import Content, SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_proportions import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/proportions-v1.json'


def candidate(source=False, quantify=False):
    doc = parse((source_composed if source else generic_composed)()[0])
    doc['statements'] = []
    text = format_graph(doc, 'compact') + '''
r za[] j[a].r zb[a] c.r zc[b] c.r zd[a] c.r zq[] b.r zr[] b.
q[k he[]].q[e[k hf[k za[] p zb]][k zr[]]].q[k hh[k za[]]].
q[k hj[k za[] p zb k zq[]]].q[k hk[k za[] p zd p zb p zc k zq[]]].q[k hl[k za[] p zb k zq[]]].
'''
    if source:
        # Put new declarations before the existing questions.
        interim = parse(text)
        statements, interim['statements'] = interim['statements'], []
        text = format_graph(interim, 'compact') + '\nr zx[a] e.r zy[] d.\n'
        doc = parse(text)
        doc['statements'] = statements
        text = format_graph(doc, 'compact')
        text += '\nq[t[k hq[k za[] p zx]][k zy[]]].' if quantify else '\nq[k hn[k za[] p zx k zq[] k zy[]]].'
    return parse(text)


def evaluate_case(doc, population, selected, ratio, threshold=Fraction(3, 5), *, outsider=None, indicator='normal', complete=True, context=True):
    domain = tuple(dict.fromkeys((*population, 'extra')))
    def numerical(condition):
        return Fraction(2 if condition else 0) if indicator == 'double' else Fraction(1) if indicator == 'always_one' else Fraction(0) if indicator == 'always_zero' else Fraction(int(condition))
    expected_count = sum((numerical(person in selected) for person in population), Fraction(0))
    model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update({'ha': lambda a, b: a + b, 'hb': lambda a, b: a * b, 'hc': lambda a, b: a < b, 'hd': numerical,
        'za': lambda: SequenceValue(tuple(population), '"individual"'), 'zb': lambda person: person in selected,
        'zc': lambda proportion: proportion >= threshold, 'zd': lambda person: person != outsider,
        'zq': lambda: Fraction(ratio), 'zr': lambda: expected_count})
    if 'zx' in model:
        model.update({'aa': lambda person: person != outsider,
            'zx': lambda person: Content(('text', 'other'), (person in selected, False)), 'zy': lambda: 'text',
            'hr': lambda pop, scene: complete and pop.items == tuple(population) and scene == 'text',
            'hs': lambda proportion, scene: scene == ('text' if context else 'other') and proportion >= threshold})
    results = [r['value'] for r in evaluate_document(doc, individuals=domain, situations=('text', 'other'),
                primitives=model, max_steps=2000000)]
    if results[1] is not True:
        raise ValueError('Noema fold count differs from independent occurrence count')
    # Report the independent number only after the Noema equality checked it.
    results[1] = expected_count
    return results


def finite_counts():
    doc = candidate()
    rows = []
    for size in range(9):
        population = tuple('p' + str(i) for i in range(size))
        for count in range(size + 1):
            ratio = Fraction(count, size) if size else Fraction(0)
            selected = set(population[:count])
            actual = evaluate_case(doc, population, selected, ratio)
            expected = [True, Fraction(count), True, bool(size), bool(size) and ratio >= Fraction(3, 5), bool(size) and ratio > Fraction(1, 2)]
            if actual != expected:
                raise ValueError('Exact population count differs')
            rows.append({'population_size': size, 'selected_count': count, 'ratio': str(ratio),
                         'exact_proportion': actual[3], 'contextual_large': actual[4], 'majority': actual[5]})
    population = tuple('p' + str(i) for i in range(64))
    actual = evaluate_case(doc, population, set(population[::2]), Fraction(1, 2))
    if actual != [True, Fraction(32), True, True, False, False]:
        raise ValueError('Larger population check differs')
    return {'cases': rows, 'larger_population': {'size': 64, 'selected': 32, 'exact_ratio': '1/2'}}


def counterexamples():
    doc = candidate()
    rows = {}
    cases = (
        ('duplicate_person', ('a', 'b', 'a'), {'a'}, Fraction(2, 3), {}, False, False),
        ('wrong_ratio', ('a', 'b', 'c'), {'a'}, Fraction(2, 3), {}, False, False),
        ('negative_ratio', ('a', 'b'), {'a'}, -1, {}, False, False),
        ('ratio_above_one', ('a', 'b'), {'a', 'b'}, 2, {}, False, False),
        ('outsider_in_domain', ('a', 'b', 'tool'), {'a', 'b'}, Fraction(2, 3), {'outsider': 'tool'}, True, False),
        ('bad_indicator_double', ('a',), {'a'}, 1, {'indicator': 'double'}, False, False),
        ('bad_indicator_always_one', ('a',), set(), 1, {'indicator': 'always_one'}, False, False),
        ('bad_indicator_always_zero', ('a',), {'a'}, 0, {'indicator': 'always_zero'}, False, False),
        ('below_half_can_meet_contextual_standard', ('a', 'b', 'c', 'd', 'e'), {'a', 'b'}, Fraction(2, 5), {'threshold': Fraction(1, 3)}, True, True),
        ('majority_can_fail_contextual_standard', ('a', 'b', 'c', 'd'), {'a', 'b', 'c'}, Fraction(3, 4), {'threshold': Fraction(9, 10)}, True, False),
        ('reordered_population', ('c', 'a', 'b'), {'a', 'b'}, Fraction(2, 3), {}, True, True),
        ('same_ratio_larger_population', ('a', 'b', 'c', 'd', 'e', 'f'), {'a', 'b', 'd', 'e'}, Fraction(2, 3), {}, True, True),
    )
    for name, population, selected, ratio, options, valid, large in cases:
        actual = evaluate_case(doc, population, selected, ratio, **options)
        if actual[3:5] != [valid, large]:
            raise ValueError('Proportion counterexample differs: ' + name)
        rows[name] = {'raw_count': str(actual[1]), 'indicator_valid': actual[0], 'unique': actual[2],
                      'exact_ratio': actual[3], 'contextual_large': actual[4], 'majority': actual[5]}
    return rows


def source_checks():
    doc = candidate(source=True)
    cases = (
        ('baseline', ('a', 'b', 'c'), {'a', 'b'}, Fraction(2, 3), {}, True),
        ('population_not_established_complete', ('a', 'b', 'c'), {'a', 'b'}, Fraction(2, 3), {'complete': False}, False),
        ('not_all_people', ('a', 'b', 'tool'), {'a', 'b'}, Fraction(2, 3), {'outsider': 'tool'}, False),
        ('wrong_context', ('a', 'b', 'c'), {'a', 'b'}, Fraction(2, 3), {'context': False}, False),
        ('empty_population', (), set(), 0, {}, False),
        ('duplicate_person', ('a', 'b', 'a'), {'a'}, Fraction(2, 3), {}, False),
        ('below_half_contextual', ('a', 'b', 'c', 'd', 'e'), {'a', 'b'}, Fraction(2, 5), {'threshold': Fraction(1, 3)}, True),
    )
    rows = {}
    for name, population, selected, ratio, options, expected in cases:
        actual = evaluate_case(doc, population, selected, ratio, **options)[-1]
        if actual != expected:
            raise ValueError('Source large share differs: ' + name)
        rows[name] = actual
    try:
        evaluate_case(candidate(source=True, quantify=True), ('a', 'b', 'c'), {'a', 'b'}, Fraction(2, 3))
    except ValueError as error:
        if 'rational number domain' not in str(error):
            raise
        refusal = str(error)
    else:
        raise ValueError('General ratio quantification was replaced by finite candidates')
    return {'cases': rows, 'unbounded_ratio_refusal': refusal}


def source_alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    units = json.loads(path.read_text(encoding='utf-8'))['units']
    unit = next(u for u in units if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Kant second paragraph differs')
    phrase = 'ein so großer Theil der Menschen'
    if unit['text'].count(phrase) != 1:
        raise ValueError('Large-share phrase missing or ambiguous')
    start = unit['text'].index(phrase)
    return {'unit': unit['id'], 'unit_sha256': digest, 'start': start, 'end': start + len(phrase), 'source': phrase,
        'definitions': ['hn', 'hq'], 'status': 'partial_quantifier_fragment',
        'full_predicate_connected': False, 'numerical_ratio_or_threshold_asserted': False,
        'population_completeness_is_explicit_assumption': True,
        'remaining': ['causes', 'longstanding natural release', 'lifelong willing persistence', 'remaining paragraph clauses', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored proportion document differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Proportion roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/proportions-basis-v1.json', 'data/kant-large-share-basis-v1.json',
        'examples/v014/kant-quoted-group.noema', 'data/kant-quoted-group-basis-v1.json',
        'scripts/compose_proportions.py', 'scripts/check_proportions.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'finite_population_proportions_partial_source_fragment', 'documents': documents,
        'finite_counts': finite_counts(), 'counterexamples': counterexamples(), 'source_checks': source_checks(),
        'source_alignment': source_alignment(), 'roundtrips': True,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Proportion report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('45 counts, 64-person case, 12 contrasts and 7 source population cases checked')


if __name__ == '__main__':
    main()
