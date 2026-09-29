"""Exact affine rational limit checks, with explicit separation from real cuts."""
import argparse
from copy import deepcopy
import hashlib
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.rational_proofs import verify
from noema.script import decode, encode
from scripts.compose_limits import ROOT, composed, v, call, app, op, lam, quant, ZERO

REPORT = ROOT / 'reports/limits-v1.json'
CLAIMS = ROOT / 'examples/v011/limit-claims.noema'
MEANINGS = {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'}
ONE, TWO, THREE = 'n p b b', 'n p c b', 'n p d b'


def claims():
    all_ = lam('x', 'b', op('e', v('x'), v('x')))
    empty = lam('x', 'b', op('u', op('e', v('x'), v('x'))))
    isolated = lam('x', 'b', op('e', v('x'), ZERO))
    positive = lam('x', 'b', call('aa', ZERO, v('x')))
    interval = lam('x', 'b', call('kf', ZERO, ONE, v('x')))
    identity = lam('x', 'b', v('x'))
    affine = lam('x', 'b', call('ab', call('ad', TWO, v('x')), THREE))
    constant = lam('x', 'b', THREE)
    rows = {
        'rational_line_has_accumulation_points': (quant('f', 'point', 'b', call('kb', all_, v('point'))), 'valid'),
        'right_hand_approach_to_zero': (call('kb', positive, ZERO), 'valid'),
        'empty_domain_is_not_an_approach': (call('kb', empty, ZERO), 'invalid'),
        'isolated_point_is_not_an_approach': (call('kb', isolated, ZERO), 'invalid'),
        'identity_limit_at_every_rational_point': (quant('f', 'point', 'b', call('kc', all_, identity, v('point'), v('point'))), 'valid'),
        'affine_limit_at_every_rational_point': (quant('f', 'point', 'b', call('kc', all_, affine, v('point'),
                                                  call('ab', call('ad', TWO, v('point')), THREE))), 'valid'),
        'wrong_limit_value_is_rejected': (call('kc', all_, identity, ZERO, ONE), 'invalid'),
        'right_hand_limit_does_not_need_value_at_point': (call('kc', positive, identity, ZERO, ZERO), 'valid'),
        'continuity_requires_point_in_domain': (call('kd', positive, identity, ZERO), 'invalid'),
        'isolated_point_is_continuous': (call('kd', isolated, affine, ZERO), 'valid'),
        'isolated_point_has_no_limit_under_accumulation_convention': (call('kc', isolated, affine, ZERO, THREE), 'invalid'),
        'empty_domain_has_no_limit': (call('kc', empty, identity, ZERO, ZERO), 'invalid'),
        'closed_interval_endpoint_is_continuous': (call('kd', interval, affine, ZERO), 'valid'),
        'affine_is_continuous_on_closed_interval': (call('ke', interval, affine), 'valid'),
        'constant_three_component_curve_is_closed': (call('kg', ZERO, ONE, constant, constant, constant), 'valid'),
        'continuous_open_line_is_not_closed': (call('kg', ZERO, ONE, identity, constant, constant), 'invalid'),
        'zero_parameter_duration_is_not_a_curve_interval': (call('kg', ZERO, ZERO, constant, constant, constant), 'invalid'),
        'zero_radius_is_not_a_neighborhood': (call('ka', ZERO, ZERO, ZERO), 'invalid'),
        'distance_equal_to_radius_is_outside': (call('ka', ONE, ZERO, ONE), 'invalid'),
    }
    return rows


def claim_document():
    doc = parse(composed()[0])
    text = format_graph(doc, 'compact') + '\n'
    text += '\n'.join('s[' + body + '].' for body, _ in claims().values())
    return format_graph(parse(text), 'compact') + '\n'


def proof_checks():
    rows = verify(parse(claim_document()), MEANINGS, timeout_ms=15000)
    results = {}
    for (name, (_, expected)), row in zip(claims().items(), rows, strict=True):
        if row['status'] != expected:
            raise ValueError('Limit proof differs: ' + name + ': ' + row['status'] + ' ' + str(row.get('reason')))
        results[name] = {'expected': expected, **row}
    return results


def finite_refusals():
    doc = parse(composed()[0])
    # Construct the AST from the very same limit assertion rather than silently
    # substituting a list of points in the domain.
    assertions = parse(claim_document())['statements']
    doc['statements'] = [deepcopy(assertions[4])]
    arithmetic = {'aa': lambda a, b: a < b, 'ab': lambda a, b: a + b,
                  'ac': lambda a: -a, 'ad': lambda a, b: a * b}
    try:
        evaluate_document(doc, individuals=('one',), situations=('now',), primitives=arithmetic)
    except ValueError as error:
        if 'rational number domain' not in str(error):
            raise
        return {'finite_sampling_refused': True, 'reason': str(error)}
    raise ValueError('A finite sample was accepted as all rationals')


def source_alignment():
    path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source artifact differs')
    source = json.loads(path.read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:u0128')
    return {'unit': unit['id'], 'text_sha256': unit['text_sha256'], 'status': 'partial', 'definitions': ['lh'],
            'scope': 'continuous closed geometric curve only',
            'uncovered': ['smoothness interpretation of stetig gekruemmte Kurve', 'polygonal approximation limit',
                          'constant physical speed', 'clock integral and acceleration law',
                          'conditional authorial assertion', 'Earth clocks']}


def build_report():
    import z3
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or CLAIMS.read_text(encoding='utf-8') != claim_document():
        raise ValueError('Stored limit document differs')
    doc = parse(text)
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Limit roundtrip differs')
    files = [basis['document'], 'data/limits-basis-v1.json', CLAIMS.relative_to(ROOT).as_posix(),
             'scripts/compose_limits.py', 'scripts/check_limits.py', 'examples/v011/real-products.noema',
             'data/real-products-basis-v1.json', 'noema/discourse.py', 'noema/finite_semantics.py',
             'noema/rational_proofs.py', 'noema/meaning_basis.py', 'reports/written-units-v1.json']
    return {'status': 'partial_limits_and_continuity_library', 'basis_audit': audit_basis(doc, basis),
            'roundtrips': True, 'rational_affine_proofs': proof_checks(), 'z3_version': z3.get_version_string(),
            'finite_refusals': finite_refusals(), 'source_alignment': source_alignment(),
            'rational_examples_prove_real_domain_continuity': False, 'general_cut_calculus_machine_verified': False,
            'curve_clock_law_derived': False, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    if not args.verify_only:
        text = claim_document()
        if CLAIMS.exists():
            if CLAIMS.read_text(encoding='utf-8') != text:
                raise ValueError('Existing limit claims differ')
        else:
            with CLAIMS.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Limit report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('19 rational affine checks; real-cut limits are defined, not finitely sampled')


if __name__ == '__main__':
    main()
