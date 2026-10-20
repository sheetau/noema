"""Check appeal, reception, affect, motivation, causation and the same action."""
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
from scripts.compose_public_incitation import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts import check_public_reversal as reversal

INDEX = 'data/semantic-review-index-v127.json'
AUDIT = 'data/public-incitation-reading-v1.json'
REPORT = 'reports/public-incitation-v1.json'
DOC = 'docs/public-incitation-v1.md'
INVENTORY = reversal.INVENTORY
PRIOR = 'reports/enlightenment-incapacity-v1.json'
PEOPLE, SCENES = reversal.PEOPLE, reversal.SCENES
EXTRA = reversal.EXTRA + 'r zname[] a.r zrecipients[] j[a].'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(root):
    doc = deepcopy(catalog().document)
    if root == 'r2nb':
        for d in doc['declarations']:
            if d['name'] in ('bf', 'up'):
                d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
                d.pop('body')
    doc.update(declarations=closure(doc, [root]), statements=[])
    if root == 'r2mz':
        body = 'k r2mz[k zinciteact[] k zreceiver[] r[k zname[]] k zincited[]]'
    elif root == 'r2na':
        body = ('c[k r2na[k zrecipients[] r[k zname[]]]]'
                '[k zinciteact[] k zpublic[] k zagitators[] k zpressure[] k zincited[]]')
    else:
        args = reversal.ARGS['r2mr'].replace(' p zrole p zincapable p zincites', '')
        body = 'k r2nb[' + args + ' r[k zname[]]]'
    return parse(format_graph(doc, 'compact') + EXTRA + 'r zreceiver[] a.q[' + body + '].')


def described(value, function):
    return json.loads(value.syntax) == dict(
        kind='apply', function=dict(kind='function_ref', symbol=function),
        arguments=[dict(kind='call', symbol='zname', arguments=[])])


def model(doc, variant='baseline', flags=(True,) * 7):
    shown, received, understood, mode, intention, emotion, causal = flags
    inherited = 'no_pressure' if variant == 'no_appeal_without_pressure' else variant
    values = reversal.model(doc, inherited)
    old_cause = values['g3']
    role = values['zrole']
    actors = values['zagitators']().items
    recipients = {'empty_recipients': (), 'outside_recipient': ('other',),
                  'duplicate_recipients': ('p', 'p')}.get(variant, ('p', 'q'))

    def cause(act, person, effect, point):
        if act != 'inciteact':
            return old_cause(act, person, effect, point)
        return causal and described(effect, 'r2my') and (act, point) == ('inciteact', 'incited') and (
            person in ('p',) if variant == 'only_one_caused' else person in ('p', 'q'))

    values.update(
        zname=lambda: 'other' if variant == 'wrong_closed_action' else 'pressure',
        zreceiver=lambda: 'p', zrecipients=lambda: seq(recipients),
        f3=lambda person, act, point: person in actors and (act, point) == ('inciteact', 'incited')
            and not (variant == 'one_sender_not_presenter' and person == actors[-1]),
        f2=lambda act, recipient, subject, message, point:
            shown and variant != 'no_appeal_without_pressure' and described(message, 'r2mx') and
            (act, subject, point) == ('inciteact', recipient, 'incited') and recipient in ('p', 'q')
            and not (variant == 'one_recipient_not_addressed' and recipient == 'q'),
        h6e=lambda act, recipient, subject, message, point:
            received and described(message, 'r2mx') and
            (act, subject, point) == ('inciteact', recipient, 'incited') and recipient in ('p', 'q'),
        h6g=lambda recipient, subject, message, point:
            understood and described(message, 'r2mx') and
            (subject, point) == (recipient, 'incited') and recipient in ('p', 'q'),
        h223t=lambda act, recipient, point:
            mode and (act, point) == ('inciteact', 'incited') and recipient in ('p', 'q'),
        h223s=lambda person, action, point:
            intention and (action, point) == (
                'other' if variant == 'different_action_intention' else 'pressure', 'incited')
            and person in ('p', 'q'),
        h223u=lambda person, action, point:
            emotion and (action, point) == (
                'other' if variant == 'different_action_emotion' else 'pressure', 'incited')
            and person in ('p', 'q'),
        g3=cause,
        dc=lambda person, target, point: target == 'p' and role(person, 'public', point),
        up=lambda p: Content(SCENES, (False,) * len(SCENES)),
        h223p=lambda p, desc, ref, point: symbol(desc) == 'up' and point == 'incited',
        h223q=lambda p, desc, ref, point: symbol(desc) == 'up',
        h223r=lambda p, desc, point: symbol(desc) == 'up',
        ae=lambda *args: False, af=lambda *args: False, ap=lambda *args: False,
    )
    if variant == 'wrong_causal_effect':
        values['g3'] = lambda act, p, effect, t: described(effect, 'r2mw')
    if variant == 'wrong_message':
        values['h6e'] = lambda act, p, subject, msg, t: described(msg, 'r2my')
    return values


@lru_cache(None)
def component_checks():
    doc = fixture('r2mz')
    count = 0
    for flags in product((False, True), repeat=7):
        actual = evaluate(doc, model(doc, flags=flags), PEOPLE, SCENES, True)
        assert actual == [all(flags)], (flags, actual)
        count += 1
    rows = {}
    for variant in ('baseline', 'different_action_intention', 'different_action_emotion',
                    'wrong_causal_effect', 'wrong_message'):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for name in ('f2', 'h6e', 'h6g', 'h223t', 'h223s', 'h223u', 'g3'):
        values = model(doc)
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(independent_conditions=count, contrasts=rows, unknown_inputs_refused=7,
                desire_emotion_and_actual_causation_required=True)


@lru_cache(None)
def group_checks():
    doc = fixture('r2na')
    positives = ('baseline', 'overlapping_cohorts', 'same_cohorts', 'no_pressure')
    negatives = ('empty_recipients', 'outside_recipient', 'duplicate_recipients',
                 'empty_agitators', 'duplicate_agitators', 'one_sender_not_presenter',
                 'missing_agitator_participation', 'one_recipient_not_addressed',
                 'only_one_caused', 'wrong_closed_action', 'different_public')
    rows = {}
    for variant in (*positives, *negatives):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant in positives], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, same_senders_recipients_and_prospective_action=True,
                actual_pressure_not_a_condition_of_incitation=True)


@lru_cache(None)
def quotation_checks():
    doc = fixture('r2na')
    values = model(doc)
    old_occurrence, old_participation = values['dg'], values['df']

    def occurrence(act, point):
        if act == 'pressure':
            raise AssertionError('The requested future action was evaluated as a fact')
        return old_occurrence(act, point)

    def participation(person, act, point):
        if act == 'pressure':
            raise AssertionError('Requested participation was evaluated as a fact')
        return old_participation(person, act, point)

    values.update(dg=occurrence, df=participation)
    assert evaluate(doc, values, PEOPLE, SCENES, True) == [True]
    return dict(requested_action_and_participation_not_executed=True,
                real_motivational_effect_still_executed=True)


@lru_cache(None)
def integration_checks():
    doc = fixture('r2nb')
    positives = ('baseline', 'overlapping_cohorts', 'no_appeal_without_pressure')
    negatives = ('no_pressure', 'only_one_former_pressured', 'one_target_no_causation',
                 'one_target_loses_state', 'wrong_closed_action')
    rows = {}
    for variant in (*positives, *negatives):
        actual = evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)
        assert actual == [variant in positives], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_three_original_function_arguments_filled=True,
                action_name_identity_guard_outside_conditional=True,
                incapacity_and_retention_native_definitions_executed=True,
                source_states_bf_and_up_are_explicit_boundaries=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    start, end = unit['text'].index('wenn es von', 449), unit['text'].index('; so schädlich', 449)
    return dict(status='public_incitation_condition_composed_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[start, end], text=unit['text'][start:end]),
                interpretation=LIMITS, whole_sentence_semantically_verified=False,
                newly_reviewed_sentence_characters=0, preserved_first_two_sentence_characters=382,
                sources=['https://korpora.org/Kant/aa08/036.html',
                         'https://www.duden.de/rechtschreibung/aufwiegeln'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 59
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in reversal.SENTENCES:
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
    return dict(new_definitions=len(MEANINGS), new_primitives=3, preserved_statements=59,
                preserved_reviews=len(reviews), preserved_sentence_characters=382, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('components', component_checks), ('group', group_checks),
                     ('quotation', quotation_checks), ('integration', integration_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in reversal.SENTENCES],
        'scripts/compose_public_incitation.py', 'scripts/check_public_incitation.py',
        'tests/test_public_incitation.py', 'scripts/check_public_reversal.py',
        'scripts/compose_enlightenment_incapacity.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='public_incitation_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_agitating_appeal_and_actual_motivational_effect'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
