"""Verify the algebra behind phi=1, keeping its physical premises explicit."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_quantities import ARITHMETIC
from scripts.compose_phi_normalization import composed

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/phi-normalization-v1.json'
MEANINGS = {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'}


def call(symbol, *args):
    return 'k ' + symbol + '[' + ' '.join(args) + ']'


def arithmetic_document():
    doc = parse(composed()[0])
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] not in ('pa', 'pb', 'pc', 'pd', 'pe', 'pf', 'eg')]
    return doc


def claims():
    from scripts.check_real_products import ZERO, ONE, op, conjunction, assertion
    mul = lambda a, b: call('ad', a, b)
    equal = lambda a, b: op('e', a, b)
    positive = lambda a: call('aa', ZERO, a)
    p, m, q, proper, left, right = ('v ' + name for name in ('p', 'm', 'q', 'proper', 'left', 'right'))
    names = 'speed light beta p m t x y z tau xi eta zeta finalt finalx finaly finalz'
    args = ['v ' + n for n in names.split()]
    speed, light, beta = args[:3]
    original, intermediate, final = args[5:9], args[9:13], args[13:]
    composite = call('fg', *args)
    facts = {
        'opposite_velocities_have_equal_positive_beta': assertion('speed light beta other', op('y',
            conjunction(call('cm', speed, light, beta), call('cm', call('ac', speed), light, 'v other')),
            equal(beta, 'v other'))),
        'opposite_transform_composition_is_common_scaling': assertion(names, op('y', composite,
            call('ff', mul(p, m), *original, *final))),
        'reciprocity_gives_identity_for_all_four_coordinates': assertion(names, op('y',
            conjunction(composite, call('fa', p, m)), conjunction(*(equal(a, b) for a, b in zip(original, final))))),
        'identity_at_a_nonzero_probe_implies_reciprocity': assertion('p m q', op('y',
            conjunction(op('u', equal(q, ZERO)), equal(mul(mul(p, m), q), q)), call('fa', p, m))),
        'reciprocity_and_evenness_only_fix_the_square': assertion('p m', op('y',
            conjunction(call('fa', p, m), call('fb', p, m)), equal(mul(p, p), ONE))),
        'positive_branch_fixes_both_factors_to_one': assertion('p m', op('y', call('fd', p, m),
            conjunction(equal(p, ONE), equal(m, ONE)))),
        'equal_positive_rod_lengths_imply_even_positive_factors': assertion('proper left right p m', op('y',
            call('fc', proper, left, right, p, m), conjunction(call('fb', p, m), positive(p), positive(m)))),
        'reciprocity_and_rod_symmetry_fix_factors_and_lengths': assertion('proper left right p m', op('y',
            call('fe', proper, left, right, p, m),
            conjunction(equal(p, ONE), equal(m, ONE), equal(left, proper), equal(right, proper)))),
        'proved_factor_yields_the_final_transformation': assertion('speed light beta p m t x y z tau xi eta zeta', op('y',
            conjunction(call('fd', p, m), call('ea', speed, light, beta, p, *original, *intermediate)),
            call('fh', speed, light, beta, *original, *intermediate))),
        'transverse_endpoint_coordinates_follow_from_transform': assertion('speed light beta p proper t x y z tau', op('y',
            call('fk', speed, light, beta, p, proper, *original, 'v tau'),
            conjunction(equal('v x', mul(speed, 'v t')), equal('v z', ZERO), equal(mul(p, 'v y'), proper)))),
    }
    errors = {
        'reciprocity_alone_does_not_fix_phi': assertion('p m', op('y', call('fa', p, m), equal(p, ONE))),
        'evenness_without_positive_branch_allows_minus_one': assertion('p m', op('y',
            conjunction(call('fa', p, m), call('fb', p, m)), equal(p, ONE))),
        'even_positive_factors_without_reciprocity_need_not_be_one': assertion('p m', op('y',
            conjunction(call('fb', p, m), positive(p)), equal(p, ONE))),
        'zero_event_identity_does_not_fix_the_scale': assertion('p m q', op('y',
            equal(mul(mul(p, m), q), q), call('fa', p, m))),
    }
    return facts, errors


def proof_checks():
    text = format_graph(arithmetic_document(), 'compact')
    facts, errors = claims()
    results = {}
    for name, claim in {**facts, **errors}.items():
        result = verify_universal(parse(text + claim), MEANINGS, timeout_ms=15000)[0]
        expected = 'valid' if name in facts else 'invalid'
        if result['status'] != expected:
            raise ValueError('Phi proof unresolved: ' + name + ' ' + repr(result))
        results[name] = result
    return results


def number(value):
    value = Fraction(value)
    return 'n ' + ('u' if value < 0 else 'p') + ' ' + number_word(abs(value.numerator)) + ' ' + number_word(value.denominator)


def numerical_checks():
    text = format_graph(arithmetic_document(), 'compact')
    cases = {}
    entries = (
        ('reciprocal_but_unequal', 'fa', (2, Fraction(1, 2)), True),
        ('reciprocal_but_not_normalized', 'fd', (2, Fraction(1, 2)), False),
        ('negative_reciprocal', 'fa', (-1, -1), True),
        ('negative_even', 'fb', (-1, -1), True),
        ('negative_branch_rejected', 'fd', (-1, -1), False),
        ('positive_even_but_nonreciprocal', 'fd', (2, 2), False),
        ('positive_rod_complete_conditions', 'fe', (7, 7, 7, 1, 1), True),
        ('unequal_observed_lengths', 'fe', (7, Fraction(7, 2), 14, 2, Fraction(1, 2)), False),
        ('zero_length_cannot_fix_phi', 'fe', (0, 0, 0, 2, Fraction(1, 2)), False),
        ('signed_negative_extent_is_not_positive_length', 'fc', (7, -7, -7, -1, -1), False),
        ('absolute_length_alone_does_not_satisfy_signed_equations', 'fc', (7, 7, 7, -1, -1), False),
    )
    for label, symbol, args, expected in entries:
        doc = parse(text + 'q[' + call(symbol, *(number(v) for v in args)) + '].')
        actual = evaluate_document(doc, individuals=('object',), situations=('now',), primitives=ARITHMETIC)[0]['value']
        if actual != expected:
            raise ValueError('Phi numerical case differs: ' + label)
        cases[label] = {'expected': expected, 'actual': actual}
    doc = parse(text + 'r zz[] h[b] b.q[k fm[n p d b k zz[]]].')
    for label, function, expected in (
        ('same_function_positive_unit', lambda v: Fraction(1), True),
        ('same_function_negative_unit', lambda v: Fraction(-1), False),
        ('same_function_even_but_scaled', lambda v: Fraction(2), False),
        ('same_function_reciprocal_but_not_even', lambda v: Fraction(2) if v > 0 else Fraction(1, 2), False),
    ):
        model = {**ARITHMETIC, 'zz': lambda function=function: FunctionValue(('number',), 'number', function)}
        actual = evaluate_document(doc, individuals=('object',), situations=('now',), primitives=model)[0]['value']
        if actual != expected:
            raise ValueError('Phi function case differs: ' + label)
        cases[label] = {'expected': expected, 'actual': actual}
    try:
        doc = parse(text + 'q[k fo[n p f b i[x b][n p b b]]].')
        evaluate_document(doc, individuals=('object',), situations=('now',), primitives=ARITHMETIC)
    except ValueError as error:
        if 'rational number domain' not in str(error):
            raise
        cases['all_admissible_velocities_not_replaced_by_samples'] = {'refused': str(error)}
    else:
        raise ValueError('All rational velocities should not be enumerated')
    return cases


def source_alignment():
    path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Einstein source artifact differs')
    source = json.loads(path.read_text(encoding='utf-8'))
    selections = []
    for unit_id, math_id, definitions in (
        ('u0094', 'M0161', ['fg', 'ff']), ('u0096', 'M0169', ['fa']),
        ('u0098', 'M0179', ['fk']), ('u0100', 'M0180', ['fk']),
        ('u0102', 'M0186', ['fc', 'fj']), ('u0104', 'M0187', ['fb']),
        ('u0105', 'M0188', ['fd', 'fe', 'fi', 'fm', 'fn', 'fo']), ('u0106', 'M0189', ['fh']),
    ):
        unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:' + unit_id)
        math = next(m for m in source['math'] if m['id'] == math_id)
        if math_id not in unit['math_ids']:
            raise ValueError('Source equation in unexpected unit')
        selections.append({'unit': unit['id'], 'source_sha256': unit['text_sha256'], 'math_id': math_id,
                           'math_sha256': hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest(),
                           'definitions': definitions, 'status': 'partial'})
    return {'selections': selections, 'physical_context_units_still_partial': [
        'einstein-1905:u0093', 'einstein-1905:u0095', 'einstein-1905:u0097', 'einstein-1905:u0101'],
        'physical_identity_and_isotropy_derived_from_algebra': False,
        'positive_length_sign_convention_explicit': True}


def build_report():
    import z3
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored phi document differs')
    doc = parse(text)
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Phi roundtrip differs')
    files = ['scripts/compose_phi_normalization.py', 'scripts/check_phi_normalization.py',
             'scripts/check_real_products.py', 'scripts/check_quantities.py',
             'examples/fragments/phi-normalization.noema.inc', basis['document'],
             'examples/v011/einstein-coordinates.noema', 'data/coordinates-basis-v1.json',
             'data/phi-normalization-basis-v1.json', 'reports/written-units-v1.json',
             'noema/discourse.py', 'noema/finite_semantics.py', 'noema/polynomial_proofs.py',
             'noema/rational_proofs.py', 'noema/grammar.py', 'noema/semantics.py', 'noema/script.py', 'noema/meaning_basis.py']
    return {'status': 'partial_phi_normalization_draft', 'basis_audit': audit_basis(doc, basis), 'roundtrips': True,
            'z3_version': z3.get_version_string(), 'polynomial_checks': proof_checks(), 'numerical_checks': numerical_checks(),
            'source_alignment': source_alignment(), 'general_cut_field_derivation_machine_verified': False,
            'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Phi normalization report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Phi composition, sign and symmetry checks reproduced; full source coverage remains partial')


if __name__ == '__main__':
    main()
