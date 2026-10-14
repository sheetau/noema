"""Check the missing time link, including zero totals and actual clause probes."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json

from noema.extraction import extract_document
from noema.grammar import parse, format_graph
from noema.integration_audit import dependency_path
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_additive_charge import bridge_doc, bridge_model, PEOPLE, used_model
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_density_interpretation import attribution_checks
from scripts.check_described_appraisals import candidate
from scripts.check_field_equations import AXES
from scripts.check_plane_waveforms import setup, OPS
from scripts.check_rod_setup import callbacks
from scripts.compose_density_time import ROOT, PARENT, PARENT_BASIS, FULL, CORE, REVIEW, INDEX, BINDINGS, SOURCE, TIME, LOCAL, FIXED, POINT, BUILDERS, review_packet

REPORT = ROOT / 'reports/density-time-v1.json'
PROBE = [('jmatter', 'a'), ('jframe', 'a'), ('jevent', 'a'), ('jtime', 'a'), ('jcontext', 'd'),
    ('jclock', 'h[a a a d] h[b] c'), ('jpoint', POINT)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def clause_document(text, *, full=False):
    doc = parse(text)
    guard = next(d for d in doc['declarations'] if d['name'] == 'seox')
    universal = guard['body']['arguments'][1]
    if not full:
        # Instantiate the ACTUAL universal body, keeping the independent clock validity check.
        probe = dict(kind='definition', name='jztime', parameters=deepcopy(guard['parameters']) + [
            dict(name=universal['variable'], sort=deepcopy(universal['sort']))], result='truth',
            body=dict(kind='and', arguments=[deepcopy(guard['body']['arguments'][0]), deepcopy(universal['body'])]))
        doc['declarations'].append(probe)
    doc['statements'] = []
    fixture = ''.join('r ' + n + '[] ' + sort + '.' for n, sort in PROBE)
    names = PROBE[:6] if full else PROBE
    query = 'q[k ' + ('seox' if full else 'jztime') + '[' + ' '.join('k '+n+'[]' for n, _ in names) + ']].'
    return abstract(candidate(format_graph(doc, 'compact'), fixture + query), OPS)


def clause_model(doc, *, point_time=F(4), clock_time=F(4), record=True, query_change=None, unknown=False):
    cuts, model = setup(doc)
    entities = dict(jmatter='matter', jframe='frame', jevent='event', jtime='time', jcontext='text')
    if query_change:
        entities[query_change] = 'other'
    for name, value in entities.items():
        model[name] = lambda value=value: value
    point = (F(1), F(2), F(3), F(point_time))
    def clock(frame, event, unit, context):
        if unknown:
            raise ValueError('Clock interpretation missing')
        return cuts.make(clock_time if (frame, event, unit, context) == ('frame', 'event', 'time', 'text') else F(clock_time)+1)
    callbacks(doc, model, {'jclock': clock,
        'jpoint': lambda axis: cuts.make(point[AXES.index(axis)] if axis in AXES else 27)})
    model['zpb'] = lambda matter, frame, event, p, context: record and (matter, frame, event, context) == ('matter', 'frame', 'event', 'text')
    return used_model(doc, model)


def clause_checks(text):
    doc = clause_document(text)
    cases = [
        ('matching', {}, True),
        ('wrong_slice', dict(clock_time=F(5)), False),
        ('wrong_point_time', dict(point_time=F(5)), False),
        ('negative_matching', dict(point_time=F(-3, 2), clock_time=F(-3, 2)), True),
        ('fractional_mismatch', dict(point_time=F(1, 3), clock_time=F(2, 3)), False),
        ('unrelated_record', dict(record=False, clock_time=F(5)), True),
        ('other_matter', dict(query_change='jmatter', clock_time=F(5)), True),
        ('other_frame', dict(query_change='jframe', clock_time=F(5)), True),
        ('other_event', dict(query_change='jevent', clock_time=F(5)), True),
        ('other_context', dict(query_change='jcontext', clock_time=F(5)), True),
        ('wrong_time_unit', dict(query_change='jtime'), False),
    ]
    rows = {}
    for name, options, expected in cases:
        result = values(doc, clause_model(doc, **options), PEOPLE + ('matter',))
        require(result == [expected], 'Time probe failed: ' + name)
        rows[name] = result[0]
    try:
        values(doc, clause_model(doc, unknown=True), PEOPLE + ('matter',))
    except ValueError as exc:
        require('Clock interpretation missing' in str(exc), 'Unexpected refusal')
    else:
        raise ValueError('Unknown time was invented')
    full = clause_document(text, full=True)
    try:
        values(full, clause_model(full), PEOPLE + ('matter',))
    except ValueError as exc:
        reason = str(exc)
        require('rational number domain' in reason, 'Unexpected full-point refusal: ' + reason)
    else:
        raise ValueError('Full point domain was finitely certified')
    return dict(cases=rows, actual_universal_clause_instantiated=True, unknown_clock_refused=True,
        full_point_domain_refusal=reason, universal_agreement_proven=False)


def zero_total_counterexample(text):
    # The old adapter is still useful on an arbitrary chosen slice. Its spatial
    # contract must not itself stipulate the expected ball time, as the old test
    # oracle did. An everywhere-zero content is additive on either slice.
    doc = bridge_doc(text)
    rows = {}
    for variant in ('baseline', 'clock_frame'):
        model = bridge_model(doc, variant=variant, weights=(F(0), F(0)))
        model['seor'] = lambda universe, domain, total: True
        result = values(doc, model, PEOPLE)
        require(result == [True], 'Zero-content counterexample changed')
        rows[variant] = result[0]
    probe = clause_document(text)
    corrected = values(probe, clause_model(probe, clock_time=F(5)), PEOPLE + ('matter',))
    require(corrected == [False], 'The same-event wrong-time witness was accepted')
    return dict(old_adapter_accepts=rows, corrected_coordinate_clause=False,
        ball_time=4, charge_slice_time=5, amount=0,
        spatial_contracts_are_explicit_oracles=True,
        full_spatial_or_density_model_certified=False,
        interpretation='The old relative-slice adapter alone cannot enforce the time of the density center.')


def structural_checks(doc, parent):
    ds = {d['name']: d for d in doc['declarations']}
    require(doc['declarations'][:len(parent['declarations'])] == parent['declarations'], 'Historical declarations changed')
    require([d['name'] for d in doc['declarations'][len(parent['declarations']):]] == ['seox', 'seoy', 'seoz'], 'Unexpected declarations')
    expected = deepcopy(parent['statements'])
    expected[INDEX]['body']['arguments'][-1]['body']['symbol'] = 'seoz'
    require(doc['statements'] == expected, 'Source revision changed beyond the content symbol')
    variable = lambda name: dict(kind='variable', name=name)
    call = lambda symbol, *arguments: dict(kind='call', symbol=symbol, arguments=list(arguments))
    apply = lambda function, *arguments: dict(kind='apply', function=function, arguments=list(arguments))
    guard = ds['seox']
    refs = {n: variable(p['name']) for (n, _), p in zip(TIME, guard['parameters'], strict=True)}
    clock = apply(refs['clock'], *(refs[n] for n in ('frame', 'event', 'timeunit', 'context')))
    require(guard['body']['kind'] == 'and' and guard['body']['arguments'][0] == call('ba', clock), 'Missing independent clock validity')
    universal = guard['body']['arguments'][1]
    require(universal['kind'] == 'forall' and universal['sort'] == parse('n:r ja[] '+POINT+'.')['declarations'][0]['result'],
        'Agreement must cover every point representation')
    point = variable(universal['variable'])
    implication = universal['body']
    require(implication['kind'] == 'implies' and implication['arguments'][1] == call('seot', point, clock), 'Coordinate time lost clock binding')
    premise = implication['arguments'][0]
    require(premise['kind'] == 'and' and premise['arguments'][1] == call('zpb', refs['matter'], refs['frame'], refs['event'], point, refs['context']),
        'Agreement refers to a different observed event')
    def flatten(node):
        return flatten(node['arguments'][0])+flatten(node['arguments'][1]) if node.get('kind') == 'and' else [node]
    require(flatten(premise['arguments'][0]) == [call('ba', apply(point, call(axis))) for axis in ('yn', 'yo', 'yp', 'zc7')],
        'Validity must check all four coordinates')
    density = ds['seoy']
    outer = {n: variable(p['name']) for (n, _), p in zip(FIXED + [('clock', '')], density['parameters'], strict=True)}
    body = density['body']
    require(body['kind'] == 'lambda', 'Density relation must be constructed')
    local = {n: variable(p['name']) for (n, _), p in zip(LOCAL, body['parameters'], strict=True)}
    combined = outer | local
    require(body['body'] == dict(kind='and', arguments=[
        apply(call('seom', *(outer[n] for n, _ in FIXED)), *(local[n] for n, _ in LOCAL)),
        call('seox', *(combined[n] for n, _ in TIME))]), 'Density lost shared time or original density condition')
    content = ds['seoz']
    refs = {n: variable(p['name']) for (n, _), p in zip(SOURCE, content['parameters'], strict=True)}
    adapted = call('seou', *(refs[n] for n in ('distribution', 'timeunit', 'measured', 'clock', 'domains', 'totals')))
    linked = call('seoy', *(adapted if n == 'measured' else refs[n] for n, _ in FIXED), refs['clock'])
    inner = call('seof', refs['light'], linked, refs['electricassigned'], refs['frames'])
    require(content['body']['kind'] == 'content' and content['body']['body'] == dict(kind='and', arguments=[
        call('sedi', refs['pi']), dict(kind='evaluate', content=inner, situation=variable(content['body']['variable']))]),
        'Clock or original interpretation route changed')
    paths = {s: dependency_path(doc, INDEX, s) for s in ('seox', 'seoy', 'seom', 'seou', 'seof', 'seoc', 'senx')}
    require(all(paths.values()), 'Correction is outside the source quotation')
    return dict(dependency_paths=paths, all_valid_event_coordinates=True, same_clock_in_density_and_charge=True,
        old_density_conditions_retained=True, source_arguments_preserved=True)


def build_report():
    documents, texts, sizes = {}, {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder()
        require((ROOT / basis['document']).read_text(encoding='utf-8') == text, 'Stored manuscript differs')
        require(json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) == basis, 'Stored basis differs')
        doc = parse(text)
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            require(parse(form) == doc and parse(decode(encode(form, 'v2'))) == doc, 'Roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        texts[basis['document']] = text
        sizes[basis['document']] = dict(characters=len(text), declarations=len(doc['declarations']), statements=len(doc['statements']))
    doc = parse(texts[FULL]); parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    require(extract_document(doc, statement_indices=[INDEX]).document == parse(texts[CORE]), 'Extracted statement differs')
    require(json.loads((ROOT / REVIEW).read_text(encoding='utf-8')) == review_packet(), 'Review packet differs')
    previous = json.loads((ROOT / 'reports/density-interpretation-v1.json').read_text(encoding='utf-8'))
    alignment = deepcopy(previous['alignment'])
    alignment['segments'][1].update(definitions=['seox', 'seoy', 'seoz'],
        review_ja='密度の中心点と総電荷の対象範囲を同じ出来事の座標時刻へ明示的に接続。時刻不一致を零量で隠せない条件を本文に反映。全域と原文の意味確認は未完。')
    paths = [PARENT, PARENT_BASIS, FULL, CORE, REVIEW,
        *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_density_time.py', 'scripts/check_density_time.py', 'tests/test_density_time.py',
        'scripts/check_additive_charge.py', 'scripts/check_density_interpretation.py',
        'scripts/check_plane_waveforms.py', 'scripts/check_rod_setup.py',
        'scripts/check_coordinate_correspondence.py', 'scripts/check_comoving_labels.py',
        'scripts/check_described_appraisals.py', 'noema/integration_audit.py', 'noema/extraction.py',
        'noema/finite_semantics.py', 'reports/density-interpretation-v1.json', 'data/density-formula-review-v3.json']
    return dict(status='partial_density_time_connection_corrected', documents=documents, sizes=sizes,
        structure=structural_checks(doc, parent), probes=clause_checks(texts[CORE]),
        counterexample=zero_total_counterexample(texts[CORE]), attribution=attribution_checks(doc, parent),
        alignment=alignment, new_definitions=3, new_primitives=0, new_author_statements=0, revised_author_statements=1,
        roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args(argv)
    result = build_report()
    if args.verify_only:
        require(json.loads(REPORT.read_text(encoding='utf-8')) == result, 'Stored report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Same-event coordinate time linked to density and signed charge, including zero-total mismatch')


if __name__ == '__main__':
    main()
