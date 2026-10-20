"""Check real reasoning, assessed dispositions, change, and two-result binding."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_thinking_reform import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_revolution_routes as routes
from scripts import check_political_withdrawal as withdrawal

INDEX = 'data/semantic-review-index-v138.json'
REPORT = 'reports/thinking-reform-v1.json'
AUDIT = 'data/thinking-reform-reading-v1.json'
DOC = 'docs/thinking-reform-v1.md'
INVENTORY = withdrawal.INVENTORY
PRIOR = 'reports/revolution-routes-v1.json'
PEOPLE = ('person', 'other', 'topic', 'second', 'judgment', 'bad', 'faculty', 'reason', 'process')
SCENES = ('before', 'after', 'normal', 'exception')
CONSTANTS = 'r zp[] a.r zscope[] d.r zanchor[] d.r zprocess[] a.r zfirst[] d.r zlast[] d.r zhistory[d] c.r zbefore[d d] c.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, text, boundaries=()):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + text)


def values(doc, variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    def counterparts(person, topic, scope, anchor, scene, judgment):
        if variant == 'missing_counterpart':
            return False
        if variant == 'mixed_counterparts':
            return person == 'person' and judgment in ('judgment', 'bad')
        wanted = 'bad' if anchor == 'before' or scene == 'exception' or (
            variant == 'only_one_topic' and topic == 'second') else 'judgment'
        if variant == 'already_reformed':
            wanted = 'judgment'
        if variant == 'opinions_only':
            wanted = 'bad'
        return person == 'person' and judgment == wanted
    v.update(
        zp=lambda: 'person', zscope=lambda: 'before', zanchor=lambda: 'after',
        zprocess=lambda: 'process', zfirst=lambda: 'before', zlast=lambda: 'after',
        zhistory=lambda point: point in ('before', 'after'),
        zbefore=lambda first, last: (first, last) == ('before', 'after') and variant != 'reversed_history',
        aa=lambda person: person in ('person', 'other'),
        h226u=lambda person, scope, topic: person == 'person' and scope == 'before' and
            topic in ('topic', 'second') and variant != 'empty_topics',
        h226v=lambda person, topic, scope, anchor, scene: scene in ('normal', 'exception') and
            variant != 'empty_cases',
        h226w=lambda person, topic, scope, anchor, scene: variant != 'changed_basis',
        h226x=lambda person, topic, scope, anchor, first, last:
            False if variant == 'both_normal' else
            (first, last) == ('normal', 'exception') if variant != 'cyclic_normality' else first != last,
        h226y=counterparts,
        hzzzv=lambda person, topic, scene: variant != 'no_opportunity',
        r2gy=lambda person, judgment, topic, scene: person == 'person' and judgment == 'judgment',
        ag=lambda process, first, last: (process, first, last) == ('process', 'before', 'after')
            and variant != 'no_process',
        la=lambda person, process, first, last:
            (person, process, first, last) == ('person', 'process', 'before', 'after')
            and variant != 'other_affected',
        dg=lambda judgment, point: judgment in ('judgment', 'bad') and variant != 'no_occurrence',
        fa=lambda person, judgment, point: person == 'person' and judgment in ('judgment', 'bad'),
        fb=lambda judgment, topic, point: judgment in ('judgment', 'bad') and topic in ('topic', 'second')
            and variant != 'other_topic',
        ab=lambda faculty, person, point: (faculty, person) == ('faculty', 'person'),
        ac=lambda person, faculty, judgment, point: (person, faculty) == ('person', 'faculty') and
            judgment in ('judgment', 'bad') and variant != 'no_own_use',
        fc=lambda judgment, reason, point: judgment == 'judgment' and reason == 'reason'
            and variant != 'reason_for_other_judgment',
        fd=lambda reason, judgment, point: (reason, judgment) == ('reason', 'judgment')
            and variant != 'unsupported_reason',
        ad=lambda other, person, judgment, point:
            variant == 'guided' and (other, person) == ('other', 'person'),
    )
    return v


@lru_cache(None)
def reasoning_checks():
    doc = fixture(['r2ql'], CONSTANTS +
                  'r ztopic[] a.r zscene[] d.'
                  'q[k r2ql[k zp[] k ztopic[] k zscope[] k zanchor[] k zscene[]]].')
    rows = {}
    for variant in ('baseline', 'no_occurrence', 'other_topic', 'no_own_use',
                    'reason_for_other_judgment', 'unsupported_reason', 'guided'):
        v = values(doc, variant)
        v.update(ztopic=lambda: 'topic', zscene=lambda: 'normal')
        actual = evaluate(doc, v, PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_own_faculty_same_judgment_and_reasons=True)


@lru_cache(None)
def disposition_checks():
    doc = fixture(['r2qm', 'r2qn'], CONSTANTS +
                  'q[k r2qm[k zp[] k zscope[] k zanchor[]]].'
                  'q[k r2qn[k zp[] k zscope[] k zanchor[]]].', ('r2gy',))
    rows = {}
    malformed = {'empty_topics', 'empty_cases', 'changed_basis', 'no_opportunity',
                 'missing_counterpart', 'cyclic_normality'}
    for variant in ('baseline', 'only_one_topic', 'opinions_only', 'mixed_counterparts',
                    'both_normal', *sorted(malformed)):
        actual = evaluate(doc, values(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant not in malformed, variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for name in ('h226u', 'h226v', 'h226w', 'h226x', 'h226y', 'hzzzv', 'r2gy'):
        v = values(doc); v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, all_fixed_topics_and_normal_counterparts=True,
                unsuccessful_exception_allowed=True, boundary=['r2gy'],
                unknown_inputs_refused=7)


@lru_cache(None)
def change_checks():
    doc = fixture(['r2qp'], CONSTANTS +
                  'q[k r2qp[k zp[] k zprocess[] k zscope[] k zfirst[] k zlast[] p zhistory p zbefore]].')
    rows = {}
    for variant in ('baseline', 'already_reformed', 'opinions_only', 'only_one_topic',
                    'no_process', 'other_affected', 'reversed_history', 'empty_cases'):
        actual = evaluate(doc, values(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_full_reform_with_reasoning_and_normality=True,
                same_person_scope_process_and_endpoints=True)


@lru_cache(None)
def route_checks():
    extra = routes.EXTRA + withdrawal.RESULT + '''
d zreform[target a] e[b point[
 t[c[k r2qq[k zfirst[] k zfirst[] p zhistory p zbefore]][v target]][v point]]].
q[k r2qk[k ztarget[] k zcommunity[] k zfirst[] p zold p zproposed p zactors
 r[p zresult] r[p zreform] p zcandidate]].
'''
    doc = fixture(['r2qk', 'r2qe', 'r2qq'], extra, ('r2qm', 'r2qn'))
    rows = {}
    for variant in ('baseline', 'revolution_also_reforms', 'reform_without_cause',
                    'cause_without_change', 'no_withdrawal'):
        v = routes.model(doc, 'still_oppression' if variant == 'no_withdrawal' else 'baseline')
        previous = v['g3']
        v.update(
            r2qm=lambda person, scope, anchor: person == 'target',
            r2qn=lambda person, scope, anchor: person == 'target' and anchor == 'after'
                and variant != 'cause_without_change',
            g3=lambda act, person, desc, point: previous(act, person, desc, point) or
                (act, person, symbol(desc), point) == ('event', 'target', 'zreform', 'after')
                and variant in ('revolution_also_reforms', 'cause_without_change'),
        )
        actual = evaluate(doc, v, routes.PEOPLE, routes.SCENES, True)
        assert actual == [variant not in ('revolution_also_reforms', 'no_withdrawal')], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_revolution_withdrawal_and_reform_transition=True,
                disposition_boundaries=['r2qm', 'r2qn'], disposition_definitions_tested_locally=True,
                cause_and_result_both_required=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    phrase = 'wahre Reform der Denkungsart'
    start = unit['text'].index(phrase)
    return dict(status='thinking_reform_result_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[start, start + len(phrase)], text=phrase),
                interpretation=LIMITS, definitions=list(MEANINGS),
                supporting_reading=['https://korpora.org/Kant/aa08/036.html',
                                    'https://korpora.org/Kant/aa08/146.html'],
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_four_sentence_characters=771,
                unresolved=['公衆全体の対象範囲と候補供給', '様相・対比・著者帰属',
                            '新旧の偏見と誘導の描写', '第五文と段落の通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 61
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in withdrawal.REVIEWS:
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
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
                unchanged_statements=61, old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('reasoning', reasoning_checks), ('disposition', disposition_checks),
                     ('change', change_checks), ('routes', route_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in withdrawal.REVIEWS],
        'scripts/compose_thinking_reform.py', 'scripts/check_thinking_reform.py',
        'tests/test_thinking_reform.py', 'scripts/check_revolution_routes.py',
        'scripts/check_political_withdrawal.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_scoped_counts.py',
        'scripts/check_public_comparison_claim.py'}
    return dict(status='thinking_reform_result_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_thinking_reform_result'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
