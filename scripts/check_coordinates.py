"""Coordinate identities and explicit event/frame countermodels."""
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
from scripts.compose_coordinates import composed
from scripts.check_quantities import ARITHMETIC, DIMENSION, dimension

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/coordinates-v1.json'
DOMAIN = ('event', 'other', 'rest', 'moving', 'lengthunit', 'timeunit', 'length', 'time', 'mass')
PHI = {'kind': 'function', 'parameters': ['number'], 'result': 'number'}


def query(doc, symbol, args, interpretations=None):
    candidate, arguments = deepcopy(doc), []
    primitives = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    primitives.update(ARITHMETIC)
    primitives.update(interpretations or {})
    for index, (sort, value) in enumerate(args):
        name = 'zz' + number_word(index)
        candidate['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
        primitives[name] = lambda value=value: value
        arguments.append({'kind': 'call', 'symbol': name, 'arguments': []})
    candidate['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': symbol, 'arguments': arguments}}]
    return evaluate_document(candidate, individuals=DOMAIN, situations=('now', 'elsewhere'), primitives=primitives)[0]['value']


def numerical_checks():
    doc = parse(composed()[0])
    cases = {}
    def check(label, symbol, args, expected):
        actual = query(doc, symbol, args)
        if actual != expected:
            raise ValueError('Coordinate arithmetic differs: ' + label)
        cases[label] = {'expected': expected, 'actual': actual}
    def numbers(values):
        return [('number', Fraction(v)) for v in values]
    initial = (2, 4, 6, 8)
    output = (Fraction(19, 10), Fraction(-5, 2), 6, 8)
    check('unit_phi_four_equations', 'ea', numbers((3, 5, Fraction(5, 4), 1, *initial, *output)), True)
    output_two = (Fraction(19, 5), -5, 12, 16)
    check('phi_two_is_not_replaced_by_one', 'ea', numbers((3, 5, Fraction(5, 4), 2, *initial, *output_two)), True)
    check('phi_two_cannot_leave_transverse_axes_unchanged', 'ea', numbers((3, 5, Fraction(5, 4), 2, *initial, Fraction(19, 5), -5, 6, 8)), False)
    check('wrong_time_mixing_sign', 'ea', numbers((3, 5, Fraction(5, 4), 1, *initial, Fraction(31, 10), *output[1:])), False)
    check('missing_light_speed_squared_denominator', 'ea', numbers((3, 5, Fraction(5, 4), 1, *initial, Fraction(-25, 2), *output[1:])), False)
    phi = FunctionValue(('number',), 'number', lambda v: v - 1)
    args = numbers((3, 5, Fraction(5, 4))) + [(PHI, phi)] + numbers((1, 2, 3, 4, *initial, Fraction(24, 5), -3, 15, 20))
    check('velocity_function_and_four_independent_origins', 'eh', args, True)
    changed = deepcopy(args)
    changed[4] = ('number', Fraction(0))
    check('dropping_time_origin_changes_relation', 'eh', changed, False)
    zero_phi = FunctionValue(('number',), 'number', lambda v: Fraction(0))
    zero_args = numbers((3, 5, Fraction(5, 4))) + [(PHI, zero_phi)] + numbers((1, 2, 3, 4, *initial, 1, 2, 3, 4))
    check('zero_phi_can_satisfy_raw_equations', 'ec', zero_args, True)
    check('zero_phi_is_not_a_coordinate_map', 'eh', zero_args, False)
    return cases


def observation_checks():
    doc = parse(composed()[0])
    cases = {}
    for change in ('baseline', 'different_event', 'wrong_target_frame', 'different_context', 'wrong_length_unit',
                   'wrong_time_unit', 'missing_coordinate', 'reversed_relative_frames', 'wrong_relative_speed',
                   'wrong_light_speed', 'axes_not_parallel', 'wrong_phi_parameter', 'wrong_origin_parameter',
                   'wrong_unit_metadata', 'wrong_parameter_units'):
        phi = FunctionValue(('number',), 'number', lambda v: v - 1)
        initial = tuple(map(Fraction, (2, 4, 6, 8)))
        final = (Fraction(24, 5), Fraction(-3), Fraction(15), Fraction(20))
        def coordinates(event, frame, context, lengthunit, timeunit, *values):
            expected_event = 'other' if change == 'different_event' and frame == 'moving' else 'event'
            if change == 'missing_coordinate' and frame == 'moving':
                return False
            return (event == expected_event and frame in (('rest', 'other') if change == 'wrong_target_frame' else ('rest', 'moving'))
                    and context == ('elsewhere' if change == 'different_context' and frame == 'moving' else 'now')
                    and lengthunit == ('other' if change == 'wrong_length_unit' else 'lengthunit')
                    and timeunit == ('other' if change == 'wrong_time_unit' else 'timeunit')
                    and values == (initial if frame == 'rest' else final))
        def metadata(unit, dim, scale):
            expected = 'length' if unit == 'lengthunit' else 'time'
            return (change != 'wrong_unit_metadata' and unit in ('lengthunit', 'timeunit') and scale == 1
                    and all(dim(axis) == (1 if axis == expected else 0) for axis in DOMAIN))
        model = {
            'pa': coordinates,
            'pb': lambda f, t, s, lu, tu, v: (f, t) == (('moving', 'rest') if change == 'reversed_relative_frames' else ('rest', 'moving'))
                and (s, lu, tu, v) == ('now', 'lengthunit', 'timeunit', 4 if change == 'wrong_relative_speed' else 3),
            'pc': lambda f, s, lu, tu, v: (f, s, lu, tu, v) == ('rest', 'now', 'lengthunit', 'timeunit', 6 if change == 'wrong_light_speed' else 5),
            'pd': lambda f, t, s: change != 'axes_not_parallel' and (f, t, s) == ('rest', 'moving', 'now'),
            'pe': metadata,
            'pf': lambda f, t, s, lu, tu, fun, ot, ox, oy, oz: (f, t, s) == ('rest', 'moving', 'now')
                and (lu, tu) == ('other' if change == 'wrong_parameter_units' else 'lengthunit', 'timeunit')
                and fun(Fraction(3)) == (1 if change == 'wrong_phi_parameter' else 2)
                and (ot, ox, oy, oz) == (0 if change == 'wrong_origin_parameter' else 1, 2, 3, 4),
        }
        args = [('individual', 'event'), ('individual', 'rest'), ('individual', 'moving'), ('situation', 'now')]
        args += [('individual', x) for x in ('lengthunit', 'timeunit', 'length', 'time')]
        args += [(DIMENSION, dimension(length=1)), (DIMENSION, dimension(time=1))]
        args += [('number', Fraction(v)) for v in (1, 1, 3, 5, Fraction(5, 4))] + [(PHI, phi)]
        args += [('number', Fraction(v)) for v in (1, 2, 3, 4, *initial, *final)]
        actual = query(doc, 'eg', args, model)
        expected = change == 'baseline'
        if actual != expected:
            raise ValueError('Observation countermodel differs: ' + change)
        cases[change] = {'expected': expected, 'actual': actual}
    return cases


def proof_checks():
    from noema.polynomial_proofs import verify_universal
    from scripts.check_real_products import MEANINGS, call, op, conjunction, assertion, ONE
    doc = parse(composed()[0])
    # Observation predicates are not arithmetic axioms and are never assigned
    # an arithmetic interpretation. The pure definitions remain unchanged.
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] not in ('pa', 'pb', 'pc', 'pd', 'pe', 'pf', 'eg')]
    text = format_graph(doc, 'compact')
    names = 'v c beta phi t x y z tau xi eta zeta'
    v, c, beta, phi, t, x, y, z, tau, xi, eta, zeta = ('v ' + n for n in names.split())
    mul = lambda a, b: call('ad', a, b)
    sub = lambda a, b: call('ab', a, call('ac', b))
    square = lambda a: mul(a, a)
    interval = lambda t, x, y, z: sub(sub(sub(mul(square(c), square(t)), square(x)), square(y)), square(z))
    transform = call('ea', v, c, beta, phi, t, x, y, z, tau, xi, eta, zeta)
    forward = call('ea', v, c, beta, ONE, t, x, y, z, tau, xi, eta, zeta)
    laws = {
        'interval_scales_by_phi_squared': assertion(names, op('y', transform,
            op('e', interval(tau, xi, eta, zeta), mul(square(phi), interval(t, x, y, z))))),
        'unit_phi_inverse_reverses_velocity': assertion(names.replace('phi ', ''), op('y', forward,
            call('ea', call('ac', v), c, beta, ONE, tau, xi, eta, zeta, t, x, y, z))),
    }
    results = {}
    for name, claim in laws.items():
        result = verify_universal(parse(text + claim), MEANINGS)[0]
        if result['status'] != 'valid':
            raise ValueError('Coordinate proof unresolved: ' + name + ' ' + repr(result))
        results[name] = result
    return results


def build_report():
    import z3
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored coordinate document differs')
    if json.loads((ROOT / 'data/coordinates-basis-v1.json').read_text(encoding='utf-8')) != basis:
        raise ValueError('Stored coordinate basis differs')
    doc = parse(text)
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Coordinate round trip differs')
    alignment = json.loads((ROOT / 'data/einstein-coordinates-v1.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    source_path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source artifact changed')
    source = json.loads(source_path.read_text(encoding='utf-8'))
    if alignment['document'] != basis['document']:
        raise ValueError('Source alignment document differs')
    for selection in alignment['selections']:
        unit = next(u for u in source['units'] if u['id'] == selection['source_unit'])
        if (unit['text_sha256'] != selection['source_sha256'] or selection['status'] != 'partial'
                or not set(selection['definitions']) <= set(basis['definitions'])):
            raise ValueError('Coordinate source unit differs')
        if 'math_id' in selection:
            math = next(m for m in source['math'] if m['id'] == selection['math_id'])
            if unit['math_ids'] != [math['id']] or hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest() != selection['math_sha256']:
                raise ValueError('Coordinate source equation differs')
    files = ['examples/v011/quantities.noema', 'data/quantities-basis-v1.json', basis['document'],
             'examples/fragments/coordinate-transform.noema.inc', 'examples/fragments/coordinate-observations.noema.inc',
             'data/coordinates-basis-v1.json', 'data/einstein-coordinates-v1.json', 'reports/written-units-v1.json',
             'scripts/compose_coordinates.py', 'scripts/check_coordinates.py', 'scripts/check_quantities.py', 'scripts/check_real_products.py',
             'noema/discourse.py', 'noema/finite_semantics.py', 'noema/polynomial_proofs.py', 'noema/rational_proofs.py',
             'noema/grammar.py', 'noema/semantics.py', 'noema/script.py', 'noema/meaning_basis.py']
    return {'status': 'partial_coordinate_and_observation_draft', 'basis_audit': audit_basis(doc, basis), 'roundtrips': True,
            'arithmetic_countermodels': numerical_checks(), 'observation_countermodels': observation_checks(),
            'z3_version': z3.get_version_string(), 'polynomial_identities': proof_checks(),
            'source_alignment': alignment, 'verified_full_units': 0,
            'general_real_coordinate_laws_machine_verified': False,
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Coordinate report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Coordinate equations and event/frame checks reproduced; full source coverage remains incomplete')


if __name__ == '__main__':
    main()
