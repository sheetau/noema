"""Check modal exclusion, shared attainment witnesses, pace and discourse."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import FunctionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_slow_attainment import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_public_comparison_claim import seq
from scripts.check_scoped_counts import arithmetic
from scripts.check_public_reversal import SENTENCES

INDEX = 'data/semantic-review-index-v135.json'
AUDIT = 'data/public-slow-attainment-reading-v1.json'
REPORT = 'reports/public-slow-attainment-v1.json'
DOC = 'docs/public-slow-attainment-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/public-reversal-reading-v1/page-484.jpg'
PRIOR = ['reports/public-third-sentence-v1.json', 'reports/public-comparison-claim-v1.json',
         'reports/prospective-liberty-v1.json', 'reports/prospective-comparison-v1.json']
REVIEWS = SENTENCES + [('data/public-third-sentence-reading-v1.json', [59])]
CONSTANTS = 'r zpublic[] a.r zreference[] d.r zcandidate[] d.r zprocess[] a.r zfirst[] d.r zlast[] d.'
ARGS = 'k zpublic[] k zreference[] k zcandidate[] k zprocess[] k zfirst[] k zlast[]'
PEOPLE = ('public', 'process', 'alternative', 'zero', 'slow', 'medium', 'fast', 'top', 'other')
SCENES = ('reference', 'branch', 'alternative', 'first', 'last')
SCALE = ('zero', 'slow', 'medium', 'fast', 'top')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, question, boundaries=()):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + CONSTANTS + question)


def base(doc):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(arithmetic(), pa=lambda n, d: n / d if d else Fraction(0),
                  zpublic=lambda: 'public', zreference=lambda: 'reference',
                  zcandidate=lambda: 'branch', zprocess=lambda: 'process',
                  zfirst=lambda: 'first', zlast=lambda: 'last')
    return values


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def call(node, name):
    found = [n for n in nodes(node) if n.get('kind') == 'call' and n['symbol'] == name]
    assert len(found) == 1
    return found[0]


@lru_cache(None)
def route_checks():
    doc = fixture(['r2ps', 'r2pr'], 'q[k r2pr[k zpublic[] k zreference[]]].'
                  'q[k r2ps[k zpublic[] k zreference[]]].', ('r2pp', 'hzne'))
    def model(variant='baseline'):
        values = base(doc)
        cases = set() if variant == 'empty_candidates' else {'branch', 'alternative'}
        routes = set() if variant == 'no_attainment' else {('branch', 'process')}
        if variant in ('fast_other_branch', 'both_slow'):
            routes.add(('alternative', 'process'))
        if variant == 'fast_same_branch':
            routes.add(('branch', 'alternative'))
        scale = () if variant == 'empty_scale' else SCALE + ('slow',) if variant == 'duplicate_scale' else SCALE
        low = {'zero', 'slow'} if variant == 'zero_is_slow' else {'top'} if variant == 'top_is_slow' else \
            {'medium'} if variant == 'hole_in_slow_band' else set() if variant == 'empty_slow_band' else {'slow', 'medium'}
        def attained(public, reference, candidate, process, first, last):
            return (public, reference, first, last) == ('public', 'reference', 'first', 'last') and \
                (candidate, process) in routes
        def pace(public, process, goal, population, first, last, reference, candidate):
            assert json.loads(goal.syntax) == dict(kind='function_ref', symbol='h4l')
            assert goal.rank == 0 and population.items == ('public', 'other')
            assert (public, reference) == ('public', 'reference')
            if variant == 'outside_rate': return 'other'
            if variant == 'zero_rate': return 'zero'
            if variant == 'fast_rate': return 'fast'
            if variant == 'fast_other_branch' and candidate == 'alternative': return 'fast'
            if variant == 'fast_same_branch' and process == 'alternative': return 'fast'
            return 'slow'
        values.update(h226e=lambda p, r: seq(scale), h226f=lambda p, r, v: v in low,
                      h226g=pace, h222i=lambda p, r: seq(('public', 'other')),
                      h222k=lambda p, r, c: (p, r) == ('public', 'reference') and c in cases,
                      h222g=lambda p, r: 'public', h222h=lambda p, r, c: 'first',
                      hzne=lambda frame, origin, candidate: variant != 'invalid_candidate_frame',
                      r2pp=attained)
        return values
    variants = ('baseline', 'both_slow', 'no_attainment', 'empty_candidates', 'fast_other_branch',
                'fast_same_branch', 'fast_rate', 'outside_rate', 'zero_rate', 'empty_scale',
                'duplicate_scale', 'zero_is_slow', 'top_is_slow', 'hole_in_slow_band',
                'empty_slow_band', 'invalid_candidate_frame')
    rows = {}
    for variant in variants:
        actual = evaluate(doc, model(variant), PEOPLE, SCENES, True)
        assert actual == [variant not in ('empty_candidates', 'no_attainment'),
                          variant in ('baseline', 'both_slow')], (variant, actual)
        rows[variant] = actual
    for name in ('h226g', 'h226f', 'h222k'):
        values = model(); values[name] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, some_failed_candidates_allowed=True,
                faster_second_process_in_same_candidate_refused=True,
                no_attainment_is_not_only_slow=True, pace_and_attainment_have_same_witnesses=True,
                unknown_inputs_refused=3, boundaries=['r2pp', 'hzne'])


@lru_cache(None)
def witness_checks():
    # Check the actual universally quantified implication and measurement
    # arguments; finite examples alone would not detect every swapped witness.
    modal = catalog().entries['r2ps']['declaration']
    assert call(modal, 'r2pp')['arguments'] == call(modal, 'r2pq')['arguments']
    pace = catalog().entries['r2pq']['declaration']
    p = [dict(kind='variable', name=x['name']) for x in pace['parameters']]
    assert call(pace, 'h226g')['arguments'] == [
        p[0], p[3], dict(kind='quote', body=dict(kind='function_ref', symbol='h4l')),
        dict(kind='call', symbol='h222i', arguments=p[:2]), p[4], p[5], p[1], p[2]]
    doc = fixture(['r2pp', 'r2ln'], 'q[k r2pp[' + ARGS + ']].'
                  'q[t[k r2ln[k zpublic[] k zreference[]]][k zcandidate[]]].', ('hzmy',))
    people = ('public', 'process', 'frame', 'p', 'q', 'r')
    scenes = ('reference', 'branch', 'first', 'last')
    def predicate(members):
        return FunctionValue(('individual',), 'truth', lambda person: person in members)
    def model(variant):
        values = base(doc)
        members = {'p', 'q', 'r'}
        rows = ('p', 'q') if variant == 'missing_population_member' else ('p', 'q', 'r')
        def order(first, last, candidate):
            return candidate == 'branch' and (first, last) == (('last', 'first') if variant == 'reverse_time' else ('first', 'last'))
        def change(public, process, first, last, candidate, scope, extent):
            return ((public, process, first, last, candidate) == ('public', 'process', 'first', 'last', 'branch')
                    and variant != 'no_change'
                    and all(scope('public', person, candidate) for person in members)
                    and extent(predicate(members), predicate({'p'} if variant == 'insufficient_extent' else {'p', 'q'})))
        values.update(h222g=lambda p, r: 'frame',
                      h222h=lambda p, r, c: 'last' if variant == 'already_completed' else 'first',
                      h222i=lambda p, r: seq(rows), h222j=lambda p, r: Fraction(1, 2),
                      h7q=lambda frame, candidate, point: (frame, candidate) == ('frame', 'branch') and
                          point in ('first', 'last') and not (variant == 'missing_endpoint' and point == 'last'),
                      ic=order, aa=lambda p: p in members,
                      h6t=lambda public, person, reference: (public, reference) ==
                          ('public', 'branch' if variant == 'wrong_reference' else 'reference') and person in members,
                      hzmy=change)
        return values
    rows = {}
    for variant in ('baseline', 'reverse_time', 'already_completed', 'missing_endpoint',
                    'wrong_reference', 'no_change', 'insufficient_extent', 'missing_population_member'):
        actual = evaluate(doc, model(variant), people, scenes, True)
        # Reversed order fails the selected first/last and the old goal too,
        # because the successful change still belongs to the original pair.
        assert actual == [variant == 'baseline'] * 2, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, old_hzng_goal_and_explicit_route_agree=True,
                native_history_order_population_and_extent=True, boundary='hzmy',
                internal_ability_transition_and_cause_unchanged=True,
                universal_implication_and_measurement_witnesses_structurally_identical=True)


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2pw'], 'q[k r2pw[]].')
    people = ('fourth', 'reversal', 'harm', 'return', 'author', 'other')
    scenes = ('context', 'other')
    def model(variant):
        values = base(doc)
        values.update(h226h=lambda: 'other' if variant == 'wrong_conclusion' else 'fourth',
                      h224m=lambda: 'reversal', h225s=lambda: 'harm', h225o=lambda: 'return',
                      wa=lambda: 'author', hzp3=lambda: 'context',
                      hznreport=lambda n, a, claim, s, c:
                          (n, a, s, c) == ('fourth', 'author', 'fourth', 'context') and
                          claim.rank == 3 and json.loads(claim.syntax) ==
                          dict(kind='call', symbol='r2pt', arguments=[]) and variant != 'no_claim',
                      ud=lambda a, premises, n, c: (a, n, c) == ('author', 'fourth', 'context') and
                          {p for p in people if premises(p)} == {'reversal', 'harm', 'return'} and variant != 'no_reason',
                      ue=lambda first, last, c: first in {'reversal', 'harm', 'return'} and
                          (last, c) == ('fourth', 'context') and
                          not (variant == 'missing_order' and first == 'return'))
        return values
    rows = {}
    for variant in ('baseline', 'no_claim', 'no_reason', 'wrong_conclusion', 'missing_order'):
        actual = evaluate(doc, model(variant), people, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, all_world_inputs_unknown_without_execution=True,
                all_three_source_clauses_bound_as_reasons=True)


CLAUSES = [
    ('Daher ', ['r2pv', 'r2pw', 'ud', 'ue'], '第三文の反転・有害さ・反作用を根拠として、第四文を帰結として提示する。'),
    ('kann ', ['r2pr', 'r2ps'], '同じ候補範囲内に、到達する過程が少なくとも一つある。現実の成功や全候補の成功は主張しない。'),
    ('ein Publikum ', ['h222e', 'r2pt', 'r2la', 'r2nd'], '前文と同じ公衆の全対象について、分類と構成員を保つ。'),
    ('nur langsam ', ['r2po', 'r2pq', 'r2ps', 'h226g'], '可能な全到達経路の進行速度が、同じ固定した正の低速度帯に入る。速い別経路を許さない。'),
    ('zur Aufklärung gelangen.', ['r2pp', 'hzmy', 'r2lc', 'h4l'], '先頭文と同じ、肯定的な自立能力への変化が所定の広がりで成立する到達目標。'),
]


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    text, position, clauses = unit['text'], 846, []
    for phrase, definitions, interpretation in CLAUSES:
        assert text.startswith(phrase, position)
        end = position + len(phrase)
        clauses.append(dict(range=[position, end], text=phrase, definitions=definitions, reading=interpretation))
        position = end
    assert position == 906
    paths = {FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, IMAGE, *PRIOR, *[p for p, _ in REVIEWS]}
    return dict(status='fourth_public_sentence_reviewed_under_explicit_reading',
                reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[846, 906], text=text[846:906]),
                clauses=clauses, selection=selection_binding(catalog(), [60]), interpretation=LIMITS,
                judgment='原刊484頁と固定本文を通読し、可能性・到達・公衆の参照・速度限定・帰結提示を確認した。記録した読みの下で第四文に未処理の項目はない。',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=52, preserved_first_three_sentence_characters=719,
                combined_first_four_sentence_characters=771,
                lexical=dict(url='https://www.duden.de/rechtschreibung/langsam', sense=1,
                             use='低い速度で進む過程という採用読解の補助。現代辞書だけで歴史的文脈を唯一に確定しない。'),
                facsimile=dict(artifact=IMAGE, page=484, visually_collated=True,
                               differences='長いsと行末分綴。固定本文を変更しない。'),
                primary_context='https://korpora.org/Kant/aa08/036.html',
                no_independent_review=True, semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:-1] == old.document['statements']
    assert len(new.document['statements']) == 61
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in REVIEWS:
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    assert read(AUDIT) == reading()
    source = read(AUDIT)['source']
    assert len(''.join(source['text'].split())) == 52
    assert ''.join(c['text'] for c in read(AUDIT)['clauses']) == source['text']
    reachable = {d['name'] for d in closure(new.document, ['r2pw'])}
    assert all(set(c['definitions']) <= reachable for c in read(AUDIT)['clauses'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_sentence_characters=719,
                reviewed_fourth_sentence_characters=52, added_statement_index=60,
                old_definitions_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('routes', route_checks), ('witnesses', witness_checks),
                     ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | set(read(AUDIT)['source_sha256']) | {
        INDEX, AUDIT, 'scripts/compose_public_slow_attainment.py', 'scripts/check_public_slow_attainment.py',
        'tests/test_public_slow_attainment.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_public_comparison_claim.py',
        'scripts/check_scoped_counts.py', 'scripts/check_public_reversal.py'}
    return dict(status='fourth_public_sentence_reviewed_under_explicit_reading', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=52, combined_first_four_sentence_characters=771,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
