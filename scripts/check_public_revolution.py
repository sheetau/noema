"""Check public proportions, result frames, shared events and attribution."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content, FunctionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_revolution import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic
from scripts import check_political_withdrawal as withdrawal

INDEX = 'data/semantic-review-index-v139.json'
REPORT = 'reports/public-revolution-v1.json'
AUDIT = 'data/public-revolution-reading-v1.json'
DOC = 'docs/public-revolution-v1.md'
INVENTORY = withdrawal.INVENTORY
PRIOR = ['reports/thinking-reform-v1.json', 'reports/revolution-routes-v1.json',
         'reports/political-withdrawal-v1.json', 'reports/public-comparison-claim-v1.json']
EXTRA = 'r zg[] a.r zr[] d.r ze[] a.r zs[] d.r zname[] a.r zrname[] d.'
PROVIDERS = '''
d h227b[public a] i[a][r[k zname[]]].
d h227c[reference d] i[d][r[k zrname[]]].
'''


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, extra, boundaries=(), providers=False):
    doc = deepcopy(catalog().document)
    split = extra.index('q[')
    declarations, questions = extra[:split], extra[split:]
    extras = parse('p:' + declarations) if declarations.strip() else {'declarations': []}
    replacements = {}
    if providers:
        supplied = parse('p:' + declarations + PROVIDERS)['declarations'][len(extras['declarations']):]
        replacements = {d['name']: d for d in supplied}
    for index, d in enumerate(doc['declarations']):
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
        if d['name'] in replacements:
            doc['declarations'][index] = replacements[d['name']]
    doc['statements'] = []
    doc['declarations'] = extras['declarations'] + doc['declarations']
    doc['declarations'] = closure(doc, roots + [d['name'] for d in extras['declarations']])
    return parse(format_graph(doc, 'compact') + questions)


def base(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


def contains_symbol(value, name):
    if hasattr(value, 'syntax'):
        value = json.loads(value.syntax)
    if isinstance(value, list):
        return any(contains_symbol(v, name) for v in value)
    return isinstance(value, dict) and (value.get('symbol') == name or
        any(contains_symbol(v, name) for v in value.values()))


@lru_cache(None)
def aggregate_checks():
    extra = EXTRA + '''
r ztrue[a d] c.
d zresult[person a] e[b point[k ztrue[v person v point]]].
q[k r2qr[k zg[] k zr[] k ze[] k zs[] r[p zresult]]].
'''
    doc = fixture(['r2qr'], extra)
    people = ('public', 'one', 'two', 'three', 'outside', 'event', 'other')
    scenes = ('reference', 'candidate', 'other')
    rows = {}
    for variant in ('baseline', 'one_only', 'split_events', 'other_candidate',
                    'cause_without_result', 'result_without_cause', 'outside_success',
                    'selected_population', 'duplicate_population', 'threshold_equal',
                    'zero_threshold', 'unit_threshold'):
        v = base(doc)
        v.update(arithmetic(), pa=lambda a, b: a / b if b else Fraction(0),
                 zg=lambda: 'public', zr=lambda: 'reference', ze=lambda: 'event', zs=lambda: 'candidate',
                 zname=lambda: 'public', zrname=lambda: 'reference',
                 aa=lambda person: person in ('one', 'two', 'three', 'outside'),
                 h6t=lambda group, person, reference: group == 'public' and
                     reference == 'reference' and person in ('one', 'two', 'three'),
                 h222i=lambda group, reference: seq(
                     ('one', 'two') if variant == 'selected_population' else
                     ('one', 'two', 'three', 'one') if variant == 'duplicate_population' else
                     ('one', 'two', 'three')),
                 h226z=lambda group, result, reference:
                     Fraction(2, 3) if variant == 'threshold_equal' else
                     Fraction(0) if variant == 'zero_threshold' else
                     Fraction(1) if variant == 'unit_threshold' else Fraction(1, 2),
                 ztrue=lambda person, point: point == 'candidate' and
                     person in ('one', 'two', 'outside') and variant != 'cause_without_result')
        def cause(act, person, result, point):
            selected = ('one',) if variant == 'one_only' else (
                'outside',) if variant == 'outside_success' else ('one', 'two')
            expected_act = 'other' if variant == 'split_events' and person == 'two' else 'event'
            return act == expected_act and person in selected and symbol(result) == 'zresult' and (
                point == ('other' if variant == 'other_candidate' else 'candidate')) and variant != 'result_without_cause'
        v['g3'] = cause
        actual = evaluate(doc, v, people, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, complete_population_and_result_specific_threshold=True,
                same_event_candidate_cause_and_actual_result=True)


@lru_cache(None)
def result_frame_checks():
    extra = EXTRA + 'r zp[] a.q[t[k r2qt[k zr[] k zg[] k zp[]]][k zs[]]].q[t[k r2qu[k zr[] k zg[] k zp[]]][k zs[]]].'
    doc = fixture(['r2qt', 'r2qu'], extra, ('r2qe', 'r2qp', 'hzne'))
    people = ('public', 'person')
    scenes = ('before', 'middle', 'after')
    rows = {}
    for variant in ('baseline', 'earlier_completion', 'wrong_community', 'wrong_person',
                    'no_withdrawal', 'no_reform', 'invalid_frame', 'no_future_change'):
        v = base(doc)
        completion = 'middle' if variant == 'earlier_completion' else 'after'
        v.update(zg=lambda: 'public', zp=lambda: 'person', zr=lambda: 'before',
                 zs=lambda: 'after', ze=lambda: 'person', zname=lambda: 'public', zrname=lambda: 'before',
                 h222g=lambda public, reference: 'public',
                 h222h=lambda public, reference, candidate: 'after' if variant == 'no_future_change' else 'before',
                 hzne=lambda period, origin, candidate: variant != 'invalid_frame',
                 h7q=lambda period, candidate, point: period == 'public' and candidate == 'after',
                 ic=lambda first, last, candidate: scenes.index(first) < scenes.index(last),
                 h227a=lambda public, reference: 'person' if variant == 'wrong_community' else 'public',
                 h226t=lambda order, community, first: community == 'public')
        def withdrawn(person, ruler, despotic, oppressor, oppressive, pressure, process,
                      first, last, history, before):
            return variant != 'no_withdrawal' and (
                person, first, last) == ('public' if variant == 'wrong_person' else 'person', 'before', completion) and (
                ruler, despotic, oppressor, oppressive, pressure, process) == ('person',) * 6 and (
                history(first) and history(last) and before(first, last))
        def reformed(person, process, scope, first, last, history, before):
            return variant != 'no_reform' and (
                person, process, scope, first, last) == (
                    'public' if variant == 'wrong_person' else 'person', 'person', 'before', 'before', completion
                ) and history(first) and history(last) and before(first, last)
        v.update(r2qe=withdrawn, r2qp=reformed)
        actual = evaluate(doc, v, people, scenes, True)
        common_failure = variant in ('wrong_person', 'invalid_frame', 'no_future_change')
        expected = [not common_failure and variant not in ('wrong_community', 'no_withdrawal'),
                    not common_failure and variant != 'no_reform']
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, person_scope_history_and_community_bound=True,
                earlier_completion_allowed=True, boundaries=['r2qe', 'r2qp', 'hzne'])


@lru_cache(None)
def route_checks():
    doc = fixture(['r2qy'], EXTRA + 'q[k r2qy[k zg[] k zr[]]].',
                  ('r2qg', 'r2qv', 'r2qw', 'hzne'), True)
    people = ('public', 'one', 'two', 'three', 'event', 'other', 'community', 'old', 'new')
    scenes = ('reference', 'candidate', 'other')
    rows = {}
    def model(variant):
        v = base(doc)
        v.update(arithmetic(), pa=lambda a, b: a / b if b else Fraction(0),
                 zg=lambda: 'public', zr=lambda: 'reference', ze=lambda: 'event', zs=lambda: 'candidate',
                 zname=lambda: 'other' if variant == 'wrong_public_name' else 'public',
                 zrname=lambda: 'other' if variant == 'wrong_reference_name' else 'reference',
                 aa=lambda person: person in ('one', 'two', 'three'),
                 h6t=lambda public, person, reference: (public, reference) == ('public', 'reference')
                     and person in ('one', 'two', 'three'),
                 h222i=lambda public, reference: seq(('one', 'two', 'three')),
                 h226z=lambda public, result, reference: Fraction(1, 2),
                 h222k=lambda public, reference, candidate: candidate in ('candidate', 'other')
                     and variant != 'empty_candidates',
                 h222g=lambda public, reference: 'public',
                 h222h=lambda public, reference, candidate: 'reference',
                 hzne=lambda period, origin, candidate: not (
                     variant == 'invalid_unused_frame' and candidate == 'other'),
                 h227d=lambda public, reference, act, candidate: act in ('event', 'other'),
                 h227a=lambda public, reference: 'community',
                 h227e=lambda public, reference, act, candidate: 'old',
                 h227f=lambda public, reference, act, candidate: 'new',
                 h227g=lambda public, reference, act, candidate: seq(('one', 'two')),
                 dg=lambda act, candidate: act in ('event', 'other') and variant != 'no_occurrence',
                 r2qg=lambda act, community, old, new, participants, candidate:
                     (community, old, new, participants.items) == ('community', 'old', 'new', ('one', 'two'))
                     and not (variant == 'other_kind_reforms' and act == 'other'),
                 r2qv=lambda reference, public: FunctionValue(('individual',), 'content',
                     lambda person: Content(scenes, tuple(reference == 'reference' and public == 'public'
                         and person in ('one', 'two') and point == 'candidate' for point in scenes))),
                 r2qw=lambda reference, public: FunctionValue(('individual',), 'content',
                     lambda person: Content(scenes, tuple(reference == 'reference' and public == 'public'
                         and person in ('one', 'two') and point == 'candidate' for point in scenes))))
        def cause(act, person, result, candidate):
            if candidate != 'candidate' or person not in ('one', 'two'):
                return False
            if contains_symbol(result, 'r2qv'):
                if variant == 'no_withdrawal':
                    return False
                return act == ('other' if variant == 'split_withdrawal_events' and person == 'two' else 'event')
            if not contains_symbol(result, 'r2qw'):
                return False
            if variant in ('another_revolution_reforms', 'other_kind_reforms'):
                return act == 'other'
            if variant == 'one_person_reforms':
                return act == 'event' and person == 'one'
            if variant == 'split_reform_events':
                return act == ('event' if person == 'one' else 'other')
            return False
        v['g3'] = cause
        return v
    accepted = {'baseline', 'one_person_reforms', 'split_reform_events', 'other_kind_reforms'}
    for variant in ('baseline', 'one_person_reforms', 'split_reform_events',
                    'another_revolution_reforms', 'other_kind_reforms', 'no_withdrawal',
                    'split_withdrawal_events', 'wrong_public_name', 'wrong_reference_name',
                    'empty_candidates', 'invalid_unused_frame', 'no_occurrence'):
        actual = evaluate(doc, model(variant), people, scenes, True)
        assert actual == [variant in accepted], (variant, actual)
        rows[variant] = actual
    for missing in ('h226z', 'h227d', 'r2qg', 'r2qv', 'r2qw', 'g3'):
        v = model('baseline'); v[missing] = unknown
        try:
            evaluate(doc, v, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, other_revolution_checked_even_without_withdrawal=True,
                closed_public_and_reference_names_checked=True,
                individual_reform_does_not_alone_refute_public_claim=True,
                separate_events_not_combined=True, unknown_inputs_refused=6,
                boundaries=['r2qg', 'r2qv', 'r2qw', 'hzne'])


@lru_cache(None)
def scope_and_attribution_checks():
    scoped = fixture(['r2qz'], 'r zr[] d.q[t[k r2qz[]][k zr[]]].', ('r2la', 'r2nd', 'r2qy'))
    rows = {}
    for variant in ('baseline', 'second_fails', 'bad_classification', 'bad_members', 'empty'):
        v = base(scoped)
        v.update(zr=lambda: 'reference', h222e=lambda public, reference: variant != 'empty',
                 r2la=lambda public, reference: variant != 'bad_classification',
                 r2nd=lambda public, reference: variant != 'bad_members',
                 r2qy=lambda public, reference: not (variant == 'second_fails' and public == 'second'))
        actual = evaluate(scoped, v, ('first', 'second'), ('reference',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    doc = fixture(['r2ra'], 'q[k r2ra[]].')
    v = base(doc)
    v.update(h227h=lambda: 'fifth', h226h=lambda: 'fourth', wa=lambda: 'author', hzp3=lambda: 'context',
             hznreport=lambda node, author, claim, scope, context:
                 (node, author, scope, context) == ('fifth', 'author', 'fifth', 'context')
                 and claim.rank == 3 and json.loads(claim.syntax) ==
                 dict(kind='call', symbol='r2qz', arguments=[]),
             ue=lambda first, last, context: (first, last, context) == ('fourth', 'fifth', 'context'))
    assert evaluate(doc, v, ('fourth', 'fifth', 'author'), ('context',), True) == [True]
    v['ue'] = lambda *args: False
    assert evaluate(doc, v, ('fourth', 'fifth', 'author'), ('context',), True) == [False]
    return dict(scope_contrasts=rows, all_publics_required=True,
                author_source_scope_and_order_bound=True, world_inputs_unknown_without_execution=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='public_revolution_outcome_core_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[907, 1101], text=unit['text'][907:1101]),
                interpretation=LIMITS, definitions=list(MEANINGS), statement=61,
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_four_sentence_characters=771,
                unresolved=['vielleicht wohlとaber/sondernの提示', '後半の新旧の偏見・誘導・予測',
                            '第五文と段落全体の通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:-1] == old.document['statements']
    assert len(new.document['statements']) == 62
    assert new.document['statements'][-1]['body']['symbol'] == 'r2ra'
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in withdrawal.REVIEWS:
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_sentence_characters=771,
                added_definitions=len(MEANINGS), added_basic_relations=len(PRIMITIVES),
                preserved_statements=61, added_statements=1, old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('aggregate', aggregate_checks), ('result_frames', result_frame_checks),
                     ('routes', route_checks), ('attribution', scope_and_attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, *[p for p, _ in withdrawal.REVIEWS],
        'scripts/compose_public_revolution.py', 'scripts/check_public_revolution.py',
        'tests/test_public_revolution.py', 'scripts/check_political_withdrawal.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_scoped_counts.py', 'scripts/check_public_comparison_claim.py'}
    return dict(status='public_revolution_outcome_core_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_public_revolution_outcome_core'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
