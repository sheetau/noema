"""Check transformed surfaces and simultaneous observations in a named frame."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from noema.discourse import definition_audit
from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_quantities import ARITHMETIC
from scripts.check_phi_normalization import MEANINGS, number, call
from scripts.compose_moving_shapes import composed

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/moving-shapes-v1.json'
CLAIMS = ROOT / 'examples/v011/einstein-moving-shape-claims.noema'


def arithmetic_document():
    doc = parse(composed()[0])
    dependencies = definition_audit(doc)['definition_primitive_dependencies']
    doc['declarations'] = [d for d in doc['declarations'] if (
        d['name'] in MEANINGS if d['kind'] == 'primitive' else set(dependencies[d['name']]) <= set(MEANINGS))]
    return doc


def claims():
    from scripts.check_real_products import ZERO, ONE, op, conjunction, assertion, apply
    mul = lambda a, b: call('ad', a, b)
    add = lambda a, b: call('ab', a, b)
    sub = lambda a, b: add(a, call('ac', b))
    sq = lambda a: mul(a, a)
    eq = lambda a, b: op('e', a, b)
    lt = lambda a, b: call('aa', a, b)
    names = 'speed light beta radius t x y z tau xi eta zeta'
    speed, light, beta, radius, t, x, y, z, tau, xi, eta, zeta = ['v ' + n for n in names.split()]
    axis, other, eps = 'v axis', 'v other', 'v epsilon'
    beta_condition = call('cm', speed, light, beta)
    axis_condition = call('ge', speed, light, radius, axis)
    facts = {
        'surface_equivalence_under_unit_phi_transform': assertion(names, op('y',
            call('fh', speed, light, beta, t, x, y, z, tau, xi, eta, zeta),
            op('z', call('ga', radius, xi, eta, zeta), call('gb', speed, light, beta, radius, t, x, y, z)))),
        'zero_time_slice_is_the_ellipsoid': assertion('speed light beta radius x y z', op('y', beta_condition,
            op('z', apply(call('gi', call('gh', speed, light, beta, radius), ZERO), x, y, z),
               call('gc', beta, radius, x, y, z)))),
        'center_moves_with_speed_in_each_slice': assertion('speed light beta radius t x y z', op('z',
            call('gb', speed, light, beta, radius, t, add(x, mul(speed, t)), y, z),
            call('gb', speed, light, beta, radius, ZERO, x, y, z))),
        'rest_sphere_has_time_independent_membership': assertion('radius t other x y z', op('z',
            apply(call('gg', radius), t, x, y, z), apply(call('gg', radius), other, x, y, z))),
        'positive_semiaxes_meet_the_ellipsoid': assertion('beta radius axis transversey transversez', op('y',
            call('gd', beta, radius, axis, 'v transversey', 'v transversez'), conjunction(
                call('gc', beta, radius, axis, ZERO, ZERO),
                call('gc', beta, radius, ZERO, 'v transversey', ZERO),
                call('gc', beta, radius, ZERO, ZERO, 'v transversez')))),
        'semiaxis_elimination_agrees_with_beta': assertion('speed light beta radius axis', op('y',
            conjunction(beta_condition, call('gd', beta, radius, axis, radius, radius)), axis_condition)),
        'zero_velocity_preserves_radius': assertion('light radius axis', op('y',
            call('ge', ZERO, light, radius, axis), eq(axis, radius))),
        'reversing_velocity_preserves_semiaxis': assertion('speed light radius axis', op('z',
            axis_condition, call('ge', call('ac', speed), light, radius, axis))),
        'longitudinal_semiaxis_never_exceeds_radius': assertion('speed light radius axis', op('y',
            axis_condition, op('u', lt(radius, axis)))),
        'larger_squared_speed_strictly_contracts_more': assertion('speed other light radius axis shorter', op('y',
            conjunction(axis_condition, call('ge', other, light, radius, 'v shorter'), lt(sq(speed), sq(other))),
            lt('v shorter', axis))),
        'axis_small_when_squared_speed_gap_is_small': assertion('speed light radius axis epsilon', op('y',
            conjunction(axis_condition, lt(ZERO, eps),
                        lt(mul(sq(radius), sub(sq(light), sq(speed))), mul(sq(light), sq(eps)))),
            lt(axis, eps))),
        'light_speed_is_not_a_positive_axis_solution': assertion('speed light radius axis', op('y',
            op('u', lt(sq(speed), sq(light))), op('u', axis_condition))),
    }
    pair_names = 'speed light beta t xone yone zone tone xione etaone zetaone xtwo ytwo ztwo ttwo xitwo etatwo zetatwo'
    pair = conjunction(
        call('fh', speed, light, beta, t, 'v xone', 'v yone', 'v zone', 'v tone', 'v xione', 'v etaone', 'v zetaone'),
        call('fh', speed, light, beta, t, 'v xtwo', 'v ytwo', 'v ztwo', 'v ttwo', 'v xitwo', 'v etatwo', 'v zetatwo'))
    facts['simultaneous_times_have_frame_dependent_difference'] = assertion(pair_names, op('y', pair,
        eq(mul(sq(light), sub('v ttwo', 'v tone')), call('ac', mul(mul(beta, speed), sub('v xtwo', 'v xone'))))))
    facts['simultaneous_in_both_frames_requires_zero_speed_or_equal_x'] = assertion(pair_names, op('y', pair,
        op('z', eq('v tone', 'v ttwo'), op('x', eq(speed, ZERO), eq('v xone', 'v xtwo')))))
    # Exact rational instances falsify tempting general claims. Keeping their
    # coordinates explicit avoids mistaking an irrational solver model for a Q witness.
    at = lambda symbol, *args: call(symbol, *(number(v) for v in args))
    errors = {
        'moving_longitudinal_endpoint_is_not_on_uncontracted_sphere': assertion('', op('y',
            at('gb', 3, 5, Fraction(5, 4), 5, 0, 4, 0, 0), at('ga', 5, 4, 0, 0))),
        'the_two_transverse_semiaxes_do_not_contract': assertion('',
            at('gd', Fraction(5, 4), 5, 4, 4, 4)),
        'two_lab_simultaneous_endpoints_are_not_rest_simultaneous': assertion('', op('y', conjunction(
            at('fh', 3, 5, Fraction(5, 4), 0, -4, 0, 0, Fraction(3, 5), -5, 0, 0),
            at('fh', 3, 5, Fraction(5, 4), 0, 4, 0, 0, Fraction(-3, 5), 5, 0, 0)),
            eq(number(Fraction(3, 5)), number(Fraction(-3, 5))))),
    }
    return facts, errors


def proof_checks():
    text = format_graph(arithmetic_document(), 'compact')
    facts, errors = claims()
    results = {}
    for label, claim in {**facts, **errors}.items():
        row = verify_universal(parse(text + claim), MEANINGS, timeout_ms=15000)[0]
        if row['status'] != ('valid' if label in facts else 'invalid'):
            raise ValueError('Shape proof unresolved: ' + label + ' ' + repr(row))
        results[label] = row
    return results


def claim_document():
    facts, _ = claims()
    text = format_graph(arithmetic_document(), 'compact') + '\n' + '\n'.join(facts.values())
    return format_graph(parse(text), 'compact') + '\n'


def numerical_checks():
    text = format_graph(arithmetic_document(), 'compact')
    cases = {}
    for label, symbol, args, expected in (
        ('longitudinal_surface_at_lab_time_zero', 'gb', (3, 5, Fraction(5, 4), 5, 0, 4, 0, 0), True),
        ('transverse_surface_at_lab_time_zero', 'gb', (3, 5, Fraction(5, 4), 5, 0, 0, 5, 0), True),
        ('contracting_transverse_axis_is_wrong', 'gb', (3, 5, Fraction(5, 4), 5, 0, 0, 4, 0), False),
        ('moving_center_at_later_time', 'gb', (3, 5, Fraction(5, 4), 5, 2, 10, 0, 0), True),
        ('earlier_slice_not_reused_at_later_time', 'gb', (3, 5, Fraction(5, 4), 5, 2, 4, 0, 0), False),
        ('center_is_not_surface', 'ga', (5, 0, 0, 0), False),
        ('zero_radius_is_not_this_sphere', 'ga', (0, 0, 0, 0), False),
        ('semiaxes_are_four_five_five', 'gd', (Fraction(5, 4), 5, 4, 5, 5), True),
        ('diameters_are_not_semiaxes', 'gd', (Fraction(5, 4), 5, 8, 10, 10), False),
        ('zero_velocity_radius_unchanged', 'ge', (0, 5, 5, 5), True),
        ('opposite_velocity_same_contraction', 'ge', (-3, 5, 5, 4), True),
        ('faster_velocity_shorter_axis', 'ge', (Fraction(24, 5), 5, 5, Fraction(7, 5)), True),
        ('finite_beta_at_light_speed_is_rejected', 'gb', (5, 5, 1, 5, 0, 0, 5, 0), False),
        ('zero_axis_at_light_speed_is_not_a_regular_sphere', 'ge', (5, 5, 5, 0), False),
    ):
        doc = parse(text + 'q[' + call(symbol, *(number(v) for v in args)) + '].')
        actual = evaluate_document(doc, individuals=('object',), situations=('now',), primitives=ARITHMETIC)[0]['value']
        if actual != expected:
            raise ValueError('Shape numerical case differs: ' + label)
        cases[label] = {'expected': expected, 'actual': actual}
    doc = parse(text + 'q[c[k gi[k gh[n p d b n p f b n p f e n p f b] n p c b]][n p k b n p a b n p a b]].')
    if not evaluate_document(doc, individuals=('object',), situations=('now',), primitives=ARITHMETIC)[0]['value']:
        raise ValueError('Generic time slice did not capture its instant')
    cases['generic_slice_captures_time_two'] = {'expected': True, 'actual': True}
    try:
        evaluate_document(parse(text + 'q[k gj[k gg[n p f b]]].'), individuals=('object',), situations=('now',), primitives=ARITHMETIC)
    except ValueError as error:
        if 'rational number domain' not in str(error):
            raise
        cases['all_times_and_positions_not_finitely_sampled'] = {'refused': str(error)}
    else:
        raise ValueError('All-time stationarity must not use finite samples')
    return cases


def observation_checks():
    base = parse(composed()[0])
    domain = ('first', 'second', 'lab', 'rest', 'length', 'time')
    rows = {
        ('first', 'lab'): tuple(map(Fraction, (0, -4, 0, 0))),
        ('second', 'lab'): tuple(map(Fraction, (0, 4, 0, 0))),
        ('first', 'rest'): (Fraction(3, 5), Fraction(-5), Fraction(0), Fraction(0)),
        ('second', 'rest'): (Fraction(-3, 5), Fraction(5), Fraction(0), Fraction(0)),
    }
    cases = {}
    for label in ('lab_slice', 'rest_time_zero', 'rest_first_event_time', 'wrong_context',
                  'wrong_length_unit', 'wrong_time_unit', 'missing_second_reading', 'second_outside_body',
                  'same_event_twice', 'wrong_geometric_radius'):
        doc = deepcopy(base)
        model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update(ARITHMETIC)
        def reading(event, frame, context, lengthunit, timeunit, *coordinates):
            if label == 'missing_second_reading' and event == 'second':
                return False
            return (context == 'now' and lengthunit == 'length' and timeunit == 'time'
                    and rows.get((event, frame)) == coordinates)
        model['pa'] = reading
        frame = 'rest' if label.startswith('rest_') else 'lab'
        instant = Fraction(3, 5) if label == 'rest_first_event_time' else Fraction(0)
        positions = (-5, 5) if frame == 'rest' else (-4, 4)
        if label == 'same_event_twice':
            positions = (-4, -4)
        body = FunctionValue(('individual',), 'truth', lambda event: event == 'first' or (event == 'second' and label != 'second_outside_body'))
        args = [({'kind': 'function', 'parameters': ['individual'], 'result': 'truth'}, body),
                ('individual', 'first'), ('individual', 'first' if label == 'same_event_twice' else 'second'),
                ('individual', frame), ('situation', 'other' if label == 'wrong_context' else 'now'),
                ('individual', 'time' if label == 'wrong_length_unit' else 'length'),
                ('individual', 'length' if label == 'wrong_time_unit' else 'time'),
                *[('number', Fraction(v)) for v in (instant, positions[0], 0, 0, positions[1], 0, 0)]]
        arguments = []
        for index, (sort, value) in enumerate(args):
            name = 'zz' + number_word(index)
            doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
            model[name] = lambda value=value: value
            arguments.append({'kind': 'call', 'symbol': name, 'arguments': []})
        radius = 6 if label == 'wrong_geometric_radius' else 5
        values = (radius,) if frame == 'rest' else (3, 5, Fraction(5, 4), radius)
        tube = {'kind': 'call', 'symbol': 'gg' if frame == 'rest' else 'gh', 'arguments': [
            {'kind': 'number', 'numerator': Fraction(v).numerator, 'denominator': Fraction(v).denominator} for v in values]}
        doc['statements'] = [
            {'kind': 'ask', 'body': {'kind': 'call', 'symbol': 'gs', 'arguments': [arguments[0], tube, *arguments[1:]]}},
            {'kind': 'ask', 'body': {'kind': 'call', 'symbol': 'gm', 'arguments': arguments}}]
        values = evaluate_document(doc, individuals=domain, situations=('now', 'other'), primitives=model)
        actual, membership = (row['value'] for row in values)
        expected = label == 'lab_slice'
        if actual != expected or membership != (label in ('lab_slice', 'wrong_geometric_radius')):
            raise ValueError('Frame-bound simultaneous events differ: ' + label)
        cases[label] = {'expected': expected, 'actual': actual, 'membership_and_simultaneity': membership}
    return cases


def source_alignment():
    path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Einstein source artifact differs')
    source = json.loads(path.read_text(encoding='utf-8'))
    selections = []
    for unit_id, math_id, definitions in (
        ('u0111', 'M0196', ['ga', 'gg', 'gn']), ('u0113', 'M0199', ['gb', 'gc', 'gi', 'go']),
        ('u0115', 'M0200', ['gd', 'ge', 'gp']),
    ):
        unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:' + unit_id)
        math = next(m for m in source['math'] if m['id'] == math_id)
        if math_id not in unit['math_ids']:
            raise ValueError('Source shape equation in unexpected unit')
        selections.append({'unit': unit['id'], 'source_sha256': unit['text_sha256'], 'math_id': math_id,
                           'math_sha256': hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest(),
                           'definitions': definitions, 'status': 'partial'})
    return {'selections': selections, 'context_units_still_partial': [
        'einstein-1905:u0110', 'einstein-1905:u0112', 'einstein-1905:u0114', 'einstein-1905:u0116', 'einstein-1905:u0117'],
        'same_time_bound_to_frame': True, 'light_speed_statement_not_a_regular_transform': True}


def build_report():
    import z3
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored shape document differs')
    if CLAIMS.read_text(encoding='utf-8') != claim_document():
        raise ValueError('Stored Noema shape claims differ')
    doc = parse(text)
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Shape roundtrip differs')
    files = [CLAIMS.relative_to(ROOT).as_posix(), 'scripts/compose_moving_shapes.py', 'scripts/check_moving_shapes.py',
             'scripts/check_phi_normalization.py', 'scripts/check_quantities.py', 'scripts/check_real_products.py',
             'examples/fragments/moving-shapes.noema.inc', basis['document'],
             'examples/v011/einstein-phi-normalization.noema', 'data/phi-normalization-basis-v1.json',
             'data/moving-shapes-basis-v1.json', 'reports/written-units-v1.json',
             'noema/discourse.py', 'noema/finite_semantics.py', 'noema/polynomial_proofs.py', 'noema/rational_proofs.py',
             'noema/grammar.py', 'noema/semantics.py', 'noema/script.py', 'noema/meaning_basis.py']
    return {'status': 'partial_moving_shapes_draft', 'basis_audit': audit_basis(doc, basis), 'roundtrips': True,
            'z3_version': z3.get_version_string(), 'polynomial_checks': proof_checks(), 'numerical_checks': numerical_checks(),
            'observation_checks': observation_checks(), 'source_alignment': source_alignment(),
            'claim_document': {'path': CLAIMS.relative_to(ROOT).as_posix(),
                               'assertions': [{'index': i, 'check': name} for i, name in enumerate(claims()[0])],
                               'scope': 'universal_rational_claims_under_explicit_conditions'},
            'general_cut_geometry_machine_verified': False, 'physical_rigidity_defined': False,
            'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    if not args.verify_only:
        text = claim_document()
        if CLAIMS.exists():
            if CLAIMS.read_text(encoding='utf-8') != text:
                raise ValueError('Existing Noema shape claims differ')
        else:
            with CLAIMS.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Moving shapes report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Sphere surfaces, semiaxes and simultaneous frames checked; source coverage remains partial')


if __name__ == '__main__':
    main()
