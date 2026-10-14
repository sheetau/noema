"""Check first milestones and same-time order/criticism permissions."""
import argparse
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_office_speech as office
from scripts.compose_limits import call as k
from scripts.compose_provisional_order import ROOT, PARENT, BUILDERS, UNTIL, WITNESS, CONFIG, SOURCE

REPORT = ROOT / 'reports/provisional-order-v1.json'
POINTS = ('start', 'middle', 'end')
SCENES = (*POINTS, 'elsewhere')
EXTRA = '''r jyanchor[] d.r jyend[] d.r jyhistory[d] c.r jybefore[d d] c.
r jyholds[d] c.r jystop[d] c.
d jymaintained[] e[b point[k jyholds[v point]]].
d jymilestone[] e[b point[k jystop[v point]]].'''
REFS = dict(history='p jyhistory', before='p jybefore', start='k jyanchor[]', end='k jyend[]',
    maintained='k jymaintained[]', milestone='k jymilestone[]')
SOURCE_EXTRA = 'r jyactive[a d] c.r jycitizens[a a d] c.r jycriterion[a] e.'
MESSAGE = 'k reu[l[h[a] e][p jycriterion]]'
SOURCE_REFS = dict(population='k zd[]', regime='k zi[]', role='k zf[]', audience='k zg[]', channel='k zh[]',
    criticism='r[' + MESSAGE + ']', authority='k zj[]', active='p jyactive', citizens='p jycitizens',
    histories='i[anchor d][p jyhistory]', milestone='k jymilestone[]')


def roundtrips(doc):
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        if parse(text) != doc or parse(decode(encode(text, 'v2'))) != doc: raise ValueError('Provisional order roundtrip differs')


def temporal_setup(text):
    queries = ''.join('q[' + k(n, *(REFS[x] for x, _ in fields)) + '].' for n, fields in
        (('rkh', WITNESS), ('rki', UNTIL), ('rkj', UNTIL), ('rkk', UNTIL)))
    return candidate(text, EXTRA + queries)


def temporal_model(doc, maintained=(True,) * 3, milestones=(False, False, True), variant='baseline'):
    model = guarded(doc)
    def before(first, second):
        if variant == 'cyclic' and (first, second) == ('end', 'start'): return True
        if variant == 'missing_order' and (first, second) == ('start', 'middle'): return False
        return first in POINTS and second in POINTS and POINTS.index(first) < POINTS.index(second)
    model.update(jyanchor=lambda: 'elsewhere' if variant == 'foreign_start' else 'start',
        jyend=lambda: 'elsewhere' if variant == 'foreign_end' else 'end',
        jyhistory=lambda p: p in POINTS and not (variant == 'missing_start' and p == 'start'), jybefore=before,
        jyholds=lambda p: p in POINTS and maintained[POINTS.index(p)],
        jystop=lambda p: p == 'elsewhere' if variant == 'foreign_milestone' else p in POINTS and milestones[POINTS.index(p)])
    return model


def temporal_checks(texts):
    docs = [temporal_setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=6):
        maintained, stops = bits[:3], bits[3:]
        first = next((i for i, yes in enumerate(stops) if yes), None)
        strong = first is not None and all(maintained[:first])
        weak = strong or first is None and all(maintained)
        inclusive = strong and maintained[first]
        want = [strong and first == 2, strong, weak, inclusive]
        rows = [values(d, temporal_model(d, maintained, stops), ('object',), SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('First milestone differs from positional temporal oracle')
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant in ('foreign_start', 'foreign_end', 'foreign_milestone', 'missing_start', 'cyclic', 'missing_order'):
        want = [False, True, True, True] if variant == 'foreign_end' else [False, False, True, False] if variant == 'foreign_milestone' else [False] * 4
        rows = [values(d, temporal_model(d, variant=variant), ('object',), SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Temporal scope contrast ' + variant)
        contrasts[variant] = want
    for doc in docs:
        for name in ('jyhistory', 'jybefore', 'jyholds', 'jystop'):
            model = temporal_model(doc); model[name] = guarded(doc)[name]
            try: values(doc, model, ('object',), SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown temporal condition guessed')
    return dict(cases=cases, contrasts=contrasts, independent_ordered_sequence_oracle=True,
        unknown_conditions_refused=True, later_failure_not_forced=True, standalone_agrees=True)


def source_setup(text):
    queries = 'q[t[' + k('hzeb', *(SOURCE_REFS[n] for n, _ in CONFIG)) + '][k jyanchor[]]].'
    queries += ''.join('q[t[' + k(symbol, *(SOURCE_REFS[n] for n, _ in SOURCE)) + '][k jyanchor[]]].' for symbol in ('hzec', 'hzed', 'hzee'))
    return candidate(text, office.EXTRA + EXTRA + SOURCE_EXTRA + queries)


def source_model(doc, bits=(True, True, True, True), variant='baseline'):
    active, first, second, reached = bits
    model = office.model_for(doc)
    model.update(temporal_model(doc, milestones=(False, False, reached)))
    # Restore the grounded public-activity interpretation after adding temporal inputs.
    base = office.model_for(doc)
    for name in ('cb', 'ca', 'cc', 'cd', 'ce', 'h6n', 'h6t'):
        indices = {'cb': (0, 1), 'ca': (0, 1), 'cc': (0,)}.get(name, ())
        def adapt(*a, name=name, indices=indices):
            if name in ('cb', 'ca') and a[:2] not in (('person', 'speech'), ('other', 'duty')): return False
            a = list(a)
            for index in indices:
                if a[index] == 'other': a[index] = 'person'
                if a[index] == 'duty': a[index] = 'speech'
            a[-1] = 'now' if a[-1] in POINTS else a[-1]
            return base[name](*a)
        model[name] = adapt
    # Constants are not evaluated under quotations, but live source fields keep their values.
    for name in ('za', 'zb', 'zc', 'zd', 'ze', 'zf', 'zg', 'zh', 'zi', 'zj', 'zk'): model[name] = base[name]
    expected = syntax(description(doc, MESSAGE))
    pairs = (('person', 'speech'), ('other', 'duty'))
    def normative(source, person, role, activity, desc, sign, point, permission):
        if (source, role) != ('authority', 'scholar') or (person, activity) not in pairs or point not in POINTS or json.loads(desc.syntax).get('symbol') != 'zzq': return False
        if permission:
            if variant == 'foreign_permission': return False
            if variant == 'missing_second_permission' and person == 'other': return False
            if variant == 'permission_gap' and point == 'middle' and person == 'other': return False
            if variant == 'boundary_permission' and point == 'end': return False
            return sign and (first if person == 'person' else second)
        return variant == 'opposed_permission' and person == 'other' and not sign
    model.update(aa=lambda person: person in ('person', 'other', 'reader'),
        h6u=lambda activity, channel, subject, desc, point: activity in ('speech', 'duty') and channel == 'channel'
            and subject == ('other' if variant == 'other_regime' else 'topic') and desc.syntax == expected and point in POINTS
            and not (variant == 'missing_second_activity' and activity == 'duty'),
        h7a=lambda *a: normative(*a, False), h7b=lambda *a: normative(*a, True),
        jyactive=lambda regime, point: active and regime == 'topic' and point in POINTS
            and not (variant == 'order_gap' and point == 'middle') and not (variant == 'boundary_order' and point == 'end'),
        jycitizens=lambda population, person, point: population == 'issuer' and person in ('person', 'other') and point in POINTS,
        ic=lambda left, right, context: context == 'start' and model['jybefore'](left, right))
    if variant == 'initial_milestone': model['jystop'] = lambda p: p == 'start'
    # Activity execution and the truth of the criticism remain deliberately unknown.
    model['cg'] = guarded(doc)['cg']
    names = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {n: value for n, value in model.items() if n in names}


def source_checks(texts):
    docs = [source_setup(t) for t in texts]; cases = []
    for bits in product((False, True), repeat=4):
        active, first, second, reached = bits; state = active and first and second
        want = [state, state and reached, state, state and reached]
        rows = [values(d, source_model(d, bits), office.DOMAIN, SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Order and criticism permission not maintained together: ' + repr((bits, rows)))
        cases.append(dict(bits=list(bits), results=want))
    contrasts = {}
    for variant in ('missing_second_permission', 'missing_second_activity', 'other_regime', 'foreign_permission', 'opposed_permission',
                    'permission_gap', 'order_gap', 'boundary_permission', 'boundary_order'):
        want = [True, False, False, False] if variant in ('permission_gap', 'order_gap') else [True, True, True, False] if variant in ('boundary_permission', 'boundary_order') else [False] * 4
        rows = [values(d, source_model(d, variant=variant), office.DOMAIN, SCENES) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Provisional source contrast ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    for doc in docs:
        if values(doc, source_model(doc, (False, False, False, True), 'initial_milestone'), office.DOMAIN, SCENES) != [False, True, True, False]: raise ValueError('Initial milestone wrongly required prior maintenance')
        for name in ('jyactive', 'jycitizens', 'h7a', 'h7b', 'jystop'):
            model = source_model(doc); model[name] = guarded(doc)[name]
            try: values(doc, model, office.DOMAIN, SCENES)
            except ValueError as exc:
                if 'Unrelated primitive' not in str(exc): raise
            else: raise ValueError('Unknown order or permission relation filled in')
        roundtrips(doc)
    return dict(cases=cases, contrasts=contrasts, initial_milestone=[False, True, True, False],
        actual_speech_and_criticism_truth_not_executed=True, each_citizen_has_eligible_activity=True,
        same_regime_and_point=True, unknown_relations_refused=True, standalone_agrees=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored provisional order differs')
        roundtrips(doc); documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrases = ['jedem der Bürger', 'frei ließe', 'in der Qualität eines Gelehrten öffentlich', 'über das Fehlerhafte der dermaligen Einrichtung seine Anmerkungen zu machen', 'indessen die eingeführte Ordnung noch immer fortdauerte, bis']
    segments = []
    for phrase in phrases:
        if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source range')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)],
            text=phrase, definitions=['rkh', 'rki', 'rkj', 'rkk', 'rkl', 'hzeb', 'hzec', 'hzed', 'hzee']))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_provisional_order.py', 'scripts/check_provisional_order.py', 'scripts/check_office_speech.py',
        'scripts/check_assessed_payments.py', 'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py',
        'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_provisional_order_and_public_criticism', documents=documents, sizes=sizes,
        temporal=temporal_checks([texts[0], texts[2]]), source=source_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=9, new_primitives=0,
        new_author_statements=0, parent_preserved=True, roundtrips=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Provisional order report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('First milestones, weak/strong maintenance and public criticism permissions checked')


if __name__ == '__main__': main()
