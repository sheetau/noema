"""Shared-event clock fixtures and algebraic (not acceleration) consequences."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.grammar import format_graph, number_word, parse
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import decode, encode
from scripts.check_finite_paths import ARITHMETIC, canonical, source_alignment as path_source_alignment
from scripts.compose_path_observations import ROOT, composed, v, call, eq, both, difference

REPORT = ROOT / 'reports/path-observations-v1.json'
CLAIMS = ROOT / 'examples/v014/path-observation-claims.noema'
DOMAIN = ('clock', 'reference', 'otherclock', 'lab', 'otherframe', 'length', 'otherlength',
          'timeunit', 'dialunit', 'otherunit', 'place', 'elsewhere', 'first', 'middle', 'last',
          'copy', 'out', 'back')


def fixture(label):
    scale = Fraction(60 if label == 'common_dial_scale' else 1)
    timeorigin = Fraction(7 if label == 'arbitrary_time_origin' else 0)
    origin = Fraction(-17 if label == 'arbitrary_dial_origin' else 10)
    times = {key: Fraction(value) + timeorigin for key, value in {'first': 0, 'middle': 5, 'last': 10, 'copy': 5}.items()}
    xs = {'first': Fraction(0), 'middle': Fraction(15), 'last': Fraction(0), 'copy': Fraction(15)}
    ys = {key: Fraction(0) for key in xs}
    zs = dict(ys)
    velocity = {'out': Fraction(3), 'back': Fraction(-3)}
    vy = {'out': Fraction(0), 'back': Fraction(0)}
    speeds = {'out': Fraction(3), 'back': Fraction(3)}
    rates = {'out': Fraction(4, 5), 'back': Fraction(4, 5)}
    if label == 'two_spatial_components':
        xs['middle'] = xs['copy'] = Fraction(9)
        ys['middle'] = ys['copy'] = Fraction(12)
        velocity = {'out': Fraction(9, 5), 'back': Fraction(-9, 5)}
        vy = {'out': Fraction(12, 5), 'back': Fraction(-12, 5)}
    if label == 'wrong_speed_norm':
        # Keep every endpoint displacement and the return position consistent;
        # only the supplied magnitude fails vx²+vy²+vz² = speed².
        ys['middle'] = ys['copy'] = Fraction(5)
        vy = {'out': Fraction(1), 'back': Fraction(-1)}
    if label in ('open_path', 'open_path_not_closed'):
        xs['last'], velocity['back'] = Fraction(30), Fraction(3)
    if label == 'stationary_intervals_have_no_gap':
        xs = {key: Fraction(0) for key in xs}
        velocity = {key: Fraction(0) for key in velocity}
        speeds = dict(velocity)
        rates = {key: Fraction(1) for key in rates}
    readings = {key: origin + scale * (times[key] - timeorigin) * rates['out'] for key in times}
    start, end = {'out': 'first', 'back': 'middle'}, {'out': 'middle', 'back': 'last'}
    elapsed = Fraction(10) * rates['out']
    args = dict(segments=('out', 'back'), start=start, end=end, clock='clock', frame='lab', scene='now',
                lengthunit='length', timeunit='timeunit', dialunit='dialunit', light=Fraction(5), scale=scale,
                first='first', last='last', time=times, x=xs, y=ys, z=zs, reading=readings,
                speed=speeds, vx=velocity, vy=vy, vz={'out': Fraction(0), 'back': Fraction(0)}, rate=rates,
                total=Fraction(10), elapsed=elapsed, lost=Fraction(10) - elapsed,
                reference='reference', place='place', offset=origin - scale * timeorigin,
                referencefirst=origin, referencelast=origin + scale * 10, gap=scale * (10 - elapsed))
    coordinates = {event: (times[event], xs[event], ys[event], zs[event]) for event in times}
    observed = {('clock', event): value for event, value in readings.items()}
    observed.update({('reference', 'first'): args['referencefirst'], ('reference', 'last'): args['referencelast']})
    if label == 'shared_event_reading_reset':
        readings['middle'] += 1
        observed['clock', 'middle'] = readings['middle']
    if label == 'equal_coordinates_different_event':
        start['back'] = 'copy'
    if label == 'wrong_interval_direction':
        velocity['back'] = Fraction(3)
    if label == 'wrong_total':
        args['total'] = Fraction(9)
    if label == 'wrong_elapsed':
        args['elapsed'] = Fraction(9)
    if label == 'wrong_scale':
        args['scale'] = Fraction(2)
    if label == 'negative_scale':
        args['scale'] = Fraction(-1)
    if label == 'same_departure_and_return_event':
        args['last'] = 'first'
    if label == 'reverse_segment_order':
        args['segments'] = ('back', 'out')
    if label == 'empty_path':
        args.update(segments=(), last='first', total=Fraction(0), elapsed=Fraction(0), lost=Fraction(0))
    if label == 'reference_not_initially_synchronous':
        args['referencefirst'] += 1
        args['referencelast'] += 1
        args['offset'] += 1
        args['gap'] += 1
        observed['reference', 'first'] += 1
        observed['reference', 'last'] += 1
    if label == 'reference_resets_at_arrival':
        args['referencelast'] += 1
        args['gap'] += 1
        observed['reference', 'last'] += 1
    if label == 'wrong_reported_gap':
        args['gap'] += 1
    if label == 'same_clock_as_reference':
        args['reference'] = 'clock'
    # All cut-valued arguments here are bb(q) for this finite set of q.
    # Midpoint probes distinguish those embeddings only; no arbitrary real
    # equality is inferred from these tests.
    candidates = sorted(set(readings.values()) | set(observed.values())
                        | {args['referencefirst'], args['referencelast']})
    probes = [(left + right) / 2 for left, right in zip(candidates, candidates[1:])]

    def coordinate(event, frame, scene, length, unit, *numbers):
        return (frame == ('otherframe' if label == 'wrong_coordinate_frame' and event == 'middle' else 'lab')
                and scene == ('other' if label == 'wrong_coordinate_context' else 'now')
                and length == ('otherlength' if label == 'wrong_length_unit' else 'length')
                and unit == ('otherunit' if label == 'wrong_coordinate_time_unit' else 'timeunit')
                and coordinates.get(event) == numbers)

    def reading(clock, event, frame, unit, cut):
        key = (clock, event)
        if label == 'different_clock_at_middle' and event == 'middle':
            key = ('clock' if clock == 'otherclock' else 'otherclock', event)
        if label == 'missing_middle_reading' and event == 'middle':
            return False
        if key not in observed:
            return False
        return (frame == ('otherframe' if label == 'wrong_reading_frame' else 'lab')
                and unit == ('otherunit' if label == 'wrong_dial_unit' and event == 'last' else 'dialunit')
                and tuple(cut(q) for q in probes) == tuple(q < observed[key] for q in probes))

    model = {d['name']: (lambda *values: False) for d in parse(composed()[0])['declarations'] if d['kind'] == 'primitive'}
    model.update(ARITHMETIC)
    model.update({'ma': lambda obj: obj in ('clock', 'reference'), 'pa': coordinate, 'me': reading,
                  'mi': lambda unit: unit in ('timeunit', 'dialunit'),
                  'pc': lambda frame, scene, length, unit, light: (frame, scene, length, unit, light) ==
                        ('lab', 'now', 'length', 'timeunit', 6 if label == 'wrong_light_speed' else 5),
                  'mc': lambda obj, frame: obj == 'reference' and frame == 'lab' and label != 'reference_not_stationary',
                  'mb': lambda obj, place, frame: obj in ('reference', 'first', 'last') and frame == 'lab'
                        and place == ('elsewhere' if (label == 'reference_at_other_place' and obj == 'reference')
                                      or (label == 'arrival_at_other_place' and obj == 'last') else 'place')})
    return args, model, candidates, probes


def evaluate_case(label):
    args, model, candidates, probes = fixture(label)
    doc = parse(composed()[0])
    symbol = 'jb' if label == 'open_path' else 'jc' if label == 'open_path_not_closed' else 'jd'
    declaration = next(d for d in doc['declarations'] if d['name'] == symbol)
    # Recover original parameter names from the unnormalized builder. Parameter
    # positions are canonicalized by parse; PATH keeps the authored contract.
    from scripts.compose_path_observations import PATH
    names = [name for name, _ in PATH]
    if symbol == 'jd':
        names += ['reference', 'place', 'offset', 'referencefirst', 'referencelast', 'gap']
    arguments = []
    for index, (name, parameter) in enumerate(zip(names, declaration['parameters'], strict=True)):
        value, sort = args[name], parameter['sort']
        if isinstance(sort, dict) and sort['kind'] == 'sequence':
            value = SequenceValue(tuple(value), canonical(sort['element']))
        elif isinstance(sort, dict) and sort['kind'] == 'function':
            mapping, default = value, ('first' if sort['result'] == 'individual' else Fraction(0))
            value = FunctionValue(tuple(sort['parameters']), sort['result'], lambda x, mapping=mapping, default=default: mapping.get(x, default))
        primitive = 'zz' + number_word(index)
        doc['declarations'].append({'kind': 'primitive', 'name': primitive, 'parameters': [], 'result': sort})
        model[primitive] = lambda value=value: value
        arguments.append({'kind': 'call', 'symbol': primitive, 'arguments': []})
    doc['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': symbol, 'arguments': arguments}}]
    result = evaluate_document(doc, individuals=DOMAIN, situations=('now', 'other'), primitives=model)[0]['value']
    return {'actual': result, 'definition': symbol,
            'rational_reading_candidates': [str(x) for x in candidates], 'distinguishing_probes': [str(x) for x in probes]}


def observation_checks():
    positives = ('baseline', 'common_dial_scale', 'arbitrary_time_origin', 'arbitrary_dial_origin',
                 'two_spatial_components', 'stationary_intervals_have_no_gap', 'open_path')
    negatives = ('open_path_not_closed', 'shared_event_reading_reset', 'equal_coordinates_different_event',
                 'wrong_interval_direction', 'wrong_speed_norm', 'wrong_total', 'wrong_elapsed', 'wrong_scale',
                 'negative_scale', 'same_departure_and_return_event', 'reverse_segment_order', 'empty_path',
                 'reference_not_initially_synchronous', 'reference_resets_at_arrival', 'wrong_reported_gap',
                 'same_clock_as_reference', 'wrong_coordinate_frame', 'wrong_coordinate_context',
                 'wrong_length_unit', 'wrong_coordinate_time_unit', 'different_clock_at_middle',
                 'missing_middle_reading', 'wrong_reading_frame', 'wrong_dial_unit', 'wrong_light_speed',
                 'reference_not_stationary', 'reference_at_other_place', 'arrival_at_other_place')
    results = {}
    for label in (*positives, *negatives):
        row = evaluate_case(label)
        row['expected'] = label in positives
        if row['actual'] != row['expected']:
            raise ValueError('Path observation differs: ' + label)
        results[label] = row
    return results


def claims():
    def assertion(names, body):
        for name in reversed(names.split()):
            body = 'f ' + name + ' b[' + body + ']'
        return 's[' + body + '].'
    mul = lambda a, b: call('ad', a, b)
    add = lambda a, b: call('ab', a, b)
    imply = lambda a, b: 'y[' + a + '][' + b + ']'
    t, middle, last, scale, rate, elapsed = [v(x) for x in ('t', 'middle', 'last', 'scale', 'rate', 'elapsed')]
    firstread, read, nextread, dt = [v(x) for x in ('firstread', 'read', 'nextread', 'dt')]
    offset = v('offset')
    return {
        'two_intervals_telescope': assertion('t middle last', eq(add(difference(middle, t), difference(last, middle)), difference(last, t))),
        'reading_invariant_survives_appending_interval': assertion('firstread read nextread scale elapsed dt rate', imply(
            both([eq(difference(read, firstread), mul(scale, elapsed)), eq(difference(nextread, read), mul(scale, mul(dt, rate)))]),
            eq(difference(nextread, firstread), mul(scale, add(elapsed, mul(dt, rate)))))),
        'elapsed_invariant_has_empty_base': assertion('firstread scale', eq(difference(firstread, firstread), mul(scale, 'n p a b'))),
        'synchronized_reference_gap_is_scaled_lost_time': assertion('t last scale offset elapsed firstread nextread', imply(
            both([eq(firstread, add(mul(scale, t), offset)), eq(difference(nextread, firstread), mul(scale, elapsed))]),
            eq(difference(add(mul(scale, last), offset), nextread), mul(scale, difference(difference(last, t), elapsed))))),
    }


def claim_document():
    return format_graph(parse('n:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.\n' + '\n'.join(claims().values())), 'compact') + '\n'


def proof_checks():
    rows = verify_universal(parse(claim_document()), {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'})
    results = dict(zip(claims(), rows, strict=True))
    if any(row['status'] != 'valid' for row in rows):
        raise ValueError('Path arithmetic invariant was not proved')
    return results


def source_alignment():
    rows = path_source_alignment()
    for row, definitions in zip(rows, (['ja', 'jb'], ['ja', 'jb', 'jc'], ['jc', 'jd']), strict=True):
        row['definitions'] = definitions
    return {'selections': rows,
            'uncovered': ['distant-clock synchronization in u0126', 'uniform motion between observed endpoints',
                          'accelerated junction law', 'continuous-curve limit', 'Earth clocks',
                          'complete attribution and source discourse']}


def build_report():
    import z3
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text or CLAIMS.read_text(encoding='utf-8') != claim_document():
        raise ValueError('Stored path observations differ')
    doc = parse(text)
    for notation in ('full', 'compact'):
        canonical_text = format_graph(doc, notation)
        if parse(canonical_text) != doc or parse(decode(encode(canonical_text, 'v2'))) != doc:
            raise ValueError('Observation roundtrip differs')
    files = [basis['document'], 'data/path-observations-basis-v1.json', CLAIMS.relative_to(ROOT).as_posix(),
             'scripts/compose_path_observations.py', 'scripts/check_path_observations.py',
             'examples/v014/einstein-finite-paths.noema', 'data/finite-paths-basis-v1.json',
             'scripts/check_finite_paths.py', 'noema/discourse.py', 'noema/finite_semantics.py',
             'noema/polynomial_proofs.py', 'noema/rational_proofs.py', 'noema/meaning_basis.py']
    return {'status': 'partial_path_observation_draft', 'basis_audit': audit_basis(doc, basis),
            'roundtrips': True, 'observation_checks': observation_checks(), 'polynomial_checks': proof_checks(),
            'z3_version': z3.get_version_string(), 'source_alignment': source_alignment(),
            'acceleration_law_derived': False, 'arbitrary_real_cut_equality_checked': False,
            'full_sequence_induction_machine_verified': False,
            'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    cli.add_argument('--finite-only', action='store_true')
    args = cli.parse_args()
    if args.finite_only:
        print(f'{len(observation_checks())} shared-event clock observations checked without a solver')
        return
    if not args.verify_only:
        text = claim_document()
        if CLAIMS.exists():
            if CLAIMS.read_text(encoding='utf-8') != text:
                raise ValueError('Stored claims differ')
        else:
            with CLAIMS.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Path observation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Shared events, clocks and units checked; acceleration physics remains an explicit premise')


if __name__ == '__main__':
    main()
