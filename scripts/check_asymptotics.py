"""Check asymptotic witness semantics and the attributed clock remainder."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.rational_proofs import verify
from noema.script import decode, encode
from scripts.compose_asymptotics import ROOT, composed, source_composed
from scripts.compose_limits import v, call, op, lam, ZERO

REPORT = ROOT / 'reports/asymptotics-v1.json'
MEANINGS = {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'}
ARITHMETIC = {'aa': lambda a, b: a < b, 'ab': lambda a, b: a + b,
              'ac': lambda a: -a, 'ad': lambda a, b: a * b}


def witness_claims():
    all_ = lam('x', 'b', op('e', v('x'), v('x')))
    empty = lam('x', 'b', op('u', op('e', v('x'), v('x'))))
    one, two, three = 'n p b b', 'n p c b', 'n p d b'
    first = lam('x', 'b', call('ad', three, v('x')))
    second = lam('x', 'b', call('ad', two, v('x')))
    scale = lam('x', 'b', v('x'))
    constant = lambda value: lam('x', 'b', value)
    return {
        'signed_linear_error_bound': (call('oa', all_, first, second, scale, ZERO, one, one), 'valid'),
        'negative_comparison_scale_uses_absolute_value': (call('oa', all_, first, second, lam('x', 'b', call('ac', v('x'))), ZERO, one, one), 'valid'),
        'too_small_constant_fails': (call('oa', all_, first, second, scale, ZERO, 'n p b c', one), 'invalid'),
        'zero_neighborhood_fails': (call('oa', all_, first, second, scale, ZERO, one, ZERO), 'invalid'),
        'wrong_approach_point_fails': (call('oa', all_, first, second, lam('x', 'b', call('ab', v('x'), call('ac', one))), one, one, one), 'invalid'),
        'empty_domain_is_not_asymptotic': (call('ob', empty, constant(ZERO), constant(ZERO), constant(one), ZERO), 'invalid'),
        'exact_equality_is_bounded_error': (call('ob', all_, constant(ZERO), constant(ZERO), constant(one), ZERO), 'valid'),
        'bounded_constant_error_need_not_tend_to_zero': (call('ob', all_, constant(one), constant(ZERO), constant(one), ZERO), 'valid'),
        'zero_scale_cannot_hide_nonzero_error': (call('ob', all_, constant(one), constant(ZERO), constant(ZERO), ZERO), 'invalid'),
    }


def witness_checks():
    text = composed()[0] + '\n' + '\n'.join('s[' + body + '].' for body, _ in witness_claims().values())
    rows = verify(parse(text), MEANINGS, timeout_ms=15000)
    results = {}
    for (name, (_, expected)), row in zip(witness_claims().items(), rows, strict=True):
        if row['status'] != expected:
            raise ValueError('Asymptotic witness differs: ' + name + ' ' + row['status'])
        results[name] = {'expected': expected, **row}
    return results


def scalar_checks():
    # Reuse the already written scalar clock claims. These concern rational
    # polynomial conditions, not the whole real-cut Big-O assertion oh.
    chosen = ('remainder_is_half_the_squared_lag', 'exact_remainder_identity',
              'fourth_order_remainder_bounds', 'nonzero_speed_second_order_formula_underestimates_lag',
              'duration_scales_the_same_remainder')
    previous = json.loads((ROOT / 'reports/moving-clocks-v1.json').read_text(encoding='utf-8'))
    relative = previous['claim_document']['path']
    path = ROOT / relative
    if hashlib.sha256(path.read_bytes()).hexdigest() != previous['source_sha256'][relative]:
        raise ValueError('Preserved clock claims changed')
    doc = parse(path.read_text(encoding='utf-8'))
    indices = {row['check']: row['index'] for row in previous['claim_document']['assertions']}
    doc['statements'] = [doc['statements'][indices[name]] for name in chosen]
    rows = verify_universal(doc, MEANINGS, timeout_ms=15000)
    if any(row['status'] != 'valid' for row in rows):
        raise ValueError('Clock remainder witness failed')
    return dict(zip(chosen, rows, strict=True))


def finite_checks():
    cases = ((1, -1, 1, True), (-1, -1, 1, True), (0, 0, 1, True),
             (1, 0, 1, False), (1, 1, -1, False), (2, 1, 1, False))
    def number(value):
        q = Fraction(value)
        from noema.grammar import number_word
        return 'n ' + ('u' if q < 0 else 'p') + ' ' + number_word(abs(q.numerator)) + ' ' + number_word(q.denominator)
    results = []
    for error, scale, constant, expected in cases:
        doc = parse(composed()[0] + 'q[' + call('oi', number(error), number(scale), number(constant)) + '].')
        actual = evaluate_document(doc, individuals=('one',), situations=('now',), primitives=ARITHMETIC)[0]['value']
        if actual != expected:
            raise ValueError('Absolute error comparison differs')
        results.append({'error': str(error), 'scale': str(scale), 'constant': str(constant), 'expected': expected, 'actual': actual})
    return results


def attribution_check():
    doc = parse(source_composed()[0])
    model = {d['name']: (lambda *args: True) for d in doc['declarations'] if d['kind'] == 'primitive'}
    ids = ('author', 'previous', 'assumption', 'conclusion', 'scope', 'text')
    for name, value in zip(('wa', 'wb', 'wc', 'wd', 'we', 'wf'), ids, strict=True):
        model[name] = lambda value=value: value
    seen = []
    def quoted(node, author, description, scope, context):
        tree = json.loads(description.syntax)
        seen.append(tree)
        return tree == {'kind': 'call', 'symbol': 'qc' if node == 'assumption' else 'qf', 'arguments': []}
    def unexpected(*args):
        raise ValueError('Quoted approximation or physical content was evaluated')
    for name in ('aa', 'ab', 'ac', 'ad', 'ta', 'tb', 'tc', 'td', 'te'):
        model[name] = unexpected
    model.update(ug=quoted, uh=quoted)
    rows = evaluate_document(doc, individuals=ids[:-1], situations=('text',), primitives=model)
    if not all(row['value'] for row in rows) or [r['symbol'] for r in seen] != ['qc', 'qf']:
        raise ValueError('Approximation was not connected to scoped source claim')
    return {'quoted_assumption': 'qc', 'quoted_conclusion': 'qf', 'contents_evaluated': False}


def source_alignment():
    path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source artifact differs')
    source = json.loads(path.read_text(encoding='utf-8'))
    result = []
    for suffix, mid in (('u0126', 'M0229'), ('u0128', 'M0241')):
        unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:' + suffix)
        math = next(m for m in source['math'] if m['id'] == mid)
        if mid not in unit['math_ids']:
            raise ValueError('Clock approximation source changed')
        result.append({'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'math_id': mid,
                       'math_sha256': hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest(),
                       'status': 'partial', 'definitions': ['qe'] if suffix == 'u0126' else ['qe', 'qf'],
                       'coefficient_and_squared_velocity_ratio_represented': True})
    return {'selections': result, 'fourth_order_bounds_are_authors_explicit_constants': False,
            'source_scope': 'M0241 is read with the fourth-and-higher-order qualification in u0126',
            'duration_held_fixed_in_asymptotic_bound': True,
            'uncovered': ['full physical worldline and units', 'preceding polygonal proof', 'Earth clock inference',
                          'full real-cut calculus proof', 'facsimile review']}


def build_report():
    import z3
    text, basis = composed()
    source, source_basis = source_composed()
    for body, record in ((text, basis), (source, source_basis)):
        if (ROOT / record['document']).read_text(encoding='utf-8') != body:
            raise ValueError('Stored asymptotic document differs')
        doc = parse(body)
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Asymptotic roundtrip differs')
    files = [basis['document'], source_basis['document'], 'data/asymptotics-basis-v1.json',
             'data/curve-approximation-basis-v1.json', 'scripts/compose_asymptotics.py', 'scripts/check_asymptotics.py',
             'scripts/compose_limits.py', 'scripts/compose_curve_discourse.py', 'reports/moving-clocks-v1.json',
             'examples/v011/einstein-moving-clock-claims.noema', 'examples/v011/limits.noema', 'data/limits-basis-v1.json',
             'examples/v014/einstein-curve-discourse.noema', 'data/curve-discourse-basis-v1.json',
             'noema/discourse.py', 'noema/rational_proofs.py', 'noema/polynomial_proofs.py', 'noema/finite_semantics.py',
             'reports/written-units-v1.json']
    return {'status': 'partial_asymptotic_clock_approximation', 'generic_basis_audit': audit_basis(parse(text), basis),
            'source_basis_audit': audit_basis(parse(source), source_basis), 'roundtrips': True,
            'finite_checks': finite_checks(), 'witness_checks': witness_checks(), 'scalar_checks': scalar_checks(),
            'attribution': attribution_check(), 'source_alignment': source_alignment(), 'z3_version': z3.get_version_string(),
            'full_real_cut_big_o_proved': False, 'source_physical_inference_proved': False,
            'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    cli.add_argument('--finite-only', action='store_true')
    args = cli.parse_args()
    if args.finite_only:
        print(f'{len(finite_checks())} finite comparisons and scoped attribution checked; no asymptotic proof claimed')
        attribution_check()
        return
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Asymptotic report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('9 witness cases and 5 scalar clock lemmas checked; exact values and approximations remain distinct')


if __name__ == '__main__':
    main()
