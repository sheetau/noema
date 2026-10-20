"""Check scope separation; deliberately do not certify the whole sentence."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product, permutations
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content, SequenceValue, FunctionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_fifth_sentence_scope import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS,
    MEANINGS, LIMITS, PAIR, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_attributed_focus import unwrap
from scripts.check_scoped_counts import arithmetic

INDEX = 'data/semantic-review-index-v113.json'
AUDIT = 'data/fifth-sentence-scope-reading-v1.json'
REPORT = 'reports/fifth-sentence-scope-v1.json'
DOC = 'docs/fifth-sentence-scope-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
SENTENCES = [('data/nature-sentence-reading-v1.json', [51]),
             ('data/confirmed-incapacity-reading-v1.json', [11, 12]),
             ('data/fetters-sentence-reading-v1.json', [10, 52]),
             ('data/fourth-sentence-reading-v1.json', [13, 53])]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, extra, boundaries=()):
    doc = deepcopy(catalog().document)
    for declaration in doc['declarations']:
        if declaration['name'] in boundaries:
            declaration.update(kind='primitive', parameters=[p['sort'] for p in declaration['parameters']])
            declaration.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


def criteria(predicate):
    sort = json.dumps(dict(kind='function', parameters=['number'], result='truth'),
                      sort_keys=True, separators=(',', ':'))
    return SequenceValue((FunctionValue(('number',), 'truth', predicate),), sort)


@lru_cache(None)
def count_checks():
    # Native count/focus/expectation definitions execute; only previously
    # established achievement and ability histories are boundary inputs.
    doc = fixture(['r2jb', 'r2jc', 'h5x', 'rsw', 'rsx', 'rsy'], '''
r zp[] j[a].r znow[] d.
d zpair[] ''' + PAIR + '''[k rst[r c[k r2jb[k zp[]]] r c[k r2jc[k zp[]]]]].
q[t[k r2jb[k zp[]]][k znow[]]].
q[t[k r2jc[k zp[]]][k znow[]]].
q[t[k h5x[k zp[]]][k znow[]]].
q[k rsx[k rsw[k zpair[]] k znow[]]].
q[k rsy[k rsw[k zpair[]] k znow[]]].
''', ('h4q', 'h5k', 'h4t'))
    people, scenes = ('one', 'two', 'three', 'author'), ('now', 'expected')

    def model(selected=('one',), expectation=True, predicted_success=False,
              population=('one', 'two', 'three'), incomplete=False, upper=2,
              expected_achievement=True):
        values = unknowns(doc)
        values.update(arithmetic())
        values.update(
            zp=lambda: SequenceValue(tuple(population), '"individual"'), znow=lambda: 'now',
            aa=lambda p: p != 'author', h4i=lambda p, s: p != 'author',
            h4h=lambda n, s: Fraction(upper),
            h5v=lambda n, s: criteria(lambda count: count >= upper),
            h4q=lambda p: Content(scenes, (p in selected, p in selected and expected_achievement)),
            h5k=lambda p: Content(scenes, (p in selected, p in selected and predicted_success)),
            h4t=lambda p, s: not (incomplete and p == 'two'),
            wa=lambda: 'author',
            ke=lambda author, p, premise, anchor, alternative:
                expectation and author == 'author' and symbol(premise) == 'h4q'
                and alternative == 'expected',
        )
        return values

    rows = {}
    for name, kwargs, expected in (
        ('baseline', {}, [True, True, True, False, True]),
        ('empty_expectation', {'expectation': False}, [True, False, False, False, False]),
        ('predicted_success', {'predicted_success': True}, [True, False, False, False, False]),
        ('premise_not_held', {'expected_achievement': False}, [True, False, False, False, False]),
        ('zero_successes', {'selected': ()}, [False, True, False, True, True]),
        ('not_few', {'selected': ('one', 'two')}, [False, True, False, True, True]),
        ('incomplete_scope', {'population': ('one',)}, [False, False, False, True, False]),
        ('duplicate', {'population': ('one', 'two', 'two')}, [False, False, False, True, False]),
        ('unqualified_missing_history', {'incomplete': True}, [False, False, False, True, False]),
        ('qualifier_missing_other_history', {'selected': ('two',), 'incomplete': True},
         [True, True, True, False, True]),
    ):
        actual = evaluate(doc, model(**kwargs), people, scenes, True)
        assert actual == expected, (name, actual)
        rows[name] = actual
    cases = 0
    for bits, expectation, predicted in product(product((False, True), repeat=3), (False, True), (False, True)):
        selected = tuple(p for p, bit in zip(people[:3], bits) if bit)
        actual = evaluate(doc, model(selected=selected, expectation=expectation,
                                     predicted_success=predicted), people, scenes, True)
        assert actual[2] == (actual[0] and actual[1])
        assert actual[3:] == [not actual[0], actual[1]]
        cases += 1
    for population in permutations(people[:3]):
        assert evaluate(doc, model(population=population), people, scenes, True) == rows['baseline']
    for missing in ('h5k', 'h4t', 'ke', 'h4h', 'h5v'):
        values = model()
        values[missing] = unknown
        try:
            evaluate(doc, values, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error), (missing, str(error))
        else:
            raise AssertionError(missing)
    foreground = deepcopy(doc)
    foreground['statements'] = foreground['statements'][:1]
    values = model()
    values['ke'] = unknown
    assert evaluate(foreground, values, people, scenes, True) == [True]
    return dict(cases=rows,old_conjunction_equivalence_cases=cases,
                permutation_cases=6, unknown_inputs_refused=5,
                foreground_does_not_execute_expectations=True,
                foreground_negation_preserves_background=True,
                established_achievement_and_history_are_explicit_test_boundaries=True)


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2jg'], 'q[k r2jg[]].')
    people, scenes = ('author', 'condition', 'reason', 'conclusion', 'concession', 'other'), ('text', 'other')

    def model(variant='baseline'):
        values = unknowns(doc)
        values.update(wa=lambda: 'author', wh=lambda: 'text', h3a=lambda: 'condition',
                      h3s=lambda: 'reason', h5t=lambda: 'conclusion', h222d=lambda: 'concession')
        def report(node, author, foreground, scope, context):
            return variant != 'no_claim' and (node, author, scope, context) == (
                'conclusion', 'other' if variant == 'wrong_author' else 'author', 'conclusion', 'text'
            ) and unwrap(foreground) == dict(kind='call', symbol='r2jd', arguments=[])
        def background(node, author, foreground, backdrop, fs, bs, context):
            return variant != 'no_background' and (node, author, fs, bs, context) == (
                'conclusion', 'author', 'conclusion',
                'conclusion' if variant == 'wrong_scope' else 'concession',
                'other' if variant == 'wrong_context' else 'text'
            ) and unwrap(foreground) == dict(kind='call', symbol='r2jd', arguments=[]) and unwrap(backdrop) == dict(
                kind='call', symbol='r2jd' if variant == 'swapped_background' else 'r2je', arguments=[])
        values.update(
            hznreport=report, hzrbgreport=background,
            ud=lambda author, premises, conclusion, context:
                (author, conclusion, context) == ('author', 'conclusion', 'text') and
                {p for p in people if premises(p)} == (
                    {'condition'} if variant == 'omitted_reason' else
                    {'condition', 'reason', 'other'} if variant == 'extra_premise' else {'condition', 'reason'}),
            ue=lambda first, last, context: (first, last, context) == (
                ('conclusion', 'reason', 'text') if variant == 'reversed_order' else ('reason', 'conclusion', 'text')),
        )
        return values
    rows = {}
    for variant in ('baseline', 'no_claim', 'no_background', 'wrong_author', 'wrong_scope',
                    'wrong_context', 'swapped_background', 'omitted_reason', 'extra_premise', 'reversed_order'):
        actual = evaluate(doc, model(variant), people, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for missing in ('hznreport', 'hzrbgreport', 'ud', 'ue'):
        values = model()
        values[missing] = unknown
        try:
            evaluate(doc, values, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(cases=rows, unknown_attributions_refused=4,
                all_world_count_and_expectation_inputs_unexecuted=True,
                inference_attributed_not_logically_proved=True)


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-9] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert len(new.document['statements']) == 54
    assert [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b] == [15]
    reviews = load_reviews(ROOT, INDEX)['works']
    assert len(reviews['kant-1784']) == 12
    for row in reviews['kant-1784']:
        indices = [s['index'] for s in row['selection']['statements']]
        assert row['selection'] == selection_binding(new, indices)
    for path, indices in SENTENCES:
        record = read(path)
        validate_hashes(ROOT, record['source_sha256'])
        assert record['selection'] == selection_binding(new, indices)
    # h5k -> h5j -> rct/h5h -> h4p -> h4q's existential witnesses.
    # The actual declarations, not a new boundary convention, supply this chain.
    for name in ('h5k', 'h5j', 'rct', 'h5h', 'h4p', 'h4q'):
        assert new.entries[name] == old.entries[name]
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        document = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(document, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == document
    return dict(added_definitions=8, added_source_references=1, added_semantic_relations=0,
                revised_statement_indices=[15], preserved_statements=53,
                preserved_whole_unit_reviews=12, preserved_reviewed_sentence_characters=544,
                roundtrips=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    start = unit['text'].index('Daher giebt')
    background_start = unit['text'].index('und dennoch', start)
    return dict(
        status='fifth_sentence_scope_revised_remaining_meaning_review',
        document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                    range=[start, len(unit['text'])], text=unit['text'][start:]),
        background_scope=dict(symbol='h222d', range=[background_start, len(unit['text'])],
                              text=unit['text'][background_start:]),
        selection=selection_binding(catalog(), [15]), interpretation_limits=LIMITS,
        reused=dict(count_and_focus=['h5w', 'h5o', 'rcz'], achievement=['h4p', 'h5j', 'h5k'],
                    gait_correspondence=['h5g', 'h5e', 'h4z']),
        pending=[
            'h4m・h4nの自己形成の意味説明を、既存の精神・判断の定義と照合する。',
            'h5c・h5dの理由支持と継続がsicheren Gangの読みとして十分か、第四文の確実性r2ibとの違いを確認する。',
            'heraus zu wikkelnの解放描写と確かな歩行を、対象側の達成・活動へ結ぶ比喩と参照を確認する。',
            'durch eigene Bearbeitung ihres Geistesが離脱と確かな活動の両方へかかる範囲を確認し、必要なら因果接続を拡張する。',
            '上限・数量代替・母集団の同一性を明示した読みとして第五文全体を再読し、続けて第三段落全体を確認する。',
        ],
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036',
                         accessed='2026-10-20', use='第五文と前後関係。固定資料のwikkelnという綴りは保持する。')],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        semantic_equivalence_automatically_proved=False, new_verified_sentence_characters=0,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in
                       sorted({INVENTORY, FULL, BASIS, DOC, 'scripts/compose_fifth_sentence_scope.py'})})


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('counts', count_checks), ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    record = reading()
    assert read(AUDIT) == record
    assert sum(not c.isspace() for c in record['source']['text']) == 147
    paths = set(build()) | set(catalog().source_sha256) | {
        AUDIT, DOC, INDEX, INVENTORY, 'scripts/compose_fifth_sentence_scope.py',
        'scripts/check_fifth_sentence_scope.py', 'tests/test_fifth_sentence_scope.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_attributed_focus.py', 'scripts/check_scoped_counts.py',
    } | {p for p, _ in SENTENCES}
    return dict(status=record['status'], document=FULL, **results,
                alignment=dict(**record['source'], definitions=['r2jg', 'r2jf', 'r2jb', 'r2jc'],
                               status='explicit_partial_scope_revision'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                new_verified_sentence_characters=0, paragraph_reviewed_sentence_characters=544,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
