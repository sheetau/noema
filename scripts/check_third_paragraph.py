"""Check final connections and bind an explicit, separately authored paragraph review."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes, REQUIREMENTS
from noema.script import transcribe
from scripts.compose_third_paragraph import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, SELECTION, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_attributed_focus import unwrap
from scripts.check_learned_familiarity import source_model

INDEX = 'data/semantic-review-index-v116.json'
AUDIT = 'data/fifth-sentence-reading-v1.json'
PARAGRAPH = 'data/third-paragraph-reading-v1.json'
REVIEW = 'data/third-paragraph-review-v1.json'
REPORT = 'reports/third-paragraph-v1.json'
DOC = 'docs/third-paragraph-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGES = ['artifacts/first-cause-reading-v1/page-482.jpg',
          'artifacts/future-dissemination-reading-v1/page-483.jpg']
SENTENCES = [('data/nature-sentence-reading-v1.json', [51]),
             ('data/confirmed-incapacity-reading-v1.json', [11, 12]),
             ('data/fetters-sentence-reading-v1.json', [10, 52]),
             ('data/fourth-sentence-reading-v1.json', [13, 53])]
PRIOR = ['reports/fifth-sentence-scope-v1.json', 'reports/reliable-course-v1.json',
         'reports/self-formed-course-v1.json', 'reports/fourth-sentence-v1.json']
REASONS = [
    '固定したu0010の全809文字・691非空白文字を対象に、原刊482頁末尾から483頁の段落末まで再読した。五文と句読点を含む全非空白位置を対応させ、原刊のwikkeln・schmalesten等の綴りを転記のまま保持する。数式はない。',
    '困難さ、本性に近い状態への変化、愛着の取得、現在の不能と許容不在の因果、無吟味な使用と言い直し、継続使用時の持続、除去の仮定と不慣れによる不確かな遂行、少数者の自立と確かな活動への自己形成の因果を順に確認した。否定・量化・時間・程度・限定・譲歩を各記録へ対応させた。',
    '先頭四文の同じ本人と未成熟、規定・定型表現と足枷、自由な活動種類への照応を保持する。第五文の関係代名詞・所有・再帰は同じ成功者へ束縛し、比較母集団は前半の対象者を含む範囲として接続する。成功者全員を現在不能だとする集合の同一視はしない。',
    'alsoとDaherは著者による推論提示であり、論理的導出の証明ではない。主張と仮定、合理的使用から誤用への言い直し、尺度背景と譲歩、身体的な足枷・跳躍・解放・歩行の描写を区別する。引用された身体内容や人数を現実の事実として実行しない。',
    '五文を通読して、各人・ほとんど・取得・現在・実際・一度も許さない・むしろ・持続・仮定・最小・のみ・理由・同種・少数・自己・達成・それでもの関係と範囲を確認した。縄の巻き方、唯一原因、永久の成功、全般的な無誤謬性、他者の援助の全面禁止を加えない。',
    '公開された能力・活動・因果・許容・種類・内的構成・判断・身体拘束・数量・帰属の意味規約を確認した。自己形成はh4mとh4nをh4oで合成する明示した読み、確かな歩みは理由支持と有効な通常比較による遂行の読みである。原語の綴りや未説明の文単位演算子を内容の代用にしていない。',
    '原文と原刊の読解、五文の判断、今回の母集団・除去・帰属の対照例、前版の数量・活動・因果検査の依存保存、記法往復を区別して示す。有限テストから意味一致を自動推定しない。アシスタントによる明示した読みの判断であり、独立した査読ではない。',
    '離脱の困難と内的定着から、愛着・不能・機械的使用、除去しても不確かな活動、少数者の自己形成による克服までを一つの段落として再読した。以上の読みの下で未処理の段落内容はないと判断する。他の解釈・語感や後続段落、理系論文の完成に判断を広げない。',
]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, extra, boundaries=()):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc):
    return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


@lru_cache(None)
def population_checks():
    doc = fixture(['r2kp'], 'r zcontext[] d.q[k r2kp[k zcontext[]]].')
    people, scenes = ('one', 'two', 'success', 'node'), ('text', 'other')
    def model(first, counted):
        return dict(aa=lambda p: p != 'node', wh=lambda: 'text', hzzq=lambda: 'node',
                    zcontext=lambda: 'text',
                    hzzn=lambda n, p, c: (n, c) == ('node', 'text') and p in first,
                    h4i=lambda p, c: p in counted and c == 'text')
    cases = 0
    for bits in product((False, True), repeat=6):
        first = {p for p, yes in zip(people[:3], bits[:3]) if yes}
        counted = {p for p, yes in zip(people[:3], bits[3:]) if yes}
        assert evaluate(doc, model(first, counted), people, scenes, True) == [first <= counted]
        cases += 1
    assert evaluate(doc, model({'one', 'two'}, set(people[:3])), people, scenes, True) == [True]
    assert evaluate(doc, model({'one', 'two'}, {'success'}), people, scenes, True) == [False]
    for missing in ('hzzn', 'h4i', 'aa'):
        values = model({'one'}, {'one', 'success'})
        values[missing] = unknown
        try:
            evaluate(doc, values, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(subset_combinations=cases, broader_population_allowed=True,
                unrelated_success_only_sample_rejected=True, unknown_inputs_refused=3,
                current_incapacity_not_imposed_on_all_successes=True)


@lru_cache(None)
def release_checks():
    doc = fixture(['h3n'], 'r za[] a.r zb[] d.q[t[k h3n[k za[]]][k zb[]]].')
    people = ('person', 'shackle', 'release', 'limb', 'movement', 'small', 'jump', 'experience', 'other')
    scenes = ('before', 'case', 'anchor')
    rows = {}
    for variant in ('baseline', 'still_bound', 'invalid_history', 'other_agent', 'no_cause', 'no_reference'):
        values = source_model(doc, variant)
        if variant == 'other_agent':
            values['df'] = lambda who, process, point: (who, process, point) == ('other', 'release', 'case')
        if variant == 'no_cause':
            values['h2q'] = lambda *args: False
        if variant == 'no_reference':
            values['h2s'] = lambda *args: False
        actual = evaluate(doc, values, people, scenes, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    return dict(cases=rows, native_reused_self_release_executed=True,
                removal_requires_agent_change_and_cause=True)


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2kt', 'r2ko'], 'q[k r2kt[]].q[k r2ko[]].', ('r2gi',))
    people, scenes = ('author', 'condition', 'reason', 'conclusion', 'concession'), ('text',)
    def model(variant='baseline'):
        values = unknowns(doc)
        values.update(wa=lambda: 'author', wh=lambda: 'text', h3a=lambda: 'condition',
                      h3s=lambda: 'reason', h5t=lambda: 'conclusion', h222d=lambda: 'concession',
                      r2gi=lambda: variant != 'missing_referents')
        fg = dict(kind='call', symbol='r2kk' if variant == 'old_population_content' else 'r2kq', arguments=[])
        bg = dict(kind='call', symbol='r2kr', arguments=[])
        values.update(
            hznreport=lambda n, a, d, scope, c: (n, a, scope, c) == ('conclusion', 'author', 'conclusion', 'text') and unwrap(d) == fg,
            hzrbgreport=lambda n, a, f, b, fs, bs, c: (n, a, fs, bs, c) == ('conclusion', 'author', 'conclusion', 'concession', 'text')
                and unwrap(f) == fg and unwrap(b) == bg,
            ud=lambda a, premises, n, c: (a, n, c) == ('author', 'conclusion', 'text') and
                {p for p in people if premises(p)} == {'condition', 'reason'},
            ue=lambda first, last, c: (first, last, c) == ('reason', 'conclusion', 'text'),
            qa=lambda n, a, target, depiction, c: (n, a, symbol(target), symbol(depiction), c) ==
                ('conclusion', 'reason' if variant == 'wrong_author' else 'author',
                 'h3n' if variant == 'swapped_target' else 'h4q', 'h3n', 'text'))
        return values
    rows = {}
    for variant, expected in [('baseline', [True, True]), ('old_population_content', [False, True]),
                              ('missing_referents', [True, False]), ('wrong_author', [True, False]),
                              ('swapped_target', [True, False])]:
        actual = evaluate(doc, model(variant), people, scenes, True)
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(cases=rows, world_and_bodily_contents_not_executed=True,
                prior_referent_mapping_is_explicit_boundary=True)


def unit():
    return next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')


def fifth_reading():
    source = unit()
    parts = [
        ('Daher ', ['r2kt', 'ud', 'ue'], '第四文の主節と理由からの結論として同じ著者へ帰属する。'),
        ('giebt es nur Wenige, ', ['r2kp', 'r2kk', 'r2kf', 'r2ke'], '前半の対象者を含む全比較母集団に、一人以上の少数の該当者がいて、数量代替を排除する。'),
        ('denen es gelungen ist, ', ['r2kc', 'r2kb', 'rct'], '同じ各該当者に基準時までの達成と確かな活動がある。'),
        ('durch eigene Bearbeitung ihres Geistes ', ['h4o', 'h4m', 'h4n', 'h4p', 'rqqu'], '本人の精神への同じ自己活動が自立を生じさせ、確かな活動にも寄与する。'),
        ('sich aus der Unmündigkeit heraus zu wikkeln, ', ['h4q', 'r2ko', 'h3n'], '同じ本人の自立達成を、自ら拘束を取り除く解放の像へ対応させる。'),
        ('und dennoch ', ['r2kg', 'r2kh', 'r2kr'], '実際の該当者について、自立を認めた通常予想と両成果との対比を背景として帰属する。'),
        ('einen sicheren Gang zu thun.', ['r2ji', 'r2jh', 'r2jy', 'h4z'], '同じ人の確かな知的活動と全過程の身体制御を持つ歩行を非字義的に対応させる。'),
    ]
    position, clauses = 635, []
    for text, definitions, reading in parts:
        assert source['text'][position:position + len(text)] == text
        clauses.append(dict(range=[position, position + len(text)], text=text,
                            definitions=definitions, reading=reading))
        position += len(text)
    assert position == 809
    paths = {FULL, BASIS, DOC, INVENTORY, *IMAGES, *PRIOR}
    return dict(status='fifth_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=source['id'], unit_sha256=source['text_sha256'], range=[635, 809],
                            text=source['text'][635:]), clauses=clauses,
                selection=selection_binding(catalog(), [14, 15, 54]),
                decision='equivalent_under_stated_reading_for_this_sentence',
                interpretation_limits=LIMITS,
                references=[
                    dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036',
                         accessed='2026-10-20', use='第五文と段落全体の原文・前後関係を再読。'),
                    dict(url='https://mateo.uni-mannheim.de/camenaref/kirsch/kirsch1/p1/Kirsch_cornucopiae_p1_246_elentesco.html',
                         title='Kirsch, Cornucopiae, 1774, Eluctatus / Eluctor, p. 1011',
                         accessed='2026-10-20', use='解放や障害から抜け出す読みの語彙的比較。カントの唯一の意図の証明ではない。')],
                original_pages=[dict(path=p, visually_inspected=True) for p in IMAGES],
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                new_verified_sentence_characters=147, paragraph_reviewed_sentence_characters=691,
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def paragraph_reading():
    source = unit()
    paths = {AUDIT, DOC, INVENTORY, FULL, BASIS, *IMAGES, *(p for p, _ in SENTENCES)}
    return dict(status='third_paragraph_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=source['id'], unit_sha256=source['text_sha256'],
                            range=[0, 809], text=source['text']),
                selection=selection_binding(catalog(), SELECTION),
                sentence_readings=[p for p, _ in SENTENCES] + [AUDIT],
                interpretation=LIMITS,
                requirements=[dict(id=k, decision='satisfied', reason=v) for k, v in zip(REQUIREMENTS, REASONS, strict=True)],
                decision='equivalent_under_stated_reading', unresolved=[],
                source_nonblank_characters=691, new_verified_sentence_characters=147,
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-6] == old.document['declarations']
    assert all(new.entries[n] == e for n, e in old.entries.items())
    assert len(new.document['statements']) == 55
    assert [i for i, (a, b) in enumerate(zip(old.document['statements'], new.document['statements'])) if a != b] == [15]
    reviews = load_reviews(ROOT, INDEX)['works']
    for row in reviews['kant-1784']:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in SENTENCES:
        record = read(path)
        validate_hashes(ROOT, record['source_sha256'])
        assert record['selection'] == selection_binding(new, indices)
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(added_definitions=6, added_primitives=0, authored_statements=55,
                revised_statement_indices=[15], added_statement_indices=[54],
                preserved_whole_unit_reviews=len(reviews['kant-1784']),
                preserved_reviewed_sentence_characters=544, roundtrips=True)


@lru_cache(None)
def reading_checks():
    assert read(AUDIT) == fifth_reading()
    assert read(PARAGRAPH) == paragraph_reading()
    source = unit()
    covered = set()
    for path in [p for p, _ in SENTENCES] + [AUDIT]:
        record = read(path)
        span = record['source']['range']
        assert record['source']['text'] == source['text'][span[0]:span[1]]
        assert record['source']['unit_sha256'] == source['text_sha256']
        covered.update(range(*span))
    assert all(i in covered for i, c in enumerate(source['text']) if not c.isspace())
    assert sum(not c.isspace() for c in source['text']) == 691
    fifth = read(AUDIT)
    assert ''.join(c['text'] for c in fifth['clauses']) == fifth['source']['text']
    assert all(set(c['definitions']) <= set(fifth['selection']['dependencies']) for c in fifth['clauses'])
    assert sum(not c.isspace() for c in fifth['source']['text']) == 147
    return dict(paragraph_nonblank_characters=691, fifth_sentence_nonblank_characters=147,
                source_sentences=5, all_nonblank_positions_covered=True,
                original_pages_visually_reread=2, reviewer_judgment_separate_from_tests=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(fifth_reading()))
    write_exact(ROOT / PARAGRAPH, encoded(paragraph_reading()))


def build_report():
    results = {}
    for name, fn in [('population', population_checks), ('release', release_checks),
                     ('attribution', attribution_checks), ('structure', structure_checks), ('reading', reading_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, PARAGRAPH, DOC, INVENTORY, *IMAGES, *PRIOR,
        'scripts/compose_third_paragraph.py', 'scripts/check_third_paragraph.py',
        'tests/test_third_paragraph.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py', 'scripts/check_attributed_focus.py', 'scripts/check_learned_familiarity.py',
    } | {p for p, _ in SENTENCES}
    record = read(AUDIT)
    return dict(status='third_paragraph_explicit_reading_and_formal_connections_checked', document=FULL, **results,
                alignment=dict(**record['source'], definitions=['r2ko', 'r2kp', 'r2kt'],
                               status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, new_verified_sentence_characters=147,
                paragraph_reviewed_sentence_characters=691,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                whole_unit_registration='separate_explicit_review_required',
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def review():
    """Bind the authored paragraph judgment only after its report is saved."""
    record = read(PARAGRAPH)
    report = read(REPORT)
    validate_hashes(ROOT, report['source_sha256'])
    evidence = dict(source_reading=[PARAGRAPH, AUDIT] + [p for p, _ in SENTENCES],
                    formal_checks=[REPORT] + PRIOR, semantic_reading=[DOC])
    pins = dict(catalog().source_sha256)
    for path in {FULL, BASIS, ANNOTATIONS, INVENTORY} | {p for paths in evidence.values() for p in paths}:
        pins[path] = digest((ROOT / path).read_bytes())
        if path.endswith('.json'):
            for child, sha in read(path).get('source_sha256', {}).items():
                assert child not in pins or pins[child] == sha
                pins[child] = sha
    validate_hashes(ROOT, pins)
    return dict(schema_version='noema-semantic-review-1', work='kant-1784', unit='kant-1784:u0010',
                reviewer='assistant_review', decision=record['decision'],
                document=FULL, meaning_basis=BASIS, identifier_annotations=ANNOTATIONS,
                source=dict(inventory=INVENTORY, unit_sha256=unit()['text_sha256'], text=unit()['text'],
                            range=[0, len(unit()['text'])], math=[]),
                selection=record['selection'], interpretation=record['interpretation'],
                limits=['明示した読みの下でのアシスタントの判断。独立査読や同義性の自動証明ではない。',
                        '原文の全語義・韻律・全歴史的含意の同時復元ではない。各文の明示した解釈上の限界を継承する。',
                        '因果や数量の現実的な正しさを証明する判断ではない。後続段落とアインシュタイン論文は未完。'],
                unresolved=[], requirements=record['requirements'], evidence=evidence, source_sha256=pins)
