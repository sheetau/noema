"""Check actual unexamined use, plural coverage, novelty, and unchanged evidence."""
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
from scripts.compose_prejudice_guidance import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic
from scripts import check_political_withdrawal as withdrawal

INDEX = 'data/semantic-review-index-v140.json'
REPORT = 'reports/prejudice-guidance-v1.json'
AUDIT = 'data/prejudice-guidance-reading-v1.json'
DOC = 'docs/prejudice-guidance-v1.md'
INVENTORY = withdrawal.INVENTORY
PRIOR = ['reports/prejudice-effects-v1.json', 'reports/public-revolution-v1.json',
         'reports/guardian-forecast-v1.json']


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, declarations, questions, boundaries=(), replacement=None):
    doc = deepcopy(catalog().document)
    extra = parse('p:' + declarations)['declarations']
    for i, d in enumerate(doc['declarations']):
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
        if replacement and d['name'] == replacement['name']:
            doc['declarations'][i] = replacement
    doc['declarations'] = extra + doc['declarations']
    doc.update(declarations=closure(doc, roots + [d['name'] for d in extra]), statements=[])
    return parse(format_graph(doc, 'compact') + questions)


def base(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


LOCAL = 'r zp[] a.r zo[] a.r zj[] a.r zd[] a.r zs[] d.r zclaim[a] e.'
LOCAL_PEOPLE = ('person', 'other', 'opinion', 'otheropinion', 'adopted', 'decision', 'review', 'topic')
LOCAL_SCENES = ('point',)


def local_values(doc, variant='baseline'):
    v = base(doc)
    def judged(person, judgment, point):
        if judgment == 'review':
            return person == ('other' if variant == 'other_reviewer' else 'person') and variant in (
                'reviewed_application', 'other_reviewer', 'other_application_review')
        if judgment == 'adopted':
            return person == ('other' if variant == 'other_adopter' else 'person')
        return person == 'person' and judgment == 'decision'
    v.update(zp=lambda: 'person', zo=lambda: 'opinion', zj=lambda: 'adopted',
             zd=lambda: 'decision', zs=lambda: 'point',
             aa=lambda person: person in ('person', 'other'), fa=judged,
             h224z=lambda opinion: 'topic',
             fb=lambda judgment, topic, point: (judgment, topic) == ('adopted', 'topic'),
             hznn=lambda judgment, topic, claim, positive, point:
                 (judgment, topic, symbol(claim), positive) == ('adopted', 'topic', 'zclaim', True)
                 and variant != 'not_affirmed',
             h224w=lambda judgment, point: judgment == 'adopted' and variant != 'provisional',
             h224x=lambda person, topic, claim, point: variant == 'examined_grounds',
             dg=lambda decision, point: decision == 'decision' and variant != 'no_occurrence',
             fc=lambda decision, reason, point: variant != 'not_used' and
                 (decision, reason) == ('decision', 'review' if variant == 'other_reason' else 'adopted'),
             h227i=lambda review, opinion, decision, point:
                 (review, opinion, decision) == ('review',
                    'otheropinion' if variant == 'other_application_review' else 'opinion', 'decision'))
    return v


@lru_cache(None)
def guidance_checks():
    replacement = parse('p:' + LOCAL + 'd h224y[opinion a] i[h[a] e][r[p zclaim]].')['declarations'][-1]
    doc = fixture(['r2rb', 'r2nz', 'r2rc', 'r2re'], LOCAL, '''
q[k r2rb[k zp[] k zo[] k zj[] k zs[]]].
q[t[c[k r2nz[k zo[]]][k zp[]]][k zs[]]].
q[k r2rc[k zp[] k zo[] k zd[] k zs[]]].
q[t[c[k r2re[k zo[]]][k zp[]]][k zs[]]].
''', replacement=replacement)
    rows = {}
    basic_failures = {'other_adopter', 'not_affirmed', 'provisional'}
    accepted_guidance = {'baseline', 'other_reviewer', 'other_application_review'}
    for variant in ('baseline', 'other_adopter', 'not_affirmed', 'provisional', 'examined_grounds',
                    'no_occurrence', 'not_used', 'other_reason', 'reviewed_application',
                    'other_reviewer', 'other_application_review'):
        actual = evaluate(doc, local_values(doc, variant), LOCAL_PEOPLE, LOCAL_SCENES, True)
        prejudice = variant not in basic_failures | {'examined_grounds'}
        expected = [prejudice, prejudice, variant in accepted_guidance, variant not in basic_failures]
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    for missing in ('h224x', 'h227i', 'fc'):
        v = local_values(doc); v[missing] = unknown
        try:
            evaluate(doc, v, LOCAL_PEOPLE, LOCAL_SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, old_prejudice_definition_preserved=True,
                native_same_person_adoption_reason_use_and_no_application_review=True,
                examined_prior_adoption_still_counts_as_existing=True,
                unknown_inputs_refused=3, opinion_truth_not_executed=True)


COLLECTIVE = '''
r zg[] a.r zr[] d.r zold[] j[a].r znew[] j[a].r zearly[] d.r zlate[] d.
r zhistory[d] c.r zbefore[d d] c.
'''
PEOPLE = ('public', 'group', 'othergroup', 'one', 'two', 'three', 'outside',
          'oldone', 'oldtwo', 'newone', 'newtwo')
SCENES = ('earlier', 'later')


def collective_values(doc, variant='baseline'):
    v = base(doc)
    def guidance(opinion, person, point):
        old = {'oldone': 'one', 'oldtwo': 'two'}
        new = {'newone': 'one', 'newtwo': 'two'}
        if point == 'earlier':
            return person == old.get(opinion) and variant != 'no_old_guidance'
        if variant == 'old_also_persists' and person == old.get(opinion):
            return True
        if variant == 'one_unused_new' and opinion == 'newtwo':
            return False
        if variant == 'one_unused_new' and opinion == 'newone':
            return person in ('one', 'two')
        if variant == 'outsider_only' and opinion == 'newtwo':
            return person == 'outside'
        return person == new.get(opinion) and variant != 'no_new_guidance'
    def adoption(opinion, person, point):
        if point == 'earlier' and opinion in ('newone', 'newtwo'):
            return person in (
                ('one', 'two') if variant == 'already_widespread' else
                ('one',) if variant == 'few_prior_adopters' else ())
        return guidance(opinion, person, point)
    family = lambda predicate: lambda opinion: FunctionValue(('individual',), 'content',
        lambda person: Content(SCENES, tuple(predicate(opinion, person, point) for point in SCENES)))
    v.update(arithmetic(), pa=lambda a, b: a / b if b else Fraction(0),
             zg=lambda: 'public', zr=lambda: 'earlier', zearly=lambda: 'earlier', zlate=lambda: 'later',
             zold=lambda: seq(('oldone', 'oldtwo')),
             znew=lambda: seq(('newone',) if variant == 'singular_new' else
                 ('newone', 'newone') if variant == 'duplicate_new' else
                 ('oldone', 'newtwo') if variant == 'same_opinion' else ('newone', 'newtwo')),
             zhistory=lambda point: point in SCENES and variant != 'missing_history',
             zbefore=lambda first, last: (first, last) == (
                 ('later', 'earlier') if variant == 'reversed' else ('earlier', 'later')),
             h223i=lambda public, reference: 'othergroup' if variant == 'other_group' else 'group',
             h223j=lambda public, reference: Fraction(3 if variant == 'not_large' else 2),
             mp=lambda group: seq(('one', 'two', 'three')) if group == 'group' else seq(()),
             aa=lambda person: person in ('one', 'two', 'three', 'outside'),
             h227k=lambda group, reference: Fraction(2, 3) if variant == 'threshold_equal' else Fraction(1, 2),
             h227j=lambda old, new: (old, new) != ('oldone', 'newone') if variant == 'renamed_only' else True,
             r2rd=family(guidance), r2re=family(adoption))
    return v


@lru_cache(None)
def collective_checks():
    doc = fixture(['r2rk'], COLLECTIVE,
                  'q[k r2rk[k zg[] k zr[] k zold[] k znew[] k zearly[] k zlate[] p zhistory p zbefore]].',
                  ('r2rd', 'r2re'))
    rows = {}
    accepted = {'baseline', 'few_prior_adopters', 'old_also_persists'}
    for variant in ('baseline', 'few_prior_adopters', 'old_also_persists', 'already_widespread',
                    'no_old_guidance', 'no_new_guidance', 'one_unused_new', 'singular_new',
                    'duplicate_new', 'same_opinion', 'renamed_only', 'threshold_equal',
                    'outsider_only', 'other_group', 'not_large', 'missing_history', 'reversed'):
        actual = evaluate(doc, collective_values(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant in accepted], (variant, actual)
        rows[variant] = actual
    for missing in ('h227j', 'h227k', 'r2rd', 'r2re'):
        v = collective_values(doc); v[missing] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, plural_real_use_and_same_mass_scope=True,
                old_persistence_and_few_prior_adopters_allowed=True,
                names_alone_do_not_establish_novelty=True, boundaries=['r2rd', 'r2re'],
                native_guidance_tested_separately=True, unknown_inputs_refused=4)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='prejudice_guidance_target_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[1102, 1216], text=unit['text'][1102:1216]),
                interpretation=LIMITS, definitions=list(MEANINGS),
                lexical=dict(url='https://www.duden.de/rechtschreibung/gedankenlos', sense=1),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_four_sentence_characters=771,
                unresolved=['新旧の意見群・時点の供給と未来予測', 'Leitbandの身体的描写と対応',
                            '呼称の語調', '前半の様相・対比', '第五文と段落の通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 62
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
                unchanged_statements=62, old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('guidance', guidance_checks), ('collective', collective_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, *[p for p, _ in withdrawal.REVIEWS],
        'scripts/compose_prejudice_guidance.py', 'scripts/check_prejudice_guidance.py',
        'tests/test_prejudice_guidance.py', 'scripts/check_political_withdrawal.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_scoped_counts.py', 'scripts/check_public_comparison_claim.py'}
    return dict(status='prejudice_guidance_target_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_prejudice_guidance_target'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
