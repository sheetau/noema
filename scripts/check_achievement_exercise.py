"""Check shared-history completion order and achieved-yet-exercised concession."""
import argparse
import hashlib
from itertools import product
import json

from noema.first_order_proofs import verify
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_controlled_gait import alignment as gait_alignment
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_achievement_exercise import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/achievement-exercise-v1.json'


def generic_checks():
    text = generic_composed()[0] + '''r za[d] c.r zb[d d] c.r zc[] a.r zd[] d.r ze[] d.r zf[] d.
r zg[a d d] c.r zh[a d d] c.
q[k rct[p za p zb k zc[] k zd[] k ze[] k zf[] p zg p zh]].'''
    doc = parse(text)
    scenes = ('first', 'second', 'third', 'outside')
    def run(attained, completed, anchor, good=True, exercised=True, variant='baseline'):
        def relation(who, point, context, expected, label):
            return (who, point, context) == ('other' if variant == label + '_person' else 'person',
                'outside' if variant == label + '_point' else expected,
                'outside' if variant == label + '_anchor' else anchor)
        model = {'za': lambda point: point != 'outside',
            'zb': lambda left, right: scenes.index(left) < scenes.index(right) or (
                variant == 'cycle' and (left, right) == ('third', 'first')),
            'zc': lambda: 'person', 'zd': lambda: attained, 'ze': lambda: completed, 'zf': lambda: anchor,
            'zg': lambda who, point, context: good and relation(who, point, context, attained, 'achievement'),
            'zh': lambda who, point, context: exercised and relation(who, point, context, completed, 'exercise')}
        return values(doc, model, ('person', 'other'), scenes)
    accepted = 0
    for (i, j, k), (good, exercised) in product(product(range(4), repeat=3), product((False, True), repeat=2)):
        actual = run(scenes[i], scenes[j], scenes[k], good, exercised)
        expected = i <= j <= k < 3 and good and exercised
        if actual != [expected]:
            raise ValueError('Completion order or history membership differs')
        accepted += actual[0]
    contrasts = {}
    for variant in ('cycle', 'achievement_person', 'achievement_point', 'achievement_anchor',
            'exercise_person', 'exercise_point', 'exercise_anchor'):
        actual = run('first', 'second', 'third', variant=variant)
        if actual != [False]:
            raise ValueError('Mixed person, endpoint or anchor accepted')
        contrasts[variant] = actual
    return {'truth_and_order_cases': 256, 'accepted_cases': accepted, 'binding_cases': contrasts}


def general_laws():
    text = generic_composed()[0] + '''r za[d] c.r zb[d d] c.r zc[] a.r zd[] d.r ze[] d.r zf[] d.
r zg[a d d] c.r zh[a d d] c.r zi[a d d] c.'''
    body = 'k rct[p za p zb k zc[] k zd[] k ze[] k zf[] p zg p zh]'
    achieved = 'k zg[k zc[] k zd[] k zf[]]'
    exercised = 'k zh[k zc[] k ze[] k zf[]]'
    order = 'x[e[k zd[]][k ze[]]][k zb[k zd[] k ze[]]]'
    not_future = 'x[e[k ze[]][k zf[]]][k zb[k ze[] k zf[]]]'
    member = 'w[k za[k zd[]]][w[k za[k ze[]]][k za[k zf[]]]]'
    claims = {'same_person_and_anchor_achieved': f'y[{body}][{achieved}]',
        'same_person_and_anchor_exercised': f'y[{body}][{exercised}]',
        'achievement_no_later_than_exercise': f'y[{body}][{order}]',
        'exercise_not_in_future': f'y[{body}][{not_future}]',
        'all_points_in_one_history': f'y[{body}][{member}]',
        'two_experiences_alone_suffice': f'y[w[{achieved}][{exercised}]][{body}]',
        'completion_order_implies_causation': f'y[{body}][k zi[k zc[] k zd[] k ze[]]]'}
    results = verify(parse(text + ''.join(f's[{formula}].' for formula in claims.values())))
    if [row['status'] for row in results] != ['valid'] * 5 + ['invalid'] * 2:
        raise ValueError('Shared-history completion laws failed')
    return {name: {'status': row['status'], 'countermodel_found': row['countermodel'] is not None,
        'formula_sha256': hashlib.sha256(row['formula'].encode()).hexdigest()}
        for name, row in zip(claims, results, strict=True)}


DOMAIN = ('person', 'other', 'process', 'faculty', 'plan', 'episode', 'early', 'late', 'matter', 'reason')
SCENES = ('before', 'exit', 'finish', 'now', 'expected')


def source_model(doc, variant='baseline'):
    timeline = ('before', 'finish', 'exit', 'now') if variant == 'exercise_before_achievement' else SCENES[:4]
    attained = 'now' if variant == 'future_achievement' else 'exit'
    completed = 'exit' if variant == 'coincident' else 'now' if variant == 'future_exercise' else 'finish'
    anchor = 'finish' if variant in ('future_achievement', 'future_exercise') else 'now'
    first = 'before' if variant in ('coincident', 'straddling', 'exercise_before_achievement') else 'exit'
    episode = 'process' if variant == 'same_process' else 'episode'
    def branch(context):
        if context == 'expected':
            if variant == 'expected_without_achievement':
                return ('before', 'expected')
            if variant == 'expected_also_exercises':
                return ('before', 'exit', 'finish', 'expected')
            return ('before', 'exit', 'expected')
        return timeline[:timeline.index(context) + 1]
    def order(left, right, context):
        path = branch(context)
        return left in path and right in path and path.index(left) < path.index(right)
    def judgments(person, act, point):
        return variant != 'no_exercise' and person == ('other' if variant == 'other_judgment_person' else 'person') and (
            (act, point) == ('early', first) or (act, point) == ('late', completed))
    def scope(act, last, point):
        return (act, last) == (episode, completed) and point in timeline and (
            timeline.index(first) <= timeline.index(point) <= timeline.index(completed))
    def available(person, plan, point):
        return (person, plan) == ('person', 'plan') and point in (attained, 'now')
    def outcomes(person, plan, start, end):
        return available(person, plan, start) and end == attained
    model = guarded(doc)
    model.update(za=lambda: 'person', zb=lambda: attained, zc=lambda: completed, zd=lambda: anchor,
        wa=lambda: 'author',
        aa=lambda who: who in ('person', 'other'),
        ia=lambda who, context, point: who in ('person', 'other') and point in branch(context), ic=order,
        ab=lambda faculty, person, point: (faculty, person) == ('faculty', 'person'),
        ac=lambda person, faculty, act, point: (person, faculty) == ('person', 'faculty') and (
            (act, point) == ('process', attained) or judgments(person, act, point)),
        ad=lambda *args: False,
        ae=available, af=outcomes,
        ap=lambda person, plan, start, end: outcomes(person, plan, start, end) and variant != 'unassessed_achievement',
        ag=lambda act, first, last: variant != 'no_achievement' and (act, first, last) == ('process', 'before', attained),
        la=lambda person, act, first, last: (person, act, first, last) == ('person', 'process', 'before', attained),
        dg=lambda act, point: (act, point) in (('process', attained), (episode, completed)),
        df=lambda person, act, point: (person, act, point) == ('person', 'process', attained),
        h4m=lambda part, person, point: (part, person, point) == ('faculty', 'person', attained),
        h4n=lambda person, part, act, point: (person, part, act, point) == (
            'other' if variant == 'other_self_work' else 'person', 'faculty', 'process', attained),
        g3=lambda act, person, desc, point: (act, person, symbol(desc), point) == ('process', 'person', 'h4l', attained),
        h5a=scope, h5b=lambda act, parent, point: parent == episode and (
            (act, point) == ('early', first) or (act, point) == ('late', completed)),
        fa=judgments, fb=lambda act, matter, point: matter == 'matter' and judgments('person', act, point),
        fc=lambda act, reason, point: reason == 'reason' and judgments('person', act, point),
        fd=lambda reason, act, point: reason == 'reason' and judgments('person', act, point) and not (
            variant == 'unsupported_early_judgment' and (act, point) == ('early', first)),
        ke=lambda author, person, description, context, alternative: variant != 'no_expectations' and (
            author, person, symbol(description), context, alternative) == (
                'other' if variant == 'other_perspective' else 'author',
                'other' if variant == 'other_expected_person' else 'person',
                'h5e' if variant == 'other_expected_premise' else 'h4q', 'now', 'expected'))
    return model


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.r zc[] d.r zd[] d.
q[t[k h4q[k za[]]][k zd[]]].q[t[k h5e[k za[]]][k zd[]]].
q[k h5j[k za[] k zb[] k zc[] k zd[]]].q[t[k h5k[k za[]]][k zd[]]].''')
    variants = {'baseline': [True] * 4, 'coincident': [True] * 4, 'straddling': [True] * 4,
        'same_process': [True] * 4, 'exercise_before_achievement': [True, True, False, False],
        'no_achievement': [False, True, False, False], 'other_self_work': [False, True, False, False],
        'unassessed_achievement': [False, True, False, False],
        'no_exercise': [True, False, False, False], 'other_judgment_person': [True, False, False, False],
        'unsupported_early_judgment': [True, False, False, False],
        'future_achievement': [False, True, False, False], 'future_exercise': [True, False, False, False]}
    rows = {}
    for variant, expected in variants.items():
        actual = values(doc, source_model(doc, variant), DOMAIN + ('author',), SCENES)
        if actual != expected:
            raise ValueError('Achievement exercise binding failed: ' + str((variant, actual, expected)))
        rows[variant] = actual
    return {'cases': rows, 'bodily_gait_primitives_guarded_against_execution': True}


def concession_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.r zc[] d.r zd[] d.
q[t[k h5l[k za[]]][k zd[]]].''')
    rows = {}
    for variant in ('baseline', 'expected_without_achievement', 'expected_also_exercises', 'no_expectations',
            'other_perspective', 'other_expected_person', 'other_expected_premise', 'no_achievement', 'no_exercise'):
        actual = values(doc, source_model(doc, variant), DOMAIN + ('author',), SCENES)
        if actual != [variant == 'baseline']:
            raise ValueError('Achievement concession failed: ' + str((variant, actual)))
        rows[variant] = actual
    return rows


def alignment():
    row = gait_alignment()
    units = json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
    text = next(unit['text'] for unit in units if unit['id'] == row['unit'])
    row['start'] = text.rindex('und dennoch', 0, row['start'])
    row['source'] = text[row['start']:row['end']]
    row['definitions'] = ['h5h', 'h5i', 'h5j', 'h5k', 'h5l']
    row['remaining'] = ['validity of nonstrict completion order reading', 'selection and adequacy of expected alternatives',
        'full meaning of intellectual stability and figurative mapping', 'final population counting and Daher inference']
    return row


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'achievement-exercise'), (source_composed, 'kant-achievement-exercise')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored achievement exercise differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Achievement exercise roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/achievement-exercise-basis-v1.json', 'data/kant-achievement-exercise-basis-v1.json',
        'scripts/compose_achievement_exercise.py', 'scripts/check_achievement_exercise.py',
        'scripts/check_controlled_gait.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'noema/first_order_proofs.py', 'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_achievement_exercise_order_and_concession', 'documents': documents,
        'generic': generic_checks(), 'general_laws': general_laws(), 'source_cases': source_checks(),
        'concession_cases': concession_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 0,
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
            raise ValueError('Achievement exercise report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Achievement, later or coincident exercise and expected alternatives checked')


if __name__ == '__main__':
    main()
