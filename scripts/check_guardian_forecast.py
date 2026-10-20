"""Check crowd, appointment, expectation and the closed source attribution."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_guardian_forecast import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic
from scripts.check_expected_focus import lambda_key
from scripts.check_focused_dissemination import subgroup
from scripts.check_dissemination_content import NAMES, names

INDEX = 'data/semantic-review-index-v122.json'
REPORT = 'reports/guardian-forecast-v1.json'
AUDIT = 'data/guardian-forecast-reading-v1.json'
DOC = 'docs/guardian-forecast-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
READING = 'data/public-first-sentence-reading-v1.json'
PRIOR = ['reports/dissemination-content-v1.json', 'reports/expected-focus-v1.json',
         'reports/attributed-focus-v1.json', 'reports/appointed-thinkers-v1.json']


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, extra, named=False):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots), statements=[])
    if named:
        doc['declarations'] = parse('p:' + NAMES)['declarations'] + [
            d for d in doc['declarations'] if d['name'] not in ('h223g', 'h223h')]
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


def label(description):
    frame, code = subgroup(description)
    assert code['kind'] == 'apply' and code['function']['kind'] == 'lambda'
    if len(code['arguments']) == 1:
        assert code['function']['body']['kind'] == 'lambda'
        assert code['function']['body']['body']['kind'] == 'not'
        return frame, 'other', code['arguments'][0]
    assert len(code['arguments']) == 3
    return frame, 'focus', code


@lru_cache(None)
def crowd_checks():
    doc = fixture(['r2m7'], 'r zg[] a.r zr[] d.q[k r2m7[k zg[] k zr[]]].')
    people = ('p', 'q', 'r', 's', 'group', 'crowd', 'object')

    def model(population, lower):
        values = unknowns(doc)
        values.update(arithmetic())
        values.update(zg=lambda: 'group', zr=lambda: 'reference', aa=lambda p: p in ('p', 'q', 'r', 's'),
                      h223i=lambda g, r: 'crowd' if (g, r) == ('group', 'reference') else 'object',
                      h223j=lambda g, r: Fraction(lower), mp=lambda g: seq(population) if g == 'crowd' else seq(()))
        return values

    count = 0
    for size, lower in product(range(5), (0, 1, 2, Fraction(5, 2), 3, 4)):
        actual = evaluate(doc, model(people[:size], lower), people, ('reference',), True)
        assert actual == [lower >= 2 and size > lower], (size, lower, actual)
        count += 1
    for population in (('p', 'q', 'q', 'r'), ('p', 'q', 'object'), ()):
        assert evaluate(doc, model(population, 2), people, ('reference',), True) == [False]
    for name in ('mp', 'h223j'):
        values = model(('p', 'q', 'r'), 2)
        values[name] = unknown
        try:
            evaluate(doc, values, people, ('reference',), True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(population_and_lower_bound_combinations=count, complete_human_population_used=True,
                duplicates_nonhumans_and_invalid_cutoffs_refused=True, unknown_inputs_refused=2)


@lru_cache(None)
def appointment_checks():
    doc = fixture(['hzhb', 'r2m6', 'h223k'], 'r zp[] a.r zg[] a.r zt[] d.'
                  'q[k hzhb[k zp[] k zg[] k zt[] p h223k p r2m6]].')
    domain = ('p', 'issuer', 'role', 'event', 'crowd', 'other')
    scenes = ('past', 'now', 'later')

    def model(variant):
        values = unknowns(doc)
        values.update(
            zp=lambda: 'p', zg=lambda: 'crowd', zt=lambda: 'now',
            aa=lambda p: variant != 'not_human' and p == 'p',
            ia=lambda p, a, t: (p, a) == ('p', 'now') and t in scenes,
            ic=lambda a, b, ctx: ctx == 'now' and scenes.index(a) < scenes.index(b),
            dg=lambda event, point: variant != 'no_event' and (event, point) == (
                'other' if variant == 'different_event' else 'event',
                'later' if variant == 'late_appointment' else 'past'),
            cf=lambda person, role, point: (person, role) == ('p', 'role') and point in (
                ('past',) if variant == 'no_current_duty' else ('now',) if variant == 'no_initial_duty' else ('past', 'now')),
            h223k=lambda event, issuer, person, role, point: variant != 'no_appointment' and
            (event, issuer, person, role, point) == ('event', 'issuer',
                'other' if variant == 'different_person' else 'p',
                'other' if variant == 'different_role' else 'role', 'past'),
            hzxg=lambda role, task, governed, point: variant != 'no_responsibility' and symbol(task) == 'r2m5' and
            (role, governed, point) == ('role', 'other' if variant == 'different_crowd' else 'crowd',
                                       'past' if variant == 'old_responsibility_only' else 'now'),
        )
        return values

    rows = {}
    variants = ('baseline', 'not_human', 'no_event', 'different_event', 'late_appointment', 'no_current_duty',
                'no_initial_duty', 'no_appointment', 'different_person', 'different_role',
                'no_responsibility', 'different_crowd', 'old_responsibility_only')
    for variant in variants:
        actual = evaluate(doc, model(variant), domain, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for name in ('h223k', 'hzxg', 'cf'):
        values = model('baseline')
        values[name] = unknown
        try:
            evaluate(doc, values, domain, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    # The task describes supervision of a member, without requiring one holder
    # to supervise the entire crowd. Quoting the task above did not execute it.
    task = fixture(['r2m5'], 'r zp[] a.r zg[] a.r zt[] d.q[t[k r2m5[k zp[] k zg[]]][k zt[]]].')
    values = unknowns(task)
    values.update(zp=lambda: 'p', zg=lambda: 'crowd', zt=lambda: 'now',
                  mp=lambda g: seq(('p', 'q', 'r')), aa=lambda p: p in ('p', 'q', 'r'),
                  dc=lambda p, target, t: (p, target, t) == ('p', 'q', 'now'))
    assert evaluate(task, values, ('p', 'q', 'r', 'crowd'), ('now',), True) == [True]
    values['dc'] = lambda p, target, t: (p, target, t) == ('p', 'p', 'now')
    assert evaluate(task, values, ('p', 'q', 'r', 'crowd'), ('now',), True) == [False]
    return dict(appointment_contrasts=rows, native_history_event_and_current_entrustment=True,
                quoted_task_not_executed_by_role_classification=True,
                supervision_of_every_member_not_required=True, unknown_inputs_refused=3)


@lru_cache(None)
def package_checks():
    doc = fixture(['r2mc', 'rsv'], 'r zg[] a.r zr[] d.'
                  'q[t[s[k rsv[k r2mc[k zg[] k zr[]]]]][k zr[]]].', named=True)
    rows = {}
    seen = set()
    for above, reverse in product((False, True), repeat=2):
        values = unknowns(doc)
        values.update(names(), zg=lambda: 'group', zr=lambda: 'reference',
                      wa=lambda: 'author', hzp3=lambda: 'text')

        def weak(observer, left, right, context):
            frame, a, focus = label(left)
            otherframe, b, otherfocus = label(right)
            assert (observer, context) == ('author', 'text')
            assert frame == otherframe and lambda_key(focus) == lambda_key(otherfocus)
            assert frame['kind'] == 'apply' and frame['function'] == dict(kind='function_ref', symbol='r2ma')
            assert [x['symbol'] for x in frame['arguments']] == ['zagroup', 'zareference']
            assert focus['kind'] == 'apply'
            assert focus['arguments'][0]['function'] == dict(kind='function_ref', symbol='h223i')
            assert [x['symbol'] for x in focus['arguments'][0]['arguments']] == ['zagroup', 'zareference']
            assert focus['arguments'][1:] == [dict(kind='function_ref', symbol='h223k'),
                                              dict(kind='function_ref', symbol='r2m6')]
            seen.add((a, b))
            return True if a == b else above if (a, b) == ('other', 'focus') else reverse

        values['hzpt'] = weak
        actual = evaluate(doc, values, ('group', 'author'), ('reference', 'text', 'other'), True)
        assert actual == [above and not reverse]
        rows[str((above, reverse))] = actual
    assert seen == set(product(('focus', 'other'), repeat=2))
    return dict(expectation_relations=rows, shared_frame_crowd_and_appointment_descriptions=True,
                all_world_facts_unexecuted=True, ties_and_incomparability_not_strictly_less_expected=True)


@lru_cache(None)
def aggregation_checks():
    doc = fixture(['r2md', 'r2me'], 'r zr[] d.q[t[k r2md[]][k zr[]]].q[t[k r2me[]][k zr[]]].')
    helper = parse('''p:
r zgfirst[] a.r zgsecond[] a.r zreference[] d.
r zpick[a i[a] i[a]] i[a].
r zforegroundtruth[a d d] c.r zbackgroundtruth[a d d] c.
d h223g[group a] i[a][k zpick[v group r[k zgfirst[]] r[k zgsecond[]]]].
d h223h[reference d] i[d][r[k zreference[]]].
d zforeground[group a reference d] e[b point[k zforegroundtruth[v group v reference v point]]].
d zbackground[group a reference d] e[b point[k zbackgroundtruth[v group v reference v point]]].
''')
    doc['declarations'] = helper['declarations'] + [d for d in doc['declarations'] if d['name'] not in ('h223g', 'h223h')]
    package = next(d for d in doc['declarations'] if d['name'] == 'r2mc')
    g, r = [p['name'] for p in package['parameters']]
    variable = lambda name: dict(kind='variable', name=name)
    applied = lambda name: dict(kind='quoted_application',
        function=dict(kind='quote', rank=2, body=dict(kind='function_ref', symbol=name)),
        arguments=[dict(kind='call', symbol='h223g', arguments=[variable(g)]),
                   dict(kind='call', symbol='h223h', arguments=[variable(r)])])
    package['body'] = dict(kind='call', symbol='rst', arguments=[applied('zforeground'), applied('zbackground')])
    # Explicit boundary for classification; source classification was checked
    # natively in the preceding public comparison report.
    for d in doc['declarations']:
        if d['name'] == 'r2la':
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc = parse(format_graph(doc, 'compact'))
    count = 0
    for bits in product((False, True), repeat=6):
        selected = {g for g, b in zip(('g', 'h'), bits[:2]) if b}
        fg = {g for g, b in zip(('g', 'h'), bits[2:4]) if b}
        bg = {g for g, b in zip(('g', 'h'), bits[4:]) if b}
        values = unknowns(doc)
        values.update(zr=lambda: 'reference', zgfirst=lambda: 'g', zgsecond=lambda: 'h', zreference=lambda: 'reference',
                      zpick=lambda g, first, second: first if g == 'g' else second,
                      h222e=lambda g, r: g in selected and r == 'reference',
                      r2la=lambda g, r: g in ('g', 'h') and r == 'reference',
                      zforegroundtruth=lambda g, r, p: g in fg and r == p == 'reference',
                      zbackgroundtruth=lambda g, r, p: g in bg and r == p == 'reference')
        actual = evaluate(doc, values, ('g', 'h'), ('reference', 'other'), True)
        assert actual == [bool(selected) and selected <= fg, bool(selected) and selected <= bg], (bits, actual)
        count += 1
    values['r2la'] = lambda g, r: g == 'g'
    assert evaluate(doc, values, ('g', 'h'), ('reference', 'other'), True) == [False, False]
    # Keep both contents true even for a wrongly named public/reference, so
    # only the outer referent guard can reject the substitution.
    values.update(r2la=lambda g, r: True, zforegroundtruth=lambda g, r, p: True,
                  zbackgroundtruth=lambda g, r, p: True)
    assert evaluate(doc, values, ('g', 'h'), ('reference', 'other'), True) == [True, True]
    values['zpick'] = lambda g, first, second: first
    assert evaluate(doc, values, ('g', 'h'), ('reference', 'other'), True) == [False, False]
    values.update(zpick=lambda g, first, second: first if g == 'g' else second,
                  zreference=lambda: 'other')
    assert evaluate(doc, values, ('g', 'h'), ('reference', 'other'), True) == [False, False]
    return dict(scope_foreground_background_combinations=count, all_selected_publics_required=True,
                foreground_and_background_independent=True, empty_and_ineligible_scopes_refused=True,
                original_public_and_reference_checked_before_disquotation=True,
                per_public_package_is_explicit_test_boundary=True)


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2mf'], 'q[k r2mf[]].')

    def quoted(value, name):
        return value.rank == 3 and json.loads(value.syntax) == dict(kind='call', symbol=name, arguments=[])

    def model(fore=True, back=True):
        values = unknowns(doc)
        values.update(hzp5=lambda: 'reason', wa=lambda: 'author', hzpz=lambda: 'foreground',
                      hzq2=lambda: 'background', hzp3=lambda: 'text',
                      hznreport=lambda n, a, c, s, r: fore and (n, a, s, r) == (
                          'reason', 'author', 'foreground', 'text') and quoted(c, 'r2md'),
                      hzrbgreport=lambda n, a, fg, bg, fs, bs, r: back and (n, a, fs, bs, r) == (
                          'reason', 'author', 'foreground', 'background', 'text') and
                      quoted(fg, 'r2md') and quoted(bg, 'r2me'))
        return values

    people, scenes = ('reason', 'author', 'foreground', 'background', 'other'), ('text', 'other')
    for fore, back in product((False, True), repeat=2):
        assert evaluate(doc, model(fore, back), people, scenes, True) == [fore and back]
    for name in ('hzp5', 'wa', 'hzpz', 'hzq2', 'hzp3'):
        values = model()
        values[name] = lambda: 'other'
        assert evaluate(doc, values, people, scenes, True) == [False]
    return dict(attribution_combinations=4, source_claim_and_background_closed=True,
                all_selection_world_and_expectation_facts_unexecuted=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='closed_guardian_forecast_and_background_second_sentence_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[129, 448], text=unit['text'][129:448]),
                selection=selection_binding(catalog(), [32, 57]), interpretation=LIMITS,
                remaining=['頚木の比喩と、予測内の同じ人物・自己離脱・伝播の前後関係を接続する。',
                           '第二文の語句・照応・提示を全体として再読し、第一文への理由提示とともに判断する。'],
                reference=dict(url='https://korpora.org/Kant/aa08/036.html', accessed='2026-10-20',
                               use='任用された後見役、大衆、sogarの焦点、後続の群衆の描写との文脈。採用解釈を唯一の読解としない。'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                preserved_first_sentence_characters=108, newly_reviewed_sentence_characters=0,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted({FULL, BASIS, DOC, INVENTORY, *PRIOR})})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert new.document['statements'][:-1] == old.document['statements']
    assert len(new.document['statements']) == 58
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    assert read(READING)['selection'] == selection_binding(new, [55, 56])
    validate_hashes(ROOT, read(READING)['source_sha256'])
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
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES), authored_statements=58,
                added_statement_index=57, preserved_whole_unit_reviews=len(reviews),
                preserved_first_sentence_characters=108, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('crowd', crowd_checks), ('appointment', appointment_checks), ('package', package_checks),
                     ('aggregation', aggregation_checks), ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, READING, *PRIOR, 'scripts/compose_guardian_forecast.py',
        'scripts/check_guardian_forecast.py', 'tests/test_guardian_forecast.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
        'scripts/check_expected_focus.py', 'scripts/check_focused_dissemination.py',
        'scripts/check_dissemination_content.py',
    }
    source = read(AUDIT)['source']
    phrase = 'sogar unter den eingesetzten Vormündern des großen Haufens'
    start = source['range'][0] + source['text'].index(phrase)
    return dict(status='closed_guardian_forecast_second_sentence_partial', document=FULL, **results,
                alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'],
                               range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS),
                               status='partial_guardian_focus_and_crowd'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
