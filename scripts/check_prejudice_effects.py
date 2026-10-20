"""Verify native judgment, communication and temporally fixed causal effects."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_prejudice_effects import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_reversal_focus as previous

INDEX = 'data/semantic-review-index-v131.json'
AUDIT = 'data/prejudice-effects-reading-v1.json'
REPORT = 'reports/prejudice-effects-v1.json'
DOC = 'docs/prejudice-effects-v1.md'
INVENTORY, PRIOR = previous.INVENTORY, previous.REPORT
PEOPLE = ('planter', 'act', 'recipient', 'opinion', 'target', 'judgment', 'topic', 'other')
SCENES = ('earlier', 'later')
EXTRA = '''
r zplanter[] a.r zact[] a.r zrecipient[] a.r zopinion[] a.r ztarget[] a.
r zname[] a.r zearly[] d.r zlate[] d.r zhistory[d] c.r zbefore[d d] c.
r zclaim[a] e.r zrole[] a.
'''


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(include_return=False):
    doc = deepcopy(catalog().document)
    extras = parse('p:' + EXTRA)['declarations']
    replacement = parse('p:' + EXTRA + 'd h224y[opinion a] i[h[a] e][r[p zclaim]].')['declarations'][-1]
    doc['declarations'] = extras + [
        replacement if d['name'] == 'h224y' else d for d in doc['declarations']]
    doc.update(declarations=closure(doc, ['r2og' if include_return else 'r2oe',
                                         'zplanter', 'zact', 'zrecipient', 'zopinion', 'ztarget',
                                         'zname', 'zearly', 'zlate', 'zhistory', 'zbefore', 'zrole']),
               statements=[])
    return parse(format_graph(doc, 'compact') + '''
q[t[c[k r2nz[k zopinion[]]][k zrecipient[]]][k zearly[]]].
q[k r2ob[k zplanter[] k zact[] k zrecipient[] k zopinion[] r[k zname[]] k zearly[]]].
q[k r2oe[k zplanter[] k zact[] k zrecipient[] k zopinion[] r[k zname[]]
 k zearly[] r[k zearly[]] k zlate[] k ztarget[] p zhistory p zbefore]].
q[t[c[k r2nz[k zopinion[]]][k zrecipient[]]][k zlate[]]].
''' + ('''
q[k r2og[k zplanter[] k zact[] k zrecipient[] k zopinion[] r[k zname[]]
 k zearly[] r[k zearly[]] k zlate[] k ztarget[] k zrole[] p zhistory p zbefore]].
''' if include_return else ''))


def application(desc, function, arguments):
    return json.loads(desc.syntax) == dict(kind='apply',
        function=dict(kind='function_ref', symbol=function),
        arguments=[dict(kind='call', symbol=n, arguments=[]) for n in arguments])


def assertion(desc):
    return json.loads(desc.syntax) == dict(kind='apply',
        function=dict(kind='function_ref', symbol='r2oa'),
        arguments=[dict(kind='function_ref', symbol='zclaim')])


def model(variant='baseline'):
    values = {d['name']: unknown for d in fixture()['declarations'] if d['kind'] == 'primitive'}
    values.update(
        zplanter=lambda: 'planter', zact=lambda: 'act', zrecipient=lambda: 'recipient',
        zopinion=lambda: 'opinion', ztarget=lambda: 'target',
        zrole=lambda: 'other',
        zname=lambda: 'other' if variant == 'wrong_closed_opinion' else 'opinion',
        zearly=lambda: 'earlier', zlate=lambda: 'later',
        zhistory=lambda point: point in SCENES and not (variant == 'missing_later' and point == 'later'),
        zbefore=lambda first, last: (first, last) ==
            (('later', 'earlier') if variant == 'reversed_time' else ('earlier', 'later')),
        aa=lambda person: person in ('planter', 'recipient', 'target') and
            not (variant == 'not_person' and person == 'recipient'),
        h224z=lambda opinion: 'topic',
        fa=lambda person, judgment, point: (person, judgment, point) ==
            ('other' if variant == 'other_judge' else 'recipient', 'judgment', 'earlier'),
        fb=lambda judgment, topic, point: (judgment, topic, point) ==
            ('judgment', 'other' if variant == 'other_topic' else 'topic', 'earlier'),
        hznn=lambda judgment, topic, claim, positive, point:
            (judgment, topic, symbol(claim), positive, point) ==
            ('judgment', 'topic', 'zclaim', variant != 'not_affirmed', 'earlier'),
        h224w=lambda judgment, point: (judgment, point) == ('judgment', 'earlier') and variant != 'provisional',
        h224x=lambda person, topic, claim, point:
            (person, topic, symbol(claim), point) == ('recipient', 'topic', 'zclaim', 'earlier')
            and variant == 'examined',
        dg=lambda act, point: (act, point) == ('act', 'earlier') and variant != 'no_occurrence',
        df=lambda person, act, point: (person, act, point) == ('planter', 'act', 'earlier')
            and variant != 'no_participation',
        f3=lambda person, act, point: (person, act, point) == ('planter', 'act', 'earlier')
            and variant != 'not_presenter',
        f2=lambda act, recipient, topic, message, point:
            (act, recipient, topic, point) == ('act', 'recipient', 'topic', 'earlier') and
            assertion(message) and variant != 'no_presentation',
        h6e=lambda act, recipient, topic, message, point:
            (act, recipient, topic, point) == ('act', 'recipient', 'topic', 'earlier') and
            assertion(message) and variant != 'not_received',
        h6g=lambda recipient, topic, message, point:
            (recipient, topic, point) == ('recipient', 'topic', 'earlier') and
            assertion(message) and variant != 'not_understood',
        g3=lambda act, recipient, state, point:
            (act, recipient, point) == ('other' if variant == 'other_generating_act' else 'act',
                                       'recipient', 'earlier') and
            application(state, 'r2nz', ['zname']) and variant != 'no_generation',
        ur=lambda target, point: (target, point) ==
            ('other' if variant == 'other_harmed_person' else 'target', 'later')
            and variant != 'no_harm',
        hzie=lambda recipient, factor, target, effect, point:
            (recipient, target, point) == ('recipient', 'target', 'later') and
            application(factor, 'r2oc', ['zname', 'zearly']) and symbol(effect) == 'r2od'
            and variant != 'no_causal_contribution',
    )
    return values


@lru_cache(None)
def judgment_checks():
    rows = {}
    for variant in ('baseline', 'not_person', 'other_judge', 'other_topic', 'not_affirmed',
                    'provisional', 'examined'):
        result = evaluate(fixture(), model(variant), PEOPLE, SCENES, True)
        expected = [variant == 'baseline'] * 3 + [False]
        assert result == expected, (variant, result)
        rows[variant] = result
    values = model()
    values['h224x'] = unknown
    try:
        evaluate(fixture(), values, PEOPLE, SCENES, True)
    except ValueError:
        pass
    else:
        raise AssertionError('Unknown examination was treated as absence')
    return dict(contrasts=rows, provisional_and_examined_judgments_not_classified_as_prejudice=True,
                unknown_examination_rejected=True, claim_truth_never_executed=True)


@lru_cache(None)
def instilling_checks():
    rows = {}
    for variant in ('baseline', 'wrong_closed_opinion', 'no_occurrence', 'no_participation',
                    'not_presenter', 'no_presentation', 'not_received', 'not_understood',
                    'other_generating_act', 'no_generation'):
        result = evaluate(fixture(), model(variant), PEOPLE, SCENES, True)
        assert result == [True, variant == 'baseline', variant == 'baseline', False], (variant, result)
        rows[variant] = result
    return dict(contrasts=rows, native_presentation_reception_understanding_and_generation=True,
                planter_belief_and_malicious_intent_not_required=True)


@lru_cache(None)
def adverse_checks():
    rows = {}
    for variant in ('baseline', 'missing_later', 'reversed_time', 'no_harm',
                    'other_harmed_person', 'no_causal_contribution'):
        result = evaluate(fixture(), model(variant), PEOPLE, SCENES, True)
        assert result == [True, True, variant == 'baseline', False], (variant, result)
        rows[variant] = result
    return dict(contrasts=rows, native_time_order_and_factive_causal_relation=True,
                prior_factor_can_have_ceased_at_later_point=True,
                temporal_succession_alone_not_enough=True)


@lru_cache(None)
def return_checks():
    rows = {}
    for variant in ('predecessor', 'own', 'unrelated', 'no_prior_role', 'no_later_role',
                    'different_role', 'reversed_succession', 'other_originator'):
        values = model()
        values.update(
            hzwn=lambda person, role, point:
                (person, role, point) in {
                    ('planter', 'topic' if variant == 'different_role' else 'other', 'earlier'),
                    ('target', 'other', 'later')} and
                not (variant == 'no_prior_role' and person == 'planter') and
                not (variant == 'no_later_role' and person == 'target'),
            h225a=lambda role, prior, successor, earlier, later:
                (role, prior, successor, earlier, later) ==
                ('other', 'recipient' if variant == 'other_originator' else
                 'target' if variant == 'reversed_succession' else 'planter',
                 'planter' if variant == 'reversed_succession' else 'target', 'earlier', 'later')
                and variant != 'unrelated')
        if variant == 'own':
            # The self branch does not require inheriting one's own role.
            old_cause = values['hzie']
            values.update(ztarget=lambda: 'planter',
                          ur=lambda person, point: (person, point) == ('planter', 'later'),
                          hzie=lambda recipient, factor, target, effect, point:
                              target == 'planter' and old_cause(recipient, factor, 'target', effect, point),
                          h225a=lambda *args: False, hzwn=lambda *args: False)
        result = evaluate(fixture(True), values, PEOPLE, SCENES, True)
        expected = variant in ('predecessor', 'own')
        assert result == [True, True, True, False, expected], (variant, result)
        rows[variant] = result
    return dict(contrasts=rows, same_causal_originator_and_harmed_target=True,
                own_or_predecessor_not_both_required=True,
                native_role_holding_and_succession_connection=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='prejudice_effect_relations_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[700, 845], text=unit['text'][700:845]),
                references=[
                    dict(url='https://korpora.org/Kant/aa08/036.html', role='primary_source_context'),
                    dict(url='https://www.rainerstumpe.de/ZLUF/kant_logik01.html',
                         role='primary_text_transcription_of_Jaesche_edited_Logik_auxiliary_reading'),
                    dict(url='https://www.duden.de/rechtschreibung/raechen',
                         role='modern_auxiliary_adverse_consequences_distinct_from_intentional_revenge')],
                interpretation=LIMITS, added_definitions=list(MEANINGS),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_two_sentence_characters=382,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements']
    assert len(new.document['statements']) == 60
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    assert selection_binding(new, [59]) == selection_binding(old, [59])
    for path, indices in previous.previous.previous.previous.reversal.SENTENCES:
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
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES),
                preserved_statements=60, preserved_reviews=len(reviews),
                preserved_sentence_characters=382, previous_claim_binding_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('judgment', judgment_checks), ('instilling', instilling_checks),
                     ('adverse_effect', adverse_checks), ('return', return_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR,
        *[p for p, _ in previous.previous.previous.previous.reversal.SENTENCES],
        'scripts/compose_prejudice_effects.py', 'scripts/check_prejudice_effects.py',
        'tests/test_prejudice_effects.py', 'scripts/check_reversal_focus.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
    }
    return dict(status='prejudice_effects_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_instilling_and_temporally_fixed_adverse_effect'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
