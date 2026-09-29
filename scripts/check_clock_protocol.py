"""Check physical role bindings separately from exact rational coordinate laws."""
from copy import deepcopy
from fractions import Fraction
import argparse
import hashlib
import json
from pathlib import Path

from noema.discourse import normalize_document
from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.rational_proofs import verify
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_clock_protocol import compose, composed_basis

MEANINGS = {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'}

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/clock-protocol-v1.json'


def physical_checks():
    doc = parse((ROOT / 'examples/v011/clock-protocol-extension.noema').read_text(encoding='utf-8'))
    people = ('clocka', 'clockb', 'placea', 'placeb', 'depart', 'reflect', 'arrive', 'ray', 'frame', 'unit')
    domain = people + ('otherframe', 'otherunit', 'unrelated')
    mapping = {}
    arguments = []
    for i, value in enumerate(people):
        symbol = 'z' + number_word(i)
        doc['declarations'].append({'kind': 'primitive', 'name': symbol, 'parameters': [], 'result': 'individual'})
        mapping[symbol] = lambda value=value: value
        arguments.append({'kind': 'call', 'symbol': symbol, 'arguments': []})
    for i, value in enumerate((0, 1, 2)):
        symbol = 'z' + number_word(i + len(people))
        doc['declarations'].append({'kind': 'primitive', 'name': symbol, 'parameters': [],
                                    'result': {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}})
        mapping[symbol] = lambda value=value: FunctionValue(('number',), 'truth', lambda q: q < value)
        arguments.append({'kind': 'call', 'symbol': symbol, 'arguments': []})
    doc['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': 'da', 'arguments': arguments}}]
    normalize_document(doc)
    base = {
        'clocks': {'clocka', 'clockb'},
        'locations': {('clocka', 'placea', 'frame'), ('clockb', 'placeb', 'frame'),
                      ('depart', 'placea', 'frame'), ('reflect', 'placeb', 'frame'), ('arrive', 'placea', 'frame')},
        'stationary': {('clocka', 'frame'), ('clockb', 'frame')},
        'same_construction': {('clocka', 'clockb')}, 'light': {'ray'}, 'time_units': {'unit'},
        'propagation': {('ray', 'depart', 'reflect', 'frame'), ('ray', 'reflect', 'arrive', 'frame')},
        'reflection': {('ray', 'reflect', 'frame')},
        'readings': {('clocka', 'depart', 'frame', 'unit'): (False, False),
                     ('clockb', 'reflect', 'frame', 'unit'): (True, False),
                     ('clocka', 'arrive', 'frame', 'unit'): (True, True)}}
    cases = {'correct_bindings': (base, True)}
    for label, key, old, new in (
        ('return_at_wrong_place', 'locations', ('arrive', 'placea', 'frame'), ('arrive', 'placeb', 'frame')),
        ('clock_in_other_frame', 'stationary', ('clockb', 'frame'), ('clockb', 'otherframe')),
        ('wrong_reflection_event', 'reflection', ('ray', 'reflect', 'frame'), ('ray', 'unrelated', 'frame')),
        ('reversed_return_leg', 'propagation', ('ray', 'reflect', 'arrive', 'frame'), ('ray', 'arrive', 'reflect', 'frame')),
    ):
        changed = deepcopy(base)
        changed[key].remove(old)
        changed[key].add(new)
        cases[label] = (changed, False)
    for label, key in (('missing_reflection', 'reflection'), ('not_a_light_ray', 'light'),
                       ('not_same_construction', 'same_construction'), ('not_a_time_unit', 'time_units')):
        changed = deepcopy(base)
        changed[key] = set()
        cases[label] = (changed, False)
    for label, old, new in (
        ('reflection_read_from_wrong_clock', ('clockb', 'reflect', 'frame', 'unit'), ('clocka', 'reflect', 'frame', 'unit')),
        ('mixed_units', ('clockb', 'reflect', 'frame', 'unit'), ('clockb', 'reflect', 'frame', 'otherunit')),
        ('mixed_reading_frames', ('clockb', 'reflect', 'frame', 'unit'), ('clockb', 'reflect', 'otherframe', 'unit')),
    ):
        changed = deepcopy(base)
        changed['readings'][new] = changed['readings'].pop(old)
        cases[label] = (changed, False)
    changed = deepcopy(base)
    del changed['readings'][('clocka', 'arrive', 'frame', 'unit')]
    cases['missing_arrival_reading'] = (changed, False)
    changed = deepcopy(base)
    changed['readings'][('clocka', 'depart', 'frame', 'unit')] = (True, True)
    changed['readings'][('clocka', 'arrive', 'frame', 'unit')] = (False, False)
    cases['swapped_departure_arrival_values'] = (changed, False)
    results = {}
    for label, (facts, expected) in cases.items():
        def reading(clock, event, frame, unit, value):
            # In these tests inputs are exactly the three embeddings 0, 1, 2.
            # These probes distinguish those inputs; they are not a test of
            # arbitrary real-cut equality or a general measurement algorithm.
            observations = (value(Fraction(1, 2)), value(Fraction(3, 2)))
            return facts['readings'].get((clock, event, frame, unit)) == observations
        primitives = {**mapping,
            'ca': lambda clock: clock in facts['clocks'],
            'cb': lambda object_, place, frame: (object_, place, frame) in facts['locations'],
            'cc': lambda object_, frame: (object_, frame) in facts['stationary'],
            'cd': lambda first, second: (first, second) in facts['same_construction'],
            'ce': reading, 'cf': lambda ray: ray in facts['light'],
            'cg': lambda ray, first, second, frame: (ray, first, second, frame) in facts['propagation'],
            'ch': lambda ray, event, frame: (ray, event, frame) in facts['reflection'],
            'ci': lambda unit: unit in facts['time_units']}
        actual = evaluate_document(doc, individuals=domain, situations=('now',), primitives=primitives)[0]['value']
        if actual != expected:
            raise ValueError('Physical binding countermodel failed: ' + label)
        results[label] = {'expected': expected, 'actual': actual}
    return results


def coordinate_checks():
    text = (ROOT / 'examples/v011/real-cuts.noema').read_text(encoding='utf-8')
    text += (ROOT / 'examples/fragments/clock-coordinate.noema.inc').read_text(encoding='utf-8')
    results = {}
    def check(label, claim, expected='valid'):
        result = verify(parse(text + claim), MEANINGS, timeout_ms=15000)[0]
        if result['status'] != expected:
            raise ValueError('Coordinate law failed: ' + label + ' ' + result['status'])
        results[label] = result
    for factor in (Fraction(1), Fraction(60), Fraction(1, 60)):
        scale = 'n p ' + number_word(factor.numerator) + ' ' + number_word(factor.denominator)
        check('scale_embedding_' + str(factor),
              's[f x b[f q b[z[c[k bj[' + scale + ' k bb[v x]]][v q]][k aa[v q k ad[' + scale + ' v x]]]]]].')
        def moved(variable):
            return 'k bk[' + scale + ' k bb[v offset] k bb[v ' + variable + ']]'
        check('common_coordinate_change_' + str(factor),
              's[f a b[f b b[f c b[f offset b[z[k bi[' + ' '.join(moved(x) for x in ('a', 'b', 'c')) +
              ']][k bi[k bb[v a] k bb[v b] k bb[v c]]]]]]]].')
    check('zero_scale_not_a_cut', 's[u[k ba[k bj[n p a b k bb[n p b b]]]]].')
    check('negative_scale_not_a_cut', 's[u[k ba[k bj[n u b b k bb[n p b b]]]]].')
    check('shifting_only_reflection_clock_preserves_sync',
          's[z[k bi[k bb[n p a b] k bb[n p b b] k bb[n p c b]]][k bi[k bb[n p a b] k bb[n p c b] k bb[n p c b]]]].', 'invalid')
    check('relative_origin_shift_must_be_zero',
          's[f a b[f b b[f c b[f offset b[y[k bi[k bb[v a] k bb[v b] k bb[v c]]][z[k bi[k bb[v a] k bb[k ab[v b v offset]] k bb[v c]]][e[v offset][n p a b]]]]]]]].')
    return results


def build_report():
    import z3
    physical = physical_checks()
    coordinate = coordinate_checks()
    text = compose()
    if (ROOT / 'examples/v011/einstein-clock-protocol.noema').read_text(encoding='utf-8') != text:
        raise ValueError('Stored protocol differs')
    doc = parse(text)
    basis = composed_basis()
    if json.loads((ROOT / 'data/clock-protocol-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored meaning basis differs')
    audit = audit_basis(doc, basis)
    alignment = json.loads((ROOT / 'data/clock-protocol-alignment-v1.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    source_path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source unit artifact changed')
    source = {u['id']: u for u in json.loads(source_path.read_text(encoding='utf-8'))['units']}
    if alignment['document'] != basis['document'] or alignment['coordinate_extension_is_source_translation'] is not False:
        raise ValueError('Invalid alignment provenance')
    for unit in alignment['units']:
        if (source[unit['source_unit']]['text_sha256'] != unit['source_sha256'] or unit['status'] != 'partial'
                or not set(unit['definitions']) <= set(basis['definitions'])):
            raise ValueError('Invalid source alignment')
    if parse(decode(encode(format_graph(doc), 'v2'))) != doc:
        raise ValueError('Protocol round trip differs')
    paths = ['examples/v011/real-cuts.noema', 'examples/v011/clock-protocol-extension.noema',
             'examples/fragments/clock-coordinate.noema.inc', 'examples/v011/einstein-clock-protocol.noema',
             'scripts/compose_clock_protocol.py', 'scripts/check_clock_protocol.py',
             'data/clock-physical-basis-v1.json', 'data/clock-protocol-basis-v1.json', 'data/real-cuts-basis-v1.json',
             'data/clock-protocol-alignment-v1.json', 'reports/written-units-v1.json',
             'noema/discourse.py', 'noema/finite_semantics.py', 'noema/rational_proofs.py']
    return {'status': 'partial_physical_semantics', 'z3_version': z3.get_version_string(),
            'basis_audit': audit, 'physical_countermodels': physical,
            'rational_coordinate_laws': coordinate, 'roundtrip': True, 'source_alignment': alignment, 'verified_full_units': 0,
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Clock protocol verification differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Clock protocol: physical bindings and rational coordinate laws reproduced; source coverage remains partial')


if __name__ == '__main__':
    main()
