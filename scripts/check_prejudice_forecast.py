"""Check future frames, all revolutionary cases, public scope and quoted tone."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_prejudice_forecast import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq
from scripts import check_prejudice_guidance as guidance
from scripts import check_political_withdrawal as withdrawal

INDEX = 'data/semantic-review-index-v141.json'
REPORT = 'reports/prejudice-forecast-v1.json'
AUDIT = 'data/prejudice-forecast-reading-v1.json'
DOC = 'docs/prejudice-forecast-v1.md'
INVENTORY = withdrawal.INVENTORY
PRIOR = ['reports/prejudice-guidance-v1.json', 'reports/public-revolution-v1.json',
         'reports/public-second-sentence-v1.json']


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
def future_frame_checks():
    doc = fixture(['r2rl'], guidance.COLLECTIVE + 'r zcandidate[] d.',
                  'q[k r2rl[k zg[] k zr[] k zcandidate[]]].', ('r2rd', 'r2re'))
    def model(variant):
        v = guidance.collective_values(doc, variant)
        v.update(
            zcandidate=lambda: 'later',
            h222g=lambda public, reference: 'public',
            h222h=lambda public, reference, candidate: 'later' if variant == 'no_future' else 'earlier',
            h7q=lambda frame, candidate, point: (frame, candidate) == ('public', 'later')
                and point in guidance.SCENES and not (variant == 'missing_later' and point == 'later'),
            ic=lambda first, last, candidate: (first, last) == (
                ('later', 'earlier') if variant == 'reversed' else ('earlier', 'later')),
            h227l=lambda public, reference: seq(
                ('newone', 'newtwo') if variant == 'wrong_old' else ('oldone', 'oldtwo')),
            h227m=lambda public, reference, candidate: seq(
                () if variant == 'empty_new' else ('oldone', 'oldtwo') if variant == 'wrong_new'
                else ('newone', 'newtwo')),
        )
        return v
    rows = {}
    accepted = {'baseline', 'few_prior_adopters', 'old_also_persists'}
    for variant in ('baseline', 'few_prior_adopters', 'old_also_persists', 'already_widespread',
                    'no_old_guidance', 'no_new_guidance', 'wrong_old', 'wrong_new', 'empty_new',
                    'other_group', 'not_large', 'no_future', 'missing_later', 'reversed'):
        actual = evaluate(doc, model(variant), guidance.PEOPLE, guidance.SCENES, True)
        assert actual == [variant in accepted], (variant, actual)
        rows[variant] = actual
    for missing in ('h227l', 'h227m', 'h7q'):
        v = model('baseline'); v[missing] = unknown
        try:
            evaluate(doc, v, guidance.PEOPLE, guidance.SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, native_time_frame_plural_comparison_and_mass_size=True,
                same_old_new_group_origin_and_future_bound=True, unknown_inputs_refused=3,
                boundaries=['r2rd', 'r2re'], local_guidance_checked_in_prior_report=True)


@lru_cache(None)
def scope_checks():
    doc = fixture(['r2rm', 'r2rn'], 'r zg[] a.r zr[] d.',
                  'q[k r2rm[k zg[] k zr[]]].q[t[k r2rn[]][k zr[]]].',
                  ('r2qx', 'r2rl', 'hzne', 'r2la', 'r2nd'))
    people, scenes = ('first', 'second', 'event', 'other'), ('reference', 'case', 'alternative')
    def model(variant):
        v = base(doc)
        cases = () if variant == 'empty_candidates' else ('case', 'alternative')
        def revolutionary(public, reference, act, candidate):
            return candidate in cases and variant != 'no_revolution' and (
                (act, candidate) == ('event', 'case') or
                (act, candidate) == ('other', 'alternative') and variant != 'nonrevolution_failure')
        def future(public, reference, candidate):
            return not (
                variant in ('second_case_fails', 'nonrevolution_failure') and candidate == 'alternative' or
                variant == 'second_public_fails' and public == 'second')
        v.update(zg=lambda: 'first', zr=lambda: 'reference',
                 h222e=lambda public, reference: public in ('first', 'second') and variant != 'empty_publics',
                 r2la=lambda public, reference: variant != 'bad_public',
                 r2nd=lambda public, reference: variant != 'bad_members',
                 h222k=lambda public, reference, candidate: candidate in cases,
                 h222g=lambda public, reference: public,
                 h222h=lambda public, reference, candidate: 'reference',
                 hzne=lambda frame, origin, candidate: not (
                     variant == 'invalid_nonrevolution_frame' and candidate == 'alternative'),
                 r2qx=revolutionary, r2rl=future)
        if variant == 'invalid_nonrevolution_frame':
            v['r2qx'] = lambda public, reference, act, candidate: (act, candidate) == ('event', 'case')
        return v
    rows = {}
    inner_failures = {'empty_candidates', 'no_revolution', 'second_case_fails', 'invalid_nonrevolution_frame'}
    outer_failures = inner_failures | {'empty_publics', 'bad_public', 'bad_members', 'second_public_fails'}
    for variant in ('baseline', 'second_case_fails', 'second_public_fails', 'nonrevolution_failure',
                    'empty_candidates', 'no_revolution', 'invalid_nonrevolution_frame',
                    'empty_publics', 'bad_public', 'bad_members'):
        actual = evaluate(doc, model(variant), people, scenes, True)
        assert actual == [variant not in inner_failures, variant not in outer_failures], (variant, actual)
        rows[variant] = actual
    for missing in ('r2qx', 'r2rl', 'h222k'):
        v = model('baseline'); v[missing] = unknown
        try:
            evaluate(doc, v, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, all_revolution_cases_and_publics_required=True,
                nonrevolution_failure_allowed_but_its_frame_checked=True,
                no_revolution_is_not_vacuous_forecast=True, unknown_inputs_refused=3,
                boundaries=['r2qx', 'r2rl', 'hzne', 'r2la', 'r2nd'])


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2rq'], '', 'q[k r2rq[]].')
    people = ('front', 'back', 'massword', 'author')
    scenes = ('context',)
    rows = {}
    for variant in ('baseline', 'no_forecast', 'no_tone', 'wrong_tone_scope', 'no_order', 'same_node'):
        v = base(doc)
        v.update(h227h=lambda: 'back' if variant == 'same_node' else 'front',
                 h227n=lambda: 'back', h227o=lambda: 'massword', wa=lambda: 'author',
                 hzp3=lambda: 'context',
                 hznreport=lambda node, author, claim, scope, context:
                     variant != 'no_forecast' and (node, author, scope, context) ==
                     ('back', 'author', 'back', 'context') and claim.rank == 3 and
                     json.loads(claim.syntax) == dict(kind='call', symbol='r2rn', arguments=[]),
                 h223l=lambda node, author, scope, referents, context:
                     variant != 'no_tone' and (node, author, context) == ('massword', 'author', 'context')
                     and scope.rank == referents.rank == 1 and symbol(scope) ==
                     ('r2rn' if variant == 'wrong_tone_scope' else 'h222e') and symbol(referents) == 'h223i',
                 ue=lambda front, back, context: variant != 'no_order' and
                     (front, back, context) == ('front', 'back', 'context'))
        actual = evaluate(doc, v, people, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, same_author_source_scope_mass_referent_and_order=True,
                all_world_relations_unknown_without_execution=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    return dict(status='prejudice_forecast_attribution_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[1102, 1216], text=unit['text'][1102:1216]),
                interpretation=LIMITS, definitions=list(MEANINGS), statement=62,
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                preserved_first_four_sentence_characters=771,
                unresolved=['Leitbandの身体的描写と対応', 'vielleicht wohlの留保と譲歩',
                            'aber/sondernの対比', '第五文と段落全体の通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:-1] == old.document['statements']
    assert len(new.document['statements']) == 63
    assert new.document['statements'][-1]['body']['symbol'] == 'r2rq'
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
                preserved_statements=62, added_statements=1, old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('future_frames', future_frame_checks), ('scope', scope_checks),
                     ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, *[p for p, _ in withdrawal.REVIEWS],
        'scripts/compose_prejudice_forecast.py', 'scripts/check_prejudice_forecast.py',
        'tests/test_prejudice_forecast.py', 'scripts/check_prejudice_guidance.py',
        'scripts/check_political_withdrawal.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_scoped_counts.py',
        'scripts/check_public_comparison_claim.py'}
    return dict(status='prejudice_forecast_attribution_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_prejudice_forecast_attribution'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
