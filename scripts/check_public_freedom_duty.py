"""Verify fixed public scope, all-time policy content and nonfactive duty."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_freedom_duty import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, LIMITS, MEANINGS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v156.json'
REPORT = 'reports/public-freedom-duty-v1.json'
AUDIT = 'data/public-freedom-duty-reading-v1.json'
DOC = 'docs/public-freedom-duty-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ('reports/question-discourse-v1.json', 'reports/public-topics-v1.json',
         'reports/temporal-norms-v1.json', 'reports/policy-norms-v1.json')
PEOPLE = ('public', 'first', 'second', 'actone', 'acttwo', 'role', 'frame')
SCENES = ('reference', 'initial', 'middle', 'last', 'outside')
PERIOD = SCENES[1:4]
EXTRA = 'r zg[] a.r zr[] d.r zs[] a.r zframe[] a.r zbranch[] d.r zperson[] a.r zrole[] a.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind, bindings=('public', 'source', 'frame')):
    doc = deepcopy(catalog().document)
    roots = {'period': ['r2ye', 'h7w'], 'adapter': ['r2yf'],
             'native_adapter': ['r2ye', 'r2yf'], 'norm': ['r2yh'], 'attribution': ['r2yi']}[kind]
    if kind == 'adapter':
        for d in doc['declarations']:
            if d['name'] == 'r2ye':
                d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
                d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    if kind == 'period':
        queries = ('q[t[k r2ye[k zg[] k zr[] k zs[] k zframe[]]][k zbranch[]]].'
                   'q[k h7w[k zs[] k zperson[] k zrole[] k zframe[] k zbranch[]]].')
    elif kind in ('adapter', 'native_adapter'):
        names = dict(public='zg', source='zs', frame='zframe')
        params = ' '.join('k ' + names[n] + '[]' for n in bindings)
        queries = 'q[t[k r2yf[l[a][' + params + ']]][k zbranch[]]].'
        if kind == 'native_adapter':
            queries += 'q[t[k r2ye[k zg[] k zr[] k zs[] k zframe[]]][k zbranch[]]].'
    elif kind == 'norm':
        queries = 'q[t[k r2yh[]][k zbranch[]]].'
    else:
        queries = 'q[k r2yi[]].'
    return parse(format_graph(doc, 'compact') + EXTRA + queries)


def period_model(doc, flags=(True, True, True), variant='baseline', seen=None, small=False):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    people, acts = (('public',), ('public',)) if small else (('first', 'second'), ('actone', 'acttwo'))

    def readers(public, person, reference):
        if seen is not None:
            seen.append(('readers', reference))
        return (public, reference) == ('public', 'reference') and person in people and variant != 'empty_readers'

    def classified(person, act, role, reference):
        if seen is not None:
            seen.append(('activity', reference))
        return (person in people and act in acts and role == 'role' and reference == 'reference'
                and variant != 'no_activities')

    def norm(source, person, role, act, code, sign, point, permit):
        matches = (source == ('frame' if variant == 'wrong_inner_source' else 'public')
                   and person in people and act in acts and role == 'role'
                   and symbol(code) == ('r2yf' if variant == 'wrong_action_code' else 'zzq'))
        if not permit:
            return matches and (not sign and variant == 'opposing_requirement' or sign and variant == 'positive_requirement')
        return (matches and sign and point in PERIOD and flags[PERIOD.index(point)]
                and not (variant == 'second_person_missing' and person == 'second')
                and not (variant == 'second_activity_missing' and act == 'acttwo'))

    def history(frame, candidate, point):
        return frame == 'frame' and point in PERIOD and variant != 'empty_history'

    def scope(frame, candidate, point):
        return frame == 'frame' and variant != 'empty_period' and point in (
            SCENES[1:] if variant == 'outside_history' else
            ('initial', 'last') if variant == 'period_gap' else
            ('initial',) if variant == 'narrowed_period' else PERIOD)

    v.update(zg=lambda: 'public', zr=lambda: 'reference', zs=lambda: 'public',
             zframe=lambda: 'frame', zbranch=lambda: 'last',
             zperson=lambda: people[0], zrole=lambda: 'role', h232v=lambda: 'reference',
             h6t=readers, aa=lambda person: person in people,
             ca=lambda person, act, reference: classified(person, act, 'role', reference),
             cb=classified, cd=lambda role, reference: (role, reference) == ('role', 'reference'),
             cc=lambda act, audience, reference: act in acts and (audience, reference) == ('public', 'reference'),
             ce=lambda audience, reference: (audience, reference) == ('public', 'reference'),
             h7a=lambda *args: norm(*args, False), h7b=lambda *args: norm(*args, True),
             h7q=history, h7r=scope,
             ic=lambda first, last, candidate: SCENES.index(first) < SCENES.index(last)
                 or variant == 'cyclic_order' and (first, last) == ('last', 'initial'))
    return v


@lru_cache(None)
def period_checks():
    doc = fixture('period')
    rows = []
    for flags in product((False, True), repeat=3):
        actual = evaluate(doc, period_model(doc, flags), PEOPLE, SCENES, True)
        # The legacy target reclassifies activities at each point; this model has
        # activities only at the reference, so the old universal is vacuous.
        assert actual == [all(flags), True], (flags, actual)
        rows.append(dict(point_permissions=list(flags), fixed_scope=actual[0], legacy_moving_scope=actual[1]))
    contrasts = {}
    for variant in ('baseline', 'empty_readers', 'no_activities', 'wrong_inner_source',
                    'wrong_action_code', 'opposing_requirement', 'positive_requirement',
                    'second_person_missing', 'second_activity_missing', 'empty_history',
                    'empty_period', 'outside_history', 'period_gap', 'cyclic_order'):
        seen = []
        actual = evaluate(doc, period_model(doc, variant=variant, seen=seen), PEOPLE, SCENES, True)[0]
        assert actual == (variant in ('baseline', 'positive_requirement')), (variant, actual)
        contrasts[variant] = actual
    # Use only the new target to ensure that all classification calls stay at
    # the reference. The legacy query deliberately uses the evaluation points.
    new = deepcopy(doc)
    new['statements'] = new['statements'][:1]
    seen = []
    assert evaluate(new, period_model(new, seen=seen), PEOPLE, SCENES, True) == [True]
    assert all(point == 'reference' for _, point in seen)
    assert evaluate(new, period_model(new, (True, False, False), 'narrowed_period'),
                    PEOPLE, SCENES, True) == [True]
    for name in ('h7a', 'h7b', 'cb', 'h7q', 'h7r', 'ic'):
        v = period_model(new)
        v[name] = unknown
        try:
            evaluate(new, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(permission_combinations=rows, contrasts=contrasts, classification_fixed_to_reference=True,
                middle_permission_required=True, execution_not_evaluated=True, unknown_inputs_refused=6,
                narrowed_input_can_pass_but_does_not_establish_complete_source_scope=True,
                semantic_boundaries=[])


@lru_cache(None)
def adapter_checks():
    rows = {}
    for bindings in (('public', 'source', 'frame'), ('source', 'public', 'frame'),
                     ('public', 'frame', 'source'), (), ('public', 'source'),
                     ('public', 'source', 'frame', 'public')):
        doc = fixture('adapter', bindings)
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        v.update(zg=lambda: 'public', zs=lambda: 'source', zframe=lambda: 'frame',
                 zr=lambda: 'reference', zbranch=lambda: 'last', zperson=lambda: 'public',
                 zrole=lambda: 'frame', h232v=lambda: 'reference',
                 r2ye=lambda public, reference, source, frame:
                     Content(SCENES, tuple((public, reference, source, frame) ==
                             ('public', 'reference', 'source', 'frame') for _ in SCENES)))
        actual = evaluate(doc, v, ('public', 'source', 'frame'), SCENES, True)[0]
        assert actual == (bindings == ('public', 'source', 'frame')), (bindings, actual)
        rows[','.join(bindings)] = actual
    # Evaluate the adapter with its real period and permission body as well.
    native = fixture('native_adapter')
    native_rows = []
    for flags in ((True, True, True), (True, False, True)):
        actual = evaluate(native, period_model(native, flags, small=True),
                          ('public', 'role', 'frame'), SCENES, True)
        assert actual == [all(flags), all(flags)]
        native_rows.append(dict(point_permissions=list(flags), adapter_and_direct=actual))
    return dict(bindings=rows, native_adapter=native_rows,
                semantic_boundaries=['binding permutation checks replace r2ye with a typed content; native adapter separately evaluates r2ye/hzna/zzo/tb/tc'])


NORM_PEOPLE = ('public', 'otherpublic', 'source', 'othersource', 'role', 'frame', 'author')


def norm_model(doc, variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    def source(public, reference):
        return 'source' if public == 'public' else 'othersource'
    def required(author, regulator, office, code, bindings, sign, evaluation):
        if len(bindings.items) != 3:
            return False
        public, inner, frame = bindings.items
        expected_source = source(public, 'reference')
        return (variant != 'missing_requirement'
                and not (variant == 'second_public_missing' and public == 'otherpublic')
                and (author, regulator, office, symbol(code), code.rank, inner, frame, sign, evaluation) == (
                    'source' if variant == 'wrong_author' else 'author',
                    'frame' if variant == 'wrong_addressee' else expected_source,
                    'frame' if variant == 'wrong_office' else 'role',
                    'h7i' if variant == 'wrong_policy_code' else 'r2yf', 0,
                    'frame' if variant == 'wrong_policy_source' else expected_source,
                    'role' if variant == 'wrong_period_frame' else 'frame',
                    variant != 'wrong_polarity', 'reference' if variant == 'wrong_evaluation' else 'last')
                and public in ('public', 'otherpublic'))
    v.update(zg=lambda: 'public', zr=lambda: 'reference', zs=lambda: 'source',
             zframe=lambda: 'frame', zbranch=lambda: 'last', zperson=lambda: 'public', zrole=lambda: 'role',
             wa=lambda: 'author', h232v=lambda: 'reference',
             h222e=lambda public, reference: reference == 'reference' and variant != 'empty_public_scope'
                 and public in ('public', 'otherpublic'),
             h222f=source, h235q=lambda public, reference: 'frame',
             h235r=lambda source, reference: 'role', h7k=required)
    return v


@lru_cache(None)
def norm_checks():
    doc = fixture('norm')
    rows = {}
    for variant in ('baseline', 'missing_requirement', 'second_public_missing', 'wrong_author',
                    'wrong_addressee', 'wrong_office', 'wrong_policy_code', 'wrong_policy_source',
                    'wrong_period_frame', 'wrong_polarity', 'wrong_evaluation', 'empty_public_scope'):
        actual = evaluate(doc, norm_model(doc, variant), NORM_PEOPLE, SCENES, True)[0]
        assert actual == (variant == 'baseline'), (variant, actual)
        rows[variant] = actual
    for name in ('h7k', 'h222e', 'h235q', 'h235r'):
        v = norm_model(doc)
        v[name] = unknown
        try:
            evaluate(doc, v, NORM_PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, actual_permissions_and_temporal_target_unknown_and_unexecuted=True,
                all_public_groups_required=True, unknown_inputs_refused=4, semantic_boundaries=[])


@lru_cache(None)
def attribution_checks():
    doc = fixture('attribution')
    rows = {}
    for variant in ('baseline', 'wrong_node', 'wrong_author', 'wrong_content', 'wrong_context'):
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        v.update(zg=lambda: 'public', zr=lambda: 'reference', zs=lambda: 'source',
                 zframe=lambda: 'frame', zbranch=lambda: 'last', zperson=lambda: 'public', zrole=lambda: 'role',
                 wa=lambda: 'author', h235s=lambda: 'public', h232o=lambda: 'outside',
                 hzon=lambda node, author, code, context: (node, author, symbol(code), code.rank, context) == (
                     'frame' if variant == 'wrong_node' else 'public',
                     'source' if variant == 'wrong_author' else 'author',
                     'r2yf' if variant == 'wrong_content' else 'r2yh', 1,
                     'last' if variant == 'wrong_context' else 'outside'))
        actual = evaluate(doc, v, NORM_PEOPLE, SCENES, True)[0]
        assert actual == (variant == 'baseline')
        rows[variant] = actual
    return dict(contrasts=rows, normative_claim_not_executed=True, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    text = unit['text'][704:768]
    assert text == 'der öffentliche Gebrauch seiner Vernunft muß jederzeit frei sein'
    return dict(status='public_freedom_duty_clause_partial_answer', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[704, 768], text=text),
                definitions=list(MEANINGS), selection=selection_binding(catalog(), [72]),
                interpretation=LIMITS, whole_sentence_semantically_verified=False,
                whole_unit_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_reviewed_sentence_characters=588,
                references=['https://korpora.org/Kant/aa08/037.html'],
                unresolved=['Ich antworteの自己提示', 'der allein kannの排他性・可能性と同じ啓蒙の実現',
                            '私的使用への許可、制限の頻度・程度', '進行を特に妨げないという留保と対照',
                            '回答文全体の原刊照合と通読'],
                source_sha256={p: digest((ROOT / p).read_bytes())
                               for p in (FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:72] == old.document['statements']
    assert len(new.document['statements']) == 73
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in (('data/question-discourse-reading-v1.json', [70, 71]),
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
    return dict(preserved_statements=72, added_statements=1, preserved_whole_unit_reviews=len(reviews),
                preserved_reviewed_sentence_characters=588, new_reviewed_sentence_characters=0,
                old_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('period', period_checks), ('adapter', adapter_checks), ('norm', norm_checks),
                     ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, 'scripts/compose_public_freedom_duty.py',
        'scripts/check_public_freedom_duty.py', 'scripts/compose_grounded_step.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'tests/test_public_freedom_duty.py', 'data/question-discourse-reading-v1.json',
        'data/everywhere-restriction-reading-v1.json', 'data/single-ruler-reading-v1.json',
        'data/role-commands-reading-v1.json', 'data/heard-prohibition-reading-v1.json'}
    return dict(status='public_freedom_duty_clause_partial_answer', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[72], definitions=list(MEANINGS),
                               status='partial_public_freedom_duty'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
