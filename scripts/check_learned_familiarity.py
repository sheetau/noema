"""Audit familiarity without equating experience, capacity or unexplained absence."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_learned_familiarity import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/learned-familiarity-v1.json'


def values(doc, model, domain, scenes):
    return [row['value'] for row in evaluate_document(doc, individuals=domain, situations=scenes,
        primitives=model, max_steps=8_000_000, memoize_definitions=True, memoize_expressions=True)]


def generic_checks():
    doc = parse(generic_composed()[0] + '''
r za[d] c.r zb[d d] c.r zc[a a i[h[a] e] d] c.r zd[a a i[h[a] e] d d] c.r ze[a i[h[a] e] d] c.
r zf[] a.r zg[] d.r zh[a] e.r zi[a] e.r zj[a d] c.
q[k rcg[k zf[] r[p zh] k zg[] p za p zb p zc p zd]].
q[k rch[k zf[] r[p zh] k zg[] p za p zb p zc p zd p ze]].
q[k rci[k zf[] r[p zh] k zg[] p za p zb p zc p zd p ze]].
q[k rcj[k zf[] r[p zh] k zg[] p za p zb p zc]].
q[k zj[k zf[] k zg[]]].
''')
    domain, scenes = ('person', 'event', 'other'), ('past', 'now', 'future', 'outside')
    def run(flags, variant='baseline'):
        experienced, contributes, settled, capable = flags
        def matches(actual, expected, relation, names):
            expected = list(expected)
            for i, name in enumerate(names):
                if variant == relation + '_' + name:
                    expected[i] = 'zi' if name == 'task' else 'outside' if name in ('earlier', 'now') else 'other'
            return tuple(actual) == tuple(expected)
        def experience(who, event, task, point):
            if variant == 'unknown_experience':
                raise ValueError('Unknown experience is not false')
            if variant == 'present_experience':
                point_expected = 'now'
            elif variant == 'future_experience':
                point_expected = 'future'
            else:
                point_expected = 'past'
            return experienced and matches((who, event, symbol(task), point), ('person', 'event', 'zh', point_expected),
                'experience', ('person', 'event', 'task', 'earlier'))
        def untouched(*args):
            raise AssertionError('The described activity must not execute')
        model = {'za': lambda p: p != 'outside' and not (variant == 'missing_now' and p == 'now')
                and not (variant == 'missing_past' and p == 'past') and variant != 'empty_history',
            'zb': lambda a, b: (variant == 'cyclic_order' and (a, b) == ('future', 'past')) or scenes.index(a) < scenes.index(b),
            'zc': experience,
            'zd': lambda event, who, task, earlier, now: contributes and matches((event, who, symbol(task), earlier, now),
                ('event', 'person', 'zh', 'past', 'now'), 'contribution', ('event', 'person', 'task', 'earlier', 'now')),
            'ze': lambda who, task, now: settled and matches((who, symbol(task), now), ('person', 'zh', 'now'),
                'settled', ('person', 'task', 'now')),
            'zf': lambda: 'person', 'zg': lambda: 'now', 'zh': untouched, 'zi': untouched,
            'zj': lambda who, now: capable and (who, now) == ('person', 'now')}
        return values(doc, model, domain, scenes)
    rows = []
    for flags in product((False, True), repeat=4):
        experience, contribution, settled, capable = flags
        origin = experience and contribution
        expected = [origin, origin and settled, not (origin and settled), experience, capable]
        actual = run(flags)
        if actual != expected:
            raise ValueError('Experience, familiarity or capacity collapsed')
        rows.append({'experience_contribution_settled_capable': flags, 'results': actual})
    contrasts = {}
    variants = ['present_experience', 'future_experience', 'missing_now', 'missing_past', 'empty_history', 'cyclic_order']
    for relation, names in (('experience', ('person', 'event', 'task', 'earlier')),
            ('contribution', ('event', 'person', 'task', 'earlier', 'now')), ('settled', ('person', 'task', 'now'))):
        variants += [relation + '_' + name for name in names]
    for variant in variants:
        actual = run((True, True, True, True), variant)
        if actual[1] or (variant in ('missing_now', 'empty_history', 'cyclic_order') and actual[2]):
            raise ValueError('Invalid learned familiarity or invalid-history negation accepted: ' + variant)
        contrasts[variant] = actual
    try:
        run((True, True, True, True), 'unknown_experience')
    except ValueError as exc:
        if str(exc) != 'Unknown experience is not false':
            raise
    else:
        raise ValueError('Unknown experience was turned into absence')
    return {'truth_cases': rows, 'binding_and_history_cases': contrasts,
        'description_unexecuted': True, 'unknown_experience_refused': True}


def movement_checks():
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k h3j[k za[]]][k zb[]]].')
    domain, scenes = ('person', 'other', 'movement', 'limb', 'object'), ('case', 'othercase')
    rows = {}
    for variant in ('baseline', 'no_movement', 'blocked', 'other_person_blocked', 'other_movement_blocked',
            'other_limb', 'other_case_blocked'):
        model = guarded(doc)
        model.update(za=lambda: 'person', zb=lambda: 'case',
            h3h=lambda who, move, point: variant != 'no_movement' and (who, move, point) == ('person', 'movement', 'case'),
            h2f=lambda limb, who, point: (limb, who, point) == ('limb', 'person', 'case'),
            h2h=lambda obj, limb, who, move, point: variant != 'baseline' and (obj, limb, who, move, point) == (
                'object', 'object' if variant == 'other_limb' else 'limb', 'other' if variant == 'other_person_blocked' else 'person',
                'object' if variant == 'other_movement_blocked' else 'movement', 'othercase' if variant == 'other_case_blocked' else 'case'))
        actual = values(doc, model, domain, scenes)
        if actual != [variant not in ('no_movement', 'blocked')]:
            raise ValueError('Physical movement mixed participants or context: ' + variant)
        rows[variant] = actual
    return rows


def source_model(doc, variant):
    scenes = ('before', 'case', 'anchor')
    model = guarded(doc)
    def foot_bound(obj, limb, who, point):
        return (obj, limb, who) == ('shackle', 'limb', 'person') and (point == 'before' or variant == 'still_bound' and point == 'case')
    def reason(factor_person, factor, effect_person, effect, point):
        expected = ('other' if variant == 'wrong_reason_person' else 'person',
            'h3k' if variant == 'wrong_factor' else 'h3l', 'person',
            'h3n' if variant == 'wrong_effect' else 'h3o', 'anchor' if variant == 'wrong_reason_case' else 'case')
        return variant != 'no_reason' and (factor_person, symbol(factor), effect_person, symbol(effect), point) == expected
    model.update(za=lambda: 'person', zb=lambda: 'case', zc=lambda: 'before' if variant == 'wrong_anchor' else 'anchor', wh=lambda: 'anchor',
        h3d=lambda who, anchor: 'small',
        h2s=lambda obj, who, anchor: (obj, who, anchor) == ('shackle', 'person', 'anchor'),
        h2r=lambda who, case, point: variant != 'invalid_history' and (who, case) == ('person', 'case') and point in scenes[:2],
        ic=lambda first, last, case: (first, last, case) == ('before', 'case', 'case'),
        ag=lambda process, first, last: (process, first, last) == ('release', 'before', 'case'),
        la=lambda who, process, first, last: (who, process, first, last) == ('person', 'release', 'before', 'case'),
        df=lambda who, process, last: (who, process, last) == ('person', 'release', 'case'),
        h2q=lambda process, obj, who, first, last: (process, obj, who, first, last) == ('release', 'shackle', 'person', 'before', 'case'),
        h2e=foot_bound, h2f=lambda limb, who, point: (limb, who) == ('limb', 'person'),
        h2g=lambda who, movement, point: (who, movement) == ('person', 'movement'),
        h2h=lambda obj, limb, who, movement, point: (obj, limb, who, movement) == ('shackle', 'limb', 'person', 'movement'),
        h2p=lambda who, ditch, anchor: (who, ditch, anchor) == ('person', 'small', 'anchor'),
        h2n=lambda ditch, case: (ditch, case) == ('small', 'case'),
        h2o=lambda first, second, case: (first, second, case) == ('small', 'small', 'case'),
        h2u=lambda who, ditch, act, case: variant != 'no_jump' and (who, ditch, act, case) == ('person', 'small', 'jump', 'case'),
        h2v=lambda act, case: variant != 'steady_jump' and (act, case) == ('jump', 'case'),
        dg=lambda act, case: (act, case) == ('jump', 'case'),
        h2t=lambda who, anchor, case: variant != 'no_cases' and (who, anchor, case) == ('person', 'anchor', 'case'),
        h3e=lambda who, event, task, point: variant != 'no_experience' and (who, event, symbol(task), point) ==
            ('person', 'experience', 'h3o' if variant == 'different_activity' else 'h3j', 'before'),
        h3f=lambda who, task, case: variant == 'familiar' and (who, symbol(task), case) == ('person', 'h3j', 'case'),
        h3g=lambda event, who, task, before, case: (event, who, symbol(task), before, case) ==
            ('experience', 'person', 'h3j', 'before', 'case'), ea=reason)
    return model


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] d.r zc[] d.
q[t[k h3k[k za[]]][k zb[]]].q[t[k h3l[k za[]]][k zb[]]].q[t[k h3m[k za[]]][k zb[]]].
q[t[k h3p[k za[]]][k zb[]]].q[t[k h3q[k za[]]][k zc[]]].''')
    domain = ('person', 'shackle', 'release', 'limb', 'movement', 'small', 'jump', 'experience', 'other')
    scenes = ('before', 'case', 'anchor')
    variants = {'baseline': [False, True, True, True, True],
        'familiar': [True, False, True, False, False], 'no_experience': [False, True, False, True, True],
        'different_activity': [False, True, False, True, True], 'still_bound': [False, True, True, True, False],
        'invalid_history': [False, False, False, False, False], 'no_cases': [False, True, True, True, False],
        'wrong_anchor': [False, True, True, True, False]}
    for key in ('no_reason', 'wrong_reason_person', 'wrong_factor', 'wrong_effect', 'wrong_reason_case', 'no_jump', 'steady_jump'):
        variants[key] = [False, True, True, False, False]
    rows = {}
    for variant, expected in variants.items():
        actual = values(doc, source_model(doc, variant), domain, scenes)
        if actual != expected:
            raise ValueError('Native reason changed its person, activity, anchor or conditional scope: ' + str((variant, actual)))
        rows[variant] = actual
    return rows


def attribution_checks():
    doc = parse(source_composed()[0])
    doc['statements'] = doc['statements'][-1:]
    rows = {}
    for variant in ('baseline', 'wrong_node', 'wrong_author', 'wrong_content', 'wrong_context', 'reversed_order'):
        model = guarded(doc)
        expected = ['reason', 'author', 'h3r', 'anchor']
        if variant in ('wrong_node', 'wrong_author', 'wrong_content', 'wrong_context'):
            expected[('wrong_node', 'wrong_author', 'wrong_content', 'wrong_context').index(variant)] = 'other'
        model.update(h3s=lambda: 'reason', h3a=lambda: 'conditional', wa=lambda: 'author', wh=lambda: 'anchor',
            uc=lambda node, author, desc, ctx: [node, author, json.loads(desc.syntax)['symbol'], ctx] == expected,
            ue=lambda first, last, ctx: (first, last, ctx) == (('reason', 'conditional', 'anchor') if variant == 'reversed_order'
                else ('conditional', 'reason', 'anchor')))
        actual = values(doc, model, ('reason', 'conditional', 'author', 'other'), ('anchor',))
        if actual != [variant == 'baseline']:
            raise ValueError('Reason attribution executed content or changed discourse order')
        rows[variant] = actual
    return {'cases': rows, 'content_unexecuted': True}


def alignment():
    path = ROOT / 'artifacts/written-units-v1/kant-1784.json'
    manifest = json.loads((ROOT / 'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['works']['kant-1784']['units_sha256']:
        raise ValueError('Source inventory changed')
    unit = next(row for row in json.loads(path.read_text(encoding='utf-8'))['units'] if row['id'] == 'kant-1784:u0010')
    text = unit['text']
    if hashlib.sha256(text.encode()).hexdigest() != unit['text_sha256']:
        raise ValueError('Source unit changed')
    start = text.index('weil er zu dergleichen')
    end = text.index('ist.', start) + len('ist.')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': end, 'source': text[start:end],
        'definitions': ['h3j', 'h3k', 'h3l', 'h3o', 'h3p', 'h3q', 'h3r', 'h3t'],
        'status': 'partial_explicit_reading', 'full_semantic_equivalence': False,
        'remaining': ['dergleichen activity-kind reference', 'full physical freedom', 'foundations of acquired response',
            'present-tense projection versus hypothetical reason', 'figurative connection to intellectual independence']}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'learned-familiarity'), (source_composed, 'kant-learned-familiarity')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored familiarity differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Familiarity roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'][:-1] != parent['statements']:
        raise ValueError('Prior conditional changed')
    paths = list(documents) + [PARENT, 'data/learned-familiarity-basis-v1.json', 'data/kant-learned-familiarity-basis-v1.json',
        'scripts/compose_learned_familiarity.py', 'scripts/check_learned_familiarity.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_experientially_acquired_familiarity_and_hypothetical_reason',
        'documents': documents, 'generic': generic_checks(), 'movement': movement_checks(), 'source_cases': source_checks(),
        'attribution': attribution_checks(), 'alignment': alignment(), 'parent_preserved': True, 'roundtrips': True,
        'reading_review': {'comparison_url': 'https://korpora.org/kant/aa08/036.html', 'location': 'AA VIII 36, lines 12–13',
            'method': '固定版と電子本文を比較。原刊画像の照合ではない。',
            'interpretation': '身体の運動への経験由来の慣れの不在を、同じ仮定内で不確かな跳躍を説明する要因に採る部分的な読み。'},
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
            raise ValueError('Learned familiarity report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Experience, retained acquired response and attributed hypothetical reason checked')


if __name__ == '__main__':
    main()
