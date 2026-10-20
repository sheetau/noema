"""Test revolutionary attempts and same-candidate causal-result binding."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_revolution_routes import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure)
from scripts import check_political_withdrawal as withdrawal
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic

INDEX = 'data/semantic-review-index-v137.json'
AUDIT = 'data/revolution-routes-reading-v1.json'
REPORT = 'reports/revolution-routes-v1.json'
DOC = 'docs/revolution-routes-v1.md'
INVENTORY = withdrawal.INVENTORY
PRIOR = 'reports/political-withdrawal-v1.json'
EXTRA = withdrawal.EXTRA + '''
r zcommunity[] a.r zevent[] a.r zold[a d] a.r zproposed[a d] a.r zactors[a d] j[a].
'''
PEOPLE = withdrawal.PEOPLE + ('community', 'replacement')
SCENES = withdrawal.SCENES


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, extra, question):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra + question)


def model(doc, variant='baseline'):
    values = withdrawal.model(doc, variant)
    values.update(arithmetic())
    previous_aim, previous_df = values['hztl'], values['df']
    previous_aa = values['aa']
    actors = () if variant == 'empty_actors' else ('target', 'other')
    def political_status(order, community, point):
        if order == 'replacement':
            raise ValueError('Unknown implementation of the proposed order: not required by an attempt')
        return (order, community) == ('despotic', 'community') and variant != 'old_not_in_force'
    def purpose(actor, act, goal, roles, point):
        if actor != 'community':
            return previous_aim(actor, act, goal, roles, point)
        return ((act, point) == ('event', 'after') and symbol(goal) == 'r2qf' and
                roles.items == ('despotic', 'replacement', 'community') and
                variant not in ('no_collective_goal', 'wrong_goal_order'))
    values.update(
        zcommunity=lambda: 'community', zevent=lambda: 'event',
        zold=lambda act, point: 'despotic',
        zproposed=lambda act, point: 'despotic' if variant == 'same_order' else 'replacement',
        zactors=lambda act, point: seq(actors),
        aa=lambda person: previous_aa(person) or person == 'other',
        mp=lambda community: seq(('target', 'other', 'ruler')) if community == 'community' else seq(()),
        df=lambda person, act, point: previous_df(person, act, point) or
            (act, point) == ('event', 'after') and person in actors and
            not (variant == 'missing_participant' and person == 'other'),
        h223o=lambda community, act, participants, point:
            (community, act, participants.items, point) == ('community', 'event', actors, 'after') and
            variant != 'not_collective',
        h226q=lambda order, community, point: community == 'community' and order in ('despotic', 'replacement')
            and not (variant == 'nonpolitical_proposal' and order == 'replacement'),
        h226r=lambda old, proposed, community, point:
            (old, proposed, community) == ('despotic', 'replacement', 'community') and variant != 'minor_adjustment',
        h226s=lambda act, old, community, point:
            (act, old, community, point) == ('event', 'despotic', 'community', 'after') and
            variant not in ('regular_succession', 'proposal_only'),
        h226t=political_status, hztl=purpose,
    )
    return values


@lru_cache(None)
def attempt_checks():
    doc = fixture(['r2qg'], EXTRA,
                  'q[k r2qg[k zevent[] k zcommunity[] k zold[k zevent[] k zlast[]]'
                  ' k zproposed[k zevent[] k zlast[]] k zactors[k zevent[] k zlast[]] k zlast[]]].')
    rows = {}
    for variant in ('baseline', 'same_order', 'nonpolitical_proposal', 'minor_adjustment',
                    'regular_succession', 'proposal_only', 'old_not_in_force', 'empty_actors',
                    'missing_participant', 'not_collective', 'no_collective_goal', 'wrong_goal_order'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for name in ('h226r', 'h226s', 'hztl'):
        values = model(doc); values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, proposed_order_implementation_unknown_without_execution=True,
                native_collective_membership_and_participation=True, unknown_inputs_refused=3,
                no_required_bloodshed_or_unanimity=True)


@lru_cache(None)
def withdrawal_route_checks():
    doc = fixture(['r2qj', 'r2qe'], EXTRA + withdrawal.RESULT,
                  'q[k r2qj[k ztarget[] k zcommunity[] k zfirst[] p zold p zproposed p zactors'
                  ' r[p zresult] p zcandidate]].')
    rows = {}
    for variant in ('baseline', 'minor_adjustment', 'proposal_only', 'no_collective_goal',
                    'no_result_cause', 'wrong_candidate', 'no_event_occurrence', 'still_oppression',
                    'no_severing', 'declassification_only'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_revolution_and_withdrawal_connected=True,
                same_event_candidate_target_and_result=True,
                success_of_the_political_goal_not_a_prerequisite=True)


@lru_cache(None)
def modal_checks():
    extra = '''
r ztarget[] a.r zreference[] d.r zclass[a] c.r zkind[a d] c.r zcases[a d d] c.
r za[a d] c.r zb[a d] c.
d zfirst[target a] e[b point[k za[v target v point]]].
d zsecond[target a] e[b point[k zb[v target v point]]].
'''
    questions = '''
q[k r2qi[k ztarget[] p zkind r[p zfirst] r[p zsecond] k zreference[] p zcases]].
q[k rqe[k ztarget[] p zclass r[p zfirst] r[p zsecond] k zreference[] p zcases p dg p g3]].
'''
    doc = fixture(['r2qi', 'rqe', 'dg', 'g3'], extra, questions)
    people, scenes = ('target', 'event', 'other'), ('reference', 'first', 'second')
    def values(variant):
        kind = {'event'} if variant == 'other_kind_can_reform' else {'event', 'other'}
        def case_kind(act, point):
            if variant == 'classification_in_other_candidate':
                return act == 'event' and point == 'second'
            return act in kind
        def caused(act, target, desc, point):
            if target != 'target':
                return False
            if symbol(desc) == 'zfirst':
                return (act, point) == ('event', 'first') and variant != 'no_first_result'
            return symbol(desc) == 'zsecond' and (act, point) == ('other', 'second') and \
                variant in ('another_activity_can_reform', 'other_kind_can_reform')
        return dict(ztarget=lambda: 'target', zreference=lambda: 'reference',
                    zclass=lambda act: act in kind, zkind=case_kind,
                    zcases=lambda act, reference, point: act in ('event', 'other') and
                        reference == 'reference' and point in ('first', 'second') and variant != 'empty_candidates',
                    dg=lambda act, point: act in ('event', 'other') and
                        not (variant == 'occurrence_in_other_candidate' and point == 'first'),
                    g3=caused, za=lambda target, point: (target, point) == ('target', 'first') and
                        variant != 'first_not_true',
                    zb=lambda target, point: (target, point) == ('target', 'second'))
    rows = {}
    for variant in ('baseline', 'another_activity_can_reform', 'other_kind_can_reform',
                    'classification_in_other_candidate', 'occurrence_in_other_candidate',
                    'no_first_result', 'first_not_true', 'empty_candidates'):
        actual = evaluate(doc, values(variant), people, scenes, True)
        wanted = [variant in ('baseline', 'other_kind_can_reform')] * 2
        if variant == 'classification_in_other_candidate':
            wanted = [False, True]
        assert actual == wanted, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, second_result_checks_all_same_kind_activities=True,
                old_rqe_agrees_for_candidate_independent_kind=True,
                category_cannot_be_borrowed_from_another_candidate=True,
                reform_is_only_a_test_content_not_yet_source_interpretation=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='revolution_attempt_routes_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[907, 928], text=unit['text'][907:928]),
                interpretation=LIMITS, definitions=list(MEANINGS),
                lexical=dict(url='https://www.duden.de/rechtschreibung/Revolution', sense=1,
                             use='政治秩序の根本的な変更への対抗。失敗する試みも含む語義の補助。成功・流血は必須にしない。'),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_four_sentence_characters=771,
                unresolved=['公衆の全対象範囲と候補供給', '真の思考様式の改革の内容',
                            '様相・対比・著者帰属', '新旧の偏見と誘導の描写', '文と段落の通読'],
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
    for name, fn in [('attempts', attempt_checks), ('withdrawal', withdrawal_route_checks),
                     ('modality', modal_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in withdrawal.REVIEWS],
        'scripts/compose_revolution_routes.py', 'scripts/check_revolution_routes.py',
        'tests/test_revolution_routes.py', 'scripts/check_political_withdrawal.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py'}
    return dict(status='revolution_attempt_routes_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_revolution_kind_and_causal_result_routes'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
