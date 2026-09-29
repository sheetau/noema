"""Concrete ordered paths; finite checks are not a proof over all paths."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from noema.discourse import definition_audit
from noema.finite_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.grammar import format_graph, number_word, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.compose_finite_paths import ROOT, composed

REPORT = ROOT / 'reports/finite-paths-v1.json'
ARITHMETIC = {'aa': lambda x, y: x < y, 'ab': lambda x, y: x + y,
              'ac': lambda x: -x, 'ad': lambda x, y: x * y}
DOMAIN = ('a', 'b', 'c', 'ab', 'bc', 'ca', 'ba')
START = {'ab': 'a', 'bc': 'b', 'ca': 'c', 'ba': 'b'}
END = {'ab': 'b', 'bc': 'c', 'ca': 'a', 'ba': 'a'}
DURATION = {'ab': Fraction(3), 'bc': Fraction(2), 'ca': Fraction(5), 'ba': Fraction(3)}


def numeric_document():
    doc = parse(composed()[0])
    dependencies = definition_audit(doc)['definition_primitive_dependencies']
    doc['declarations'] = [d for d in doc['declarations']
                           if (d['name'] in ARITHMETIC if d['kind'] == 'primitive'
                               else set(dependencies[d['name']]) <= set(ARITHMETIC))]
    return doc


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def check_call(base, symbol, values, *, expected_number=None, max_steps=100000):
    doc = deepcopy(base)
    declaration = next(d for d in doc['declarations'] if d['name'] == symbol)
    model, arguments = dict(ARITHMETIC), []
    for index, (parameter, value) in enumerate(zip(declaration['parameters'], values, strict=True)):
        sort = parameter['sort']
        if isinstance(sort, dict) and sort['kind'] == 'sequence':
            value = SequenceValue(tuple(value), canonical(sort['element']))
        elif isinstance(sort, dict) and sort['kind'] == 'function':
            value = FunctionValue(tuple(sort['parameters']), sort['result'], value)
        elif sort == 'number':
            value = Fraction(value)
        name = 'zz' + number_word(index)
        doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
        model[name] = lambda value=value: value
        arguments.append({'kind': 'call', 'symbol': name, 'arguments': []})
    expression = {'kind': 'call', 'symbol': symbol, 'arguments': arguments}
    if expected_number is not None:
        value = Fraction(expected_number)
        expression = {'kind': 'equal', 'arguments': [expression,
                      {'kind': 'number', 'numerator': value.numerator, 'denominator': value.denominator}]}
    doc['statements'] = [{'kind': 'ask', 'body': expression}]
    return evaluate_document(doc, individuals=DOMAIN, situations=('now',), primitives=model,
                             max_steps=max_steps)[0]['value']


def checks():
    doc, results = numeric_document(), {}
    duration = lambda segment: DURATION.get(segment, Fraction(0))
    start = lambda segment: START.get(segment, 'a')
    end = lambda segment: END.get(segment, 'a')
    speed = lambda segment: Fraction(3)
    rate = lambda segment: Fraction(4, 5)

    def record(label, symbol, args, expected, number=None):
        actual = check_call(doc, symbol, args, expected_number=number)
        if actual != expected:
            raise ValueError('Finite path differs: ' + label)
        results[label] = {'expected': expected, 'actual': actual}

    triangle = ('ab', 'bc', 'ca')
    record('empty_sum_is_zero', 'ib', ((), duration), True, 0)
    record('empty_path_is_not_a_clock_trip', 'id', ((), duration, speed, 5, rate), False)
    record('triangle_total', 'ib', (triangle, duration), True, 10)
    record('triangle_elapsed', 'ic', (triangle, duration, rate), True, 8)
    record('triangle_closed_and_lost_two', 'ig', (triangle, start, end, 'a', duration, speed, 5, rate, 10, 8, 2), True)
    record('repeated_segments_are_counted_twice', 'ig', (triangle * 2, start, end, 'a', duration, speed, 5, rate, 20, 16, 4), True)
    record('swapping_edges_preserves_sum', 'ib', (('ab', 'ca', 'bc'), duration), True, 10)
    record('swapping_edges_breaks_connection', 'if', (('ab', 'ca', 'bc'), start, end, 'a', 'a'), False)
    record('correct_open_path', 'if', (('ab', 'bc'), start, end, 'a', 'c'), True)
    record('open_path_is_not_closed', 'if', (('ab', 'bc'), start, end, 'a', 'a'), False)
    record('wrong_origin', 'if', (triangle, start, end, 'b', 'a'), False)
    record('wrong_destination', 'if', (triangle, start, end, 'a', 'b'), False)
    record('empty_connection_at_same_place', 'if', ((), start, end, 'a', 'a'), True)
    record('empty_connection_cannot_change_place', 'if', ((), start, end, 'a', 'b'), False)
    record('closed_empty_path_is_not_a_trip', 'ig', ((), start, end, 'a', duration, speed, 5, rate, 0, 0, 0), False)
    record('common_rate', 'ih', (triangle, rate, Fraction(4, 5)), True)
    record('wrong_common_rate', 'ih', (triangle, rate, Fraction(3, 5)), False)
    varied_speed = lambda segment: Fraction(0 if segment == 'bc' else 3)
    varied_rate = lambda segment: Fraction(1 if segment == 'bc' else Fraction(4, 5))
    record('different_rates_are_integrated_per_segment', 'ie',
           (triangle, duration, varied_speed, 5, varied_rate, 10, Fraction(42, 5), Fraction(8, 5)), True)
    record('first_rate_cannot_replace_all_rates', 'ie',
           (triangle, duration, varied_speed, 5, varied_rate, 10, 8, 2), False)
    for label, changed_duration, changed_speed, light, changed_rate in (
        ('zero_duration', lambda x: Fraction(0) if x == 'bc' else duration(x), speed, 5, rate),
        ('negative_duration', lambda x: Fraction(-2) if x == 'bc' else duration(x), speed, 5, rate),
        ('light_speed_segment', duration, lambda x: Fraction(5) if x == 'bc' else speed(x), 5, rate),
        ('zero_light_speed', duration, speed, 0, rate),
        ('negative_rate', duration, speed, 5, lambda x: -rate(x)),
        ('beta_instead_of_rate', duration, speed, 5, lambda x: Fraction(5, 4)),
    ):
        record(label, 'id', (triangle, changed_duration, changed_speed, light, changed_rate), False)
    record('wrong_total', 'ie', (triangle, duration, speed, 5, rate, 9, 8, 2), False)
    record('approximation_is_not_exact', 'ie', (triangle, duration, speed, 5, rate, 10, 8, Fraction(9, 5)), False)
    # Finite family of explicit lists, including repeated edges and empty lists.
    # This is independent exact Python arithmetic, not induction over all lists.
    for length in range(21):
        segments = tuple(triangle[i % 3] for i in range(length))
        total = sum((duration(x) for x in segments), Fraction(0))
        elapsed = sum((duration(x) * varied_rate(x) for x in segments), Fraction(0))
        record(f'length_{length}_sum', 'ib', (segments, duration), True, total)
        record(f'length_{length}_weighted_sum', 'ic', (segments, duration, varied_rate), True, elapsed)
    return results


def source_alignment():
    path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source artifact differs')
    source = json.loads(path.read_text(encoding='utf-8'))
    result = []
    for short in ('u0126', 'u0127', 'u0128'):
        unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:' + short)
        result.append({'unit': unit['id'], 'text_sha256': unit['text_sha256'], 'status': 'partial',
                       'definitions': ['id', 'ie', 'if', 'ig', 'ih']})
    return result


def build_report():
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored path text differs')
    doc = parse(text)
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        if parse(text) != doc or parse(decode(encode(text, 'v2'))) != doc:
            raise ValueError('Path roundtrip differs')
    procedure = parse((ROOT / 'examples/v014/procedure-order.noema').read_text(encoding='utf-8'))
    result = evaluate_document(procedure, individuals=('one',), situations=('now',), primitives={})
    if not all(row['value'] for row in result):
        raise ValueError('Procedure order differs')
    files = [basis['document'], 'data/finite-paths-basis-v1.json', 'examples/fragments/finite-paths.noema.inc',
             'examples/v014/procedure-order.noema', 'scripts/compose_finite_paths.py', 'scripts/check_finite_paths.py',
             'noema/discourse.py', 'noema/finite_semantics.py', 'noema/grammar.py', 'noema/language.py',
             'noema/semantics.py', 'noema/render.py', 'noema/script.py', 'noema/meaning_basis.py',
             'examples/v011/einstein-moving-clocks.noema', 'data/moving-clocks-basis-v1.json',
             'reports/written-units-v1.json']
    return {'status': 'partial_finite_path_arithmetic', 'basis_audit': audit_basis(doc, basis),
            'roundtrips': True, 'finite_cases': checks(), 'procedure_cases': len(result),
            'source_alignment': source_alignment(), 'new_physical_primitives': 0,
            'universal_sequence_laws_machine_proven': False, 'acceleration_physics_derived': False,
            'continuous_curve_limit_covered': False, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Finite path report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(f"{len(report['finite_cases'])} finite path checks and {report['procedure_cases']} order checks passed; source remains partial")


if __name__ == '__main__':
    main()
