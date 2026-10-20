"""Check temporal scope, scenario bindings and preserved earlier judgments."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_dissemination_opportunities import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, REMAINING, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v120.json'
REPORT = 'reports/dissemination-opportunities-v1.json'
AUDIT = 'data/dissemination-opportunities-reading-v1.json'
DOC = 'docs/dissemination-opportunities-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/shared-public-scope-v1.json', 'reports/existential-route-fields-v1.json',
         'reports/qualitative-receipt-v1.json', 'reports/public-first-sentence-v1.json']
READING = 'data/public-first-sentence-reading-v1.json'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, extra, boundaries=()):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


@lru_cache(None)
def opportunity_checks():
    doc = fixture(['r2lp'], 'r zh[d] c.r zb[d d] c.r zo[d] c.r zr[d] c.r zi[] d.'
                  'q[k r2lp[p zh p zb k zi[] p zo p zr]].')
    points = ('past', 'base', 'middle', 'last')

    def model(selected, succeeds, base='base', history=points):
        return dict(zh=lambda p: p in history, zb=lambda a, b: points.index(a) < points.index(b),
                    zo=lambda p: p in selected, zr=lambda p: p in succeeds, zi=lambda: base)

    count = 0
    for bits in product((False, True), repeat=8):
        selected = {p for p, b in zip(points, bits[:4]) if b}
        succeeds = {p for p, b in zip(points, bits[4:]) if b}
        wanted = bool(selected) and selected <= {'middle'} and selected <= succeeds
        assert evaluate(doc, model(selected, succeeds), ('person',), points, True) == [wanted], bits
        count += 1
    for selected, history, wanted in [
        ({'middle'}, points, True), ({'last'}, points, False),
        ({'middle', 'last'}, points, False), ({'middle'}, ('past', 'base', 'middle'), False),
        ({'middle'}, ('past', 'middle', 'last'), False), ({'base'}, points, False),
        (set(), points, False), ({'past', 'middle'}, points, False),
    ]:
        assert evaluate(doc, model(selected, points, history=history), ('person',), points, True) == [wanted]
    cyclic = model({'middle'}, points)
    cyclic['zb'] = lambda a, b: a != b
    assert evaluate(doc, cyclic, ('person',), points, True) == [False]
    for name in ('zh', 'zb', 'zo', 'zr'):
        values = model({'middle'}, {'middle'})
        values[name] = unknown
        try:
            evaluate(doc, values, ('person',), points, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    # Diagnostic of the finite endpoint problem: a future completion is required
    # after each evaluation point. The old all-points reading includes the endpoint.
    contrast = fixture(['r2lp', 'rqtj'], 'r zh[d] c.r zb[d d] c.r zo[d] c.r zi[] d.'
                       'd zlater[point d] c[g next d[w[k zh[v next]][k zb[v point v next]]]].'
                       'q[k rqtj[p zh p zb k zi[] p zlater]].'
                       'q[k r2lp[p zh p zb k zi[] p zo p zlater]].')
    values = model({'middle'}, {'middle'})
    values.pop('zr')
    assert evaluate(contrast, values, ('person',), points, True) == [False, True]
    return dict(opportunity_and_response_combinations=count, endpoint_diagnostic=[False, True],
                invalid_opportunities_not_silently_filtered=True, unknown_inputs_refused=4)


EXTRA = '''
r zg[] a.r zr[] d.r zsubgroup[a d] c.
r zsubject[d a d] a.r zmessage[a] f.r zstate[a] e.
r zextent[h[a] c h[a] c] c.r zscope[d a a d] c.
r zthinkcases[d a d d] c.r zpreferred[d a d d d] c.
r ztopics[d a d d] a.r zpresented[d a a d] c.r zopportunities[d d] c.
'''
SUPPLIED = [
    'i[branch d][i[person a point d][k zsubject[v branch v person v point]]]',
    'i[branch d][i[person a point d][r[p zmessage]]]',
    'i[branch d][r[p zstate]]',
    'i[branch d][p zextent]',
    'i[branch d][i[center a recipient a reference d][k zscope[v branch v center v recipient v reference]]]',
    'i[branch d][i[person a point d scene d][k zthinkcases[v branch v person v point v scene]]]',
    'i[branch d][i[person a point d first d last d][k zpreferred[v branch v person v point v first v last]]]',
    'i[branch d][i[person a point d scene d][k ztopics[v branch v person v point v scene]]]',
    'i[branch d][i[person a matter a scene d][k zpresented[v branch v person v matter v scene]]]',
    'i[branch d][i[point d][k zopportunities[v branch v point]]]',
]


@lru_cache(None)
def connected_document():
    assert [n for n, t in REMAINING] == ['subject', 'message', 'state', 'extent', 'scope',
        'thinkcases', 'thinkpreferred', 'thinktopics', 'thinkpresented', 'opportunities']
    return fixture(['r2lt'], EXTRA + 'q[t[c[k r2lt[k zg[] k zr[] ' + ' '.join(SUPPLIED) +
                   ']][r[p zsubgroup]]][k zr[]]].', ('hznf', 'hzr6'))


@lru_cache(None)
def connection_checks():
    doc = connected_document()
    people = ('p', 'q', 'outside', 'group', 'frame', 'source', 'subject')
    times = ('past', 'base', 'first', 'second', 'last')
    scenes = (*times, 'reference', 'branch', 'alternate')
    records = set()

    def model(variant='baseline', allowed=('branch', 'alternate'), successful=('branch', 'alternate')):
        values = unknowns(doc)

        def at_field(branch, *args):
            assert branch in scenes, branch
            records.add((branch, *args))

        def subject(branch, person, opportunity):
            at_field(branch, person, opportunity)
            return 'subject'

        def valid_history(frame, branch, point):
            return frame == 'frame' and branch in ('branch', 'alternate') and point in times and not (
                variant == 'invalid_unpermitted_branch' and branch == 'alternate' and point == 'base')

        def opportunities(branch, point):
            return point in ({'last'} if variant == 'terminal_opportunity' else
                             {'first', 'second'} if variant == 'missing_later_thinkers' else
                             set() if variant == 'empty_opportunities' else
                             {'reference'} if variant == 'outside_opportunity' else {'first'})

        def permission(group, reference, source, frame, initial, branch):
            assert (group, reference, source, frame, initial) == ('group', 'reference', 'source', 'frame', 'base')
            return branch in allowed

        def qualified(reference, person, matter, message, state, frame, opportunity, branch,
                      extent, scope, cases, preferred, topics, presented):
            assert (reference, matter, frame) == ('reference', 'subject', 'frame')
            assert branch in scenes
            assert symbol(message) == 'zmessage' and symbol(state) == 'zstate'
            # Exercise the actual higher-order inputs with the same candidate.
            assert scope(person, 'outside', reference)
            assert cases(person, opportunity, branch)
            assert not cases(person, opportunity, 'alternate' if branch != 'alternate' else 'branch')
            assert preferred(person, opportunity, branch, 'last')
            assert topics(person, opportunity, branch) == 'subject'
            assert presented(person, 'subject', branch)
            # The endpoint guard is native r2lp; this boundary tests person/time
            # wiring, not the truth of unbounded transmission quantifiers.
            return person in ('p', 'q') and branch in successful and not (
                variant == 'missing_later_thinkers' and opportunity == 'second') and not (
                variant == 'one_thinker' and person == 'q')

        values.update(zg=lambda: 'group', zr=lambda: 'reference',
                      h222f=lambda g, r: 'source' if (g, r) == ('group', 'reference') else 'outside',
                      h222g=lambda g, r: 'frame' if (g, r) == ('group', 'reference') else 'outside',
                      h222h=lambda g, r, b: 'base' if (g, r) == ('group', 'reference') else 'reference',
                      h222k=lambda g, r, b: (g, r) == ('group', 'reference') and b in ('branch', 'alternate'),
                      h7q=valid_history,
                      ic=lambda first, last, branch: branch in ('branch', 'alternate') and first in times and
                      last in times and times.index(first) < times.index(last),
                      aa=lambda p: p in ('p', 'q', 'outside'),
                      h6t=lambda g, p, r: (g, r) == ('group', 'reference') and p in (
                          ('p', 'q', 'frame') if variant == 'nonhuman_member' else ('p', 'q')),
                      hznf=permission, hzr6=qualified, zsubject=subject,
                      zextent=lambda population, changed: True,
                      zsubgroup=lambda p, t: p == ('outside' if variant == 'missing_subgroup' else 'p'),
                      zscope=lambda b, p, q, r: (at_field(b, p, q, r) is None) and r == 'reference',
                      zthinkcases=lambda b, p, t, s: at_field(b, p, t, s) is None and b == s,
                      zpreferred=lambda b, p, t, f, l: at_field(b, p, t, f, l) is None and b == f and l == 'last',
                      ztopics=lambda b, p, t, s: 'subject' if at_field(b, p, t, s) is None and b == s else 'outside',
                      zpresented=lambda b, p, m, s: at_field(b, p, m, s) is None and b == s,
                      zopportunities=opportunities)
        return values

    count = 0
    for flags in product((False, True), repeat=4):
        allowed = {b for b, flag in zip(('branch', 'alternate'), flags[:2]) if flag}
        successful = {b for b, flag in zip(('branch', 'alternate'), flags[2:]) if flag}
        actual = evaluate(doc, model(allowed=allowed, successful=successful), people, scenes, True)
        assert actual == [bool(allowed) and allowed <= successful], (flags, actual)
        count += 1
    rows = {}
    for variant in ('terminal_opportunity', 'empty_opportunities', 'outside_opportunity',
                    'missing_later_thinkers', 'one_thinker', 'missing_subgroup', 'nonhuman_member',
                    'invalid_unpermitted_branch'):
        values = model(variant, allowed=('branch',))
        actual = evaluate(doc, values, people, scenes, True)
        assert actual == [False], (variant, actual)
        rows[variant] = actual
    assert {'branch', 'alternate'} <= {r[0] for r in records}
    for name in ('zopportunities', 'h7q', 'h6t', 'hzr6'):
        values = model()
        values[name] = unknown
        try:
            evaluate(doc, values, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(permission_and_forecast_combinations=count, contrasts=rows, shared_reference_period_and_candidate=True,
                complete_selected_opportunity_scope_checked=True, native_history_and_quantification=True,
                permission_and_unbounded_dissemination_are_explicit_boundaries=True, unknown_inputs_refused=4)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='second_sentence_opportunity_and_scenario_connection_partial',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[129, 448], text=unit['text'][129:448]),
                interpretation=LIMITS,
                remaining=['十供給関数を原文に合う内容・性向・周囲・広がり・評価機会へ束縛する。',
                           '任用・大衆、sogarの背景、頚木の比喩、自己離脱との照応を閉じた著者帰属へ接続する。',
                           '第二文全体の意味要件を再読し、第一文への理由提示を含めて判断する。'],
                reference=dict(url='https://korpora.org/Kant/aa08/036.html', accessed='2026-10-20',
                               use='immerを伴う存在予測と、同じ人々による後続の伝播の区別。機会の限定は明示した解釈であり、原文に特定日時はない。'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=0, preserved_first_sentence_characters=108,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted({FULL, BASIS, DOC, INVENTORY, *PRIOR})})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert new.document['statements'] == old.document['statements']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    # Only the outer temporal quantifier changes. Remove that change and
    # canonicalize binders: the remaining declaration must equal the old AST.
    before = old.entries['hzr7']['declaration']['body']['body']
    after = new.entries['r2lq']['declaration']['body']['body']
    assert before['symbol'] == 'rqtj' and after['symbol'] == 'r2lp'
    restored = deepcopy(new.entries['r2lq']['declaration'])
    restored['name'] = 'hzr7'
    restored['parameters'].pop()
    restored['body']['body']['symbol'] = 'rqtj'
    restored['body']['body']['arguments'].pop(3)
    context = deepcopy(old.document)
    position = next(i for i, d in enumerate(context['declarations']) if d['name'] == 'hzr7')
    context['declarations'][position] = restored
    assert parse(format_graph(context, 'compact')) == old.document
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
    return dict(new_definitions=len(MEANINGS), new_primitives=0, statements_preserved=57,
                remaining_providers=len(REMAINING), preserved_whole_unit_reviews=len(reviews),
                preserved_first_sentence_characters=108, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('opportunities', opportunity_checks), ('connection', connection_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, READING, *PRIOR,
        'scripts/compose_dissemination_opportunities.py', 'scripts/check_dissemination_opportunities.py',
        'tests/test_dissemination_opportunities.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/compose_shared_public_scope.py',
        'scripts/compose_shared_future_period.py', 'scripts/compose_existential_route_fields.py',
        'scripts/compose_described_dissemination.py', 'scripts/compose_thinking_disseminators.py',
        'scripts/compose_existential_focus.py',
    }
    source = read(AUDIT)['source']
    phrase = 'werden sich immer'
    start = source['range'][0] + source['text'].index(phrase)
    return dict(status='second_sentence_temporal_connection_partial', document=FULL, **results,
                alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'],
                               range=[start, start + len(phrase)], text=phrase,
                               definitions=list(MEANINGS), status='partial_opportunity_scope'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
