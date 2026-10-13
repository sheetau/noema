"""Check common-factor binding, independent units, and missing interpretations."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, OPS
from scripts.check_rod_setup import callbacks
from scripts.compose_limits import call as k
from scripts.compose_shared_light_law import ROOT, PARENT, BUILDERS, INPUTS, CUT

REPORT = ROOT/'reports/shared-light-law-v1.json'
SYMBOLS = {name: 'jz'+number_word(i) for i, (name, _) in enumerate(INPUTS)}
DOMAIN = ('complex', 'old', 'new', 'energy', 'rate', 'other',
    'oldobserver', 'newobserver', 'oldevent', 'newevent',
    *[side+kind+field for side in ('old', 'new') for kind in ('energy', 'rate') for field in ('record', 'unit')])


def query_document(text):
    if set(SYMBOLS.values()) & {d['name'] for d in parse(text)['declarations']}:
        raise ValueError('Fixture identifiers collide')
    args = [k(SYMBOLS[name]) for name, _ in INPUTS]
    physical = [k('bj', k(SYMBOLS[side+kind+'scale']), k(SYMBOLS[side+kind+'value']))
        for kind in ('energy', 'rate') for side in ('old', 'new')]
    numeric = k('seck', *(k(SYMBOLS[n]) for n in ('light', 'speed', 'ax')), *physical)
    text = ''.join('r '+SYMBOLS[name]+'[] '+sort+'.' for name, sort in INPUTS) + ''.join(
        'q['+expr+'].' for expr in (k('seib', *args), numeric, k('seic', *args)))
    return text


def fixture_model(doc, *, speed=3, ax=1, scales=(1, 1, 1, 1), energy=2, rate=7,
                  changes=None, row_change=None, flag=None):
    fixture, model = setup(doc); make, read = fixture.make, fixture.read
    speed, ax, energy, rate = map(F, (speed, ax, energy, rate))
    factor = (F(5, 4) if speed else F(1))*(1-ax*speed/5)
    config = dict(target='complex', oldframe='old', newframe='new', energykind='energy', ratekind='rate',
                  context='motion', light=F(5), speed=speed, ax=ax)
    profiles, records, owners = [], [], []
    for i, (side, kind) in enumerate(product(('old', 'new'), ('energy', 'rate'))):
        prefix = side+kind
        scale = F(scales[i]); value = (energy if kind == 'energy' else rate)*(1 if side == 'old' else factor)/scale
        config.update({side+'observer': side+'observer', side+'event': side+'event',
            prefix+'record': prefix+'record', prefix+'unit': prefix+'unit', prefix+'scale': scale, prefix+'value': value})
        profiles.append([prefix+'unit', kind, scale, 'motion'])
        records.append([prefix+'record', 'complex', kind, side, side+'event', prefix+'unit', value, 'motion'])
        owners.append([prefix+'record', side+'observer', 'motion'])
    config.update(changes or {})
    # Records can faithfully state a value that fails the transformation law.
    for i, (side, kind) in enumerate(product(('old', 'new'), ('energy', 'rate'))):
        records[i][6] = F(config[side+kind+'value'])
    if row_change:
        table, row, column, value = row_change
        {'records': records, 'profiles': profiles, 'owners': owners}[table][row][column] = value
    for name, sort in INPUTS:
        if name in ('motion', 'recordedby'): continue
        value = config[name]
        if sort in ('b', CUT): value = F(value)
        model[SYMBOLS[name]] = (lambda value=value: make(value)) if sort == CUT else (lambda value=value: value)
    model.update(cf=lambda obj: obj == 'complex', va=lambda frame: frame in ('old', 'new'),
        xb=lambda person: person in ('oldobserver', 'newobserver'),
        x4=lambda observer, frame, context: flag != 'wrong_rest_frame' and
            (observer, frame, context) in (('oldobserver', 'old', 'motion'), ('newobserver', 'new', 'motion')),
        zof=lambda unit, kind, scale, context: [unit, kind, scale, context] in profiles)
    def reading(record, target, kind, frame, event, unit, value, context):
        if flag == 'unknown_readings': raise ValueError('Reading interpretation missing')
        return [record, target, kind, frame, event, unit, read(value), context] in records
    model['zog'] = reading
    callbacks(doc, model, {
        SYMBOLS['recordedby']: lambda record, observer, context: [record, observer, context] in owners,
        SYMBOLS['motion']: lambda old, new, light, velocity, context:
            flag != 'wrong_motion' and (old, new, read(light), read(velocity), context) == ('old', 'new', F(5), speed, 'motion'),
    })
    return model


def evaluate(doc, model):
    used = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return values(doc, {name: value for name, value in model.items() if name in used}, DOMAIN)


def binding_checks(texts):
    docs = [abstract(candidate(text, query_document(text)), OPS) for text in texts]
    def run(**options):
        rows = [evaluate(doc, fixture_model(doc, **options)) for doc in docs]
        if rows[0] != rows[1]: raise ValueError('Extracted common-factor condition differs')
        return rows[0]
    cases = []
    for speed, ax, scales in product((-3, 0, 3), (-1, 0, F(3, 5), 1), ((1, 1, 1, 1), (2, 3, 5, 7))):
        result = run(speed=speed, ax=ax, scales=scales)
        if result != [True]*3: raise ValueError('Valid common-factor binding failed')
        cases.append(dict(speed=speed, ax=str(ax), scales=list(scales), results=result))
    contrasts = {}
    def check(name, expected, **options):
        actual = run(**options)
        if actual != expected: raise ValueError(name+': '+repr(actual))
        contrasts[name] = actual
    # Change the interpretation of one record, leaving all numbers unchanged.
    for row in range(4):
        for column, label in ((1, 'target'), (2, 'kind'), (3, 'frame'), (4, 'event'), (5, 'unit'), (7, 'context')):
            check('record_'+str(row)+'_wrong_'+label, [False, True, False], row_change=('records', row, column, 'other'))
        check('record_'+str(row)+'_wrong_owner', [False, True, False], row_change=('owners', row, 1, 'other'))
        check('record_'+str(row)+'_wrong_unit_kind', [False, True, False], row_change=('profiles', row, 1, 'other'))
    for name, changes in {
        'same_frame': {'newframe': 'old'}, 'same_kind': {'ratekind': 'energy'},
        'wrong_observer': {'newobserver': 'other'}, 'wrong_context': {'context': 'other'},
        'wrong_target': {'target': 'other'}, 'frames_swapped': {'oldframe': 'new', 'newframe': 'old'},
        'scale_without_value_conversion': {'newenergyscale': 2},
        'zero_scale': {'newenergyscale': 0}, 'negative_scale': {'newenergyscale': -1},
    }.items():
        numeric = False if 'scale' in name else True
        check(name, [False, numeric, False], changes=changes)
    for flag in ('wrong_rest_frame', 'wrong_motion'):
        check(flag, [False, True, False], flag=flag)
    for name, changes in {
        'energy_uses_squared_factor': {'newenergyvalue': F(1, 2)},
        'rate_unchanged': {'newratevalue': 7},
        'same_ratio_wrong_motion_factor': {'newenergyvalue': 4, 'newratevalue': 14},
        'zero_energy_ratio_undefined': {'oldenergyvalue': 0, 'newenergyvalue': 0},
        'negative_rates': {'oldratevalue': -7, 'newratevalue': F(-7, 2)},
        'zero_frequency': {'oldratevalue': 0, 'newratevalue': 0},
    }.items(): check(name, [True, False, False], changes=changes)
    check('different_energy_to_frequency_ratio', [True]*3, energy=11, rate=3)
    for doc in docs:
        try: evaluate(doc, fixture_model(doc, flag='unknown_readings'))
        except ValueError as exc:
            if 'Reading interpretation missing' not in str(exc): raise
        else: raise ValueError('Unknown readings silently supplied')
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True, missing_reading_refused=True,
        actual_real_arithmetic_abstracted_to_registered_rational_cuts=True,
        universal_physical_law_proved=False, energy_equals_frequency_required=False,
        universal_energy_frequency_constant_asserted=False)


def alignment():
    source = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:u0214')
    excerpt = 'die Energie und die Frequenz eines Lichtkomplexes sich nach demselben Gesetze mit dem Bewegungszustande des Beobachters ändern'
    if unit['text'].count(excerpt) != 1: raise ValueError('Ambiguous shared-law source range')
    start = unit['text'].index(excerpt)
    return {'segments': [dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start+len(excerpt)],
        text=excerpt, definitions=['seia', 'seib', 'seic'], status='partial',
        review_ja='四つの仮定上の記録を用いた明示的設定で、同じ光・二系・観測者・単位尺度を共通変換係数へ結ぶ。普遍的な物理法則の成立、光と方向の帰属、bemerkenswertの評価と帰属は未完。')],
        'semantic_completion': False}


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored common-factor document differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Common-factor roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[0]), parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents, PARENT, *['data/'+stem+'-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_shared_light_law.py', 'scripts/check_shared_light_law.py', 'scripts/check_plane_waveforms.py',
        'scripts/check_tau_differential.py', 'scripts/check_angle_composition.py', 'scripts/check_rod_setup.py',
        'scripts/check_comoving_labels.py', 'scripts/check_coordinate_correspondence.py', 'scripts/check_described_appraisals.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'artifacts/written-units-v1/einstein-1905.json']
    return dict(status='partial_same_light_observer_and_unit_binding', documents=documents, sizes=sizes,
        bindings=binding_checks(texts), alignment=alignment(), parent_preserved=True, roundtrips=True,
        new_definitions=3, new_primitives=0, new_author_statements=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Shared-law report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Same-light common factor, unit conversion, and observer binding checked')


if __name__ == '__main__': main()
