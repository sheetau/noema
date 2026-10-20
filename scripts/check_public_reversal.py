"""Execute the prior and reversed actions with separate conditional agitators."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_reversal import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic

INDEX = 'data/semantic-review-index-v125.json'
AUDIT = 'data/public-reversal-reading-v1.json'
REPORT = 'reports/public-reversal-v1.json'
DOC = 'docs/public-reversal-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = 'reports/collective-retention-v1.json'
SENTENCES = [('data/public-first-sentence-reading-v1.json', [55, 56]),
             ('data/public-second-sentence-reading-v1.json', [58])]
PEOPLE = ('public', 'guardians', 'prioract', 'inciteact', 'pressure',
          'p', 'q', 'g', 'h', 'i', 'j', 'other')
SCENES = ('earlier', 'incited', 'first', 'middle', 'last')
EXTRA = '''
r zpublic[] a.r zguardians[] a.r zaffected[] j[a].r zformer[] j[a].
r zagitators[] j[a].r zprioract[] a.r zearlier[] d.
r zinciteact[] a.r zincited[] d.r zpressure[] a.r zparticipants[] j[a].
r zhistory[d] c.r zbefore[d d] c.r zfirst[] d.r zlast[] d.r zanchor[] d.
r zrole[a a d] c.r zincapable[a d] c.r zincites[a a j[a] a d] c.
'''
ARGS = {
    'r2mp': 'k zpublic[] k zguardians[] k zaffected[] k zformer[] k zprioract[] k zearlier[]',
    'r2mq': 'k zpublic[] k zagitators[] k zinciteact[] k zpressure[] k zincited[] p zrole p zincapable p zincites',
    'r2mr': '''k zpublic[] k zguardians[] k zaffected[] k zformer[]
        k zagitators[] k zprioract[] k zearlier[] k zinciteact[] k zincited[]
        k zpressure[] k zparticipants[] r[p zhistory] r[p zbefore]
        r[k zfirst[]] r[k zlast[]] k zanchor[] p zrole p zincapable p zincites''',
}


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(root):
    doc = deepcopy(catalog().document)
    # Only intellectual immaturity is a boundary; collective retention and both
    # causal links execute their actual definitions, including quoted effects.
    d = next(d for d in doc['declarations'] if d['name'] == 'bf')
    d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
    d.pop('body')
    doc.update(declarations=closure(doc, [root]), statements=[])
    return parse(format_graph(doc, 'compact') + EXTRA + 'q[k ' + root + '[' + ARGS[root] + ']].')


def model(doc, variant='baseline'):
    affected = {'empty_affected': (), 'duplicate_affected': ('p', 'p'),
                'outside_affected': ('other',), 'nonhuman_affected': ('pressure',)}.get(variant, ('p',))
    former = ('g', 'h')
    agitators = {'overlapping_cohorts': ('g', 'i'), 'same_cohorts': former,
                 'single_agitator': ('i',), 'duplicate_agitators': ('i', 'i'),
                 'empty_agitators': (), 'nonhuman_agitator': ('i', 'pressure')}.get(variant, ('i', 'j'))
    earlier, incited = 'earlier', 'incited'
    if variant == 'incitation_before_prior':
        earlier, incited = incited, earlier
    if variant == 'simultaneous_prior_and_incitation':
        incited = earlier
    if variant == 'prior_at_pressure':
        earlier = 'first'
    if variant == 'incitation_at_pressure':
        incited = 'first'

    def state(person):
        return Content(SCENES, tuple(
            (person in affected and point == earlier and variant != 'no_prior_state') or
            (person in former and SCENES.index(point) >= 2 and not (
                variant == 'one_target_loses_state' and person == 'h' and point == 'middle'))
            for point in SCENES))

    def causes(act, factor, target, effect, anchor):
        factor, effect = json.loads(factor.syntax), json.loads(effect.syntax)
        assert factor == dict(kind='apply', function=dict(kind='function_ref', symbol='r2mj'),
                             arguments=[dict(kind='call', symbol='zfirst', arguments=[])])
        assert effect['function'] == dict(kind='function_ref', symbol='r2mk')
        assert [a['symbol'] for a in effect['arguments']] == ['zhistory', 'zbefore', 'zfirst', 'zlast', 'bf']
        return (act, anchor) == ('pressure', 'last') and target in former and not (
            variant == 'one_target_no_causation' and target == 'h')

    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(arithmetic())
    values.update(
        zpublic=lambda: 'other' if variant == 'different_public' else 'public',
        zguardians=lambda: 'guardians', zaffected=lambda: seq(affected), zformer=lambda: seq(former),
        zagitators=lambda: seq(agitators), zprioract=lambda: 'prioract', zearlier=lambda: earlier,
        zinciteact=lambda: 'inciteact', zincited=lambda: incited, zpressure=lambda: 'pressure',
        zparticipants=lambda: seq(('p', 'q')),
        zhistory=lambda t: not (variant == 'missing_prior_from_history' and t == earlier),
        zbefore=lambda a, b: SCENES.index(a) < SCENES.index(b) or
            variant == 'cyclic_history' and (a, b) == ('last', 'first'),
        zfirst=lambda: 'first', zlast=lambda: 'first' if variant == 'zero_duration' else 'last',
        zanchor=lambda: 'middle' if variant == 'future_end' else 'last',
        aa=lambda p: p in ('p', 'q', 'g', 'h', 'i', 'j', 'other'),
        mp=lambda group: seq(('p', 'q')) if group == 'public' else
            seq(('g', 'h', 'i', 'j')) if group == 'guardians' else seq(()),
        bf=state,
        dg=lambda act, t: (act, t) in {('prioract', earlier), ('inciteact', incited), ('pressure', 'first')}
            and not (variant == 'no_inciting_occurrence' and act == 'inciteact'),
        df=lambda person, act, t:
            ((person in former and (act, t) == ('prioract', earlier)) or
             (person in agitators and (act, t) == ('inciteact', incited)) or
             (person in ('p', 'q') and (act, t) == ('pressure', 'first')))
            and not (variant == 'missing_prior_participation' and (person, act) == ('h', 'prioract'))
            and not (variant == 'missing_agitator_participation' and (person, act) == ('j', 'inciteact')),
        h223o=lambda group, act, actors, t:
            (group, act, actors.items, t) in {
                ('guardians', 'prioract', former, earlier),
                ('public', 'pressure', ('p', 'q'), 'first')}
            and not (variant == 'no_prior_joint_action' and act == 'prioract')
            and not (variant == 'no_public_joint_action' and act == 'pressure'),
        g3=lambda act, target, prop, t:
            (act, symbol(prop), t) == ('prioract', 'bf', earlier) and target in affected
            and variant != 'no_prior_causation',
        zrole=lambda person, public, t: public == 'public' and
            (person in former and t == earlier or person in agitators and t == incited)
            and not (variant == 'former_not_guardian' and person == 'h')
            and not (variant == 'agitator_not_guardian' and person == 'j'),
        zincapable=lambda person, t: person in agitators and t == incited and
            not (variant == 'capable_agitator' and person == 'j'),
        zincites=lambda act, public, actors, pressure, t:
            (act, public, actors.items, pressure, t) == (
                'other' if variant == 'different_inciting_act' else 'inciteact',
                'other' if variant == 'different_incited_public' else 'public',
                ('i',) if variant == 'different_inciting_cohort' else agitators,
                'other' if variant == 'different_intended_pressure' else 'pressure',
                'first' if variant == 'different_incitation_time' else incited)
            and variant not in ('no_incitation', 'false_antecedent_without_pressure'),
        h223n=lambda act, target, prop, t:
            (act, symbol(prop), t) == ('pressure', 'bf', 'first') and target in former
            and variant not in ('no_pressure', 'false_antecedent_without_pressure')
            and not (variant == 'only_one_former_pressured' and target == 'h'),
        hzie=causes,
    )
    return values


def run(root, variant):
    doc = fixture(root)
    return evaluate(doc, model(doc, variant), PEOPLE, SCENES, True)


@lru_cache(None)
def prior_checks():
    variants = ('baseline', 'empty_affected', 'duplicate_affected', 'outside_affected',
                'nonhuman_affected', 'no_prior_state', 'no_prior_causation',
                'missing_prior_participation', 'no_prior_joint_action', 'different_public')
    rows = {}
    for variant in variants:
        actual = run('r2mp', variant)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, affected_scope_is_contextual_subset=True,
                state_without_prior_action_causation_rejected=True)


@lru_cache(None)
def incitation_checks():
    positives = ('baseline', 'overlapping_cohorts', 'same_cohorts')
    negatives = ('single_agitator', 'duplicate_agitators', 'empty_agitators',
                 'nonhuman_agitator', 'no_inciting_occurrence', 'missing_agitator_participation',
                 'agitator_not_guardian', 'capable_agitator', 'different_inciting_act',
                 'different_incited_public', 'different_inciting_cohort', 'different_intended_pressure',
                 'different_incitation_time', 'no_incitation')
    rows = {}
    for variant in (*positives, *negatives):
        actual = run('r2mq', variant)
        assert actual == [variant in positives], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, three_function_parameters_remain_explicit_boundaries=True,
                plural_actual_participants_required=True)


@lru_cache(None)
def reversal_checks():
    positives = ('baseline', 'overlapping_cohorts', 'same_cohorts',
                 'incitation_before_prior', 'simultaneous_prior_and_incitation',
                 'false_antecedent_without_pressure')
    negatives = ('no_prior_state', 'no_prior_causation', 'former_not_guardian',
                 'no_prior_joint_action', 'no_public_joint_action', 'different_public',
                 'only_one_former_pressured', 'no_pressure', 'one_target_no_causation',
                 'one_target_loses_state', 'prior_at_pressure', 'incitation_at_pressure',
                 'missing_prior_from_history', 'cyclic_history', 'zero_duration', 'future_end')
    rows = {}
    for variant in (*positives, *negatives):
        actual = run('r2mr', variant)
        assert actual == [variant in positives], (variant, actual)
        rows[variant] = actual
    doc = fixture('r2mr')
    for name in ('g3', 'h223n', 'h223o', 'hzie', 'bf', 'zrole', 'zincapable', 'zincites', 'zbefore'):
        values = model(doc)
        values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, all_actual_prior_guardians_are_later_targets=True,
                actual_retention_and_causal_definitions_executed=True, unknown_inputs_refused=9,
                prior_and_inciting_actions_not_ordered_against_each_other=True,
                incapacity_not_asserted_of_every_guardian=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    start, end = 449, unit['text'].index('; so schädlich', 449)
    return dict(status='public_reversal_role_and_time_binding_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[start, end], text=unit['text'][start:end]),
                third_sentence=dict(range=[449, 845], text=unit['text'][449:845]),
                interpretation=LIMITS, whole_sentence_semantically_verified=False,
                newly_reviewed_sentence_characters=0, preserved_first_two_sentence_characters=382,
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
    for path, indices in SENTENCES:
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
    return dict(new_definitions=len(MEANINGS), new_primitives=0, preserved_statements=59,
                preserved_reviews=len(reviews), preserved_sentence_characters=382, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('prior_action', prior_checks), ('incitation', incitation_checks),
                     ('reversal', reversal_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in SENTENCES],
        'scripts/compose_public_reversal.py', 'scripts/check_public_reversal.py',
        'tests/test_public_reversal.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='public_reversal_third_sentence_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_prior_and_reversed_action_with_conditional_incitation'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
