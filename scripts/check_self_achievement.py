"""Check agent-bound achievement and count past achievers without future projection."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, SequenceValue
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.compose_self_achievement import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/self-achievement-v1.json'


def generic_checks():
    doc = parse(generic_composed()[0] + '''
r za[d] c.r zb[d d] c.r zc[a d d] c.r zd[a a d d] c.r ze[a d] c.r zf[a a d] c.r zg[a a d] c.
r zh[a a i[h[a] e] d] c.r zi[a] e.r zj[] e.r zk[] a.r zl[] a.r zm[] d.r zn[] d.
q[k rcp[p za p zb k zk[] k zl[] k zm[] k zn[] k zj[] k zi[k zk[]] r[p zi] p zc p zd p ze p zf p zg p zh]].
''')
    domain, scenes = ('person', 'process', 'other'), ('before', 'after', 'outside')
    def run(flags, variant='baseline'):
        priorbefore, priorafter, goalbefore, goalafter, change, affected, occurs, agent, work, produces = flags
        def match(actual, expected, relation, fields):
            expected = list(expected)
            for i, field in enumerate(fields):
                if variant == relation + '_' + field:
                    expected[i] = 'outside' if field in ('before', 'after') else 'zj' if field == 'description' else 'other'
            return tuple(actual) == tuple(expected)
        model = {'za': lambda point: point in scenes[:2] and not (variant == 'missing_end' and point == 'after'),
            'zb': lambda a, b: (a, b) == ('before', 'after') or variant == 'cyclic_history' and (a, b) == ('after', 'before'),
            'zc': lambda act, first, last: change and match((act, first, last), ('process', 'before', 'after'), 'change', ('process', 'before', 'after')),
            'zd': lambda who, act, first, last: affected and match((who, act, first, last), ('person', 'process', 'before', 'after'), 'affected', ('person', 'process', 'before', 'after')),
            'ze': lambda act, last: occurs and match((act, last), ('process', 'after'), 'occurs', ('process', 'after')),
            'zf': lambda who, act, last: agent and match((who, act, last), ('person', 'process', 'after'), 'agent', ('person', 'process', 'after')),
            'zg': lambda who, act, last: work and match((who, act, last), ('person', 'process', 'after'), 'work', ('person', 'process', 'after')),
            'zh': lambda act, who, desc, last: produces and match((act, who, symbol(desc), last), ('process', 'person', 'zi', 'after'),
                'produces', ('process', 'person', 'description', 'after')),
            'zi': lambda who: Content(scenes, (goalbefore, goalafter, False) if who == 'person' else (False,) * 3),
            'zj': lambda: Content(scenes, (priorbefore, priorafter, False)),
            'zk': lambda: 'person', 'zl': lambda: 'process', 'zm': lambda: 'before', 'zn': lambda: 'after'}
        return values(doc, model, domain, scenes)
    accepted = 0
    for flags in product((False, True), repeat=10):
        expected = flags[0] and not flags[1] and not flags[2] and flags[3] and all(flags[4:])
        actual = run(flags)
        if actual != [expected]:
            raise ValueError('Self achievement collapsed with a state or unrelated act')
        accepted += actual[0]
    correct = (True, False, False, True, True, True, True, True, True, True)
    variants = ['missing_end', 'cyclic_history']
    for relation, fields in (('change', ('process', 'before', 'after')), ('affected', ('person', 'process', 'before', 'after')),
            ('occurs', ('process', 'after')), ('agent', ('person', 'process', 'after')), ('work', ('person', 'process', 'after')),
            ('produces', ('process', 'person', 'description', 'after'))):
        variants += [relation + '_' + field for field in fields]
    contrasts = {}
    for variant in variants:
        actual = run(correct, variant)
        if actual != [False]:
            raise ValueError('Mismatched achievement accepted: ' + variant)
        contrasts[variant] = actual
    return {'truth_cases': 1024, 'accepted_truth_cases': accepted, 'binding_and_history_cases': contrasts}


def source_model(doc, variant):
    scenes = ('before', 'end', 'anchor')
    endpoint = 'anchor' if variant == 'future_achievement' else 'end'
    evaluated = 'end' if variant in ('future_achievement', 'unassessed_future', 'other_unassessed_future') else 'anchor'
    def available(who, plan, point):
        if variant == 'other_unassessed' and (who, plan, point) == ('other', 'plan', 'before'):
            return True
        if variant == 'other_unassessed_future' and (who, plan, point) == ('other', 'plan', 'anchor'):
            return True
        if (who, plan) != ('person', 'plan'):
            return False
        if variant in ('already_capable', 'unassessed_before') and point == 'before':
            return True
        return point == endpoint or point == 'anchor' and variant not in ('later_loss', 'future_achievement')
    def outcome(who, plan, start, end):
        return available(who, plan, start) and end == endpoint
    def selected(who, plan, start, end):
        return outcome(who, plan, start, end) and not (variant == 'unassessed_before' and start == 'before'
            or variant == 'unassessed_after' and start == endpoint
            or variant in ('unassessed_current_after_success', 'unassessed_future') and start == 'anchor'
            or variant in ('other_unassessed', 'other_unassessed_future') and who == 'other')
    model = guarded(doc)
    model.update(arithmetic())
    model.update(za=lambda: 'person', zb=lambda: 'process', zc=lambda: 'before', zd=lambda: endpoint, ze=lambda: evaluated,
        zf=lambda: SequenceValue(('person', 'other'), '"individual"'),
        aa=lambda who: who in ('person', 'other'),
        ab=lambda faculty, who, point: (faculty, who, point) == ('faculty', 'person', endpoint),
        ac=lambda who, faculty, act, point: (who, faculty, act, point) == ('person', 'faculty', 'process', endpoint),
        ad=lambda guide, who, act, point: variant == 'guided_outcome' and (guide, who, act, point) == ('other', 'person', 'process', endpoint),
        ae=available, af=outcome, ap=selected,
        ia=lambda who, anchor, point: who in ('person', 'other') and point in scenes and not (variant == 'anchor_outside_history' and point == anchor),
        ic=lambda first, last, anchor: scenes.index(first) < scenes.index(last),
        ag=lambda act, first, last: variant != 'no_change' and (act, first, last) == ('process', 'before', endpoint),
        la=lambda who, act, first, last: (who, act, first, last) == ('other' if variant == 'other_person_changed' else 'person', 'process', 'before', endpoint),
        dg=lambda act, point: (act, point) == ('process', endpoint),
        df=lambda who, act, point: (who, act, point) == ('other' if variant == 'other_agent' else 'person', 'process', endpoint),
        h4m=lambda part, who, point: (part, who, point) == ('faculty', 'other' if variant == 'other_mind' else 'person', endpoint),
        h4n=lambda who, part, act, point: variant != 'no_self_work' and (who, part, act, point) ==
            ('person', 'faculty', 'other' if variant == 'unrelated_work' else 'process', endpoint),
        g3=lambda act, who, desc, point: variant != 'no_causal_result' and (act, who, symbol(desc), point) ==
            ('process', 'person', 'bf' if variant == 'wrong_result_description' else 'h4l', endpoint),
        h4i=lambda who, ctx: who in ('person', 'other') and ctx == evaluated,
        h4h=lambda size, ctx: Fraction(2))
    return model


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] a.r zc[] d.r zd[] d.r ze[] d.r zf[] j[a].
q[k h4p[k za[] k zb[] k zc[] k zd[] k ze[]]].q[t[k h4q[k za[]]][k ze[]]].
q[k h4r[k zf[] k ze[]]].q[k h4s[k zf[] k ze[]]].''')
    domain, scenes = ('person', 'other', 'process', 'faculty', 'plan'), ('before', 'end', 'anchor')
    variants = ('baseline', 'later_loss', 'already_capable', 'unassessed_before', 'unassessed_after', 'guided_outcome',
        'anchor_outside_history', 'future_achievement', 'no_change', 'other_person_changed', 'other_agent', 'other_mind',
        'no_self_work', 'unrelated_work', 'no_causal_result', 'wrong_result_description',
        'other_unassessed', 'unassessed_current_after_success', 'unassessed_future', 'other_unassessed_future')
    rows = {}
    for variant in variants:
        expected = [True] * 4 if variant in ('baseline', 'later_loss', 'unassessed_current_after_success', 'unassessed_future', 'other_unassessed_future') else [False, False, True, False]
        if variant in ('unassessed_before', 'unassessed_after', 'anchor_outside_history'):
            expected = [False] * 4
        if variant == 'other_unassessed':
            expected = [True, True, False, False]
        actual = values(doc, source_model(doc, variant), domain, scenes)
        if actual != expected:
            raise ValueError('Native self achievement/count differs: ' + str((variant, actual)))
        rows[variant] = actual
    return rows


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0010')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source unit changed')
    start = text.index('denen es gelungen ist')
    end = text.index(', und dennoch', start)
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': end, 'source': text[start:end],
        'definitions': ['h4l', 'h4o', 'h4p', 'h4q'], 'status': 'partial_explicit_reading', 'full_semantic_equivalence': False,
        'remaining': ['mental self-cultivation foundations', 'validity of ability assessment and causal production',
            'secure gait and concession', 'Daher inference and final few-person attribution']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'self-achievement'), (source_composed, 'kant-self-achievement')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored self achievement differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Achievement roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/self-achievement-basis-v1.json', 'data/kant-self-achievement-basis-v1.json',
        'scripts/compose_self_achievement.py', 'scripts/check_self_achievement.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_historical_self_achievement_and_counting', 'documents': documents,
        'generic': generic_checks(), 'source_cases': source_checks(), 'alignment': alignment(),
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
            raise ValueError('Self achievement report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Agent-bound achieved change, historical scope and exact counts checked')


if __name__ == '__main__':
    main()
