"""Verify frame, region and unit binding without manufacturing an answer."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, OPS
from scripts.check_parallel_composition import transform
from scripts.check_rod_setup import callbacks, guarded
from scripts.compose_limits import call as k
from scripts.compose_energy_questions import ROOT, PARENT, BUILDERS, REFERENCES, NUMBERS, CUT

REPORT = ROOT / 'reports/energy-questions-v1.json'
DOMAIN = ('x', 'y', 'z', 't', 'complex', 'old', 'new', 'energy', 'unit', 'author', 'node', 'scope', 'other')


def query_document(text):
    doc = candidate(text, 'r ja[] '+CUT+'.q[h[k sehd[]][k ja[]]].')
    attributed = parse(text)['statements'][-1]
    doc['statements'].append(attributed)
    return abstract(doc, OPS | {'sedi', 'sedo'})


def fixture_model(doc, *, speed=3, direction=(1, 0, 0), radius=1, scale=1, changes=None, flags=()):
    """Pi=3 is a synthetic binding token after abstracting sedi, NEVER actual pi."""
    fixture, model = setup(doc)
    make, read = fixture.make, fixture.read
    speed, radius, scale = map(F, (speed, radius, scale)); direction = tuple(map(F, direction))
    beta = F(5, 4) if speed else F(1)
    D = beta * (1 - direction[0]*speed/5)
    pi = F(3); oldvolume = F(4, 3)*pi*radius**3
    power = 8*pi*2/oldvolume
    config = dict(zip(NUMBERS, (F(5), speed, *direction, radius, pi, power, power*D**2, oldvolume/D)))
    config.update(complex='complex', oldframe='old', newframe='new', kind='energy', unit='unit', scale=scale,
        context='motion', node='node', scope='scope', author='author', text_context='text', value=2*D/scale)
    expected_volume = tuple(config[n] for n in ('light', 'speed', 'ax', 'ay', 'az', 'radius', 'pi', 'volume'))
    config.update(changes or {})
    config['scale'] = F(config['scale'])
    for role, symbol in REFERENCES.items():
        if role in ('assigned', 'motion'):
            continue
        value = config[role]
        model[symbol] = (lambda value=value: make(value)) if role in NUMBERS else (lambda value=value: value)
    model.update(ra=lambda: config['oldframe'], rd=lambda: config['author'], ri=lambda: config['text_context'],
        ja=lambda: make(config['value']), cf=lambda obj: obj == 'complex', va=lambda frame: frame in ('old', 'new'),
        zof=lambda unit, kind, multiplier, context: (unit, kind, multiplier, context) == ('unit', 'energy', scale, 'motion'),
        sedi=lambda value: 'unknown_pi' not in flags and read(value) == pi,
        sedo=lambda *args: 'unknown_volume' not in flags and tuple(map(read, args)) == expected_volume)
    # Probe actual pulled-back regions at three points. These finite fingerprints
    # check argument wiring; they do not decide global function equality.
    oldpoints = ((F(0), F(0), F(0), F(0)), (radius, F(0), F(0), F(0)),
                 (2*radius, F(0), F(0), F(0)))
    probes = []
    def assigned(obj, frame, region, context):
        if (obj, context) != ('complex', 'motion') or frame not in ('old', 'new'):
            return False
        points = oldpoints if frame == 'old' else tuple(transform(p, speed, F(5)) for p in oldpoints)
        if 'wrong_region' in flags and frame == 'new':
            points = ((F(100), F(0), F(0), F(0)), *points[1:])
        results = [region(*map(make, point)) for point in points]
        probes.append((frame, results))
        return 'unassigned' not in flags and results == [True, True, False]
    callbacks(doc, model, {
        REFERENCES['assigned']: assigned,
        REFERENCES['motion']: lambda old, new, light, velocity, context:
            'wrong_motion' not in flags and (old, new, read(light), read(velocity), context) == ('old', 'new', F(5), speed, 'motion'),
    })
    def attribution(node, author, description, scope, context):
        syntax = json.loads(description.syntax)
        wanted = 'sehc' if 'wrong_question' in flags else 'sehd'
        return ('no_attribution' not in flags and (node, author, scope, context) == ('node', 'author', 'scope', 'text')
            and syntax == {'kind': 'call', 'symbol': wanted, 'arguments': []})
    model['zih'] = attribution
    return fixture, model, probes


def evaluate(doc, model):
    used = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return values(doc, {name: value for name, value in model.items() if name in used}, DOMAIN)


def question_checks(texts):
    docs = [query_document(text) for text in texts]
    def run(**options):
        rows, probes = [], []
        for doc in docs:
            _, model, sampled = fixture_model(doc, **options)
            rows.append(evaluate(doc, model)); probes.append(sampled)
        if rows[0] != rows[1] or probes[0] != probes[1]:
            raise ValueError('Standalone question binding differs')
        return rows[0]
    rows = []
    for speed, direction, scale in product((-3, 0, 3), ((1, 0, 0), (0, 1, 0), (F(3, 5), F(4, 5), 0)), (1, 2)):
        actual = run(speed=speed, direction=direction, scale=scale)
        if actual != [True, True]:
            raise ValueError('Valid candidate/question attribution failed: '+repr((speed, direction, scale, actual)))
        rows.append({'speed': speed, 'direction': list(map(str, direction)), 'scale': scale, 'results': actual})
    cases = {
        'wrong_value': ({'value': 2}, (), [False, True]),
        'wrong_target': ({'complex': 'other'}, (), [False, True]),
        'frames_swapped': ({'oldframe': 'new', 'newframe': 'old'}, (), [False, True]),
        'same_frame': ({'newframe': 'old'}, (), [False, True]),
        'wrong_kind': ({'kind': 'other'}, (), [False, True]),
        'wrong_unit': ({'unit': 'other'}, (), [False, True]),
        'wrong_physical_context': ({'context': 'other'}, (), [False, True]),
        'wrong_amplitude': ({'newpower': 12}, (), [False, True]),
        'wrong_volume': ({'volume': 4}, (), [False, True]),
        'missing_pi_premise': ({}, ('unknown_pi',), [False, True]),
        'missing_volume_premise': ({}, ('unknown_volume',), [False, True]),
        'unassigned_complex': ({}, ('unassigned',), [False, True]),
        'wrong_region': ({}, ('wrong_region',), [False, True]),
        'wrong_motion': ({}, ('wrong_motion',), [False, True]),
        'zero_amplitude_zero_energy': ({'power': 0, 'newpower': 0, 'value': 0}, (), [True, True]),
        'negative_energy': ({'value': -1}, (), [False, True]),
        'zero_scale': ({'scale': 0}, (), [False, True]),
        'negative_scale': ({'scale': -1, 'value': -1}, (), [False, True]),
        'wrong_author': ({'author': 'other'}, (), [True, False]),
        'wrong_scope': ({'scope': 'other'}, (), [True, False]),
        'wrong_text_context': ({'text_context': 'other'}, (), [True, False]),
        'wrong_question_description': ({}, ('wrong_question',), [True, False]),
        'no_attribution': ({}, ('no_attribution',), [True, False]),
        'neither_candidate_nor_attribution': ({'value': 2}, ('no_attribution',), [False, False]),
    }
    contrasts = {}
    for name, (changes, flags, expected) in cases.items():
        actual = run(changes=changes, flags=flags)
        if actual != expected:
            raise ValueError('Energy question contrast failed: '+name+repr(actual))
        contrasts[name] = actual
    return {'cases': rows, 'contrasts': contrasts, 'standalone_agrees': True,
        'pi_3_is_only_an_abstract_binding_token': True, 'global_pi_and_volume_conditions_abstracted': True,
        'region_fingerprints_are_not_global_proofs': True, 'actual_real_arithmetic_abstracted_to_registered_rational_cuts': True}


def quoted_question_check(text):
    doc = parse(text); doc['statements'] = doc['statements'][-1:]
    model = guarded(doc)
    model.update(zvaj=lambda: 'node', rd=lambda: 'author', zvai=lambda: 'scope', ri=lambda: 'text')
    received = []
    def presented(node, author, description, scope, context):
        received.append(json.loads(description.syntax))
        return (node, author, scope, context) == ('node', 'author', 'scope', 'text')
    model['zih'] = presented
    if evaluate(doc, model) != [True] or received != [{'kind': 'call', 'symbol': 'sehd', 'arguments': []}]:
        raise ValueError('Question attribution evaluated unasserted physical premises')
    return {'uninterpreted_physical_inputs_not_executed': True, 'quoted_question': received[0]}


def finite_refusal(text):
    doc = abstract(candidate(text, 'q[k sehd[]].'), OPS | {'sedi', 'sedo'})
    _, model, _ = fixture_model(doc)
    try:
        evaluate(doc, model)
    except ValueError as exc:
        if 'Cannot finitely quantify' not in str(exc):
            raise
        return {'refused': True, 'reason': str(exc), 'no_finite_answer_search_claim': True}
    raise ValueError('Real-valued question silently enumerated a finite answer set')


def alignment():
    source = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:u0205')
    excerpts = ('Wir fragen nach der Energiemenge, welche diese Fläche im System [M0356] betrachtet umschließt',
                'nach der Energie des Lichtkomplexes relativ zum System [M0357]')
    rows = []
    for excerpt in excerpts:
        if unit['text'].count(excerpt) != 1:
            raise ValueError('Question source span is ambiguous')
        start = unit['text'].index(excerpt)
        rows.append({'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'range': [start, start+len(excerpt)],
            'text': excerpt, 'definitions': ['seha', 'sehb', 'sehc', 'sehd'], 'status': 'partial',
            'review_ja': '同じ対象・新系k・単位を保持した実数値の問い。後続の振幅・体積・エネルギー式を候補条件へ接続する明示的モデル。光の集合の物理的帰属、エネルギーの一般的定義、d.h.の言い換えの談話は未完。'})
    return {'segments': rows, 'semantic_completion': False, 'question_does_not_assert_an_answer_exists': True}


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored energy question differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Energy question roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = {'characters': len(text), 'statements': len(doc['statements'])}
    doc, parent = parse(texts[0]), parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'][:-1] != parent['statements']:
        raise ValueError('Parent definition or author statement changed')
    paths = [*documents, PARENT, *['data/'+stem+'-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_energy_questions.py', 'scripts/check_energy_questions.py', 'scripts/check_plane_waveforms.py',
        'scripts/check_tau_differential.py', 'scripts/check_parallel_composition.py', 'scripts/check_rod_setup.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'noema/discourse.py',
        'artifacts/written-units-v1/einstein-1905.json']
    return json.loads(json.dumps({'status': 'partial_frame_bound_energy_question', 'documents': documents, 'sizes': sizes,
        'questions': question_checks(texts), 'quotation': quoted_question_check(texts[1]), 'finite_refusal': finite_refusal(texts[1]),
        'alignment': alignment(), 'new_local_references': len(REFERENCES), 'new_logical_or_grammatical_primitives': 0,
        'new_author_question_attributions': 1, 'new_author_assertions_of_energy_value': 0,
        'parent_preserved': True, 'roundtrips': True, 'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Energy question report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Same-target frame-bound energy questions and separate attribution checked')


if __name__ == '__main__':
    main()
