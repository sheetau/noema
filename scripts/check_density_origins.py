"""Check common-zero event identity, scope and retained density quotation."""
import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import product
import json
import subprocess
import sys
from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.extraction import extract_document
from noema.meaning_basis import audit_basis
from noema.integration_audit import dependency_path
from noema.script import transcribe
from scripts.compose_density_origins import ROOT, PARENT, FULL, CORE, INDEX, FIELDS, MEANINGS, CUT, build
from scripts.compose_limits import call as k, app
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded, callbacks
from scripts.check_plane_waveforms import setup, OPS

REPORT = ROOT/'reports/density-origins-v1.json'
DOMAIN = ('event', 'other_event', 'oldrecord', 'newrecord', 'old', 'new', 'third',
          'oldorigin', 'neworigin', 'otherorigin', 'x', 'y', 'z', 't')


@lru_cache(None)
def text(path): return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc, model, memoize=True):
    names = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=('text', 'other'),
        primitives={n: m for n, m in model.items() if n in names}, max_steps=5_000_000,
        memoize_definitions=memoize, memoize_expressions=memoize)]


@lru_cache(None)
def fixture(path=CORE):
    extra = 'r jaevent[] a.r jafirst[] a.r jasecond[] a.r javalue[] '+CUT+'.r jacontext[] d.'
    extra += 'q['+k('sexu', k('jaevent'), k('jacontext'))+'].'
    extra += 'q['+app(k('sexv'), *(k('ja'+n) for n in ('first', 'second', 'value', 'context')))+'].'
    # Actual smk/sha/sexu/sexv execute. Existing coordinate assignment and the
    # prior full frame condition are explicit boundaries, not inferred facts.
    return abstract(candidate(text(path), extra), OPS | {'shd', 'sext'})


def model_for(doc, variant):
    cuts, model = setup(doc)
    coords = {r: dict.fromkeys(('x', 'y', 'z', 't'), 0) for r in ('oldrecord', 'newrecord')}
    if variant.startswith('nonzero_'):
        _, frame, role = variant.split('_'); coords[frame+'record'][role] = 1
    if variant == 'moving_origin_at_later_time': coords['oldrecord'].update(x=3, t=1)
    if variant == 'shifted_both_origins':
        for row in coords.values(): row['x'] = 2
    if variant == 'shifted_both_times':
        for row in coords.values(): row['t'] = 1
    witness = 'other_event' if variant == 'second_event_is_common_witness' else 'event'
    pairs = {(witness, 'oldrecord', 'old', 'text'),
        ('other_event' if variant == 'different_events_same_zero_values' else witness, 'newrecord', 'new', 'text')}
    if variant == 'missing_assignment': pairs.remove((witness, 'newrecord', 'new', 'text'))
    if variant in ('assignment_wrong_frame', 'assignment_wrong_context'):
        pairs.remove((witness, 'newrecord', 'new', 'text'))
        pairs.add((witness, 'newrecord', 'old' if variant.endswith('frame') else 'new',
                   'other' if variant.endswith('context') else 'text'))
    def record(event, frame, context): return 'oldrecord' if frame == 'old' else 'newrecord'
    def coordinate(record, role):
        if variant == 'unknown_coordinate' and record == 'newrecord' and role == 't':
            raise ValueError('missing coordinate input')
        return cuts.make(coords[record][role])
    def assigned(event, rec, frame, context):
        if variant == 'unknown_assignment': raise ValueError('missing assignment input')
        return (event, rec, frame, context) in pairs
    origins = {'old': 'oldorigin', 'new': 'neworigin'}
    def origin(frame, context): return origins.get(frame, 'otherorigin')
    def origin_assigned(frame, point, context):
        return (frame in origins and point == origins[frame] and context == 'text'
            and variant != 'missing_'+frame+'_origin_assignment')
    def placed(event, point, frame):
        return (event == witness and frame in origins and point == origins[frame]
            and variant != 'missing_'+frame+'_origin_placement')
    constants = dict(jaevent='event', jafirst='old', jasecond='new', jacontext='text',
        ra='old', zbm='new', yn='x', yo='y', yp='z', zc7='t')
    if variant == 'wrong_supplied_context': constants['jacontext'] = 'other'
    if variant == 'wrong_supplied_frame': constants['jafirst'] = 'third'
    if variant == 'duplicate_roles': constants['zc7'] = 'z'
    for n, value in constants.items(): model[n] = lambda value=value: value
    model.update(zdz=record, zc6=coordinate, shd=assigned, zbn=origin, zbv=origin_assigned, cb=placed,
        zc4=lambda event: variant != 'not_an_event' and event in ('event', 'other_event'),
        zc5=lambda rec: rec in coords and variant != 'invalid_'+rec,
        zb7=lambda: cuts.make(3), javalue=lambda: cuts.make(2 if variant == 'wrong_supplied_speed' else 3))
    if variant == 'invalid_cut': model['ba'] = lambda value: False
    if variant == 'unknown_validity':
        def unknown(value): raise ValueError('missing validity input')
        model['ba'] = unknown
    callbacks(doc, model, {'sext': lambda first, second, value, context:
        variant != 'prior_frame_condition_false' and
        (first, second, cuts.read(value), context) == ('old', 'new', 3, 'text')})
    return model


@lru_cache(None)
def origin_checks():
    cases = {'baseline': [True, True], 'second_event_is_common_witness': [False, True]}
    bad = ('different_events_same_zero_values', 'missing_assignment', 'assignment_wrong_frame',
        'assignment_wrong_context', 'wrong_supplied_context', 'not_an_event', 'invalid_oldrecord',
        'invalid_newrecord', 'invalid_cut', 'duplicate_roles', 'moving_origin_at_later_time',
        'shifted_both_origins', 'shifted_both_times')
    bad += tuple('missing_'+frame+'_origin_'+kind for frame in ('old', 'new') for kind in ('assignment', 'placement'))
    bad += tuple('nonzero_'+frame+'_'+role for frame in ('old', 'new') for role in ('x', 'y', 'z', 't'))
    cases.update({n: [False, False] for n in bad})
    cases.update({n: [True, False] for n in ('prior_frame_condition_false', 'wrong_supplied_frame', 'wrong_supplied_speed')})
    rows = {}; refused = []; uncached = {}
    for path in (CORE, FULL):
        doc = fixture(path); rows[path] = {}
        for name, expected in cases.items():
            actual = evaluate(doc, model_for(doc, name)); assert actual == expected, (path, name, actual)
            rows[path][name] = actual
        for name in ('baseline', 'different_events_same_zero_values', 'second_event_is_common_witness', 'prior_frame_condition_false'):
            actual = evaluate(doc, model_for(doc, name), memoize=False)
            assert actual == cases[name]; uncached[path+':'+name] = actual
    doc = fixture()
    for name in ('unknown_coordinate', 'unknown_assignment', 'unknown_validity'):
        try: evaluate(doc, model_for(doc, name))
        except ValueError as exc: assert 'missing' in str(exc); refused.append(name)
        else: raise AssertionError(name)
    return dict(cases=rows, uncached=uncached, unknown_inputs_refused=refused,
        abstracted_boundaries=['shd', 'sext'], arithmetic_boundary=sorted(OPS),
        actual_definitions=['smk', 'sha', 'sexu', 'sexv'], finite_constructed_rational_cuts_only=True,
        distinct_origin_objects_permitted=True, general_origin_offsets_covered=False, physical_assignment_proved=False)


def structure_and_attribution():
    old, doc = parse(text(PARENT)), parse(text(FULL))
    assert len(old['statements']) == len(doc['statements']) == 206
    assert doc['declarations'][:len(old['declarations'])] == old['declarations']
    added = doc['declarations'][len(old['declarations']):]
    assert {d['name'] for d in added} == set(MEANINGS) and all(d['kind'] == 'definition' for d in added)
    original = old['statements'][INDEX]['body']['arguments'][-1]['body']
    revised = doc['statements'][INDEX]['body']['arguments'][-1]['body']
    assert [n for (n, _), a, b in zip(FIELDS, original['arguments'], revised['arguments'], strict=True) if a != b] == ['frames']
    restored = deepcopy(doc['statements']); restored[INDEX] = old['statements'][INDEX]
    assert restored == old['statements']
    paths = {n: dependency_path(doc, INDEX, n) for n in ('sexv', 'sexu', 'smk', 'sha', 'sext', 'zqf', 'shd', 'zbv', 'zbn', 'cb', 'zdz', 'zc4', 'zc5', 'zc6', 'ra', 'zbm', 'zb7')}
    assert all(paths.values())
    quoted = extract_document(doc, statement_indices=[INDEX]).document
    assert quoted == parse(text(CORE))
    rows = []
    for present, explain, order in product((False, True), repeat=3):
        model = guarded(quoted)
        for name, value in dict(rd='event', zqa='old', zqb='new', zqc='third', ri='text').items():
            model[name] = lambda value=value: value
        model.update(uh=lambda node, author, content, scope, context: present and json.loads(content.syntax) == revised,
            uf=lambda *args: explain, ue=lambda *args: order)
        actual = evaluate(quoted, model); assert actual == [present and explain and order]; rows.append(actual[0])
    prior = extract_document(old, statement_indices=[INDEX]).document
    previous = guarded(prior); previous.update(model); assert evaluate(prior, previous) == [False]
    return dict(new_primitives=0, new_definitions=2, changed_arguments=['frames'],
        other_205_statements_unchanged=True, old_declarations_unchanged=True, dependency_paths=paths,
        core_equals_full_extraction=True, attribution_cases=rows, quoted_conditions_not_executed=True,
        old_quote_not_substituted=True, manuscript_character_increase=len(text(FULL))-len(text(PARENT)))


def build_report():
    files = build(); audits = {}
    for p, body in files.items(): assert text(p) == body, p
    for p in (FULL, CORE):
        doc = parse(text(p)); basis = next(json.loads(x) for q, x in files.items() if q.endswith('-basis-v1.json') and json.loads(x)['document'] == p)
        audits[p] = {k: v for k, v in audit_basis(doc, basis).items() if k != 'definition_dependencies'}
        for notation in ('full', 'compact'):
            formatted = format_graph(doc, notation)
            assert parse(formatted) == parse(transcribe(formatted, alphabet='v2')) == doc
        result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'noema', 'parse', '-i', str(ROOT/p)],
            check=True, capture_output=True, encoding='utf-8')
        assert json.loads(result.stdout) == doc
    paths = set(files) | {PARENT, 'data/einstein-positive-axis-calibration-basis-v1.json', 'data/density-formula-review-v10.json',
        'artifacts/written-units-v1/einstein-1905.json', 'docs/density-origins-v1.md', 'tests/test_density_origins.py'}
    paths.update('scripts/'+n+'.py' for n in ('compose_density_origins', 'check_density_origins', 'compose_positive_axis_calibration',
        'compose_density_boost', 'compose_origin_clock', 'compose_limits', 'check_coordinate_correspondence',
        'check_described_appraisals', 'check_rod_setup', 'check_plane_waveforms', 'check_field_equations',
        'check_tau_differential', 'check_angle_composition', 'check_rod_measurements'))
    paths.update('noema/'+n+'.py' for n in ('grammar', 'language', 'discourse', 'semantics', 'finite_semantics', 'extraction', 'meaning_basis', 'script', 'integration_audit'))
    source = json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    units = {u['id']: u for u in source['units']}; unit = units['einstein-1905:u0236']
    math = next(m for m in source['math'] if m['id'] == 'M0390')
    return dict(status='partial_density_formula_with_common_zero_event', document=FULL, basis_audits=audits,
        origins=origin_checks(), structure=structure_and_attribution(), roundtrips=True, cli_parse=True,
        source_context=[dict(unit=u, text_sha256=units[u]['text_sha256']) for u in ('einstein-1905:u0064', 'einstein-1905:u0085')],
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        alignment=dict(segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'], math_id='M0390', math_sha256=math['sha256'],
            status='partial_density_formula_with_common_zero_event', definitions=['sexv', 'sexu', 'smk', 'seoz'])]),
        source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli = argparse.ArgumentParser(); cli.add_argument('--verify-only', action='store_true'); options = cli.parse_args()
    report = build_report()
    if options.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('Same-event zero coordinates, origin assignments and density quotation checked', flush=True)


if __name__ == '__main__': main()
