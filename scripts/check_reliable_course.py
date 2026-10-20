"""Verify real course judgments and their binding into count, background and metaphor."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_reliable_course import (
    ROOT, PARENT, PARENT_BASIS, FULL, CORE, BASIS, ANNOTATIONS, REBOUND,
    MEANINGS, LIMITS, parent, build, closure, substitute,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_attributed_focus import unwrap
from scripts.check_uncertain_judgment import source_values, PEOPLE, SCENES

INDEX = 'data/semantic-review-index-v114.json'
AUDIT = 'data/reliable-course-reading-v1.json'
REPORT = 'reports/reliable-course-v1.json'
DOC = 'docs/reliable-course-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
SENTENCES = [('data/nature-sentence-reading-v1.json', [51]),
             ('data/confirmed-incapacity-reading-v1.json', [11, 12]),
             ('data/fetters-sentence-reading-v1.json', [10, 52]),
             ('data/fourth-sentence-reading-v1.json', [13, 53])]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, text):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + text)


def unknowns(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


@lru_cache(None)
def judgment_checks():
    doc = fixture(['r2jh', 'h5c'], '''
r zperson[] a.r zact[] a.r zanchor[] d.
q[k h5c[k zperson[] k zact[] k zanchor[]]].
q[k r2jh[k zperson[] k zact[] k zanchor[]]].
''')
    for actual, first, second in product((False, True), repeat=3):
        values = source_values(doc, actual_support=actual, responses=(first, second))
        assert evaluate(doc, values, PEOPLE, SCENES, True) == [actual, actual and first and second]
    rows = {}
    for variant in ('baseline', 'wrong_actual_topic', 'wrong_counterpart_topic', 'missing_counterpart',
                    'empty_profile', 'changed_basis', 'no_opportunity', 'guided_actual', 'cycle',
                    'support_for_other_judgment', 'missed_response'):
        actual = evaluate(doc, source_values(doc, variant, responses=(True, True)), PEOPLE, SCENES, True)
        assert actual[1] == (variant == 'baseline'), (variant, actual)
        rows[variant] = actual
    for missing in ('hzzzt', 'hzzzu', 'hzzzv', 'hzzzw', 'hzzzx', 'fd'):
        values = source_values(doc, responses=(True, True))
        values[missing] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(current_and_comparison_combinations=8, cases=rows, unknown_inputs_refused=6,
                present_reason_support_does_not_imply_reliable_performance=True,
                same_topic_and_nonempty_valid_comparison_required=True)


@lru_cache(None)
def episode_checks():
    doc = fixture(['h5d', 'r2ji', 'r2jj'], '''
r zp[] a.r ze[] a.r zlast[] d.
q[k h5d[k zp[] k ze[] k zlast[] k zlast[]]].
q[k r2ji[k zp[] k ze[] k zlast[] k zlast[]]].
q[t[k r2jj[k zp[]]][k zlast[]]].
''')
    people = ('person', 'other', 'faculty', 'episode', 'early', 'late',
              'copyearly', 'copylate', 'topic', 'reason', 'foreign')
    scenes = ('earlytime', 'end', 'comparison')

    def model(variant='baseline'):
        values = unknowns(doc)
        pairs = {('early', 'earlytime'), ('late', 'end'), ('copyearly', 'comparison'), ('copylate', 'comparison')}
        def performed(p, act, point):
            return p == 'person' and (act, point) in pairs and not (
                variant == 'no_early_judgment' and act == 'early')
        def support(reason, act, point):
            return reason == 'reason' and performed('person', act, point) and not (
                variant == 'early_unreliable' and act == 'copyearly' or
                variant == 'late_unreliable' and act == 'copylate' or
                variant == 'early_unsupported' and act == 'early' or
                variant == 'unrelated_unreliable_activity' and act == 'foreign')
        values.update(
            zp=lambda: 'person', ze=lambda: 'episode', zlast=lambda: 'end',
            aa=lambda p: p == 'person',
            ia=lambda p, anchor, point: p == 'person' and point in scenes[:2],
            ic=lambda first, last, anchor: (first, last) == ('earlytime', 'end'),
            h5a=lambda episode, last, point: (episode, last) == ('episode', 'end') and point in scenes[:2],
            h5b=lambda act, episode, point: episode == 'episode' and (act, point) in pairs and act in ('early', 'late'),
            fa=performed,
            dg=lambda act, point: performed('person', act, point) or (act, point) == ('episode', 'end'),
            ab=lambda faculty, p, point: (faculty, p) == ('faculty', 'person'),
            ac=lambda p, faculty, act, point: faculty == 'faculty' and performed(p, act, point),
            fb=lambda act, topic, point: topic == ('other' if variant == 'foreign_comparison_topic' and act == 'copyearly' else 'topic')
                and performed('person', act, point),
            fc=lambda act, reason, point: reason == 'reason' and performed('person', act, point), fd=support,
            ad=lambda guide, p, act, point: variant == 'guided_early' and
                (guide, p, act, point) == ('other', 'person', 'early', 'earlytime'),
            hzzzt=lambda p, act, topic, anchor, point: p == 'person' and topic == 'topic' and
                (act, anchor) in (('early', 'earlytime'), ('late', 'end')) and point == 'comparison' and
                not (variant == 'empty_early_comparison' and act == 'early'),
            hzzzu=lambda p, act, topic, anchor, point: not (variant == 'changed_early_basis' and act == 'early'),
            hzzzv=lambda p, topic, point: (p, topic) == ('person', 'topic'),
            hzzzw=lambda *args: False,
            hzzzx=lambda p, act, topic, anchor, point, copy:
                (p, topic, point) == ('person', 'topic', 'comparison') and
                (act, anchor, copy) in (('early', 'earlytime', 'copyearly'), ('late', 'end', 'copylate')) and
                not (variant == 'missing_early_counterpart' and act == 'early'),
        )
        if variant == 'unrelated_unreliable_activity':
            pairs.add(('foreign', 'earlytime'))  # Not a part of the chosen episode.
        return values
    rows = {}
    for variant in ('baseline', 'early_unreliable', 'late_unreliable', 'early_unsupported',
                    'no_early_judgment', 'guided_early', 'empty_early_comparison', 'changed_early_basis',
                    'missing_early_counterpart', 'foreign_comparison_topic', 'unrelated_unreliable_activity'):
        expected_old = variant not in ('early_unsupported', 'no_early_judgment', 'guided_early')
        expected_new = variant in ('baseline', 'unrelated_unreliable_activity')
        actual = evaluate(doc, model(variant), people, scenes, True)
        assert actual == [expected_old, expected_new, expected_new], (variant, actual)
        rows[variant] = actual
    return dict(cases=rows, native_episode_and_existential_course_executed=True,
                all_actual_episode_judgments_checked=True, achievement_and_body_inputs_unexecuted=True)


@lru_cache(None)
def connection_checks():
    old, new = parent(), catalog()
    declarations = {d['name']: d for d in new.document['declarations']}
    for source, target in REBOUND.items():
        expected = substitute(old.entries[source]['declaration'], REBOUND)
        expected['name'] = target
        if source == 'h5d':
            expected = substitute(expected, {'h5c': 'r2jh'})
        assert declarations[target] == expected, (source, target)
    # These saved checks exercised the unchanged count/attribution operations;
    # exact syntax rebinding proves where the new success property is supplied.
    prior = read('reports/fifth-sentence-scope-v1.json')
    validate_hashes(ROOT, prior['source_sha256'])
    assert prior['counts']['foreground_negation_preserves_background']
    assert prior['counts']['foreground_does_not_execute_expectations']
    doc = fixture(['r2jx', 'r2jy'], 'q[k r2jx[]].q[k r2jy[]].')
    people = ('author', 'condition', 'reason', 'conclusion', 'concession', 'gait')
    scenes = ('text',)
    def model(variant='baseline'):
        values = unknowns(doc)
        values.update(wa=lambda: 'author', wh=lambda: 'text', h3a=lambda: 'condition',
                      h3s=lambda: 'reason', h5t=lambda: 'conclusion', h222d=lambda: 'concession', h5f=lambda: 'gait')
        values.update(
            hznreport=lambda n, a, fg, scope, c: (n, a, scope, c) == ('conclusion', 'author', 'conclusion', 'text') and
                unwrap(fg) == dict(kind='call', symbol='r2jd' if variant == 'old_count' else 'r2ju', arguments=[]),
            hzrbgreport=lambda n, a, fg, bg, fs, bs, c:
                (n, a, fs, bs, c) == ('conclusion', 'author', 'conclusion', 'concession', 'text') and
                unwrap(bg) == dict(kind='call', symbol='r2je' if variant == 'old_background' else 'r2jv', arguments=[]),
            ud=lambda a, premises, n, c: (a, n, c) == ('author', 'conclusion', 'text') and
                {p for p in people if premises(p)} == {'condition', 'reason'},
            ue=lambda first, last, c: (first, last, c) == ('reason', 'conclusion', 'text'),
            qa=lambda n, a, target, depiction, c: (n, a, symbol(target), symbol(depiction), c) ==
                ('gait', 'author', 'h5e' if variant == 'old_metaphor' else 'r2jj', 'h4z', 'text'))
        return values
    rows = {}
    for variant, expected in [('baseline', [True, True]), ('old_count', [False, True]),
                              ('old_background', [False, True]), ('old_metaphor', [True, False])]:
        actual = evaluate(doc, model(variant), people, scenes, True)
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(rebound_definitions=len(REBOUND), exact_rebinding_verified=True, cases=rows,
                native_course_used_in_count_background_and_correspondence=True,
                prior_scope_checks_reused_with_unchanged_operations=True,
                quoted_world_contents_unexecuted=True)


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-18] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert len(new.document['statements']) == 54
    assert [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b] == [14, 15]
    reviews = load_reviews(ROOT, INDEX)['works']
    for row in reviews['kant-1784']:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in SENTENCES:
        record = read(path)
        validate_hashes(ROOT, record['source_sha256'])
        assert record['selection'] == selection_binding(new, indices)
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(added_definitions=18, added_primitives=0, revised_statement_indices=[14, 15],
                preserved_whole_unit_reviews=len(reviews['kant-1784']),
                preserved_reviewed_sentence_characters=544, roundtrips=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    phrase = 'einen sicheren Gang zu thun.'
    start = unit['text'].index(phrase)
    return dict(status='reliable_course_connected_fifth_sentence_still_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase),
                selection=selection_binding(catalog(), [14, 15]), interpretation_limits=LIMITS,
                decision='adopt_reliable_course_as_explicit_target_reading_not_whole_sentence_review',
                reviewer='assistant_review', remaining=['自己形成の意味説明と原文照合', '解放の描写と対象側の対応',
                    '自己活動の因果が離脱と確かな活動へ及ぶ範囲', '第五文および第三段落全体の通し確認'],
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                new_verified_sentence_characters=0, semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted({
                    INVENTORY, FULL, BASIS, DOC, PARENT_BASIS, 'reports/fifth-sentence-scope-v1.json',
                    'scripts/compose_reliable_course.py'})})


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('judgment', judgment_checks), ('episode', episode_checks),
                     ('connection', connection_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    record = reading()
    assert read(AUDIT) == record
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, 'scripts/compose_reliable_course.py', 'scripts/check_reliable_course.py',
        'tests/test_reliable_course.py', 'scripts/check_uncertain_judgment.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_attributed_focus.py', 'reports/fifth-sentence-scope-v1.json',
    } | {p for p, _ in SENTENCES}
    return dict(status=record['status'], document=FULL, **results,
                alignment=dict(**record['source'], definitions=['r2jh', 'r2ji', 'r2jj', 'r2jy'],
                               status='explicit_partial_reliable_course_reading'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                new_verified_sentence_characters=0, paragraph_reviewed_sentence_characters=544,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
