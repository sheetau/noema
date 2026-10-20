"""Check same-process public production, possibility and exclusion separately."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_enlightenment_route import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_enlightenment_extent as extent

INDEX = 'data/semantic-review-index-v157.json'
REPORT = 'reports/public-enlightenment-route-v1.json'
AUDIT = 'data/public-enlightenment-route-reading-v1.json'
DOC = 'docs/public-enlightenment-route-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ('reports/public-freedom-duty-v1.json', 'reports/enlightenment-extent-v1.json',
         'reports/audience-change-v1.json', 'reports/public-comparison-claim-v1.json')
PEOPLE, SCENES = extent.PEOPLE, extent.SCENES
EXTRA = extent.EXTRA
PREFIX = 'k zpublic[] k zreference[]'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    roots = {'episode': ['r2yj', 'r2ln'], 'part': ['r2yk'], 'quantified': ['r2yl'],
             'combined': ['r2yl'], 'claim': ['r2ym'], 'attribution': ['r2yn']}[kind]
    boundaries = {'episode': ('hzmx', 'r2la'), 'part': ('hzmx',),
                  'quantified': ('r2wy', 'r2wz', 'r2yj', 'r2yk'),
                  'combined': ('hzmx', 'r2la'), 'claim': ('r2yl',), 'attribution': ()}[kind]
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    if kind == 'episode':
        queries = ''.join(
            'q[t[k r2ln[' + PREFIX + ']][k z' + side + '[]]].'
            'q[g process a[g before d[g after d[k r2yj[' + PREFIX +
            ' k z' + side + '[] v process v before v after]]]]].' for side in ('left', 'right'))
    elif kind == 'part':
        queries = 'q[k r2yk[' + PREFIX + ' k zleft[] k zpublic[] k zreference[] k zleft[]]].'
    elif kind == 'claim':
        queries = 'q[t[k r2ym[]][k zreference[]]].'
    elif kind == 'attribution':
        queries = 'q[k r2yn[]].'
    else:
        queries = 'q[k r2yl[' + PREFIX + ']].'
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + EXTRA + queries)


def model(doc, changes=None, variant='baseline'):
    changes = changes or {}
    v = extent.model(doc, changes)
    def changed(group, actor, person, process, part, before, after, branch, scope):
        # Keep the already checked hzmx boundary consistent with distinct
        # internal actor/recipient, even in a two-person audience.
        counterpart = 'two' if person == 'one' else 'one'
        expected_part = 'two' if process == 'process' or variant == 'incidental_public_activity' else 'process'
        if (group, actor, part, before, after) != (
                'process' if variant == 'other_public' else 'public',
                'public' if variant == 'other_actor' else counterpart,
                expected_part,
                'right' if variant == 'other_start' else 'reference',
                'right' if variant == 'other_end' else branch):
            return False
        assert {p for p in PEOPLE if scope('public', p, branch)} == {'one', 'two'}
        wanted_process = 'process' if variant == 'other_process' else process
        return variant != 'no_productive_part' and person in changes.get((branch, wanted_process), set())
    v.update(hzmx=changed,
             h222k=lambda public, reference, branch: (public, reference) == ('public', 'reference')
                 and branch in ('left', 'right'),
             ca=lambda person, act, reference: person in ('one', 'two') and act in ('process', 'two')
                 and reference == 'reference' and variant != 'not_own_reason',
             cb=lambda person, act, role, reference: person in ('one', 'two') and act == 'process'
                 and role == 'process' and reference == ('left' if variant == 'moving_classification' else 'reference'),
             cd=lambda role, reference: (role, reference) == ('process', 'reference') and variant != 'not_scholar',
             cc=lambda act, audience, reference: (act, audience, reference) == ('process', 'public', 'reference'),
             ce=lambda audience, reference: (audience, reference) == ('public', 'reference') and variant != 'private_audience')
    return v


@lru_cache(None)
def episode_checks():
    doc = fixture('episode')
    sets = (set(), {'one'}, {'two'}, {'one', 'two'})
    rows = []
    for left, right in product(sets, repeat=2):
        actual = evaluate(doc, model(doc, {('left', 'public'): left, ('right', 'public'): right}),
                          PEOPLE, SCENES, True)
        wanted = [len(left) == 2] * 2 + [len(right) == 2] * 2
        assert actual == wanted, (left, right, actual)
        rows.append(dict(left=sorted(left), right=sorted(right), old_goal_and_episode=actual))
    split = {('left', 'public'): {'one'}, ('left', 'process'): {'two'}}
    assert evaluate(doc, model(doc, split), PEOPLE, SCENES, True) == [False] * 4
    return dict(goal_equivalence_cases=rows, separate_processes_not_merged=True,
                threshold_equality_not_attainment=True,
                semantic_boundaries=['hzmx and r2la retain prior meaning and tests; ratio, temporal placement and old r2ln execute natively'])


@lru_cache(None)
def part_checks():
    doc = fixture('part')
    changes = {('left', 'public'): {'one', 'two'}}
    rows = {}
    for variant in ('baseline', 'no_productive_part', 'incidental_public_activity', 'other_public',
                    'other_actor', 'other_start', 'other_end', 'other_process',
                    'not_own_reason', 'moving_classification', 'not_scholar', 'private_audience'):
        actual = evaluate(doc, model(doc, changes, variant), PEOPLE, SCENES, True)[0]
        assert actual == (variant == 'baseline'), (variant, actual)
        rows[variant] = actual
    for name in ('hzmx', 'ca', 'cb', 'cd', 'ce'):
        v = model(doc, changes)
        v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, unknown_inputs_refused=5, native_public_use_classification=True,
                semantic_boundaries=['hzmx supplies checked same-process causal change; public-use composition remains native'])


EPISODES = (('left', 'public'), ('left', 'process'), ('right', 'public'), ('right', 'process'))


def quantified_model(doc, goals, public_parts, variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    def selected(public, reference, branch):
        return variant != 'empty_candidates' and (public, reference) == ('public', 'reference') and branch in ('left', 'right')
    def evidence(public, reference, branch, process, before, after, selected_set):
        return (public, reference, before, after) == ('public', 'reference', 'reference', branch) and (
            branch, process) in selected_set
    v.update(zpublic=lambda: 'public', zreference=lambda: 'reference', zleft=lambda: 'left',
             zright=lambda: 'right', zexpected=lambda: 0, h222k=selected,
             r2wy=lambda public, reference: variant != 'invalid_public' and (public, reference) == ('public', 'reference'),
             r2wz=lambda public, reference, branch: selected(public, reference, branch)
                 and not (variant == 'invalid_failure_candidate' and branch == 'right'),
             r2yj=lambda *args: evidence(*args, goals),
             r2yk=lambda *args: evidence(*args, public_parts))
    return v


@lru_cache(None)
def quantifier_checks():
    doc = fixture('quantified')
    count = 0
    for states in product(range(4), repeat=4):
        goals = {e for e, state in zip(EPISODES, states) if state & 1}
        public_parts = {e for e, state in zip(EPISODES, states) if state & 2}
        actual = evaluate(doc, quantified_model(doc, goals, public_parts), PEOPLE, SCENES, True)[0]
        assert actual == (bool(goals) and goals <= public_parts), (states, actual)
        count += 1
    good = {('left', 'public')}
    rows = {}
    for variant in ('baseline', 'empty_candidates', 'invalid_public', 'invalid_failure_candidate'):
        actual = evaluate(doc, quantified_model(doc, good, good, variant), PEOPLE, SCENES, True)[0]
        assert actual == (variant == 'baseline')
        rows[variant] = actual
    for name in ('h222k', 'r2wy', 'r2wz', 'r2yj', 'r2yk'):
        v = quantified_model(doc, good, good)
        v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(independently_enumerated_goal_and_public_part_combinations=count, contrasts=rows,
                no_success_is_not_possible=True, failure_candidates_allowed=True,
                every_productive_process_in_every_candidate_checked=True, unknown_inputs_refused=5,
                semantic_boundaries=['r2wy/r2wz/r2yj/r2yk isolate the quantification; native composition checked separately'])


@lru_cache(None)
def combined_checks():
    doc = fixture('combined')
    rows = {}
    for label, changes, variant, expected in (
        ('public_success_and_failure', {('left', 'public'): {'one', 'two'}}, 'baseline', True),
        ('private_success_same_candidate', {('left', 'public'): {'one', 'two'},
                                           ('left', 'process'): {'one', 'two'}}, 'baseline', False),
        ('private_success_other_candidate', {('left', 'public'): {'one', 'two'},
                                            ('right', 'process'): {'one', 'two'}}, 'baseline', False),
        ('incidental_public_activity', {('left', 'public'): {'one', 'two'}}, 'incidental_public_activity', False),
    ):
        actual = evaluate(doc, model(doc, changes, variant), PEOPLE, SCENES, True)[0]
        assert actual == expected, (label, actual)
        rows[label] = actual
    return dict(contrasts=rows, native_goal_ratio_period_public_classification_and_quantification=True,
                semantic_boundaries=['hzmx/r2la only, as in episode checks; no supplied success or public-route verdict'])


@lru_cache(None)
def claim_checks():
    doc = fixture('claim')
    rows = {}
    for variant in ('baseline', 'empty_scope', 'second_public_missing', 'wrong_reference'):
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        v.update(zpublic=lambda: 'public', zreference=lambda: 'reference', zleft=lambda: 'left',
                 zright=lambda: 'right', zexpected=lambda: 0, h232v=lambda: 'reference',
                 h222e=lambda public, reference: variant != 'empty_scope' and reference == 'reference'
                     and public in ('public', 'process'),
                 r2yl=lambda public, reference: reference == ('left' if variant == 'wrong_reference' else 'reference')
                     and public in (('public',) if variant == 'second_public_missing' else ('public', 'process')))
        actual = evaluate(doc, v, PEOPLE, SCENES, True)[0]
        assert actual == (variant == 'baseline')
        rows[variant] = actual
    quoted = fixture('attribution')
    attribution = {}
    for variant in ('baseline', 'wrong_content', 'wrong_author', 'wrong_node', 'wrong_context', 'reversed_order'):
        v = {d['name']: unknown for d in quoted['declarations'] if d['kind'] == 'primitive'}
        v.update(zpublic=lambda: 'public', zreference=lambda: 'reference', zleft=lambda: 'left',
                 zright=lambda: 'right', zexpected=lambda: 0,
                 wa=lambda: 'one', h235s=lambda: 'public', h235t=lambda: 'process', h232o=lambda: 'reference',
                 hzon=lambda node, author, code, context: (node, author, symbol(code), code.rank, context) == (
                     'public' if variant == 'wrong_node' else 'process',
                     'two' if variant == 'wrong_author' else 'one',
                     'r2yh' if variant == 'wrong_content' else 'r2ym', 1,
                     'left' if variant == 'wrong_context' else 'reference'),
                 ue=lambda first, second, context: (first, second, context) == (
                     ('process', 'public', 'reference') if variant == 'reversed_order' else ('public', 'process', 'reference')))
        actual = evaluate(quoted, v, PEOPLE, SCENES, True)[0]
        assert actual == (variant == 'baseline')
        attribution[variant] = actual
    return dict(public_scope=rows, attribution=attribution, quoted_claim_not_executed=True,
                semantic_boundaries=['r2yl for all-public wrapper only; attribution keeps all quoted dependencies unknown'])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    text = unit['text'][768:833]
    assert text == ', und der allein kann Aufklärung unter Menschen zu Stande bringen'
    return dict(status='public_enlightenment_route_clause_partial_answer', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[768, 833], text=text),
                definitions=list(MEANINGS), selection=selection_binding(catalog(), [73]),
                interpretation=LIMITS, whole_sentence_semantically_verified=False,
                whole_unit_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_reviewed_sentence_characters=588,
                references=['https://korpora.org/Kant/aa08/037.html'],
                unresolved=['Ich antworteの自己提示', '私的使用の頻度・程度・進行への留保',
                            '回答文全体の対照と原刊照合・通読'],
                source_sha256={p: digest((ROOT / p).read_bytes())
                               for p in (FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:73] == old.document['statements']
    assert len(new.document['statements']) == 74
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in (('data/public-freedom-duty-reading-v1.json', [72]),
                          ('data/question-discourse-reading-v1.json', [70, 71]),
                          ('data/everywhere-restriction-reading-v1.json', [69]),
                          ('data/single-ruler-reading-v1.json', [68]),
                          ('data/role-commands-reading-v1.json', [65, 66, 67]),
                          ('data/heard-prohibition-reading-v1.json', [64])):
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    first = read('data/heard-prohibition-reading-v1.json')['first_sentence_recheck']
    assert first['selection'] == selection_binding(new, [63])
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
    return dict(preserved_statements=73, added_statements=1, preserved_whole_unit_reviews=len(reviews),
                preserved_reviewed_sentence_characters=588, new_reviewed_sentence_characters=0,
                old_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('episode', episode_checks), ('part', part_checks), ('quantifiers', quantifier_checks),
                     ('combined', combined_checks), ('claim', claim_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, 'scripts/compose_public_enlightenment_route.py',
        'scripts/check_public_enlightenment_route.py', 'scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py', 'scripts/check_enlightenment_extent.py',
        'scripts/check_scoped_counts.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'tests/test_public_enlightenment_route.py', 'data/public-freedom-duty-reading-v1.json',
        'data/question-discourse-reading-v1.json', 'data/everywhere-restriction-reading-v1.json',
        'data/single-ruler-reading-v1.json', 'data/role-commands-reading-v1.json',
        'data/heard-prohibition-reading-v1.json'}
    return dict(status='public_enlightenment_route_clause_partial_answer', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[73], definitions=list(MEANINGS),
                               status='partial_public_enlightenment_route'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
