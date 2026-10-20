"""Check literal force guidance, identical roles and nonfactive metaphor."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_leading_band import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts import check_political_withdrawal as withdrawal

INDEX = 'data/semantic-review-index-v142.json'
REPORT = 'reports/leading-band-v1.json'
AUDIT = 'data/leading-band-reading-v1.json'
DOC = 'docs/leading-band-v1.md'
INVENTORY = withdrawal.INVENTORY
LEXICON = 'artifacts/leading-band-reading-v1/adelung-leitband.html'
PRIOR = ['reports/prejudice-forecast-v1.json', 'reports/prejudice-guidance-v1.json']


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, declarations, questions, boundaries=()):
    doc = deepcopy(catalog().document)
    extra = parse('p:' + declarations)['declarations'] if declarations.strip() else []
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc['declarations'] = extra + doc['declarations']
    doc.update(declarations=closure(doc, roots + [d['name'] for d in extra]), statements=[])
    return parse(format_graph(doc, 'compact') + questions)


def base(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


@lru_cache(None)
def physical_checks():
    doc = fixture(['r2rs'], 'r zband[] a.r zperson[] a.r zact[] a.r zpoint[] d.',
                  'q[k r2rs[k zband[] k zperson[] k zact[] k zpoint[]]].')
    people, scenes = ('band', 'child', 'walk', 'holder', 'other'), ('point', 'otherpoint')

    def model(variant):
        v = base(doc)
        v.update(zband=lambda: 'band', zperson=lambda: 'band' if variant == 'same_roles' else 'child',
                 zact=lambda: 'walk', zpoint=lambda: 'point',
                 zad=lambda obj, point: (obj, point) == ('band', 'point') and variant != 'unmade',
                 h227p=lambda obj, point: (obj, point) == ('band', 'point') and variant != 'no_band_shape',
                 zah=lambda person: person == 'child' and variant != 'not_child',
                 zae=lambda band, users, activity, point:
                     (band, point) == ('band', 'point') and users.rank == activity.rank == 0
                     and symbol(users) == 'zah' and symbol(activity) == 'zal'
                     and variant != 'no_training_use',
                 dg=lambda act, point: (act, point) == ('walk', 'point') and variant != 'no_occurrence',
                 zai=lambda person, act, point:
                     (person, act, point) == ('child', 'walk', 'point') and variant != 'not_walking',
                 zaj=lambda person, act, point:
                     (person, act, point) == ('child', 'walk', 'point') and variant != 'no_support',
                 h227q=lambda band, person, point:
                     (band, person, point) == ('band', 'child', 'point') and variant != 'no_connection',
                 h227s=lambda band, person, act, point:
                     (band, person, act, point) ==
                     ('other' if variant == 'other_band' else 'band',
                      'other' if variant == 'other_body' else 'child',
                      'other' if variant == 'other_movement' else 'walk',
                      'otherpoint' if variant == 'other_time' else 'point')
                     and variant != 'no_force_effect',
                 aa=lambda person: person in ('holder', 'child'),
                 h227r=lambda holder, band, point:
                     (holder, band, point) ==
                     ('child' if variant == 'self_holding' else 'holder', 'band', 'point')
                     and variant != 'no_holder')
        return v

    rows = {}
    for variant in ('baseline', 'unmade', 'no_band_shape', 'not_child', 'no_training_use',
                    'no_occurrence', 'not_walking', 'no_support', 'no_connection', 'no_force_effect',
                    'other_band', 'other_body', 'other_movement', 'other_time', 'no_holder',
                    'self_holding', 'same_roles'):
        actual = evaluate(doc, model(variant), people, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for missing in ('h227q', 'h227r', 'h227s'):
        v = model('baseline'); v[missing] = unknown
        try:
            evaluate(doc, v, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, native_physical_relations=True, no_semantic_boundaries=True,
                training_goal_quoted_without_requiring_achievement=True, unknown_inputs_refused=3)


@lru_cache(None)
def scope_checks():
    doc = fixture(['r2rt'], 'r zold[] a.r znew[] a.r zperson[] a.r zearly[] d.r zlate[] d.',
                  'q[k r2rt[k zold[] k zperson[] k zearly[]]].'
                  'q[k r2rt[k znew[] k zperson[] k zlate[]]].',
                  ('r2qx', 'r2qs', 'hzne'))
    people = ('public', 'mass', 'old', 'new', 'person', 'event', 'other')
    scenes = ('reference', 'origin', 'future')

    def model(variant):
        v = base(doc)
        v.update(zold=lambda: 'old', znew=lambda: 'new', zperson=lambda: 'person',
                 zearly=lambda: 'origin', zlate=lambda: 'future',
                 h222e=lambda public, reference:
                     (public, reference) == ('public', 'reference') and variant != 'no_public',
                 h223i=lambda public, reference: 'other' if variant == 'other_mass' else 'mass',
                 mp=lambda mass: seq(('person',) if mass == 'mass' and variant != 'outsider' else ()),
                 h222g=lambda public, reference: 'public',
                 h222h=lambda public, reference, candidate: 'future' if variant == 'wrong_origin' else 'origin',
                 h227l=lambda public, reference: seq(
                     ('old',) if (public, reference) == ('public', 'reference') and variant != 'wrong_old' else ()),
                 h227m=lambda public, reference, candidate: seq(
                     ('new',) if (public, reference, candidate) ==
                     ('public', 'reference', 'origin' if variant == 'other_candidate' else 'future')
                     and variant != 'wrong_new' else ()),
                 r2qx=lambda public, reference, act, candidate:
                     (public, reference, act, candidate) == ('public', 'reference', 'event', 'future')
                     and variant != 'no_revolution',
                 hzne=lambda frame, origin, candidate:
                     (frame, origin, candidate) == ('public', 'origin', 'future') and variant != 'bad_frame',
                 r2qs=lambda public, reference, candidate, first, last:
                     (public, reference, candidate, first, last) ==
                     ('public', 'reference', 'future', 'origin', 'future') and variant != 'no_later_frame')
        return v

    rows = {}
    both_fail = {'no_public', 'other_mass', 'outsider', 'no_revolution', 'bad_frame', 'wrong_origin'}
    for variant in ('baseline', *sorted(both_fail), 'wrong_old', 'wrong_new',
                    'other_candidate', 'no_later_frame'):
        actual = evaluate(doc, model(variant), people, scenes, True)
        expected = [variant not in both_fail | {'wrong_old'},
                    variant not in both_fail | {'wrong_new', 'other_candidate', 'no_later_frame'}]
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, same_public_mass_candidate_opinions_and_times=True,
                boundaries=['r2qx', 'r2qs', 'hzne'],
                target_and_depiction_not_used_to_select_scope=True)


@lru_cache(None)
def role_checks():
    doc = fixture(['r2ru', 'r2rv', 'r2rw'], 'r zroles[] j[a].r zpoint[] d.',
                  ''.join('q[t[k ' + n + '[k zroles[]]][k zpoint[]]].'
                          for n in ('r2ru', 'r2rv', 'r2rw')), ('r2rt', 'r2rc', 'r2rs'))
    people, scenes = ('opinion', 'person', 'act', 'other'), ('point', 'otherpoint')
    rows = {}
    variants = (
        ('baseline', ('opinion', 'person', 'act')),
        ('swapped', ('person', 'opinion', 'act')),
        ('other_opinion', ('other', 'person', 'act')),
        ('other_person', ('opinion', 'other', 'act')),
        ('other_act', ('opinion', 'person', 'other')),
        ('empty', ()), ('extra', ('opinion', 'person', 'act', 'other')),
        ('other_time', ('opinion', 'person', 'act')),
        ('no_target', ('opinion', 'person', 'act')),
        ('no_picture', ('opinion', 'person', 'act')),
    )
    for variant, roles in variants:
        v = base(doc)
        v.update(zroles=lambda: seq(roles),
                 zpoint=lambda: 'otherpoint' if variant == 'other_time' else 'point',
                 r2rt=lambda opinion, person, point: (opinion, person, point) == ('opinion', 'person', 'point'),
                 r2rc=lambda person, opinion, act, point:
                     (person, opinion, act, point) == ('person', 'opinion', 'act', 'point')
                     and variant != 'no_target',
                 r2rs=lambda opinion, person, act, point:
                     (opinion, person, act, point) == ('opinion', 'person', 'act', 'point')
                     and variant != 'no_picture')
        actual = evaluate(doc, v, people, scenes, True)
        accepted = {'baseline', 'no_target', 'no_picture'}
        expected = [variant in accepted | {'other_act'}, variant in {'baseline', 'no_picture'},
                    variant in {'baseline', 'no_target'}]
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, identical_three_positions_and_evaluation_point=True,
                scope_independent_of_target_and_depiction_success=True,
                boundaries=['r2rt', 'r2rc', 'r2rs'])


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2ry'], '', 'q[k r2ry[]].', ('r2rq',))
    rows = {}
    for variant in ('baseline', 'no_previous', 'no_metaphor', 'wrong_claim', 'wrong_scope',
                    'swapped_sides', 'wrong_author', 'wrong_node', 'wrong_context'):
        v = base(doc)
        def metaphor(node, author, claim, scope, target, picture, context):
            expected = ('r2rn', 'r2ru', 'r2rv', 'r2rw')
            if variant == 'wrong_claim':
                expected = ('r2qz', *expected[1:])
            if variant == 'wrong_scope':
                expected = (expected[0], 'r2rv', *expected[2:])
            if variant == 'swapped_sides':
                expected = (*expected[:2], expected[3], expected[2])
            return (variant != 'no_metaphor' and all(d.rank == 3 for d in (claim, scope, target, picture))
                    and tuple(symbol(d) for d in (claim, scope, target, picture)) == expected
                    and (node, author, context) == ('back', 'author', 'context'))
        v.update(r2rq=lambda: variant != 'no_previous',
                 h227n=lambda: 'other' if variant == 'wrong_node' else 'back',
                 wa=lambda: 'other' if variant == 'wrong_author' else 'author',
                 hzp3=lambda: 'othercontext' if variant == 'wrong_context' else 'context',
                 h224n=metaphor)
        actual = evaluate(doc, v, ('back', 'author', 'other'), ('context', 'othercontext'), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_world_relations_unknown_without_execution=True,
                shared_forecast_and_order_preserved=True, boundaries=['r2rq'])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='leading_band_depiction_integrated_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[1102, 1216], text=unit['text'][1102:1216]),
                references=[
                    dict(url='https://korpora.org/Kant/aa08/036.html', role='primary_text'),
                    dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009132_7_1_1207',
                         role='historical_dictionary_body_retrieved', artifact=LEXICON),
                    dict(url='https://www.duden.de/rechtschreibung/Gaengelband',
                         role='modern_auxiliary_walking_guidance_and_holding')],
                interpretation=LIMITS, selection=selection_binding(catalog(), [62]),
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_four_sentence_characters=771,
                unresolved=['vielleicht wohlの留保と譲歩', 'aber/sondernの対比',
                            'niemalsの否定範囲と第五文・段落全体の通読'],
                source_sha256={p: digest((ROOT / p).read_bytes())
                               for p in (FULL, BASIS, DOC, INVENTORY, LEXICON, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:-1] == old.document['statements'][:-1]
    assert len(new.document['statements']) == len(old.document['statements']) == 63
    assert new.document['statements'][-1]['body']['symbol'] == 'r2ry'
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
                preserved_statements=62, integrated_statement_index=62,
                old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('physical', physical_checks), ('scope', scope_checks),
                     ('roles', role_checks), ('attribution', attribution_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, LEXICON, *PRIOR, *[p for p, _ in withdrawal.REVIEWS],
        'scripts/compose_leading_band.py', 'scripts/check_leading_band.py',
        'tests/test_leading_band.py', 'scripts/check_political_withdrawal.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_public_comparison_claim.py'}
    return dict(status='leading_band_depiction_integrated_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_leading_band_metaphor'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
