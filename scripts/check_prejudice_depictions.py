"""Test shared roles, intentional depictions and nonfactive attribution."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_prejudice_depictions import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts.check_public_reversal import SENTENCES
from scripts import check_prejudice_claim as cases

INDEX = 'data/semantic-review-index-v134.json'
AUDIT = 'data/prejudice-depictions-reading-v1.json'
REPORT = 'reports/prejudice-depictions-v1.json'
DOC = 'docs/prejudice-depictions-v1.md'
INVENTORY = cases.INVENTORY
PRIOR = 'reports/prejudice-reason-v1.json'
EXTRA = cases.EXTRA + 'r zmediumname[] a.r ztargetname[] a.r zresponse[] a.'
DESCRIPTIONS = cases.DESCRIPTIONS + '''
d h225x[case a] i[a][r[k zmediumname[]]].
d h226a[case a target a] i[a][r[k ztargetname[]]].
'''


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(root, boundaries=()):
    doc = deepcopy(catalog().document)
    extras = parse('p:' + EXTRA)['declarations']
    replacements = {d['name']: d for d in parse('p:' + EXTRA + DESCRIPTIONS)['declarations'][len(extras):]}
    for index, declaration in enumerate(doc['declarations']):
        if declaration['name'] in boundaries:
            declaration.update(kind='primitive', parameters=[p['sort'] for p in declaration['parameters']])
            declaration.pop('body')
        if declaration['name'] in replacements:
            doc['declarations'][index] = replacements[declaration['name']]
    roots = {
        'plant': ['r2pc', 'r2pd'],
        'revenge': ['r2oi', 'r2pk'],
        'plant_families': ['r2pe', 'r2pf', 'r2pg'],
        'r2pn': ['r2pn'],
    }[root]
    doc['declarations'] = extras + doc['declarations']
    doc.update(declarations=closure(doc, [*roots, *[d['name'] for d in extras]]), statements=[])
    question = {
        'plant': 'q[k r2pc[k zcase[]]].q[k r2pd[k zcase[]]].',
        'revenge': 'q[k r2oi[k zcase[] k ztarget[]]].q[k r2pk[k zcase[] k ztarget[]]].',
        'plant_families': ''.join('q[t[k ' + n + '[k zroles[]]][k zreference[]]].'
                                 for n in ('r2pe', 'r2pf', 'r2pg')),
        'r2pn': 'q[k r2pn[]].',
    }[root]
    return parse(format_graph(doc, 'compact') + question)


def applied(desc, function, arguments):
    return json.loads(desc.syntax) == dict(kind='apply',
        function=dict(kind='function_ref', symbol=function),
        arguments=[dict(kind='call', symbol=n, arguments=[]) for n in arguments])


def model(doc, variant='baseline'):
    values = cases.model(doc, variant)
    values.update(zmediumname=lambda: 'other' if variant == 'wrong_medium_name' else 'recipient',
                  ztargetname=lambda: 'other' if variant == 'wrong_target_name' else values['ztarget'](),
                  zresponse=lambda: 'response',
                  h225z=lambda case, target: 'response')
    old_cause, old_df, old_dg = values['hzie'], values['df'], values['dg']
    values.update(
        h225t=lambda plant, point: (plant, point) == ('opinion', 'earlier') and variant != 'not_plant',
        h225u=lambda medium, point: (medium, point) == ('recipient', 'earlier') and variant != 'not_medium',
        h225v=lambda plant, medium, point:
            (plant, medium, point) == ('opinion', 'other' if variant == 'wrong_root_medium' else 'recipient', 'earlier')
            and variant != 'no_root_contact',
        h226b=lambda actor, prior, point:
            (actor, prior, point) == ('opinion', 'other' if variant == 'wrong_prior' else 'act', 'later')
            and variant != 'no_perceived_wrong',
        h226c=lambda response, prior, point:
            (response, prior, point) == ('response', 'other' if variant == 'wrong_prior' else 'act', 'later')
            and variant != 'no_retributive_response',
        df=lambda actor, act, point: old_df(actor, act, point) or
            (actor, act, point) == ('recipient' if variant == 'wrong_response_actor' else 'opinion', 'response', 'later'),
        dg=lambda act, point: old_dg(act, point) or
            (act, point) == ('response', 'later') and variant != 'no_response_occurrence',
    )
    def purpose(actor, act, goal, point):
        planting = ((actor, act, point) == ('planter', 'act', 'earlier') and
                    applied(goal, 'r2oz', ['zname', 'zmediumname']) and variant != 'no_growth_purpose')
        revenge = ((actor, act, point) == ('opinion', 'response', 'later') and
                   applied(goal, 'r2od', ['ztargetname']) and variant != 'no_harm_intent')
        return planting or revenge
    def cause(actor, factor, target, effect, point):
        if json.loads(factor.syntax) == dict(kind='function_ref', symbol='r2pb'):
            if applied(effect, 'r2oy', ['zmediumname']):
                return (actor, target, point) == ('act', 'opinion', 'earlier') and variant != 'no_placement_cause'
            if symbol(effect) == 'r2od':
                return (actor, target, point) == ('response', values['ztarget'](), 'later') and variant != 'no_response_cause'
            return False
        return old_cause(actor, factor, target, effect, point)
    values.update(hzu=purpose, hzie=cause)
    # h225w is intentionally left unknown: the intended growth is not executed.
    return values


@lru_cache(None)
def planting_checks():
    doc = fixture('plant')
    rows = {}
    for variant in ('baseline', 'not_plant', 'not_medium', 'wrong_root_medium', 'no_root_contact',
                    'no_growth_purpose', 'no_placement_cause', 'wrong_medium_name'):
        actual = evaluate(doc, model(doc, variant), (*cases.PEOPLE, 'response'), cases.previous.SCENES, True)
        assert actual == [True, variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, native_classification_placement_purpose_and_cause=True,
                actual_instilling_does_not_require_bodily_planting=True, growth_goal_not_executed=True)


@lru_cache(None)
def retaliation_checks():
    doc = fixture('revenge')
    rows = {}
    for variant in ('baseline', 'no_perceived_wrong', 'no_retributive_response', 'no_harm_intent',
                    'wrong_response_actor', 'no_response_occurrence', 'no_response_cause',
                    'wrong_target_name', 'wrong_prior', 'no_generation', 'no_harm'):
        actual = evaluate(doc, model(doc, variant), (*cases.PEOPLE, 'response'), cases.previous.SCENES, True)
        expected = [False, False] if variant in ('no_generation', 'no_harm') else [True, variant == 'baseline']
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    # Same-person branch remains supported, without an inherited role.
    values = model(doc)
    old_ur, old_cause = values['ur'], values['hzie']
    values.update(ztarget=lambda: 'planter',
                  ur=lambda person, point: old_ur('target' if person == 'planter' else person, point),
                  hzie=lambda actor, factor, target, effect, point:
                      old_cause(actor, factor, 'target' if target == 'planter' and actor != 'response' else target,
                                effect, point),
                  hzwn=lambda *args: False, h225a=lambda *args: False)
    actual = evaluate(doc, values, (*cases.PEOPLE, 'response'), cases.previous.SCENES, True)
    assert actual == [True, True], actual
    rows['originator_self'] = actual
    return dict(contrasts=rows, native_intentional_response_distinct_from_adverse_effect=True,
                originator_and_predecessor_branches_preserved=True)


@lru_cache(None)
def binding_checks():
    doc = fixture('plant_families', ('r2pc', 'r2pd'))
    rows = {}
    for variant, roles in [('baseline', ('case',)), ('other_case', ('othercase',)),
                           ('empty', ()), ('extra', ('case', 'opinion'))]:
        values = cases.model(doc)
        values.update(zroles=lambda: seq(roles),
                      r2pc=lambda case: case == 'case', r2pd=lambda case: case == 'case')
        actual = evaluate(doc, values, cases.PEOPLE, cases.previous.SCENES, True)
        assert actual == [variant == 'baseline'] * 3, (variant, actual)
        rows[variant] = actual
    # Only the terminal relation symbol differs in the two three-role families.
    old = deepcopy(parent().entries['r2on']['declaration'])
    old['name'] = 'r2pl'
    def replace(value):
        if isinstance(value, dict):
            if value.get('symbol') == 'r2oi':
                value['symbol'] = 'r2pk'
            for child in value.values():
                replace(child)
        elif isinstance(value, list):
            for child in value:
                replace(child)
    replace(old['body'])
    assert old == catalog().entries['r2pl']['declaration']
    retained = catalog().entries['r2pk']['declaration']
    params = [dict(kind='variable', name=p['name']) for p in retained['parameters']]
    assert retained['body']['arguments'][0] == dict(kind='call', symbol='r2oi', arguments=params)
    return dict(contrasts=rows, same_case_and_role_positions=True,
                retaliation_retains_entire_original_case_relation=True)


@lru_cache(None)
def attribution_checks():
    doc = fixture('r2pn', ('r2ox',))
    rows = {}
    for variant in ('baseline', 'missing_previous', 'missing_planting', 'missing_revenge',
                    'wrong_claim', 'swapped_target_and_depiction'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        def depiction(node, author, claim, scope, target, picture, context):
            expected = {
                'planting': ('r2ot', 'r2pg', 'r2pe', 'r2pf'),
                'revenge': ('r2ok', 'r2om', 'r2on', 'r2pl'),
            }[node]
            if variant == 'wrong_claim':
                expected = ('r2nf', *expected[1:])
            if variant == 'swapped_target_and_depiction':
                expected = (*expected[:2], expected[3], expected[2])
            return ((author, context) == ('author', 'context') and
                    all(d.rank == 3 for d in (claim, scope, target, picture)) and
                    (symbol(claim), symbol(scope), symbol(target), symbol(picture)) == expected and
                    not (variant == 'missing_planting' and node == 'planting') and
                    not (variant == 'missing_revenge' and node == 'revenge'))
        values.update(r2ox=lambda: variant != 'missing_previous', h225y=lambda: 'planting',
                      h226d=lambda: 'revenge', wa=lambda: 'author', hzp3=lambda: 'context', h224n=depiction)
        actual = evaluate(doc, values, ('planting', 'revenge', 'author'), ('context',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_world_inputs_unknown_without_execution=True,
                target_and_depiction_both_bound_to_their_actual_claim=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='prejudice_depictions_integrated_not_sentence_reviewed',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[721, 790], text=unit['text'][721:790],
                            depiction_ranges=[[721, 744], [751, 790]]),
                references=[
                    dict(url='https://korpora.org/Kant/aa08/036.html', role='primary_source_context'),
                    dict(url='https://www.duden.de/rechtschreibung/pflanzen',
                         role='modern_auxiliary_root_placement_for_growth'),
                    dict(url='https://www.duden.de/rechtschreibung/raechen',
                         role='modern_auxiliary_intentional_retaliation_and_adverse_effect_distinguished')],
                interpretation=LIMITS, selection=selection_binding(catalog(), [59]),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_two_sentence_characters=382,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:59] == old.document['statements'][:59]
    assert len(new.document['statements']) == len(old.document['statements']) == 60
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
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
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES),
                preserved_statements=59, integrated_statement_index=59, preserved_reviews=len(reviews),
                preserved_sentence_characters=382, inherited_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('planting', planting_checks), ('retaliation', retaliation_checks),
                     ('binding', binding_checks), ('attribution', attribution_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, *[p for p, _ in SENTENCES],
        'scripts/compose_prejudice_depictions.py', 'scripts/check_prejudice_depictions.py',
        'tests/test_prejudice_depictions.py', 'scripts/check_prejudice_claim.py',
        'scripts/check_prejudice_effects.py', 'scripts/check_public_reversal.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    return dict(status='prejudice_depictions_integrated_not_sentence_reviewed', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_planting_and_retaliation_nonliteral_depictions'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
