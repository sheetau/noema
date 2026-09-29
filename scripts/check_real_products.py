"""Universal rational polynomial lemmas and partial Einstein beta alignment."""
import argparse
import hashlib
import json
from pathlib import Path

import z3

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.compose_real_products import composed

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/real-products-v1.json'
MEANINGS = {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'}
ZERO, ONE, TWO = 'n p a b', 'n p b b', 'n p c b'


def call(symbol, *args):
    return 'k ' + symbol + '[' + ' '.join(args) + ']'


def apply(function, *args):
    return 'c[' + function + '][' + ' '.join(args) + ']'


def op(symbol, *args):
    return symbol + ''.join('[' + a + ']' for a in args)


def conjunction(*args):
    return args[0] if len(args) == 1 else op('w', args[0], conjunction(*args[1:]))


def assertion(names, body):
    for name in reversed(names.split()):
        body = 'f ' + name + ' b[' + body + ']'
    return 's[' + body + '].'


def claims():
    r, q, a, b, x, y, gap, speed, light, factor, other = ('v ' + n for n in ('r', 'q', 'a', 'b', 'x', 'y', 'gap', 'speed', 'light', 'factor', 'other'))
    lt = lambda a, b: call('aa', a, b)
    ge = lambda a, b: op('u', lt(a, b))
    add = lambda a, b: call('ab', a, b)
    sub = lambda a, b: add(a, call('ac', b))
    mul = lambda a, b: call('ad', a, b)
    square = lambda a: mul(a, a)
    beta = lambda v, c, f: call('cm', v, c, f)
    lemmas = {
        'sqrt_of_nonnegative_rational_square': assertion('r q', op('y', ge(r, ZERO),
            op('z', apply(call('cj', call('bb', square(r))), q), lt(q, r)))),
        'general_sqrt_agrees_with_previous_sqrt_two': assertion('q', op('z',
            apply(call('cj', call('bb', TWO)), q), apply(call('bh'), q))),
        'positive_product_witness_is_below_product': assertion('a b x y q', op('y',
            conjunction(lt(ZERO, x), lt(x, a), lt(ZERO, y), lt(y, b), lt(q, mul(x, y))), lt(q, mul(a, b)))),
        'positive_product_given_gap_certifies_witness': assertion('a b q gap', op('y',
            conjunction(lt(ZERO, gap), lt(gap, a), lt(gap, b), lt(mul(gap, add(a, b)), sub(mul(a, b), q))),
            conjunction(lt(ZERO, sub(a, gap)), lt(ZERO, sub(b, gap)), lt(q, mul(sub(a, gap), sub(b, gap)))))),
        'positive_reciprocal_witness_is_below_inverse': assertion('r q a', op('y',
            conjunction(lt(ZERO, r), ge(a, r), lt(mul(q, a), ONE)), lt(mul(q, r), ONE))),
        'sqrt_gap_formula_certifies_larger_member': assertion('r q gap', op('y',
            conjunction(ge(q, ZERO), lt(square(q), r),
                        op('e', mul(mul(TWO, add(add(q, r), ONE)), gap), sub(r, square(q)))),
            conjunction(lt(ZERO, gap), lt(square(add(q, gap)), r)))),
        'beta_positive_branch_is_unique': assertion('speed light factor other', op('y',
            conjunction(beta(speed, light, factor), beta(speed, light, other)), op('e', factor, other))),
        'beta_is_even_in_speed': assertion('speed light factor', op('z',
            beta(speed, light, factor), beta(call('ac', speed), light, factor))),
        'beta_is_at_least_one': assertion('speed light factor', op('y', beta(speed, light, factor), ge(factor, ONE))),
        'zero_speed_has_factor_one': assertion('light', op('y', lt(ZERO, light), beta(ZERO, light, ONE))),
        'light_speed_and_beyond_have_no_finite_factor': assertion('speed light factor', op('y',
            ge(square(speed), square(light)), op('u', beta(speed, light, factor)))),
        'three_fifths_has_five_fourths_factor': assertion('', beta('n p d f', ONE, 'n p f e')),
        'negative_speed_has_same_factor': assertion('', beta('n u d f', ONE, 'n p f e')),
    }
    counterclaims = {
        'wrong_reciprocal_four_fifths': assertion('', beta('n p d f', ONE, 'n p e f')),
        'negative_sqrt_branch': assertion('', beta('n p d f', ONE, 'n u f e')),
        'superluminal_has_finite_factor': assertion('', beta('n p c b', ONE, ONE)),
    }
    return lemmas, counterclaims


def proof_checks():
    text, _ = composed()
    lemmas, counterclaims = claims()
    results = {}
    for name, claim in {**lemmas, **counterclaims}.items():
        result = verify_universal(parse(text + claim), MEANINGS)[0]
        if result['status'] != ('valid' if name in lemmas else 'invalid'):
            raise ValueError('Unexpected polynomial result: ' + name + ' ' + repr(result))
        results[name] = result
    return results


def build_report():
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored products document differs')
    if json.loads((ROOT / 'data/real-products-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored products basis differs')
    doc = parse(text)
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Products round trip differs')
    alignment = json.loads((ROOT / 'data/einstein-beta-v1.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    source_path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source artifact changed')
    source = json.loads(source_path.read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == alignment['source_unit'])
    math = next(m for m in source['math'] if m['id'] == alignment['math_id'])
    if (unit['text_sha256'] != alignment['source_sha256'] or unit['math_ids'] != [math['id']]
            or hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest() != alignment['math_sha256']
            or alignment['document'] != basis['document'] or alignment['definition'] not in basis['definitions']
            or alignment['status'] != 'partial'):
        raise ValueError('Beta alignment differs')
    files = ['examples/v011/real-cuts.noema', 'examples/fragments/real-products.noema.inc', basis['document'],
             'data/real-cuts-basis-v1.json', 'data/real-products-basis-v1.json', 'data/einstein-beta-v1.json',
             'scripts/compose_real_products.py', 'scripts/check_real_products.py', 'noema/polynomial_proofs.py',
             'noema/rational_proofs.py', 'noema/discourse.py', 'noema/meaning_basis.py', 'noema/grammar.py',
             'noema/script.py', 'noema/semantics.py', 'reports/written-units-v1.json']
    return {'status': 'partial_real_arithmetic_and_beta_draft', 'basis_audit': audit_basis(doc, basis),
            'z3_version': z3.get_version_string(), 'universal_rational_polynomial_checks': proof_checks(),
            'roundtrips': True, 'source_alignment': alignment, 'verified_full_units': 0,
            'general_real_field_laws_machine_verified': False, 'cut_beta_and_algebraic_beta_equivalence_machine_verified': False,
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Real products report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('13 polynomial lemmas valid, 3 counterclaims invalid; beta source alignment remains partial')


if __name__ == '__main__':
    main()
