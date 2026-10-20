"""Check the prospective comparison, parameter sharing and quoted attribution."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import FunctionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_prospective_comparison import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS,
    FIELDS, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_self_formed_course import source_values, PEOPLE, SCENES

INDEX = 'data/semantic-review-index-v117.json'
REPORT = 'reports/prospective-comparison-v1.json'
AUDIT = 'data/prospective-comparison-reading-v1.json'
DOC = 'docs/prospective-comparison-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/prospective-liberty-v1.json', 'reports/graded-modality-v1.json',
         'reports/self-formed-course-v1.json', 'reports/third-paragraph-v1.json']
FUNCTIONS = dict(origins='[d] d', extent='[h[a] c h[a] c] c', cases='[d] c',
                 scale='[a] c', less='[a a] c', near='[a] c')
EXPRS = {n: 'p z' + n if n in FUNCTIONS else 'k z' + n + '[]' for n, _ in FIELDS}
INPUTS = ''.join('r z' + n + (FUNCTIONS[n] if n in FUNCTIONS else '[] ' + t) + '.'
                 for n, t in FIELDS)
ARGS = ' '.join(EXPRS[n] for n, _ in FIELDS)


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
def individual_checks():
    doc = fixture(['r2ku'],
                  'r zperson[] a.r zframe[] a.r zinitial[] d.r zbranch[] d.'
                  'q[k r2ku[k zperson[] k zframe[] k zinitial[] k zbranch[]]].', ('bf', 'h4l'))
    rows = {}
    for variant in ('baseline', 'already_completed', 'later_origin', 'other_person',
                    'other_frame', 'missing_endpoint', 'other_worker', 'other_mind',
                    'no_self_work', 'no_autonomy_cause', 'outside_person_history'):
        values = source_values(doc, variant)
        initial = 'attained' if variant == 'already_completed' else 'completed' if variant == 'later_origin' else 'before'
        values.update(aa=lambda p: p in ('person', 'other'),
                      zperson=lambda: 'other' if variant == 'other_person' else 'person',
                      zframe=lambda: 'unrelated' if variant == 'other_frame' else 'part',
                      zinitial=lambda: initial, zbranch=lambda: 'completed',
                      h7q=lambda frame, branch, point: (frame, branch) == ('part', 'completed')
                      and point in SCENES and not (variant == 'missing_endpoint' and point == 'attained'))
        if variant == 'outside_person_history':
            values['ia'] = lambda p, branch, point: p == 'person' and point != 'attained'
        actual = evaluate(doc, values, PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for name in ('h7q', 'h4m', 'g3'):
        values = source_values(doc)
        values.update(aa=lambda p: p == 'person', zperson=lambda: 'person',
                      zframe=lambda: 'part', zinitial=lambda: 'before', zbranch=lambda: 'completed',
                      h7q=lambda f, b, p: (f, b) == ('part', 'completed'))
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(cases=rows, native_self_work_transition_and_cause_executed=True,
                existing_ability_contents_are_explicit_boundaries=True,
                past_success_not_reused_as_future_success=True, unknown_inputs_refused=3)


DOMAIN = ('person', 'group', 'source', 'frame', 'process', 'low', 'individual', 'public', 'near', 'high')
WORLDS = ('s0', 's1', 'f0', 'f1', 'e0', 'e1', 'actual')
SCALE = ('low', 'individual', 'public', 'near', 'high')


@lru_cache(None)
def modal_document():
    return fixture(['r2kv', 'r2kw'], INPUTS + 'r zreference[] d.' +
                   'q[k r2kv[k zreference[] ' + ARGS + ']].' +
                   'q[k r2kw[k zreference[] ' + ARGS + ']].',
                   ('hzmy', 'h4p', 'hzna'))


def modal_values(doc, variant='baseline', seen=None):
    def record(*row):
        if seen is not None:
            seen.add(row)
    cases = {'s1', 'f1', 'e1'}
    if variant == 'invalid_candidate':
        cases.add('actual')
    if variant == 'no_distinguishing_case':
        cases.remove('e1')
    public = {'s1', 'e1'}
    individual = {'s1'}
    if variant == 'same_outcomes':
        individual = set(public)
    if variant == 'individual_superset':
        individual = {'s1', 'e1', 'f1'}
    if variant == 'no_public_change':
        public = set()
    if variant == 'all_conditioned_success':
        public = {'s1', 'f1', 'e1'}

    def history(frame, branch, point):
        record('history_frame', frame)
        return frame == 'frame' and branch in ('s1', 'f1', 'e1') and point in (branch[0] + '0', branch)

    def before(first, last, branch):
        return history('frame', branch, first) and history('frame', branch, last) and first.endswith('0') and last.endswith('1')

    def scope(group, p, reference):
        record('reference', reference)
        return (group, p, reference) == ('group', 'person', 'actual')

    def change(group, process, start, end, branch, members, extent):
        # Explicit boundary for the already tested native group change. Inspect
        # the actual scope lambda supplied by hzng; do not assume it is fixed.
        record('public_branch', branch)
        return (group, process, start, end) == ('group', 'process', branch[0] + '0', branch) and \
            members('group', 'person', branch) and extent(
                FunctionValue(('individual',), 'truth', lambda p: p == 'person'),
                FunctionValue(('individual',), 'truth', lambda p: p == 'person')) and branch in public

    def self_work(person, process, start, end, branch):
        record('individual_branch', branch)
        return (person, process, start, end) == ('person', 'process', branch[0] + '0', branch) and branch in individual

    def permission(group, reference, source, point):
        record('permission_reference', reference)
        return (group, reference, source) == ('group', 'actual', 'source') and \
            variant != 'no_permission' and point[0] in ('s', 'f') and \
            not (variant == 'withdrawn_permission' and point.endswith('1'))

    values = unknowns(doc)
    values.update(
        zaudience=lambda: 'source' if variant == 'wrong_public' else 'group',
        zperson=lambda: 'source' if variant in ('wrong_person', 'nonhuman_zero_degree') else 'person',
        zsource=lambda: 'group' if variant == 'wrong_source' else 'source',
        zframe=lambda: 'frame', zreference=lambda: 's1' if variant == 'wrong_reference' else 'actual',
        zorigins=lambda b: b if variant == 'already_completed' else b[0] + '0' if b in ('s1', 'f1', 'e1') else 'actual',
        zextent=lambda members, changed: members('person') and changed('person'),
        zcases=lambda b: b in cases, zscale=lambda d: d in SCALE,
        zless=lambda a, b: a in SCALE and b in SCALE and SCALE.index(a) < SCALE.index(b),
        znear=lambda d: d == 'near', zlow=lambda: 'low', zhigh=lambda: 'high',
        zpublicdegree=lambda: 'high' if variant == 'all_conditioned_success' else 'public',
        zindividualdegree=lambda: 'public' if variant == 'reversed_comparison' else
            'high' if variant == 'individual_superset' else 'low' if variant == 'nonhuman_zero_degree' else 'individual',
        zconditioneddegree=lambda: 'public' if variant == 'not_near' else 'near',
        aa=lambda p: p == 'person', h7q=history, ic=before, h6t=scope,
        hzmy=change, h4p=self_work, hzna=permission,
    )
    return values


@lru_cache(None)
def modal_checks():
    doc = modal_document()
    rows = {}
    expected = {
        'baseline': [True, True], 'same_outcomes': [False, False],
        'individual_superset': [False, False], 'no_public_change': [False, False],
        'no_distinguishing_case': [False, False], 'already_completed': [False, False],
        'invalid_candidate': [False, False], 'wrong_public': [False, False],
        'nonhuman_zero_degree': [False, False],
        'wrong_person': [False, False], 'wrong_reference': [False, False],
        'wrong_source': [True, False], 'no_permission': [True, False],
        'withdrawn_permission': [True, False], 'not_near': [True, False],
        'all_conditioned_success': [True, False], 'reversed_comparison': [False, False],
    }
    for variant, wanted in expected.items():
        seen = set()
        actual = evaluate(doc, modal_values(doc, variant, seen), DOMAIN, WORLDS, True)
        assert actual == wanted, (variant, actual)
        rows[variant] = actual
        if variant == 'baseline':
            assert {r[1] for r in seen if r[0] in ('reference', 'permission_reference')} == {'actual'}
            assert {r[1] for r in seen if r[0] == 'history_frame'} == {'frame'}
    for name in ('zorigins', 'h7q', 'hzmy', 'h4p', 'zless'):
        values = modal_values(doc)
        values[name] = unknown
        try:
            evaluate(doc, values, DOMAIN, WORLDS, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(cases=rows, same_future_and_reference_used_by_both_goals=True,
                current_permission_and_actual_outcomes_not_required=True,
                liberty_not_made_necessary_or_sufficient=True,
                group_change_self_change_and_permission_are_explicit_boundaries=True,
                unknown_inputs_refused=5)


@lru_cache(None)
def attribution_checks():
    described = ' '.join('r[' + EXPRS[n] + ']' for n, _ in FIELDS)
    doc = fixture(['r2kz'], INPUTS + 'q[k r2kz[' + described + ']].')
    expected_arguments = [
        dict(kind='function_ref', symbol='z' + n) if n in FUNCTIONS else
        dict(kind='call', symbol='z' + n, arguments=[]) for n, _ in FIELDS
    ]
    expected = dict(kind='apply', function=dict(kind='function_ref', symbol='r2kx'), arguments=expected_arguments)
    seen = []

    def reports(node, author, description, context):
        seen.append(description)
        assert description.rank == 1 and description.result_type == '"content"'
        return (node, author, context) == ('conclusion', 'author', 'text') and json.loads(description.syntax) == expected

    values = unknowns(doc)
    values.update(hzp4=lambda: 'conclusion', wa=lambda: 'author', hzp3=lambda: 'text', hzon=reports)
    assert evaluate(doc, values, ('conclusion', 'author', 'other'), ('text', 'other'), True) == [True]
    for key in ('hzp4', 'wa', 'hzp3'):
        altered = dict(values)
        altered[key] = lambda: 'other'
        assert evaluate(doc, altered, ('conclusion', 'author', 'other'), ('text', 'other'), True) == [False]
    alternate = fixture(['r2kz'], INPUTS + 'q[k r2kz[' +
                        described.replace('r[k zperson[]]', 'r[k zsource[]]') + ']].')
    assert evaluate(alternate, values, ('conclusion', 'author', 'other'), ('text', 'other'), True) == [False]
    bad = dict(values, hzon=unknown)
    try:
        evaluate(doc, bad, ('conclusion', 'author', 'other'), ('text', 'other'), True)
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('unknown attribution')
    return dict(all_arguments_bound=15, closed_content_rank=1, content_inputs_not_executed=True,
                changed_comparison_person_not_accepted=True, unknown_attribution_refused=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    text = unit['text'][:128]
    assert text.endswith('beinahe unausbleiblich.')
    paths = {FULL, BASIS, DOC, INVENTORY, *PRIOR}
    return dict(status='prospective_comparison_partial_reading',
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[0, 128], text=text),
                document=FULL, meaning_basis=BASIS, definitions=list(MEANINGS),
                interpretation=LIMITS,
                unresolved=['公衆の社会的な範囲と広がり基準を明示し、任意の読者集合と区別する。',
                            '比較個人を先行段落の一般的な個人の読みへ接続し、全十五引数を原文用に固定する。',
                            'aber、ja、nurの範囲・提示関係と、自由の採用解釈を確定する。',
                            '固定した閉じた内容を本文へ帰属し、第一文全体を再読する。'],
                references=[dict(url='https://korpora.org/Kant/aa08/036.html', accessed='2026-10-20',
                                 use='第三・第四段落の前後関係と、後続する自由の限定を確認。')],
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-6] == old.document['declarations']
    assert new.document['statements'] == old.document['statements']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']
    for row in reviews['kant-1784']:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    # Both the comparative and conditioned paths have the exact same public
    # goal: the declaration is inherited, not an altered copy of hzng/hznh.
    assert all(new.entries[n] == old.entries[n] for n in ('hzng', 'hznh', 'hzmy', 'h4p', 'rqst', 'rqsu'))
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(added_definitions=6, added_primitives=0, authored_statements=55,
                preserved_whole_unit_reviews=len(reviews['kant-1784']), roundtrips=True,
                earlier_native_modal_and_capacity_evidence_preserved=True,
                first_sentence_review_still_pending=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('individual', individual_checks), ('modal', modal_checks),
                     ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR,
        'scripts/compose_prospective_comparison.py', 'scripts/check_prospective_comparison.py',
        'tests/test_prospective_comparison.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_self_formed_course.py',
        'scripts/compose_described_dissemination.py',
    }
    source = read(AUDIT)['source']
    # The complete first sentence is a locator, not an assertion of all its
    # wording being handled. Only the comparative/modal fragments are mapped.
    fragments = []
    for phrase in ('ist eher möglich', 'beinahe unausbleiblich'):
        start = source['text'].index(phrase)
        fragments.append(dict(unit=source['unit'], unit_sha256=source['unit_sha256'],
                              range=[start, start + len(phrase)], text=phrase,
                              definitions=['r2kv', 'r2kw'], status='explicit_partial_prospective_comparison'))
    return dict(status='prospective_comparison_connected_source_sentence_partial',
                document=FULL, **results, alignment=dict(segments=fragments),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
