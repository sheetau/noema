"""Check focused assurance and review the second sentence under a stated reading."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_confirmed_incapacity import ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, RESTORED_FROM, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_attributed_focus import unwrap
from scripts.check_affection_sentence import expected_background
from scripts.check_current_deprivation import capacity_values, PEOPLE, SCENES

INDEX = 'data/semantic-review-index-v97.json'
AUDIT = 'data/confirmed-incapacity-reading-v1.json'
REPORT = 'reports/confirmed-incapacity-v1.json'
DOC = 'docs/confirmed-incapacity-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
FIRST = 'data/nature-sentence-reading-v1.json'
IMAGE = 'artifacts/future-dissemination-reading-v1/page-483.jpg'
COMPONENTS = {'affection-sentence': ['r2ee', 'r2ef', 'r2eg', 'r2eh', 'r2ei', 'r2ej', 'r2ek', 'r2el', 'r2em'],
              'current-deprivation': ['r2cf', 'r2cg'], 'acquired-affection': ['r2ck'],
              'guardian-reading': ['hzxu', 'rqyy'], 'nature-sentence': ['r2eb', 'h2c', 'h3b']}


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(roots, suffix):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, roots.split()), statements=[])
    return parse(format_graph(doc, 'compact') + suffix)


@lru_cache(None)
def capacity_checks():
    doc = fixture('r2en wh r2cf', '''r zperson[] a.r zanchor[] d.
q[t[k r2en[]][k wh[]]].q[t[k r2cf[k zperson[]]][k zanchor[]]].''')
    def model(variant='baseline', scope=('person',), **options):
        values = capacity_values(doc, variant, **options)
        values.update(hzzq=lambda: 'process', wh=lambda: 'anchor',
            hzzn=lambda node, p, point: (node, point) == ('process', 'anchor') and p in scope)
        return values
    rows = []
    for now, first, second, preferred in product((False, True), repeat=4):
        expected = not(first and (preferred or second))
        actual = evaluate(doc, model(now=now, passes=(first, second), prefer_first=preferred), PEOPLE, SCENES, True)
        assert actual == [expected, expected], (now, first, second, preferred, actual)
        rows.append(dict(current_opportunity=now, first=first, second=second, first_preferred=preferred, values=actual))
    contrasts = {}
    for variant, opts, wanted in [
        ('guided', {}, [False, False]),
        ('training_only', {'now': True, 'passes': (False, False)}, [True, True]),
        ('unclassified_training', {'passes': (False, False)}, [False, False]),
        ('empty_profile', {}, [False, False]),
        ('changed_person_state', {}, [False, False]),
        ('missing_external_opportunity', {}, [False, False]),
        ('cyclic_order', {}, [False, False]),
        ('missing_assessment', {}, [False, False]),
    ]:
        actual = evaluate(doc, model(variant, **opts), PEOPLE, SCENES, True)
        assert actual == wanted, (variant, actual)
        contrasts[variant] = actual
    for name, scope in [('empty_scope', ()), ('nonhuman_scope', ('guide',))]:
        actual = evaluate(doc, model(scope=scope, passes=(False, False)), PEOPLE, SCENES, True)
        assert actual == [False, True], (name, actual)
        contrasts[name] = actual
    probe = deepcopy(doc); probe['statements'] = [doc['statements'][0]]
    for name in ('hzzn', 'aa', 'hzsc', 'hzsd', 'hzse', 'hzsf', 'hzsg', 'hzsh', 'ap'):
        values = model(); values[name] = unknown
        try: evaluate(probe, values, PEOPLE, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=9,
        native_current_capacity_definitions_executed=True, training_not_current_exercise=True,
        assured_focus_excludes_attachment_and_cause=True)


@lru_cache(None)
def discourse_checks():
    doc = fixture('r2eo r2em', 'q[k r2eo[]].q[k r2em[]].')
    fg = dict(kind='call', symbol='r2ei', arguments=[]); bg = expected_background()
    focus = dict(kind='call', symbol='r2en', arguments=[])
    people = ('firstnode', 'secondnode', 'author', 'whole', 'focus', 'other')
    scenes = ('now', 'elsewhere')
    def model(bits=(True, True, True, True), variant='baseline'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(hzzq=lambda: 'firstnode', hzzr=lambda: 'secondnode', wa=lambda: 'author',
            hzzs=lambda: 'whole', hzzt=lambda: 'focus', wh=lambda: 'now')
        assurance = ['secondnode', 'author', fg, focus, 'now']
        changes = {'assurance_other_node': (0, 'other'), 'assurance_other_author': (1, 'other'),
            'assurance_other_context': (4, 'elsewhere'),
            'assurance_only_attachment_claim': (2, dict(fg, symbol='r2eg')),
            'assurance_whole_claim_focus': (3, fg),
            'assurance_attachment_focus': (3, dict(focus, symbol='r2eg')),
            'assurance_nature_focus': (3, dict(focus, symbol='r2eh'))}
        if variant in changes:
            i, value = changes[variant]; assurance[i] = value
        if variant in ('other_author', 'other_node', 'other_context'):
            name = dict(other_author='wa', other_node='hzzr', other_context='wh')[variant]
            values[name] = (lambda: 'elsewhere') if name == 'wh' else (lambda: 'other')
        foreground = dict(fg, symbol='r2eg') if variant == 'only_attachment_foreground' else fg
        background = deepcopy(bg)
        if variant == 'whole_sentence_expectation_focus': background['arguments'][0]['body']['symbol'] = 'r2ei'
        values.update(
            hznreport=lambda node, author, content, scope, point: bits[0] and (
                node, author, scope, point) == ('secondnode', 'author', 'whole', 'now') and unwrap(content) == foreground,
            hzrbgreport=lambda node, author, content, background_content, fs, bs, point: bits[1] and (
                node, author, fs, bs, point) == ('secondnode', 'author', 'whole', 'focus', 'now') and
                unwrap(content) == foreground and unwrap(background_content) == background,
            hzxu=lambda node, author, claim, part, point: bits[2] and
                [node, author, json.loads(claim.syntax), json.loads(part.syntax), point] == assurance,
            ue=lambda first, last, point: bits[3] and (first, last, point) == (
                ('secondnode', 'firstnode', 'now') if variant == 'reversed_order' else ('firstnode', 'secondnode', 'now')))
        return values
    for bits in product((False, True), repeat=4):
        actual = evaluate(doc, model(bits), people, scenes, True)
        assert actual == [all(bits[:3]), bits[3]], (bits, actual)
    contrasts = {}
    for name in ('baseline', 'assurance_other_node', 'assurance_other_author', 'assurance_other_context',
                 'assurance_only_attachment_claim', 'assurance_whole_claim_focus', 'assurance_attachment_focus',
                 'assurance_nature_focus', 'other_author', 'other_node', 'other_context',
                 'only_attachment_foreground', 'whole_sentence_expectation_focus', 'reversed_order'):
        actual = evaluate(doc, model(variant=name), people, scenes, True)
        wanted = [name in ('baseline', 'reversed_order'), name not in ('other_node', 'other_context', 'reversed_order')]
        assert actual == wanted, (name, actual, wanted)
        contrasts[name] = actual
    for name, position in [('hznreport', 0), ('hzrbgreport', 0), ('hzxu', 0), ('ue', 1)]:
        probe = deepcopy(doc); probe['statements'] = [doc['statements'][position]]
        values = model(); values[name] = unknown
        try: evaluate(probe, values, people, scenes, True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(combinations=16, contrasts=contrasts, unknown_inputs_refused=4,
        assurance_claim_matches_attributed_foreground=True, assurance_focus_only_current_incapacity=True,
        world_contents_and_expectation_comparison_unknown=True, order_separate=True)


@lru_cache(None)
def reused_checks():
    current = catalog(); rows = {}
    for name, roots in COMPONENTS.items():
        path = 'reports/' + name + '-v1.json'; report = read(path); validate_hashes(ROOT, report['source_sha256'])
        old = parse((ROOT / report['document']).read_text(encoding='utf-8'))
        assert closure(old, roots) == closure(current.document, roots)
        dependencies = {d['name'] for d in closure(current.document, roots)}
        rebound = [n for n in dependencies if current.entries[n]['meaning_basis'] not in report['source_sha256']]
        historical = load_catalog(ROOT, 'data/' + name + '-basis-v1.json') if rebound else None
        if historical:
            assert historical.document == old
            assert all(report['source_sha256'][p] == h for p, h in historical.source_sha256.items())
        for n in dependencies:
            basis = current.entries[n]['meaning_basis']
            if n in rebound:
                assert historical.entries[n].keys() == current.entries[n].keys()
                provenance = {'meaning_basis', 'declaration_document'}
                assert {k: v for k, v in historical.entries[n].items() if k not in provenance} == {
                    k: v for k, v in current.entries[n].items() if k not in provenance}, (path, n)
            else:
                assert report['source_sha256'][basis] == current.source_sha256[basis], (path, n)
        rows[path] = dict(roots=roots, dependency_count=len(dependencies), declarations_and_meaning_conventions_unchanged=True,
            identical_conventions_reissued_under_new_basis=sorted(rebound))
    first = read(FIRST); validate_hashes(ROOT, first['source_sha256'])
    assert first['decision'] == 'equivalent_under_stated_reading_for_this_sentence'
    assert first['selection'] == selection_binding(current, [51])
    return dict(reports=rows, finite_evidence_reused_without_claiming_new_execution=True,
        first_sentence_review_preserved=True, first_sentence_nonblank_characters=108)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    pieces = [
        (126, 137, ['r2ef', 'r2ck'], '第一文と同じ各人について、その人自身の未成熟を指す。'),
        (137, 143, ['r2ej', 'r2el'], '愛着の取得だけを焦点にした期待比較を帰属する。'),
        (143, 157, ['r2ck', 'r2eg'], '愛着を得て、現在保持している。'),
        (157, 166, ['r2ee', 'r2ei'], '同じ各人について愛着と不能・原因を併記する。'),
        (166, 179, ['r2ef', 'r2cf'], '現在の局面の基準に限定し、将来の回復や永続を決めない。'),
        (179, 188, ['r2en', 'r2eo', 'hzxu'], '現在の不能だけを確かな内容として述べる。'),
        (188, 241, ['r2cf', 'bm'], '自分の理解力の使用について、現在の基盤と通常機会での評価済みの不能。'),
        (241, 292, ['h3', 'r2cg', 'hzie'], '過去の試行の許容不在が、同じ人の現在の不能へ寄与する。'),
    ]
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, FIRST, IMAGE, RESTORED_FROM}
    paths.update('reports/' + name + '-v1.json' for name in COMPONENTS)
    return dict(status='second_sentence_reviewed_under_explicit_reading', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[126, 292], text=unit['text'][126:292]),
        clauses=[dict(range=[a, b], text=unit['text'][a:b], definitions=roots, reading=meaning) for a, b, roots, meaning in pieces],
        selection=selection_binding(catalog(), [11, 12]), decision='equivalent_under_stated_reading_for_this_sentence',
        references=[
            dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20', use='第二文の全文、代名詞と接続、時間限定と因果の範囲を照合。'),
            dict(url='https://www.duden.de/rechtschreibung/wirklich_tatsaechlich_eigentlich', title='Duden wirklich (Adverb)', accessed='2026-10-20', use='確認・強調の副詞用法を比較する。現代の説明から歴史的語義の唯一性を導かない。'),
            dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_5_1_1450', title='Adelung: Vor', accessed='2026-10-20', use='vor der Handを現在についての表現とする項目を照合。'),
        ], original_page=dict(path=IMAGE, visually_inspected=True, page=483),
        interpretation_limits=LIMITS, revised_statement_indices=[11], whole_sentence_semantically_verified=True,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=139,
        preserved_first_sentence_characters=108, paragraph_reviewed_sentence_characters=247,
        old_reformulation=dict(statement=10, symbol='ho2', node='hk2', belongs_to='third_sentence', preserved=True),
        restoration=dict(document=RESTORED_FROM, original_indices=[11, 12], current_indices=[52, 53],
            symbols=['h2c', 'h3b'], belongs_to=['third_sentence', 'fourth_sentence'],
            correction='前版で第二文の部分帰属と取り違えて置換した別文の記述を復元する。原文の新しい範囲の記述や、その二文の意味確認とは数えない。'),
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-2] == old.document['declarations']
    assert len(new.document['statements']) == 54 and len(old.document['statements']) == 52
    assert [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b] == [11]
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert set(new.entries) - set(old.entries) == set(MEANINGS)
    assert new.document['statements'][10]['body']['symbol'] == 'ho2'
    original = parse((ROOT / RESTORED_FROM).read_text(encoding='utf-8'))
    restored = original['statements'][11:13]
    assert [s['body']['symbol'] for s in restored] == ['h2c', 'h3b']
    assert new.document['statements'][52:] == restored
    for statement in restored:
        assert new.document['statements'].count(statement) == 1
    assert closure(original, ['h2c', 'h3b']) == closure(new.document, ['h2c', 'h3b'])
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        review = read(path); validate_hashes(ROOT, review['source_sha256'])
        ids = [s['index'] for s in review['selection']['statements']]
        assert 11 not in ids and review['selection'] == selection_binding(old, ids) == selection_binding(new, ids)
    assert len(read(INDEX)['works']['kant-1784']['reviews']) == 12
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    record = reading(); assert record == read(AUDIT); validate_hashes(ROOT, record['source_sha256'])
    clauses = record['clauses']; assert clauses[0]['range'][0] == 126 and clauses[-1]['range'][1] == 292
    assert all(a['range'][1] == b['range'][0] for a, b in zip(clauses, clauses[1:]))
    assert ''.join(c['text'] for c in clauses) == record['source']['text']
    assert sum(not c.isspace() for c in record['source']['text']) == 139
    assert all(set(c['definitions']) <= set(record['selection']['dependencies']) for c in clauses)
    return dict(new_definitions=2, new_primitives=0, preserved_statements=51, revised_statement_indices=[11],
        authored_statements=54, restored_statement_indices=[52, 53], restored_original_indices=[11, 12],
        restoration_source=RESTORED_FROM, preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_first_sentence_characters=108, reviewed_second_sentence_characters=139,
        paragraph_reviewed_sentence_characters=247, source_partition_parts=8, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('capacity', capacity_checks), ('discourse', discourse_checks), ('reused', reused_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_confirmed_incapacity.py', 'scripts/check_confirmed_incapacity.py', 'scripts/register_confirmed_incapacity.py',
        'tests/test_confirmed_incapacity.py', 'scripts/check_affection_sentence.py', 'scripts/check_current_deprivation.py',
        'scripts/check_exercise_capacity.py', 'scripts/check_standing_ability.py', 'scripts/compose_grounded_step.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/check_attributed_focus.py',
        'noema/constructed.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    for name in COMPONENTS: paths.update(read('reports/' + name + '-v1.json')['source_sha256'])
    return dict(status='whole_second_sentence_reviewed_under_explicit_reading', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        review_decision=record['decision'], reviewer='assistant_review', whole_sentence_semantically_verified=True,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=139, preserved_first_sentence_characters=108,
        paragraph_reviewed_sentence_characters=247, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
