"""Dimensions, exact unit conversions, and scale invariance of beta."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_quantities import composed

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/quantities-v1.json'
DIMENSION = {'kind': 'function', 'parameters': ['individual'], 'result': 'number'}
DOMAIN = ('length', 'time', 'mass', 'speedkind', 'otherkind')
ARITHMETIC = {'aa': lambda a, b: a < b, 'ab': lambda a, b: a + b, 'ac': lambda a: -a, 'ad': lambda a, b: a * b}


def dimension(**exponents):
    return FunctionValue(('individual',), 'number', lambda axis: Fraction(exponents.get(axis, 0)))


def query(doc, symbol, args):
    candidate, primitives, arguments = deepcopy(doc), dict(ARITHMETIC), []
    for index, (sort, value) in enumerate(args):
        name = 'z' + number_word(index)
        candidate['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
        primitives[name] = lambda value=value: value
        arguments.append({'kind': 'call', 'symbol': name, 'arguments': []})
    candidate['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': symbol, 'arguments': arguments}}]
    return evaluate_document(candidate, individuals=DOMAIN, situations=('now',), primitives=primitives)[0]['value']


def finite_checks():
    text, _ = composed()
    doc, cases = parse(text), {}
    length, time = dimension(length=1), dimension(time=1)
    velocity, scalar = dimension(length=1, time=-1), dimension()
    def check(label, symbol, kinds, dims, numbers, expected):
        args = [('individual', x) for x in kinds] + [(DIMENSION, d) for d in dims] + [('number', Fraction(x)) for x in numbers]
        actual = query(doc, symbol, args)
        if actual != expected:
            raise ValueError('Quantity countermodel differs: ' + label)
        cases[label] = {'expected': expected, 'actual': actual}
    check('kind_dimension_and_scale_conversion', 'dj', ('speedkind', 'speedkind'), (velocity, velocity), (Fraction(5, 18), 1, 36, 10), True)
    check('same_dimension_different_kind_rejected', 'dj', ('speedkind', 'otherkind'), (velocity, velocity), (1, 1, 3, 3), False)
    check('different_dimensions_rejected', 'dj', ('speedkind', 'speedkind'), (velocity, length), (1, 1, 3, 3), False)
    check('unconverted_readings_rejected', 'dj', ('speedkind', 'speedkind'), (velocity, velocity), (1, 1, 36, 10), False)
    check('negative_unit_scale_rejected', 'dj', ('speedkind', 'speedkind'), (velocity, velocity), (-1, 1, -3, 3), False)
    check('zero_unit_scale_rejected', 'dj', ('speedkind', 'speedkind'), (velocity, velocity), (0, 1, 3, 0), False)
    check('speed_times_duration_is_length', 'dl', (), (velocity, time, length), (1, 1, 1, 3, 2, 6), True)
    check('product_wrong_dimension_rejected', 'dl', (), (velocity, time, velocity), (1, 1, 1, 3, 2, 6), False)
    check('distance_over_duration_is_speed', 'dm', (), (length, time, velocity), (1, 1, 1, 12, 4, 3), True)
    check('zero_duration_is_not_a_quotient', 'dm', (), (length, time, velocity), (1, 1, 1, 0, 0, 3), False)
    check('wrong_quotient_dimension_rejected', 'dm', (), (length, time, length), (1, 1, 1, 12, 4, 3), False)
    kinds = ('length', 'time', 'speedkind', 'speedkind')
    dims = (length, time, velocity, velocity, scalar)
    base = (1, 1, 1, 3, 5, Fraction(5, 4))
    check('beta_reference_scales', 'do', kinds, dims, base, True)
    check('beta_mixed_velocity_scales', 'do', kinds, dims, (Fraction(5, 18), 1, 1, Fraction(54, 5), 5, Fraction(5, 4)), True)
    check('beta_missing_velocity_conversion', 'do', kinds, dims, (1, 1, 1, Fraction(54, 5), 5, Fraction(5, 4)), False)
    check('beta_coefficient_scale_one_hundredth', 'do', kinds, dims, (1, 1, Fraction(1, 100), 3, 5, 125), True)
    check('beta_common_velocity_scale', 'do', kinds, dims, (7, 7, 1, 3, 5, Fraction(5, 4)), True)
    check('beta_speed_length_dimension_rejected', 'do', kinds, (length, time, length, velocity, scalar), base, False)
    check('beta_coefficient_time_dimension_rejected', 'do', kinds, (length, time, velocity, velocity, time), base, False)
    check('beta_different_velocity_kinds_rejected', 'do', (*kinds[:3], 'otherkind'), dims, base, False)
    check('beta_same_base_axis_rejected', 'do', ('length', 'length', 'speedkind', 'speedkind'), dims, base, False)
    check('beta_bad_base_vector_rejected', 'do', kinds, (dimension(length=1, mass=1), time, velocity, velocity, scalar), base, False)
    check('beta_zero_factor_scale_rejected', 'do', kinds, dims, (1, 1, 0, 3, 5, 0), False)
    return cases


def proof_checks():
    from noema.polynomial_proofs import verify_universal
    from scripts.check_real_products import MEANINGS, call, op, conjunction, assertion, ZERO, ONE
    text, _ = composed()
    ss, ls, fs, v, c, b, k, newscale, newvalue = ('v ' + n for n in ('ss', 'ls', 'fs', 'v', 'c', 'b', 'k', 'newscale', 'newvalue'))
    mul = lambda a, b: call('ad', a, b)
    positive = lambda x: call('aa', ZERO, x)
    beta = lambda a, d, e, f, g, h: call('dp', a, d, e, f, g, h)
    base = beta(ss, ls, fs, v, c, b)
    laws = {
        'beta_common_positive_velocity_scale_invariant': assertion('ss ls fs v c b k', op('y', positive(k),
            op('z', base, beta(mul(k, ss), mul(k, ls), fs, v, c, b)))),
        'beta_velocity_unit_and_reading_change_invariant': assertion('ss ls fs v c b newscale newvalue', op('y',
            conjunction(positive(ss), positive(newscale), op('e', mul(ss, v), mul(newscale, newvalue))),
            op('z', base, beta(newscale, ls, fs, newvalue, c, b)))),
        'beta_factor_unit_and_reading_change_invariant': assertion('ss ls fs v c b newscale newvalue', op('y',
            conjunction(positive(fs), positive(newscale), op('e', mul(fs, b), mul(newscale, newvalue))),
            op('z', base, beta(ss, ls, newscale, v, c, newvalue)))),
        'beta_unit_scale_zero_never_accepted': assertion('ss ls fs v c b', op('y', op('e', ss, ZERO), op('u', base))),
    }
    wrong = {'adding_common_offset_is_unit_conversion': assertion('',
        beta(ONE, ONE, ONE, 'n p e b', 'n p g b', 'n p f e'))}
    results = {}
    for name, claim in {**laws, **wrong}.items():
        result = verify_universal(parse(text + claim), MEANINGS)[0]
        if result['status'] != ('valid' if name in laws else 'invalid'):
            raise ValueError('Unexpected quantity proof: ' + name + ' ' + repr(result))
        results[name] = result
    return results


def build_report():
    import z3
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored quantities text differs')
    if json.loads((ROOT / 'data/quantities-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored quantities basis differs')
    doc = parse(text)
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Quantities round trip differs')
    paths = ['examples/v011/real-products.noema', 'examples/fragments/clock-coordinate.noema.inc',
             'examples/fragments/quantities.noema.inc', basis['document'], 'data/real-products-basis-v1.json',
             'data/quantities-basis-v1.json', 'scripts/compose_quantities.py', 'scripts/check_quantities.py',
             'scripts/check_real_products.py', 'noema/discourse.py', 'noema/finite_semantics.py',
             'noema/polynomial_proofs.py', 'noema/rational_proofs.py', 'noema/grammar.py', 'noema/semantics.py',
             'noema/script.py', 'noema/meaning_basis.py']
    return {'status': 'partial_quantity_foundation', 'basis_audit': audit_basis(doc, basis), 'roundtrips': True,
            'z3_version': z3.get_version_string(), 'finite_countermodels': finite_checks(), 'polynomial_checks': proof_checks(),
            'verified_full_source_units': 0, 'general_real_quantity_laws_machine_verified': False,
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Quantity report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('22 quantity countermodels and 5 polynomial checks reproduced; source coverage still partial')


if __name__ == '__main__':
    main()
