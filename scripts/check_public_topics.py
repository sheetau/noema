"""Check topic coverage without excluding forbidden or unperformed activities."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_topics import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v144.json'
REPORT = 'reports/public-topics-v1.json'
AUDIT = 'data/public-topics-reading-v1.json'
DOC = 'docs/public-topics-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/audience-liberty-v1.json', 'reports/prospective-liberty-v1.json',
         'reports/public-first-sentence-v1.json', 'reports/fourth-paragraph-v1.json']
PEOPLE = ('public', 'first', 'second', 'actone', 'acttwo', 'role', 'topicone', 'topictwo')
SCENES = ('reference', 'initial', 'later', 'outside')
EXTRA = 'r zg[] a.r zr[] d.r zs[] a.r zp[] d.r zbranch[] d.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    roots = ['r2sj', 'hzna', 'r2sk'] if kind == 'point' else ['r2lm', 'r2sl']
    queries = ('q[k r2sj[k zg[] k zr[]]].q[k hzna[k zg[] k zr[] k zs[] k zp[]]].'
               'q[k r2sk[k zg[] k zr[] k zs[] k zp[]]].') if kind == 'point' else (
               'q[t[k r2lm[k zg[] k zr[]]][k zbranch[]]].'
               'q[t[k r2sl[k zg[] k zr[]]][k zbranch[]]].')
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + EXTRA + queries)


def model(doc, variant='baseline', observed=None):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    def readers(public, person, reference):
        if observed is not None:
            observed.append(('scope', reference))
        return (public, reference) == ('public', 'reference') and variant != 'no_readers' and (
            person in ('first', 'second') or variant == 'nonhuman_reader' and person == 'role')
    def classified(person, act, role, reference):
        if observed is not None:
            observed.append(('scope', reference))
        return (person in ('first', 'second') and role == 'role' and reference == 'reference'
                and act in (('actone', 'acttwo', 'public') if variant == 'unmapped_activity' else ('actone', 'acttwo'))
                and not (variant == 'missing_second_topic_activity' and (person, act) == ('second', 'acttwo')))
    def topic(public, reference, subject):
        if observed is not None:
            observed.append(('scope', reference))
        return (public, reference) == ('public', 'reference') and variant != 'no_topics' and subject in ('topicone', 'topictwo')
    def relation(act, subject, reference):
        if observed is not None:
            observed.append(('scope', reference))
        return reference == 'reference' and (act, subject) in (
            (('actone', 'topicone'),) if variant == 'unmapped_second_topic'
            else (('actone', 'topicone'), ('acttwo', 'topictwo')))
    def norm(source, person, role, act, desc, sign, point, allow):
        if observed is not None:
            observed.append(('norm', point))
        matches = (source == ('role' if variant == 'wrong_source' else 'public')
                   and classified(person, act, role, 'reference')
                   and symbol(desc) == ('r2sl' if variant == 'wrong_description' else 'zzq'))
        if not allow:
            return matches and (not sign and variant == 'opposed_requirement'
                                or sign and variant == 'positive_requirement')
        return (matches and (not sign if variant == 'opposite_permission' else sign)
                and point in ('initial', 'later')
                and not (variant == 'second_subject_forbidden' and act == 'acttwo')
                and not (variant == 'later_permission_missing' and point == 'later')
                and not (variant == 'initial_permission_missing' and point == 'initial'))
    v.update(zg=lambda: 'public', zr=lambda: 'reference', zs=lambda: 'public',
             zp=lambda: 'later', zbranch=lambda: 'later',
             h6t=readers, aa=lambda person: person in ('first', 'second'),
             ca=lambda person, act, reference:
                 classified(person, act, 'role', reference) and variant != 'not_own_reason',
             cb=classified,
             cd=lambda role, reference: (role, reference) == ('role', 'reference') and variant != 'not_scholar_role',
             cc=lambda act, audience, reference:
                 act in ('actone', 'acttwo', 'public') and (audience, reference) == ('public', 'reference'),
             ce=lambda audience, reference: (audience, reference) == ('public', 'reference')
                 and variant != 'private_audience',
             h232a=topic, h227z=relation,
             h7a=lambda *args: norm(*args, False), h7b=lambda *args: norm(*args, True),
             h222f=lambda public, reference: 'public',
             h222g=lambda public, reference: 'public',
             h222h=lambda public, reference, candidate: 'initial',
             h7q=lambda frame, branch, point: (frame, branch) == ('public', 'later')
                 and point in ('initial', 'later') and not (variant == 'no_future' and point == 'later'),
             ic=lambda first, last, branch:
                 branch == 'later' and (first, last) == (
                     ('later', 'initial') if variant == 'reversed_time' else ('initial', 'later')))
    return v


@lru_cache(None)
def scope_checks():
    doc = fixture('point')
    rows = {}
    scope_only_fail = {'no_topics', 'unmapped_second_topic', 'missing_second_topic_activity', 'unmapped_activity'}
    both_fail = {'no_readers', 'nonhuman_reader', 'not_own_reason', 'not_scholar_role', 'private_audience'}
    for variant in ('baseline', *sorted(scope_only_fail), *sorted(both_fail)):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline', variant not in both_fail, variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for missing in ('h232a', 'h227z', 'ca'):
        v = model(doc); v[missing] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, every_reader_and_subject_covered=True,
                no_public_activity_silently_excluded=True, native_public_use_classification=True,
                unknown_inputs_refused=3, semantic_boundaries=[])


@lru_cache(None)
def permission_checks():
    doc = fixture('point')
    rows = {}
    for variant in ('baseline', 'second_subject_forbidden', 'opposed_requirement',
                    'opposite_permission', 'wrong_source', 'wrong_description', 'positive_requirement'):
        seen = []
        actual = evaluate(doc, model(doc, variant, seen), PEOPLE, SCENES, True)
        permitted = variant in ('baseline', 'positive_requirement')
        assert actual == [True, permitted, permitted], (variant, actual)
        assert all(point == 'reference' for kind, point in seen if kind == 'scope')
        rows[variant] = actual
    for missing in ('h7a', 'h7b'):
        v = model(doc); v[missing] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, forbidden_subject_not_removed_from_scope=True,
                fixed_reference_for_all_activity_and_topic_classification=True,
                execution_unknown_and_unexecuted=True, native_hzna_and_rdm=True, unknown_inputs_refused=2)


@lru_cache(None)
def period_checks():
    doc = fixture('period')
    rows = {}
    for variant in ('baseline', 'unmapped_second_topic', 'missing_second_topic_activity',
                    'initial_permission_missing', 'later_permission_missing', 'no_future', 'reversed_time'):
        seen = []
        actual = evaluate(doc, model(doc, variant, seen), PEOPLE, SCENES, True)
        old_ok = variant in ('baseline', 'unmapped_second_topic', 'missing_second_topic_activity')
        assert actual == [old_ok, variant == 'baseline'], (variant, actual)
        assert all(point == 'reference' for kind, point in seen if kind == 'scope')
        rows[variant] = actual
    return dict(contrasts=rows, old_permission_and_time_content_preserved=True,
                new_topic_condition_is_stricter_without_rewriting_old_definition=True,
                native_r2lm_hznf_and_hzna=True, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    start = unit['text'].index('von seiner Vernunft')
    return dict(status='all_public_subjects_permission_scope_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[start, 214], text=unit['text'][start:214]),
                interpretation=LIMITS, definitions=list(MEANINGS),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                authored_statements_added=0,
                references=['https://korpora.org/Kant/aa08/036.html',
                            'https://korpora.org/Kant/aa08/037.html'],
                unresolved=['同じ啓蒙への照応', '自由以外の要件を求めない限定', '最も無害な自由の比較',
                            'aber/und zwar/nämlichの提示', '第一文全体の帰属と通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements']
    assert len(new.document['statements']) == 63
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
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
    return dict(preserved_whole_unit_reviews=len(reviews), added_definitions=len(MEANINGS),
                added_basic_relations=len(PRIMITIVES), preserved_statements=63, added_statements=0,
                old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('scope', scope_checks), ('permission', permission_checks),
                     ('period', period_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, 'scripts/compose_public_topics.py',
        'scripts/check_public_topics.py', 'tests/test_public_topics.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='all_public_subjects_permission_scope_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_all_public_subjects_permission'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
