"""Review the final sentence as a whole; test attribution without asserting it true."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.check_defeasible_learning import catalog, ROOT, FULL, BASIS, INVENTORY
from scripts.compose_defeasible_learning import ANNOTATIONS, closure, reindex_binding
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_reasoned_concession as discourse

INDEX = 'data/semantic-review-index-v86.json'
CORE = 'examples/v016/deterrence-sentence-core.noema'
AUDIT = 'data/deterrence-sentence-reading-v1.json'
REPORT = 'reports/deterrence-sentence-v1.json'
DOC = 'docs/deterrence-sentence-v1.md'
SELECTION = [37, 38, 49, 50]
PRECEDING = ('first-cause', 'convenience', 'delegation', 'payment', 'guardian', 'guarded-walking')
COMPONENTS = {
    'defeasible-learning': ['r2by', 'r2bz', 'r2ca', 'r2cc', 'r2cd', 'r2ce'],
    'fear-proneness': ['r2bp', 'r2bq', 'r2br', 'r2bs', 'r2bt', 'r2bv'],
    'generalized-deterrence': ['r2bh', 'r2bi'],
    'recognized-example': ['gr', 'r2bb', 'r2bc'],
    'walking-acquisition': ['fq', 'r2ax', 'hzun', 'hzuo', 'hzup'],
}
CLAUSES = [
    ('danger', 'Nun ist diese Gefahr zwar eben so groß nicht, ', ['e3', 'e4'],
     'dieseとsoを、前文の同じ対象者・自立的活動・非常に高い危険の基準へ戻す。不利益の可能性は残り、その高い基準は満たさない。危険ゼロとはしない。'),
    ('learning', 'denn sie würden durch einigemahl Fallen wohl endlich gehen lernen; ', ['r2bz', 'r2ca', 'r2cc', 'r2cd', 'hzup'],
     '同じ対象者が試みると仮定した将来の経過で、少数回の不成功経験が能力の取得に寄与するという著者の見込みを、低い危険評価の理由とする。仮定範囲を結果で選別せず、認識的に優先する経過での取得を述べる。転倒と歩行学習は同じ本人・経験・活動に対応する身体像。endlichは経験の後の到達点と読み、長期間や成功保証を足さない。'),
    ('proneness', 'allein ein Beispiel von der Art macht doch schüchtern, ', ['gr', 'r2bq', 'r2br', 'r2bs', 'r2bc'],
     '同種の先行する不成功例を認識する事例が、同じ人の恐れやすさに因果的に寄与するという一般化。経験者と認識者は別でもよい。通常の比較状況と通常の事例を区別し、現在の恐れ、勇気の欠如、恒久的性格は必須としない。例を認識する節にも転倒像を明示する。'),
    ('avoidance', 'und schrekt gemeiniglich von allen ferneren Versuchen ab.', ['gt', 'r2bi', 'r2bt', 'r2bv', 'r2ce'],
     '同じ比較状況で例を認識する事例全体を分母とし、通常は、その本人が関連する後続の試み全てを恐れに基づき避けると述べる。分母から萎縮の例外を除かない。文脈の有限な等重み事例範囲で過半数と追加の割合基準を満たす読みを採る。単なる非実行や全生活の行為を意味しない。zwar・allein・dochは低い危険評価と反応の間の反期待として、同じ著者と文脈に帰属する。'),
]
LIMITS = [
    '固定した原文に対するアシスタントの読解判断。独立査読でも、有限モデルの合格から得た意味同値の自動証明でもない。',
    '実際に認識される先行例、局所的な恐れやすさ、文脈上の有限・等重みの比較事例という読みを採る。架空の例を含む全用法、無限母集団の測度、全ての語感を同時には表していない。',
    '見込みの背景、通常性、危険・回数・割合の文脈基準を明示的入力に残す。著者の因果・頻度・見込みが現実に正しいという判断ではない。',
    '認知・身体・因果など基本関係の説明の拡充と、二作品の残りの読解は継続課題。この一文の確認を任意の内容の表現率へ一般化しない。',
]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def input_paths():
    return set(catalog().source_sha256) | {
        INDEX, FULL, BASIS, ANNOTATIONS, CORE, INVENTORY,
        'artifacts/publication-header-v1/page-481.jpg',
        'artifacts/first-cause-reading-v1/page-482.jpg',
        'reports/guarded-walking-reading-v1.json',
    } | {'reports/' + n + '-v1.json' for n in COMPONENTS} | {
        'data/' + n + '-reading-v1.json' for n in (*PRECEDING, *COMPONENTS)}


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0009')
    cursor = 1213
    clauses = []
    for name, text, definitions, interpretation in CLAUSES:
        end = cursor + len(text)
        assert unit['text'][cursor:end] == text
        clauses.append(dict(id=name, range=[cursor, end], text=text, definitions=definitions,
                            interpretation_ja=interpretation, status='reviewed_under_stated_reading'))
        cursor = end
    assert cursor == len(unit['text']) == 1438
    return dict(status='deterrence_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
        decision='equivalent_under_stated_reading_for_this_sentence', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[1213, 1438],
                    text=unit['text'][1213:], nonblank_characters=190), clauses=clauses,
        selection=selection_binding(catalog(), SELECTION),
        source_review='原刊481・482頁を目視で再読。末尾一文の理由節後のセミコロンと、萎縮・回避の接続を確認。固定電子転記の表記差は意味の差として補わない。',
        interpretation_limits=LIMITS, whole_sentence_semantically_verified=True,
        whole_unit_semantically_verified=False, new_verified_sentence_characters=190,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(input_paths())})


@lru_cache(None)
def core():
    d = deepcopy(catalog().document)
    d['statements'] = [d['statements'][i] for i in SELECTION]
    d['declarations'] = closure(d, _references(d['statements']))
    return d


def model(bits=(True,) * 6, depictions=(True,) * 3, variant='baseline'):
    v = discourse.source_model(core(), bits, variant)
    same = lambda a, s: (a, s) == ('other' if variant == 'other_author' else 'author',
                                  'elsewhere' if variant == 'other_context' else 'anchor')
    def claim(node, author, content, scene):
        names = {'low': ('e4', bits[0]), 'learn': ('r2cc', bits[1]), 'outcome': ('r2bt', bits[2])}
        if node not in names:
            return False
        name, flag = names[node]
        if variant == 'swapped_claims' and node in ('low', 'learn'):
            name = 'r2cc' if node == 'low' else 'e4'
        return same(author, scene) and flag and json.loads(content.syntax) == dict(kind='call', symbol=name, arguments=[])
    def report(node, author, content, scope, scene):
        return bits[4] and same(author, scene) and (node, scope) == (
            'outcome', 'other' if variant == 'other_foreground_scope' else 'outcome') and discourse.unwrap(content) == dict(kind='call', symbol='r2bt', arguments=[])
    def background(node, author, fg, bg, fs, bs, scene):
        names = ('r2bv', 'r2bt') if variant == 'swapped_background' else ('r2bt', 'r2bv')
        return bits[5] and same(author, scene) and (node, fs, bs) == (
            'other' if variant == 'other_node' else 'outcome', 'outcome',
            'other' if variant == 'other_background_scope' else 'contrast') and [discourse.unwrap(fg), discourse.unwrap(bg)] == [dict(kind='call', symbol=n, arguments=[]) for n in names]
    def falling(node, author, target, body, scene):
        return depictions[0] and same(author, scene) and (node, symbol(target), symbol(body)) == (
            'outcome' if variant == 'fall_in_wrong_clause' else 'learn', 'hzun', 'hzuo')
    def depiction(node, author, target, body, scene):
        wanted = [('learn', 'r2bz', 'r2ca'), ('outcome', 'gr', 'r2bb')]
        if variant == 'swapped_depiction_clauses':
            wanted = [('outcome', 'r2bz', 'r2ca'), ('learn', 'gr', 'r2bb')]
        if variant == 'reversed_depiction':
            wanted = [(n, b, t) for n, t, b in wanted]
        if variant == 'obsolete_prospect':
            wanted[0] = ('learn', 'fr', 'r2ay')
        return same(author, scene) and any(flag and (node, symbol(target), symbol(body)) == item
            for flag, item in zip(depictions[1:], wanted))
    v.update(uc=claim, hznreport=report, hzrbgreport=background, rbt=falling, qa=depiction)
    return v


@lru_cache(None)
def interface_checks():
    d = core()
    run = lambda v: evaluate(d, v, discourse.DOMAIN, discourse.SCENES)
    for bits in product((False, True), repeat=6):
        assert run(model(bits)) == [all(bits), True, True, True], bits
    for bits in product((False, True), repeat=3):
        assert run(model(depictions=bits)) == [True, *bits], bits
    rows = {}
    ordinary = ('swapped_claims', 'reversed_reason', 'extra_premise', 'missing_prior_link',
        'reversed_learning', 'both_directions', 'other_foreground_scope', 'other_background_scope',
        'other_node', 'swapped_background')
    expected = {n: [False, True, True, True] for n in ordinary}
    expected.update(baseline=[True] * 4, other_author=[False] * 4, other_context=[False] * 4,
        fall_in_wrong_clause=[True, False, True, True], swapped_depiction_clauses=[True, True, False, False],
        reversed_depiction=[True, True, False, False], obsolete_prospect=[True, True, False, True])
    for name, wanted in expected.items():
        actual = run(model(variant=name))
        assert actual == wanted, (name, actual, wanted)
        rows[name] = actual
    for name in ('uc', 'ud', 'ue', 'hznreport', 'hzrbgreport', 'rbt', 'qa'):
        v = model(); v[name] = unknown
        try:
            run(v)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(attribution_combinations=64, independent_depiction_combinations=8, contrasts=rows,
        unknown_inputs_refused=7, current_four_statements_executed=True,
        world_contents_and_expectation_truth_unknown=True, uncached_evaluation=True)


@lru_cache(None)
def reused_checks():
    current = catalog(); rows = {}
    for name, roots in COMPONENTS.items():
        path = 'reports/' + name + '-v1.json'; report = read(path)
        validate_hashes(ROOT, report['source_sha256'])
        old = parse((ROOT / report['document']).read_text(encoding='utf-8'))
        assert closure(old, roots) == closure(current.document, roots)
        dependencies = {d['name'] for d in closure(current.document, roots)}
        for n in dependencies:
            assert current.entries[n]['meaning_basis'] in report['source_sha256'], (name, n)
        rows[path] = dict(roots=roots, dependency_count=len(dependencies),
                         declarations_and_meaning_sources_unchanged=True)
    return dict(reports=rows, finite_evidence_reused_without_claiming_new_execution=True)


@lru_cache(None)
def preceding_checks():
    report = read('reports/guarded-walking-reading-v1.json')
    validate_hashes(ROOT, report['source_sha256'])
    rows = {}; total = 0
    for name in PRECEDING:
        path = 'data/' + name + '-reading-v1.json'; r = read(path)
        validate_hashes(ROOT, r['source_sha256'])
        assert r['decision'] == 'equivalent_under_stated_reading_for_this_sentence'
        before = r['selection'] if name == 'guarded-walking' else report['preceding']['reviews'][path]['current_selection']
        binding = reindex_binding(before)
        assert binding == selection_binding(catalog(), [s['index'] for s in binding['statements']])
        rows[path] = dict(current_selection=binding, range=r['source']['range'],
                         nonblank_characters=r['source']['nonblank_characters'])
        total += r['source']['nonblank_characters']
    assert total == 1021
    return dict(reviews=rows, reviewed_nonblank_characters=total, meaning_and_statements_preserved=True)


@lru_cache(None)
def structure_checks():
    c = catalog(); r = reading()
    assert r == read(AUDIT); validate_hashes(ROOT, r['source_sha256'])
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == r['source']['unit'])
    assert digest(unit['text'].encode('utf-8')) == unit['text_sha256'] == r['source']['unit_sha256']
    assert sum(not ch.isspace() for ch in r['source']['text']) == 190
    assert all(set(cl['definitions']) <= set(r['selection']['dependencies']) for cl in r['clauses'])
    assert parse((ROOT / CORE).read_text(encoding='utf-8')) == core()
    for style in ('compact', 'full'):
        text = format_graph(core(), style)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == core()
    covered = set(range(1213, 1438))
    for row in preceding_checks()['reviews'].values():
        covered.update(range(*row['range']))
    assert all(i in covered for i, ch in enumerate(unit['text']) if not ch.isspace())
    index = read(INDEX)
    assert index['works']['kant-1784']['document'] == FULL
    for p in index['works']['kant-1784']['reviews']:
        review = read(p); validate_hashes(ROOT, review['source_sha256'])
        assert review['selection'] == selection_binding(c, [s['index'] for s in review['selection']['statements']])
    assert len(index['works']['kant-1784']['reviews']) == 11
    return dict(clause_partition=4, unchanged_statements=51, new_definitions=0, new_primitives=0,
        preserved_unit_reviews=11, reviewed_sentence_characters=190, paragraph_sentence_characters=1211,
        nonblank_source_partition_complete=True, roundtrips=True, semantic_equivalence_automatically_proved=False)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / CORE, format_graph(core(), 'compact').rstrip() + '\n')
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('interfaces', interface_checks), ('reused', reused_checks),
                     ('preceding', preceding_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading(); paths = input_paths() | {AUDIT, DOC, 'scripts/check_deterrence_sentence.py',
        'tests/test_deterrence_sentence.py', 'scripts/register_kant_second_paragraph.py',
        'scripts/check_defeasible_learning.py', 'scripts/compose_defeasible_learning.py',
        'scripts/check_reasoned_concession.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py', 'noema/constructed.py', 'noema/constructed_semantics.py',
        'noema/semantic_reviews.py', 'noema/meaning_catalog.py', 'noema/script.py'}
    for path in input_paths():
        if path.endswith('.json'):
            paths.update(read(path).get('source_sha256', {}))
    return dict(status='whole_deterrence_sentence_reviewed_under_explicit_reading', document=FULL, **results,
        alignment=dict(**r['source'], definitions=['r2ce', 'hzup', 'r2cb', 'r2bc'], status='explicit_interpretive_annotation'),
        review_decision=r['decision'], reviewer='assistant_review', whole_sentence_semantically_verified=True,
        new_verified_sentence_characters=190, new_covered_characters=2,
        new_coverage_explanation='Previously uncovered comma at 1257 and semicolon at 1324; manuscript unchanged.',
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare()
    write_exact(ROOT / REPORT, encoded(build_report()))
