"""Check weighted frequency, period identity and per-point classification."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.compose_restriction_frequency import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/restriction-frequency-v1.json'
SCENES = ('first', 'middle', 'last', 'outside')


def finite_checks():
    doc = parse(generic_composed()[0] + '''
r za[] j[d].r zb[d] c.r zc[d] c.r zd[d] c.r ze[d] b.r zf[] b.r zg[b] c.
q[k rd6[k za[] p zb p zc p zd p ze k zf[]]].
q[k rd7[k za[] p zb p zc p zd p ze k zf[] p zg]].
''')
    def run(points=SCENES[:3], scope=SCENES[:3], classified=SCENES[:3], hits=('first',),
            weights=(1, 1, 1, 1), ratio=Fraction(1, 3), threshold=Fraction(1, 2), bad_indicator=False, unknown=False):
        def assessed(point):
            if unknown and point == 'middle':
                raise ValueError('Unassessed temporal condition')
            return point in classified
        model = {**arithmetic(bad_indicator), 'za': lambda: SequenceValue(tuple(points), '"situation"'),
            'zb': lambda point: point in scope, 'zc': assessed, 'zd': lambda point: point in hits,
            'ze': lambda point: Fraction(weights[SCENES.index(point)]), 'zf': lambda: Fraction(ratio),
            'zg': lambda value: value >= threshold}
        return values(doc, model, ('person',), SCENES)
    cases = 0
    for flags in product((False, True), repeat=6):
        classified = tuple(point for point, yes in zip(SCENES, flags[:3]) if yes)
        hits = tuple(point for point, yes in zip(SCENES, flags[3:]) if yes)
        for weights in ((1, 1, 1, 1), (2, 1, 3, 1)):
            exact = Fraction(sum(weights[i] for i in range(3) if flags[i+3]), sum(weights[:3]))
            for ratio in {Fraction(0), Fraction(1, 2), Fraction(1), exact}:
                actual = run(classified=classified, hits=hits, weights=weights, ratio=ratio)
                valid = all(flags[:3]) and ratio == exact
                if actual != [valid, valid and ratio >= Fraction(1, 2)]:
                    raise ValueError('Weighted frequency differs')
                cases += 1
    contrasts = {}
    for name, options, expected in (
        ('reordered', {'points': tuple(reversed(SCENES[:3]))}, [True, False]),
        ('omitted_middle', {'points': ('first', 'last'), 'ratio': Fraction(1, 2)}, [False, False]),
        ('duplicate', {'points': ('first', 'first', 'middle', 'last'), 'ratio': Fraction(1, 2)}, [False, False]),
        ('empty', {'points': (), 'scope': (), 'ratio': 0}, [False, False]),
        ('extra_point', {'points': SCENES, 'ratio': Fraction(1, 4)}, [False, False]),
        ('zero_weight', {'weights': (1, 0, 1, 1), 'ratio': Fraction(1, 2)}, [False, False]),
        ('negative_weight', {'weights': (1, -1, 1, 1), 'ratio': 1}, [False, False]),
        ('negative_ratio', {'ratio': -1}, [False, False]),
        ('ratio_over_one', {'ratio': 2}, [False, False]),
        ('bad_indicator', {'bad_indicator': True}, [False, False]),
        ('unclassified_miss', {'classified': ('first', 'last')}, [False, False]),
        ('unclassified_hit', {'classified': ('middle', 'last')}, [False, False]),
        ('weighted_half', {'weights': (2, 1, 1, 1), 'ratio': Fraction(1, 2)}, [True, True]),
        ('uniform_weight_scaling', {'weights': (6, 3, 3, 3), 'ratio': Fraction(1, 2)}, [True, True]),
        ('fractional_weight_scaling', {'weights': (1, Fraction(1, 2), Fraction(1, 2), 1), 'ratio': Fraction(1, 2)}, [True, True]),
        ('split_hit_preserving_mass', {'points': SCENES, 'scope': SCENES, 'classified': SCENES,
            'hits': ('first', 'outside'), 'weights': (1, 1, 1, 1), 'ratio': Fraction(1, 2)}, [True, True]),
        ('split_miss_preserving_mass', {'points': SCENES, 'scope': SCENES, 'classified': SCENES,
            'weights': (2, Fraction(1, 2), 1, Fraction(1, 2)), 'ratio': Fraction(1, 2)}, [True, True]),
        ('split_without_preserving_mass', {'points': SCENES, 'scope': SCENES, 'classified': SCENES,
            'hits': ('first', 'outside'), 'ratio': Fraction(1, 3)}, [False, False]),
        ('narrowed_scope', {'points': ('first',), 'scope': ('first',), 'ratio': 1}, [True, True]),
        ('no_hits', {'hits': (), 'ratio': 0}, [True, False]),
        ('all_hits', {'hits': SCENES[:3], 'ratio': 1}, [True, True]),
    ):
        actual = run(**options)
        if actual != expected:
            raise ValueError('Frequency contrast differs: ' + str((name, actual)))
        contrasts[name] = actual
    try:
        run(unknown=True)
    except ValueError as exc:
        if 'Unassessed temporal' not in str(exc):
            raise
    else:
        raise ValueError('Unknown temporal classification treated as false')
    return {'state_weight_ratio_cases': cases, 'contrasts': contrasts, 'unknown_classification_refused': True}


def source_checks():
    text, basis = source_composed()
    mapping = basis['role_linkage']['symbols']['roles']
    args = 'k za[] k zb[] k zc[] k zd[] p ze p zf p zg k zh[] p zi k zj[] '
    extra = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[d] j[a].r zf[d] b.r zg[b] c.
r zh[] j[d].r zi[d] b.r zj[] b.r zk[b] c.r zl[] d.
'''
    doc = candidate(text, extra + 'q[k h76[' + args + 'p zk k zl[]]].q[k h76[' + args + 'i[value b][e[n p a b][n p a b]] k zl[]]].')
    activities = ('one', 'two')
    domain = ('source', 'person', 'role', 'frame', *activities)
    def run(counts=(2, 1, 0), frequency=Fraction(2, 3), weights=(1, 1, 1, 1), degree_threshold=Fraction(1, 2),
            frequency_threshold=Fraction(1, 2), variant='baseline'):
        def norm(kind, source, person, role, activity, desc, sign, context):
            if (source, person, role, symbol(desc)) != ('source', 'person', 'role', mapping['dc']) or activity not in activities or context not in SCENES[:3]:
                return False
            if variant == 'unknown_norm' and context == 'middle':
                raise ValueError('Unknown inner normative classification')
            if variant == 'unclassified_middle' and context == 'middle':
                return False
            banned = activities.index(activity) < counts[SCENES.index(context)]
            if variant == 'conflicting_middle' and context == 'middle':
                return kind == 'required' and not sign or kind == 'allowed' and sign
            return kind == 'required' and not sign and banned or kind == 'allowed' and sign and not banned
        def history(frame, anchor, point):
            return frame == 'frame' and point in SCENES[:3] and variant != 'empty_history'
        def scope(frame, anchor, point):
            if frame != 'frame' or variant == 'empty_scope':
                return False
            if variant == 'scope_outside':
                return True
            if variant == 'gap':
                return point in ('first', 'last')
            if variant == 'other_context_scope' and anchor != 'first':
                return point == 'last'
            return point in SCENES[:3]
        def population(point):
            items = activities if point in SCENES[:3] else ()
            if variant == 'missing_middle_activity' and point == 'middle':
                items = ('one',)
            return SequenceValue(items, '"individual"')
        def degree(point):
            if variant == 'wrong_middle_degree' and point == 'middle':
                return Fraction(0)
            return Fraction(counts[SCENES.index(point)], 2) if point in SCENES[:3] else Fraction(0)
        points = ('first', 'last') if variant in ('gap', 'missing_middle_point') else SCENES if variant == 'scope_outside' else SCENES[:3]
        model = guarded(doc)
        model.update(arithmetic())
        model.update(za=lambda: 'source', zb=lambda: 'person', zc=lambda: 'role', zd=lambda: 'person' if variant == 'wrong_frame' else 'frame',
            ze=population, zf=degree, zg=lambda ratio: ratio >= degree_threshold,
            zh=lambda: SequenceValue(tuple(points), '"situation"'), zi=lambda point: Fraction(weights[SCENES.index(point)]),
            zj=lambda: Fraction(frequency), zk=lambda ratio: ratio >= frequency_threshold, zl=lambda: 'first',
            h7q=history, h7r=scope,
            ic=lambda first, last, anchor: SCENES.index(first) < SCENES.index(last) or variant == 'cyclic_order' and (first, last) == ('last', 'first'),
            h7a=lambda *args: norm('required', *args), h7b=lambda *args: norm('allowed', *args))
        model[mapping['ca']] = lambda person, activity, point: person == 'person' and activity in activities and point in SCENES[:3]
        model[mapping['cb']] = lambda person, activity, role, point: (person, role) == ('person', 'role') and activity in activities and point in SCENES[:3]
        model[mapping['cf']] = lambda person, role, point: (person, role) == ('person', 'role') and point in SCENES[:3]
        return values(doc, model, domain, SCENES)
    rows = []
    for counts in product(range(3), repeat=3):
        frequency = Fraction(sum(count >= 1 for count in counts), 3)
        actual = run(counts, frequency)
        if actual != [frequency >= Fraction(1, 2), True]:
            raise ValueError('Activity degree and temporal frequency conflated')
        rows.append({'banned_activity_counts': list(counts), 'frequency': str(frequency), 'results': actual})
    contrasts = {}
    for name, options, expected in (
        *((name, {'variant': name}, [False, False]) for name in ('unclassified_middle', 'conflicting_middle',
            'wrong_middle_degree', 'missing_middle_activity', 'missing_middle_point', 'empty_scope', 'empty_history',
            'scope_outside', 'gap', 'cyclic_order', 'wrong_frame')),
        ('other_context_scope', {'variant': 'other_context_scope'}, [True, True]),
        ('stricter_degree', {'degree_threshold': Fraction(3, 4), 'frequency': Fraction(1, 3)}, [False, True]),
        ('stricter_frequency', {'frequency_threshold': Fraction(3, 4)}, [False, True]),
        ('weighted_frequency', {'weights': (2, 1, 1, 1), 'frequency': Fraction(3, 4)}, [True, True]),
        ('wrong_frequency', {'frequency': Fraction(1, 2)}, [False, False]),
        ('zero_middle_weight', {'weights': (1, 0, 1, 1), 'frequency': Fraction(1, 2)}, [False, False]),
    ):
        actual = run(**options)
        if actual != expected:
            raise ValueError('Source frequency contrast differs: ' + str((name, actual)))
        contrasts[name] = actual
    try:
        run(variant='unknown_norm')
    except ValueError as exc:
        if 'Unknown inner normative' not in str(exc):
            raise
    else:
        raise ValueError('Unknown inner norm accepted')
    return {'degree_frequency_cases': rows, 'contrasts': contrasts, 'unknown_inner_norm_refused': True,
        'execution_and_author_permissions_guarded': True}


def alignment():
    old = json.loads((ROOT / 'reports/restriction-degree-v1.json').read_text(encoding='utf-8'))['alignment']
    row = dict(old['segments'][0])
    row['definitions'] = ['h75', 'h76']
    row['review_ja'] = '私的活動内の制限の程度と、期間内でその基準を満たす頻度を分けた候補。全時点の分類を検査し、重み・期間・程度基準を明示する。規範の許可・留保への接続と原文の意味一致は未完。'
    return {'segments': [row], 'new_source_ranges': False, 'semantic_completion': False}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'restriction-frequency'), (source_composed, 'kant-restriction-frequency')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored restriction frequency differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Restriction frequency roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = [*documents, PARENT, 'data/restriction-frequency-basis-v1.json', 'data/kant-restriction-frequency-basis-v1.json',
        'scripts/compose_restriction_frequency.py', 'scripts/check_restriction_frequency.py', 'reports/restriction-degree-v1.json',
        'noema/finite_semantics.py', 'noema/discourse.py']
    return json.loads(json.dumps({'status': 'partial_finite_weighted_frequency_not_complete_oefters_semantics',
        'documents': documents, 'finite': finite_checks(), 'source': source_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0, 'new_primitives': 0,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Restriction frequency report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Weighted frequency and complete per-point degree classification checked')


if __name__ == '__main__':
    main()
