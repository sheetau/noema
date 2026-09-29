"""Check individual real-embedded observations, not a sampled continuum."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import format_graph, number_word, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.compose_worldlines import ROOT, composed

REPORT = ROOT / 'reports/worldlines-v1.json'
DOMAIN = ('clock', 'otherclock', 'event', 'other', 'frame', 'otherframe', 'lengthunit', 'timeunit', 'otherunit',
          'lengthaxis', 'timeaxis', 'author', 'previous', 'assumption', 'conclusion', 'scope')
CANDIDATES = tuple(map(Fraction, (-1, 0, 1, 2, 5, 8, 10, 14, 15, 16, 99)))
PROBES = tuple((a + b) / 2 for a, b in zip(CANDIDATES, CANDIDATES[1:]))
ARITHMETIC = {'aa': lambda a, b: a < b, 'ab': lambda a, b: a + b,
              'ac': lambda a: -a, 'ad': lambda a, b: a * b}


def rational_embedding(cut):
    values = tuple(cut(q) for q in PROBES)
    for candidate in CANDIDATES:
        if values == tuple(q < candidate for q in PROBES):
            return candidate
    raise ValueError('Not one of this fixture\'s rational embeddings')


def model_for(doc, variant):
    model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(ARITHMETIC)
    def coordinate(event, frame, context, length, timeunit, *cuts):
        numbers = tuple(rational_embedding(cut) for cut in cuts)
        allowed = {(Fraction(5), Fraction(15), Fraction(0), Fraction(0))}
        if variant == 'contradictory_coordinates':
            allowed.add((Fraction(5), Fraction(16), Fraction(0), Fraction(0)))
        return (event == ('other' if variant == 'wrong_event' else 'event')
                and frame == ('otherframe' if variant == 'wrong_frame' else 'frame')
                and context == ('othercontext' if variant == 'wrong_context' else 'context')
                and length == ('otherunit' if variant == 'wrong_length_unit' else 'lengthunit')
                and timeunit == ('otherunit' if variant == 'wrong_time_unit' else 'timeunit') and numbers in allowed)
    def reading(clock, event, frame, unit, cut):
        number = rational_embedding(cut)
        return (clock == 'clock' and event == 'event' and frame == 'frame'
                and unit == ('otherunit' if variant == 'wrong_reading_unit' else 'timeunit')
                and number in ({Fraction(14), Fraction(15)} if variant == 'contradictory_readings' else {Fraction(14)})
                and variant != 'missing_reading')
    def incidence(obj, event, context):
        return (obj == ('otherclock' if variant == 'wrong_object' else 'clock') and event == 'event'
                and context == ('othercontext' if variant == 'wrong_incidence_context' else 'context') and variant != 'missing_incidence')
    def unit_metadata(unit, dimension, scale):
        target = 'lengthaxis' if unit == 'lengthunit' else 'timeaxis'
        if variant == 'wrong_unit_dimension' and unit == 'lengthunit':
            target = 'timeaxis'
        expected_scale = Fraction(1, 1000) if variant == 'alternate_length_scale' and unit == 'lengthunit' else Fraction(1)
        if variant == 'negative_unit_scale' and unit == 'lengthunit':
            expected_scale = Fraction(-1)
        return unit in ('lengthunit', 'timeunit') and scale == expected_scale and all(dimension(x) == Fraction(x == target) for x in DOMAIN)
    model.update({'tf': coordinate, 'tg': incidence, 'tb': reading,
                  'ta': lambda obj: obj == 'clock' and variant != 'not_a_clock',
                  'te': lambda unit: unit == 'timeunit',
                  'tk': lambda frame, context: (frame, context) == ('frame', 'context') and variant != 'noninertial_frame',
                  'tj': lambda frame, context, length, timeunit, cut: (frame, context, length, timeunit, rational_embedding(cut)) ==
                        ('frame', 'othercontext' if variant == 'wrong_light_context' else 'context',
                         'otherunit' if variant == 'wrong_light_length_unit' else 'lengthunit', 'timeunit', 8 if variant == 'wrong_light_value' else 5),
                  'tl': unit_metadata})
    return model


def invoke_case(symbol, values, variant='baseline'):
    doc = parse(composed()[0])
    doc['statements'] = []
    declaration = next(d for d in doc['declarations'] if d['name'] == symbol)
    model, arguments = model_for(doc, variant), []
    for index, (param, value) in enumerate(zip(declaration['parameters'], values, strict=True)):
        sort = param['sort']
        if isinstance(sort, dict):
            value = FunctionValue(tuple(sort['parameters']), sort['result'], value)
        elif sort == 'number':
            value = Fraction(value)
        name = 'zz' + number_word(index)
        doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': sort})
        model[name] = lambda value=value: value
        arguments.append({'kind': 'call', 'symbol': name, 'arguments': []})
    doc['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': symbol, 'arguments': arguments}}]
    return evaluate_document(doc, individuals=DOMAIN, situations=('context', 'othercontext'), primitives=model)[0]['value']


def observation_checks():
    results = {}
    def record(name, symbol, values, expected, variant=None):
        actual = invoke_case(symbol, values, variant or name)
        if actual != expected:
            raise ValueError('Worldline fixture differs: ' + name)
        results[name] = {'symbol': symbol, 'expected': expected, 'actual': actual}
    point = ('clock', 'event', 'frame', 'context', 'lengthunit', 'timeunit', 5, 15, 0, 0, 14)
    for name in ('baseline', 'wrong_event', 'wrong_frame', 'wrong_context', 'wrong_length_unit', 'wrong_time_unit',
                 'wrong_reading_unit', 'missing_reading', 'wrong_object', 'wrong_incidence_context', 'missing_incidence', 'not_a_clock'):
        record(name, 'sk', point, name == 'baseline')
    record('wrong_coordinate_value', 'sk', (*point[:7], 16, *point[8:]), False, 'baseline')
    record('wrong_reading_value', 'sk', (*point[:-1], 15), False, 'baseline')
    length = lambda axis: Fraction(axis == 'lengthaxis')
    time = lambda axis: Fraction(axis == 'timeaxis')
    unit_args = ('frame', 'context', 'lengthunit', 'timeunit', 'lengthaxis', 'timeaxis', length, time, 1, 1, 5)
    for name in ('units_baseline', 'noninertial_frame', 'wrong_light_context', 'wrong_light_length_unit', 'wrong_light_value', 'wrong_unit_dimension'):
        record(name, 'sl', unit_args, name == 'units_baseline')
    record('alternate_length_scale', 'sl', (*unit_args[:8], Fraction(1, 1000), *unit_args[9:]), True)
    record('negative_unit_scale', 'sl', (*unit_args[:8], -1, *unit_args[9:]), False)
    record('merged_dimension_axes', 'sl', (*unit_args[:5], 'lengthaxis', *unit_args[6:]), False, 'baseline')
    record('wrong_supplied_dimension', 'sl', (*unit_args[:6], time, *unit_args[7:]), False, 'baseline')
    record('same_unit_for_space_and_time', 'sl', (*unit_args[:3], 'lengthunit', *unit_args[4:]), False, 'baseline')
    coords = ('event', 'frame', 'context', 'lengthunit', 'timeunit', 5, 15, 0, 0)
    record('duplicate_coordinates_agree', 'sm', (*coords, 5, 15, 0, 0), True, 'baseline')
    record('contradictory_coordinates', 'sm', (*coords, 5, 16, 0, 0), False)
    record('absent_second_coordinate_does_not_establish_existence', 'sm', (*coords, 5, 16, 0, 0), True, 'baseline')
    record('duplicate_readings_agree', 'so', ('clock', 'event', 'frame', 'context', 'timeunit', 14, 14), True, 'baseline')
    record('contradictory_readings', 'so', ('clock', 'event', 'frame', 'context', 'timeunit', 14, 15), False)
    record('absent_second_reading_does_not_establish_existence', 'so', ('clock', 'event', 'frame', 'context', 'timeunit', 14, 15), True, 'baseline')
    return results


def attribution_check():
    doc = parse(composed()[0])
    model = {d['name']: (lambda *args: True) for d in doc['declarations'] if d['kind'] == 'primitive'}
    for name, value in zip(('wa', 'wb', 'wc', 'wd', 'we', 'wf'),
                           ('author', 'previous', 'assumption', 'conclusion', 'scope', 'context'), strict=True):
        model[name] = lambda value=value: value
    seen = []
    def described(node, author, description, scope, context):
        seen.append(json.loads(description.syntax))
        return True
    def unexpected(*args):
        raise ValueError('Source attribution evaluated a worldline')
    for name in ('aa', 'ab', 'ac', 'ad', 'ta', 'tb', 'tc', 'td', 'te', 'tf', 'tg', 'tj', 'tk', 'tl'):
        model[name] = unexpected
    model.update(ug=described, uh=described)
    rows = evaluate_document(doc, individuals=DOMAIN, situations=('context',), primitives=model)
    if not all(row['value'] for row in rows) or [r['symbol'] for r in seen] != ['qi', 'qj']:
        raise ValueError('Full worldline conditions not attached to scoped source content')
    return {'premise': 'qi', 'conclusion': 'qj', 'contents_evaluated': False}


def refusal_check():
    # Directly request the general uniqueness assertion; no finite subset of
    # cut-valued coordinates may stand in for the entire domain.
    doc = parse(composed()[0])
    doc['statements'] = []
    for name, result in (('zza', 'individual'), ('zzb', 'situation'), ('zzc', 'individual'), ('zzd', 'individual')):
        doc['declarations'].append({'kind': 'primitive', 'name': name, 'parameters': [], 'result': result})
    doc['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': 'sd', 'arguments':
                          [{'kind': 'call', 'symbol': name, 'arguments': []} for name in ('zza', 'zzb', 'zzc', 'zzd')]}}]
    model = model_for(doc, 'baseline')
    model.update(zza=lambda: 'frame', zzb=lambda: 'context', zzc=lambda: 'lengthunit', zzd=lambda: 'timeunit')
    try:
        evaluate_document(doc, individuals=DOMAIN, situations=('context',), primitives=model)
    except ValueError as error:
        if 'rational number domain' not in str(error):
            raise
        return str(error)
    raise ValueError('Full coordinate uniqueness was replaced by finite sampling')


def build_report():
    text, basis = composed()
    if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
        raise ValueError('Stored worldline text differs')
    doc = parse(text)
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
            raise ValueError('Worldline roundtrip differs')
    from scripts.check_asymptotics import source_alignment
    alignment = source_alignment()
    for row in alignment['selections']:
        row['definitions'] = ['sh', 'qi', 'qj'] if row['math_id'] == 'M0241' else ['qe']
    alignment['uncovered'] = ['physical realization and grounding of new observation relations',
                              'preceding polygonal proof', 'Earth clock inference', 'full real-cut proof and facsimile review']
    files = [basis['document'], 'data/worldlines-basis-v1.json', 'scripts/compose_worldlines.py', 'scripts/check_worldlines.py',
             'scripts/compose_curve_discourse.py', 'scripts/compose_limits.py', 'scripts/check_asymptotics.py',
             'examples/v014/einstein-curve-approximation.noema', 'data/curve-approximation-basis-v1.json',
             'examples/v011/quantities.noema', 'data/quantities-basis-v1.json', 'data/path-observations-basis-v1.json',
             'noema/discourse.py', 'noema/finite_semantics.py', 'reports/written-units-v1.json']
    return {'status': 'partial_whole_interval_worldline_bindings', 'basis_audit': audit_basis(doc, basis), 'roundtrips': True,
            'observation_checks': observation_checks(), 'attribution': attribution_check(), 'finite_refusal': refusal_check(),
            'reading_fixture': {'candidates': [str(q) for q in CANDIDATES], 'probes': [str(q) for q in PROBES],
                                'scope': 'explicitly constructed rational embeddings only'},
            'source_alignment': alignment, 'all_real_times_finitely_verified': False, 'physical_laws_proved': False,
            'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
            'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Worldline report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(f"{len(report['observation_checks'])} point and unit checks; a continuum is not replaced by a finite sample")


if __name__ == '__main__':
    main()
