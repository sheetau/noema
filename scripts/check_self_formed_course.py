"""Check same-person self-work, both outcomes, and real causal contribution."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_self_formed_course import (
    ROOT, PARENT, PARENT_BASIS, FULL, CORE, BASIS, ANNOTATIONS,
    REBOUND, SUBSTITUTIONS, LIMITS, parent, build, closure, substitute,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_attributed_focus import unwrap

INDEX = 'data/semantic-review-index-v115.json'
AUDIT = 'data/self-formed-course-reading-v1.json'
REPORT = 'reports/self-formed-course-v1.json'
DOC = 'docs/self-formed-course-v1.md'
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


def fixture(roots, text, boundaries=()):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + text)


def unknowns(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


PEOPLE = ('person', 'other', 'work', 'episode', 'part', 'unrelated')
SCENES = ('before', 'attained', 'completed')
ARGUMENTS = 'k zp[] k zw[] k zbefore[] k zattained[] k ze[] k zcompleted[] k zanchor[]'
CONSTANTS = 'r zp[] a.r zw[] a.r ze[] a.r zbefore[] d.r zattained[] d.r zcompleted[] d.r zanchor[] d.'


def source_values(doc, variant='baseline'):
    values = unknowns(doc)
    completion = 'before' if variant == 'course_before_achievement' else 'attained' if variant == 'simultaneous' else 'completed'
    episode = 'work' if variant == 'same_complex_process' else 'episode'
    values.update(
        zp=lambda: 'person', zw=lambda: 'work', ze=lambda: episode,
        zbefore=lambda: 'before', zattained=lambda: 'attained',
        zcompleted=lambda: completion, zanchor=lambda: 'completed',
        ia=lambda p, anchor, point: p == 'person' and point in SCENES,
        ic=lambda first, last, anchor: SCENES.index(first) < SCENES.index(last),
        bf=lambda p: Content(SCENES, (p == 'person', False, False)),
        h4l=lambda p: Content(SCENES, (False, p == 'person', p == 'person')),
        ag=lambda process, earlier, later: (process, earlier, later) == ('work', 'before', 'attained'),
        la=lambda p, process, earlier, later: (p, process, earlier, later) == ('person', 'work', 'before', 'attained'),
        dg=lambda process, point: (process, point) == ('work', 'attained'),
        df=lambda p, process, point: (p, process, point) ==
            ('other' if variant == 'other_worker' else 'person', 'work', 'attained'),
        h4m=lambda part, p, point: (part, p, point) ==
            ('part', 'other' if variant == 'other_mind' else 'person', 'attained'),
        h4n=lambda p, part, process, point: variant != 'no_self_work' and (p, part, process, point) ==
            ('person', 'part', 'unrelated' if variant == 'unrelated_self_work' else 'work', 'attained'),
        g3=lambda process, p, description, point: variant != 'no_autonomy_cause' and
            (process, p, symbol(description), point) == ('work', 'person', 'h4l', 'attained'),
        r2ji=lambda p, act, last, anchor: variant != 'no_reliable_course' and
            (p, act, last, anchor) == ('other' if variant == 'other_course_owner' else 'person',
                                     episode, completion, 'completed'),
        hzie=lambda process, factor, act, effect, anchor: variant != 'no_course_cause' and
            (process, symbol(factor), act, symbol(effect), anchor) ==
            ('unrelated' if variant == 'other_cause_process' else 'work',
             'r2ka' if variant == 'wrong_factor_description' else 'r2jz',
             'unrelated' if variant == 'other_cause_episode' else episode,
             'r2jz' if variant == 'wrong_effect_description' else 'r2ka',
             'attained' if variant == 'wrong_cause_context' else 'completed'),
        ea=lambda *args: True,  # An explanatory attribution cannot replace hzie.
    )
    if variant == 'other_worker_also_participates':
        values['df'] = lambda p, process, point: p in ('person', 'other') and (process, point) == ('work', 'attained')
    return values


@lru_cache(None)
def causal_checks():
    doc = fixture(['h4p', 'r2kb'], CONSTANTS +
                  'q[k h4p[k zp[] k zw[] k zbefore[] k zattained[] k zanchor[]]].' +
                  'q[k r2kb[' + ARGUMENTS + ']].', ('bf', 'h4l', 'r2ji'))
    rows = {}
    failures_of_achievement = {'other_worker', 'other_mind', 'no_self_work', 'unrelated_self_work', 'no_autonomy_cause'}
    accepted = {'baseline', 'simultaneous', 'same_complex_process', 'other_worker_also_participates'}
    for variant in ('baseline', 'no_course_cause', 'other_cause_process', 'other_cause_episode',
                    'wrong_factor_description', 'wrong_effect_description', 'wrong_cause_context',
                    'no_reliable_course', 'other_course_owner', 'course_before_achievement',
                    'other_worker', 'other_mind', 'no_self_work', 'unrelated_self_work', 'no_autonomy_cause',
                    'simultaneous', 'same_complex_process', 'other_worker_also_participates'):
        actual = evaluate(doc, source_values(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant not in failures_of_achievement, variant in accepted], (variant, actual)
        rows[variant] = actual
    for missing in ('h4m', 'h4n', 'df', 'g3', 'hzie', 'r2ji'):
        values = source_values(doc)
        values[missing] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error), (missing, str(error))
        else:
            raise AssertionError(missing)
    # Execute the actual witness quantifiers once positively and once with
    # co-occurring outcomes but no causal contribution to the course.
    quantified = fixture(['r2kc'], CONSTANTS + 'q[t[k r2kc[k zp[]]][k zanchor[]]].',
                         ('bf', 'h4l', 'r2ji'))
    existential = {}
    for variant in ('baseline', 'no_course_cause'):
        actual = evaluate(quantified, source_values(quantified, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        existential[variant] = actual
    return dict(cases=rows, existential_success_cases=existential,
                unknown_inputs_refused=6, native_self_work_and_achievement_executed=True,
                ability_contents_and_prior_reliable_course_are_explicit_boundaries=True,
                time_order_and_explanation_do_not_replace_causation=True,
                same_person_work_part_and_course_required=True,
                simultaneous_completion_and_shared_process_allowed=True)


@lru_cache(None)
def connection_checks():
    old, new = parent(), catalog()
    for source, target in REBOUND.items():
        expected = substitute(old.entries[source]['declaration'], SUBSTITUTIONS)
        expected['name'] = target
        assert new.entries[target]['declaration'] == expected, (source, target)
    prior = read('reports/reliable-course-v1.json')
    validate_hashes(ROOT, prior['source_sha256'])
    assert prior['episode']['native_episode_and_existential_course_executed']
    assert new.entries['r2ji'] == old.entries['r2ji']
    assert new.document['statements'][14] == old.document['statements'][14]
    doc = fixture(['r2kn'], 'q[k r2kn[]].')
    people = ('author', 'condition', 'reason', 'conclusion', 'concession')
    values = unknowns(doc)
    values.update(wa=lambda: 'author', wh=lambda: 'text', h3a=lambda: 'condition',
                  h3s=lambda: 'reason', h5t=lambda: 'conclusion', h222d=lambda: 'concession')
    fg, bg = [dict(kind='call', symbol=n, arguments=[]) for n in ('r2kk', 'r2kl')]
    values.update(
        hznreport=lambda n, a, content, scope, c: (n, a, scope, c) == ('conclusion', 'author', 'conclusion', 'text')
            and unwrap(content) == fg,
        hzrbgreport=lambda n, a, front, back, fs, bs, c: (n, a, fs, bs, c) ==
            ('conclusion', 'author', 'conclusion', 'concession', 'text') and unwrap(front) == fg and unwrap(back) == bg,
        ud=lambda a, premises, n, c: (a, n, c) == ('author', 'conclusion', 'text')
            and {p for p in people if premises(p)} == {'condition', 'reason'},
        ue=lambda first, last, c: (first, last, c) == ('reason', 'conclusion', 'text'))
    assert evaluate(doc, values, people, ('text',), True) == [True]
    for stale, wanted in [('r2ju', fg), ('r2jv', bg)]:
        original = deepcopy(wanted)
        wanted['symbol'] = stale
        assert evaluate(doc, values, people, ('text',), True) == [False]
        wanted.update(original)
    return dict(exact_rebound_definitions=len(REBOUND),
                new_causal_success_used_by_counts_and_background=True,
                earlier_reliable_course_and_gait_correspondence_preserved=True,
                stale_foreground_and_background_rejected=True,
                all_world_and_causal_inputs_unexecuted_in_attribution=True)


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-15] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert len(new.document['statements']) == 54
    assert [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b] == [15]
    reviews = load_reviews(ROOT, INDEX)['works']
    for row in reviews['kant-1784']:
        indices = [s['index'] for s in row['selection']['statements']]
        assert row['selection'] == selection_binding(new, indices)
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
    return dict(added_definitions=15, added_primitives=0, revised_statement_indices=[15],
                preserved_whole_unit_reviews=len(reviews['kant-1784']),
                preserved_reviewed_sentence_characters=544, roundtrips=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    start = unit['text'].index('durch eigene Bearbeitung')
    return dict(status='self_formation_and_both_outcomes_causally_connected_sentence_partial',
                reviewer='assistant_review', decision='adopt_explicit_wide_instrumental_scope',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, len(unit['text'])],
                            text=unit['text'][start:]),
                selection=selection_binding(catalog(), [15]), interpretation_limits=LIMITS,
                mental_work_reading=dict(part='h4m', self_work='h4n', same_person_and_part='h4o',
                    outcome_not_built_into_work_kind=True,
                    mechanics_effort_and_repetition_not_specified_by_source=True,
                    basic_conventions_explicit_not_a_complete_theory_of_mind=True),
                references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036',
                                 accessed='2026-10-20',
                                 use='第五文の並列とdurchの範囲を再読。両成果への広い範囲は明示した読解であり唯一性の証明ではない。')],
                remaining=['heraus zu wikkelnの解放描写と対象側の対応',
                           '第五文と第三段落の全関係・参照・提示範囲の通し確認'],
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                new_verified_sentence_characters=0, semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted({
                    INVENTORY, FULL, BASIS, DOC, PARENT_BASIS, 'reports/reliable-course-v1.json',
                    'scripts/compose_self_formed_course.py'})})


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('causal', causal_checks), ('connection', connection_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    record = reading()
    assert read(AUDIT) == record
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, 'scripts/compose_self_formed_course.py',
        'scripts/compose_reliable_course.py', 'scripts/check_self_formed_course.py',
        'tests/test_self_formed_course.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_attributed_focus.py', 'reports/reliable-course-v1.json',
    } | {p for p, _ in SENTENCES}
    return dict(status=record['status'], document=FULL, **results,
                alignment=dict(**record['source'], definitions=['r2jz', 'r2ka', 'r2kb', 'r2kc'],
                               status='explicit_partial_wide_instrumental_reading'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                new_verified_sentence_characters=0, paragraph_reviewed_sentence_characters=544,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
