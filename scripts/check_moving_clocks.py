"""Exact rational rate laws and fourth-order remainder, with clock bindings."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from noema.discourse import definition_audit
from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_phi_normalization import MEANINGS, number, call
from scripts.check_quantities import ARITHMETIC
from scripts.compose_moving_clocks import composed, ALIASES

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/moving-clocks-v1.json'
CLAIMS = ROOT / 'examples/v011/einstein-moving-clock-claims.noema'


def arithmetic_document():
    doc = parse(composed()[0])
    dependencies = definition_audit(doc)['definition_primitive_dependencies']
    doc['declarations'] = [d for d in doc['declarations'] if (
        d['name'] in MEANINGS if d['kind'] == 'primitive' else set(dependencies[d['name']]) <= set(MEANINGS))]
    return doc


def claims():
    from scripts.check_real_products import ZERO, ONE, op, conjunction, assertion
    mul = lambda a, b: call('ad', a, b)
    add = lambda a, b: call('ab', a, b)
    sub = lambda a, b: add(a, call('ac', b))
    sq = lambda a: mul(a, a)
    eq = lambda a, b: op('e', a, b)
    lt = lambda a, b: call('aa', a, b)
    le = lambda a, b: op('u', lt(b, a))
    v, c, beta, rate, s, lag, approx, error = ['v ' + n for n in ('speed', 'light', 'beta', 'rate', 's', 'lag', 'approx', 'error')]
    ha = call('ha', v, c, rate)
    hg = call('hg', s, rate, lag, approx, error)
    first, last, firstproper, lastproper, scale, offset, firstread, lastread = [
        'v ' + n for n in ('first', 'last', 'firstproper', 'lastproper', 'scale', 'offset', 'firstread', 'lastread')]
    duration, elapsed, lost = 'v duration', 'v elapsed', 'v lost'
    hd = call('hd', v, c, beta, first, firstproper, last, lastproper)
    two, eight = number(2), number(8)
    facts = {
        'inverse_beta_is_the_positive_clock_rate': assertion('speed light beta rate', op('y', call('hb', v, c, beta, rate), ha)),
        'positive_rate_and_beta_fix_the_reciprocal': assertion('speed light beta rate', op('y',
            conjunction(ha, call('cm', v, c, beta)), eq(mul(beta, rate), ONE))),
        'positive_clock_rate_is_unique': assertion('speed light rate other', op('y',
            conjunction(ha, call('ha', v, c, 'v other')), eq(rate, 'v other'))),
        'zero_speed_has_rate_one': assertion('light rate', op('y', call('ha', ZERO, c, rate), eq(rate, ONE))),
        'rate_is_positive_and_at_most_one': assertion('speed light rate', op('y', ha, conjunction(lt(ZERO, rate), le(rate, ONE)))),
        'nonzero_velocity_has_strictly_smaller_rate': assertion('speed light rate', op('y',
            conjunction(ha, op('u', eq(v, ZERO))), lt(rate, ONE))),
        'rate_is_even_in_velocity': assertion('speed light rate', op('z', ha, call('ha', call('ac', v), c, rate))),
        'clock_worldline_gives_beta_times_proper_time': assertion('speed light beta time proper', op('y',
            call('hc', v, c, beta, 'v time', 'v proper'), eq(mul(beta, 'v proper'), 'v time'))),
        'ordered_events_have_positive_proper_elapsed': assertion('speed light beta first firstproper last lastproper', op('y', hd,
            conjunction(lt(firstproper, lastproper), eq(mul(beta, sub(lastproper, firstproper)), sub(last, first))))),
        'common_calibration_origin_cancels_in_elapsed_reading': assertion(
            'speed light beta first firstproper last lastproper scale offset firstread lastread', op('y',
                conjunction(hd, call('hk', scale, offset, firstproper, firstread), call('hk', scale, offset, lastproper, lastread)),
                eq(mul(beta, sub(lastread, firstread)), mul(scale, sub(last, first))))),
        'elapsed_and_lost_time_are_nonnegative': assertion('speed light rate duration elapsed lost', op('y',
            call('he', v, c, rate, duration, elapsed, lost), conjunction(le(ZERO, elapsed), le(ZERO, lost), le(lost, duration)))),
        'remainder_is_half_the_squared_lag': assertion('s rate lag approx error', op('y', hg,
            eq(mul(two, error), sq(lag)))),
        'exact_remainder_identity': assertion('s rate lag approx error', op('y', hg,
            eq(mul(mul(two, error), sq(add(ONE, rate))), sq(s)))),
        'fourth_order_remainder_bounds': assertion('s rate lag approx error', op('y', hg,
            conjunction(le(ZERO, error), le(sq(s), mul(eight, error)), le(mul(two, error), sq(s))))),
        'nonzero_speed_second_order_formula_underestimates_lag': assertion('speed light s rate lag approx error', op('y',
            conjunction(call('hi', v, c, s, rate, lag, approx, error), op('u', eq(v, ZERO))), lt(ZERO, error))),
        'duration_scales_the_same_remainder': assertion('speed light s rate lag approx error duration elapsed lost approximatelost errorlost', op('y',
            call('hj', v, c, s, rate, lag, approx, error, duration, elapsed, lost, 'v approximatelost', 'v errorlost'),
            conjunction(eq(sub(lost, 'v approximatelost'), 'v errorlost'),
                        le(mul(duration, sq(s)), mul(eight, 'v errorlost')),
                        le(mul(two, 'v errorlost'), mul(duration, sq(s)))))),
        'light_speed_and_beyond_not_a_positive_rate_solution': assertion('speed light rate', op('y',
            le(sq(c), sq(v)), op('u', ha))),
    }
    at = lambda symbol, *args: call(symbol, *(number(x) for x in args))
    errors = {
        'beta_is_not_the_clock_rate': assertion('', at('ha', 3, 5, Fraction(5, 4))),
        'negative_square_root_is_not_a_rate': assertion('', at('ha', 3, 5, Fraction(-4, 5))),
        'second_order_approximation_is_not_exact': assertion('', op('y',
            at('hg', Fraction(9, 25), Fraction(4, 5), Fraction(1, 5), Fraction(9, 50), Fraction(1, 50)),
            eq(number(Fraction(1, 5)), number(Fraction(9, 50))))),
        'absolute_reading_order_depends_on_origin': assertion('', op('y',
            at('hc', 3, 5, Fraction(5, 4), -10, -8), le(number(-8), number(-10)))),
        'independent_dial_origins_do_not_cancel': assertion('', op('y', conjunction(
            at('hk', 1, 10, 0, 10), at('hk', 1, 11, 8, 19)), eq(sub(number(19), number(10)), number(8)))),
    }
    return facts, errors


def proof_checks():
    text = format_graph(arithmetic_document(), 'compact')
    facts, errors = claims()
    results = {}
    for name, claim in {**facts, **errors}.items():
        row = verify_universal(parse(text + claim), MEANINGS, timeout_ms=15000)[0]
        if row['status'] != ('valid' if name in facts else 'invalid'):
            raise ValueError('Clock proof unresolved: ' + name + ' ' + repr(row))
        results[name] = row
    return results


def claim_document():
    return format_graph(parse(format_graph(arithmetic_document(), 'compact') + '\n' + '\n'.join(claims()[0].values())), 'compact') + '\n'


def numerical_checks():
    text = format_graph(arithmetic_document(), 'compact')
    cases = {}
    for label, symbol, args, expected in (
        ('three_fifths_speed_four_fifths_rate', 'ha', (3, 5, Fraction(4, 5)), True),
        ('beta_is_not_rate', 'ha', (3, 5, Fraction(5, 4)), False),
        ('clock_at_rest', 'ha', (0, 5, 1), True),
        ('negative_root_rejected', 'ha', (3, 5, Fraction(-4, 5)), False),
        ('superluminal_rate_rejected', 'ha', (6, 5, 1), False),
        ('two_events_eight_elapsed_out_of_ten', 'hd', (3, 5, Fraction(5, 4), 0, 0, 10, 8), True),
        ('wrong_elapsed_rejected', 'hd', (3, 5, Fraction(5, 4), 0, 0, 10, 10), False),
        ('unordered_events_rejected', 'hd', (3, 5, Fraction(5, 4), 10, 8, 0, 0), False),
        ('zero_interval_cannot_measure_a_rate', 'hd', (3, 5, Fraction(5, 4), 0, 0, 0, 0), False),
        ('past_origin_readings_are_allowed', 'hc', (3, 5, Fraction(5, 4), -10, -8), True),
        ('lag_and_quadratic_error_separate', 'hi', (3, 5, Fraction(9, 25), Fraction(4, 5), Fraction(1, 5), Fraction(9, 50), Fraction(1, 50)), True),
        ('zero_error_is_wrong_at_nonzero_speed', 'hi', (3, 5, Fraction(9, 25), Fraction(4, 5), Fraction(1, 5), Fraction(9, 50), 0), False),
        ('duration_ten_lost_two_approx_one_point_eight', 'hj', (3, 5, Fraction(9, 25), Fraction(4, 5), Fraction(1, 5), Fraction(9, 50), Fraction(1, 50), 10, 8, 2, Fraction(9, 5), Fraction(1, 5)), True),
        ('negative_duration_rejected', 'he', (3, 5, Fraction(4, 5), -10, -8, -2), False),
        ('arbitrary_common_dial_origin', 'hk', (1, 10, 8, 18), True),
        ('explicit_dial_scale', 'hk', (60, 10, 8, 490), True),
    ):
        doc = parse(text + 'q[' + call(symbol, *(number(x) for x in args)) + '].')
        actual = evaluate_document(doc, individuals=('object',), situations=('now',), primitives=ARITHMETIC)[0]['value']
        if actual != expected:
            raise ValueError('Clock numerical case differs: ' + label)
        cases[label] = {'expected': expected, 'actual': actual}
    return cases


def observation_checks():
    base = parse(composed()[0])
    domain = ('clock', 'otherclock', 'first', 'last', 'place', 'elsewhere', 'lab', 'rest', 'length', 'coordinateunit', 'dialunit')
    cases = {}
    for label in ('baseline', 'scaled_dial', 'not_a_clock', 'not_stationary_in_rest_frame', 'clock_at_other_place',
                  'last_event_at_other_place', 'wrong_reading_clock', 'wrong_reading_event', 'wrong_reading_unit',
                  'missing_last_reading', 'different_calibration_origin', 'wrong_context', 'wrong_velocity_direction',
                  'wrong_light_speed', 'wrong_frame_configuration', 'last_coordinate_not_on_clock_worldline',
                  'coordinate_unit_not_time', 'dial_unit_not_time'):
        doc, model = deepcopy(base), {d['name']: (lambda *args: False) for d in base['declarations'] if d['kind'] == 'primitive'}
        model.update(ARITHMETIC)
        scale = Fraction(60 if label == 'scaled_dial' else 1)
        firstread, lastread = Fraction(10), 8 * scale + 10
        # Every tested reading is a known rational embedding. These probes
        # distinguish this fixed set; they are not equality of arbitrary cuts.
        values = sorted({Fraction(10), Fraction(18), Fraction(19), Fraction(490)})
        probes = [(a + b) / 2 for a, b in zip(values, values[1:])]
        def reading(clock, event, frame, unit, cut):
            if label == 'missing_last_reading' and event == 'last':
                return False
            expected = firstread if event == 'first' else lastread
            if label == 'different_calibration_origin' and event == 'last':
                expected = Fraction(19)
            return (clock == ('otherclock' if label == 'wrong_reading_clock' else 'clock')
                    and event in (('first',) if label == 'wrong_reading_event' else ('first', 'last'))
                    and frame == 'rest' and unit == ('coordinateunit' if label == 'wrong_reading_unit' else 'dialunit')
                    and tuple(cut(q) for q in probes) == tuple(q < expected for q in probes))
        def location(obj, place, frame):
            expected = 'elsewhere' if ((label == 'clock_at_other_place' and obj == 'clock')
                                      or (label == 'last_event_at_other_place' and obj == 'last')) else 'place'
            return obj in ('clock', 'first', 'last') and place == expected and frame == 'rest'
        def coordinates(event, frame, scene, length, unit, *numbers):
            readings = {('first', 'lab'): (0, 0, 0, 0), ('last', 'lab'): (10, 30, 0, 0),
                        ('first', 'rest'): (0, 0, 0, 0), ('last', 'rest'): (8, 0, 0, 0)}
            if label == 'last_coordinate_not_on_clock_worldline':
                readings['last', 'rest'] = (8, 1, 0, 0)
            return scene == ('other' if label == 'wrong_context' else 'now') and length == 'length' and unit == 'coordinateunit' and readings.get((event, frame)) == numbers
        model.update({
            'ma': lambda clock: label != 'not_a_clock' and clock == 'clock',
            'mb': location,
            'mc': lambda clock, frame: clock == 'clock' and frame == ('lab' if label == 'not_stationary_in_rest_frame' else 'rest'),
            'me': reading,
            'mi': lambda unit: unit in ({'dialunit'} if label == 'coordinate_unit_not_time' else {'coordinateunit'} if label == 'dial_unit_not_time' else {'coordinateunit', 'dialunit'}),
            'pa': coordinates,
            'pb': lambda lab, rest, scene, length, unit, speed: (lab, rest, scene, length, unit, speed) == ('lab', 'rest', 'now', 'length', 'coordinateunit', -3 if label == 'wrong_velocity_direction' else 3),
            'pc': lambda lab, scene, length, unit, light: (lab, scene, length, unit, light) == ('lab', 'now', 'length', 'coordinateunit', 6 if label == 'wrong_light_speed' else 5),
            'pd': lambda lab, rest, scene: label != 'wrong_frame_configuration' and (lab, rest, scene) == ('lab', 'rest', 'now')})
        ids = ('clock', 'first', 'last', 'place', 'lab', 'rest', 'now', 'length', 'coordinateunit', 'dialunit')
        args = [('situation' if i == 6 else 'individual', value) for i, value in enumerate(ids)]
        args += [('number', Fraction(v)) for v in (3, 5, Fraction(5, 4), 0, 10, 0, 8, firstread,
                 19 if label == 'different_calibration_origin' else lastread, scale, 10)]
        arguments = []
        for i, (sort, value) in enumerate(args):
            name = 'zz' + number_word(i)
            doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
            model[name] = lambda value=value: value
            arguments.append({'kind': 'call', 'symbol': name, 'arguments': []})
        doc['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': 'hn', 'arguments': arguments}}]
        actual = evaluate_document(doc, individuals=domain, situations=('now', 'other'), primitives=model)[0]['value']
        expected = label in ('baseline', 'scaled_dial')
        if actual != expected:
            raise ValueError('Clock observation differs: ' + label)
        cases[label] = {'expected': expected, 'actual': actual}
    return cases


def source_alignment():
    path = ROOT / 'artifacts/written-units-v1/einstein-1905.json'
    inventory = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != inventory['works']['einstein-1905']['units_sha256']:
        raise ValueError('Source artifact differs')
    source = json.loads(path.read_text(encoding='utf-8'))
    selections = []
    for unit_id, math_id, definitions in (
        ('u0120', 'M0214', ['hc']), ('u0122', 'M0215', ['hc']), ('u0124', 'M0216', ['ha', 'hb', 'he', 'hl', 'hm']),
        ('u0125', 'M0217', ['hf', 'hi']), ('u0125', 'M0218', ['hg', 'hh', 'hi', 'hj']),
    ):
        unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:' + unit_id)
        math = next(m for m in source['math'] if m['id'] == math_id)
        if math_id not in unit['math_ids']:
            raise ValueError('Source clock equation in unexpected unit')
        selections.append({'unit': unit['id'], 'source_sha256': unit['text_sha256'], 'math_id': math_id,
                           'math_sha256': hashlib.sha256(math['mathml'].encode('utf-8')).hexdigest(),
                           'definitions': definitions, 'status': 'partial'})
    return {'selections': selections, 'context_units_still_partial': ['einstein-1905:u0118', 'einstein-1905:u0119', 'einstein-1905:u0125'],
            'accelerated_or_closed_paths_covered': False, 'approximation_not_identified_with_exact_value': True}


def build_report():
    import z3
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or CLAIMS.read_text(encoding='utf-8') != claim_document():
        raise ValueError('Stored clock document differs')
    doc = parse(text)
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Clock roundtrip differs')
    files = [CLAIMS.relative_to(ROOT).as_posix(), basis['document'], 'data/moving-clocks-basis-v1.json',
             'examples/fragments/moving-clocks.noema.inc', 'examples/v011/einstein-moving-shapes.noema',
             'data/moving-shapes-basis-v1.json', 'examples/v011/clock-protocol-extension.noema', 'data/clock-physical-basis-v1.json',
             'scripts/compose_moving_clocks.py', 'scripts/check_moving_clocks.py', 'scripts/check_phi_normalization.py',
             'scripts/check_quantities.py', 'scripts/check_real_products.py', 'reports/written-units-v1.json',
             'noema/discourse.py', 'noema/finite_semantics.py', 'noema/polynomial_proofs.py', 'noema/rational_proofs.py',
             'noema/grammar.py', 'noema/semantics.py', 'noema/script.py', 'noema/meaning_basis.py']
    return {'status': 'partial_moving_clocks_draft', 'basis_audit': audit_basis(doc, basis), 'roundtrips': True,
            'z3_version': z3.get_version_string(), 'polynomial_checks': proof_checks(), 'numerical_checks': numerical_checks(),
            'observation_checks': observation_checks(), 'source_alignment': source_alignment(), 'reused_clock_primitives': ALIASES,
            'reading_fixture': {'candidate_rational_readings': ['10', '18', '19', '490'],
                                'distinguishing_rational_probes': ['14', '37/2', '509/2'],
                                'scope': 'only the explicitly constructed rational embeddings'},
            'claim_document': {'path': CLAIMS.relative_to(ROOT).as_posix(),
                               'assertions': [{'index': i, 'check': name} for i, name in enumerate(claims()[0])]},
            'arbitrary_real_reading_equality_tested': False, 'general_cut_clock_laws_machine_verified': False,
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
                raise ValueError('Existing clock claims differ')
        else:
            with CLAIMS.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Moving clocks report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Clock rates, common origins and fourth-order remainder checked; source coverage remains partial')


if __name__ == '__main__':
    main()
