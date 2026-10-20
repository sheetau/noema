"""Record the full interpretive review and execute its integrated attribution."""
from copy import deepcopy
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from scripts.compose_prejudice_depictions import ROOT, FULL, BASIS, ANNOTATIONS, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_public_reversal import SENTENCES

INDEX = 'data/semantic-review-index-v135.json'
AUDIT = 'data/public-third-sentence-reading-v1.json'
REPORT = 'reports/public-third-sentence-v1.json'
DOC = 'docs/public-third-sentence-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGES = ['artifacts/future-dissemination-reading-v1/page-483.jpg',
          'artifacts/public-reversal-reading-v1/page-484.jpg']
PRIOR = ['reports/' + name + '-v1.json' for name in (
    'collective-retention', 'public-reversal', 'enlightenment-incapacity',
    'public-incitation', 'reversal-attribution', 'reversal-yoke',
    'reversal-focus', 'prejudice-effects', 'prejudice-claim',
    'prejudice-reason', 'prejudice-depictions')]

CLAUSES = [
    ('Besonders ist hiebei: ', ['r2nw', 'h224r'], '前二文の議論に関する特異な点として、同じ前半の内容を提示する。'),
    ('daß das Publikum, ', ['r2ng', 'r2nf', 'r2la', 'r2nd'], '同じ著者が、先行文と同じ公衆範囲・成員について内容を帰属する。'),
    ('welches zuvor ', ['r2ne', 'r2mr'], '同じ公衆の事例内で、先行作用は後の圧力開始より前である。'),
    ('von ihnen ', ['h223x', 'h223y', 'r2mp'], '先行作用を実際に担った文脈上の後見人たち。前文の自己思考者全員への同定は採らない。'),
    ('unter dieses Joch ', ['r2no', 'r2np', 'r2nh', 'bf', 'hzpk'], '前文の頚木を、同じ未成熟状態と同種の身体的拘束の描写として受ける。'),
    ('gebracht worden, ', ['r2mp', 'r2nc', 'r2ml'], '同じ共同行為が固定された全被作用者の未成熟の成立に寄与する。以前の自立を全員に要求しない。'),
    ('sie hernach ', ['r2mr', 'h223y'], '先行作用の同じ参加後見人全員が後の被強制者となる。別の人へ選び直さない。'),
    ('selbst ', ['r2nx', 'r2ns', 'r2nt'], '作用を受けた公衆自身が強制の担い手になることを、条件付きのまま取り立てる。'),
    ('zwingt ', ['r2mn', 'r2mm', 'r2ml', 'h223n'], '公衆に帰属する参加行為と、身体的制約または脅しによる強制、保持への実際の因果を要求する。'),
    ('darunter zu bleiben, ', ['r2mk', 'r2np', 'r2nh'], '同じ未成熟状態が正の保持期間全体に成立する。頚木の種類の照応も保持する。'),
    ('wenn es ', ['r2mr', 'r2mq'], '同じ公衆の扇動条件が成立するなら後の保持が成立する。強制の無条件化はしない。'),
    ('von einigen seiner Vormünder, ', ['r2mq', 'r2mu', 'r2m5'], '同じ公衆の後見役を担う異なる二人以上。先行後見人との重なりは許し、全員でないとは要求しない。'),
    ('die selbst ', ['r2nx', 'r2nu', 'r2nv'], '条件内の同じ扇動者全員について、本人の不能を取り立てる。全後見人へ広げない。'),
    ('aller Aufklärung unfähig sind, ', ['r2mt', 'up'], '固定した取得機会の全域で、自力・学習・助力を含む達成方法が利用できない。全世界の永久不能へ強めない。'),
    ('dazu ', ['r2nb', 'r2na', 'h224l'], '公衆が後見人を未成熟に保持する同じ予定圧力行為を指す。閉じた名前を元の行為と照合する。'),
    ('aufgewiegelt worden; ', ['r2na', 'r2mz', 'h223s', 'h223t', 'h223u'], '同じ後見人の働きかけの受領・理解・感情への訴えと、反抗的な気分・参加への構えに至る因果。後の実行そのものとは分ける。'),
    ('so schädlich ist es ', ['r2ou', 'r2ot', 'r2os', 'r2ov'], '前半の同じ条件付き内容を受け、同じ事例全体の害を高程度として評価する。個別の大損害・数値は補わない。'),
    ('Vorurtheile ', ['r2nz', 'r2oa', 'r2ob', 'h224w', 'h224x'], '十分に吟味しない意見を確立した原理として採用すること。意見の偽性とは同一視しない。'),
    ('zu pflanzen, ', ['r2pc', 'r2pd', 'r2ph', 'r2pa'], '同じ意見・受け手への採用生成を、生育を目的とする植え付けで非字義的に描く。'),
    ('weil ', ['r2ow', 'ud', 'ue'], '反作用の理由節から有害さの評価へ根拠を向け、前半・評価・理由の本文順を保持する。'),
    ('sie sich ', ['r2om', 'r2on', 'r2pl', 'r2pm'], '植え付けた同じ意見を反作用の要因とし、描写では応答主体とする。自傷の対象とは読まない。'),
    ('zuletzt ', ['r2oh', 'r2oi'], '同じ文脈上の経過の終点。世界全体の最後や最初の被害時は要求しない。'),
    ('an denen selbst ', ['r2oo', 'r2om', 'r2on'], '生み手本人またはその役割を継いだ人が、まさに害を受けることを取り立てる。'),
    ('rächen, ', ['r2oe', 'r2pk', 'r2pj', 'r2pm'], '偏見採用から本人側への害という対象内容を、意図を伴う応報の描写に結ぶ。'),
    ('die, oder deren Vorgänger, ', ['r2og', 'r2of', 'h225a'], '生み手が被害者本人である枝、または同じ実践の役割の先任者である枝の選言。血縁・単なる先行ではない。'),
    ('ihre Urheber gewesen sind.', ['r2ob', 'r2og', 'r2oj', 'r2ok'], '同じ意見の採用を先行時点に生じさせた人。全関連事例・対象者を量化し、世界最初の発明者とは限定しない。'),
]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def quoted(name, rank=3, kind='call'):
    return ('quote', rank, kind, name)


def normalized(value):
    if isinstance(value, str):
        return value
    if hasattr(value, 'syntax'):
        ast = json.loads(value.syntax)
        return ('quote', value.rank, ast['kind'], ast['symbol'])
    if hasattr(value, 'items'):
        return tuple(normalized(x) for x in value.items)
    raise AssertionError(type(value))


def expectations():
    q = quoted
    p = lambda n: quoted(n, 3, 'function_ref')
    p0 = lambda n: quoted(n, 0, 'function_ref')
    a, c = 'wa', 'hzp3'
    rows = [
        ('hznreport', ('h224m', a, q('r2nf'), 'h224m', c)),
        ('hznreport', ('h225s', a, q('r2ot'), 'h225s', c)),
        ('hznreport', ('h225o', a, q('r2ok'), 'h225o', c)),
        ('h224n', ('h224m', a, q('r2nf'), p('r2nm'), p('r2nl'), p('r2nn'), c)),
        ('h224n', ('h225y', a, q('r2ot'), p('r2pg'), p('r2pe'), p('r2pf'), c)),
        ('h224n', ('h226d', a, q('r2ok'), p('r2om'), p('r2on'), p('r2pl'), c)),
        ('h224p', ('h224o', 'hzpo', a, p0('bf'), p0('r2nh'), c)),
        ('h224p', ('h224q', 'h224o', a, p0('bf'), p0('r2nh'), c)),
        ('h224r', ('h224t', a, q('r2nf'), q('r2nf'), ('hzp4', 'hzp5'), c)),
        ('h224s', ('h224u', a, q('r2nf'), p('r2ns'), p('r2nt'), c)),
        ('h224s', ('h224v', a, q('r2nf'), p('r2nu'), p('r2nv'), c)),
        ('h224s', ('h225p', a, q('r2ok'), p('r2om'), p('r2on'), c)),
        ('h225r', ('h225s', a, q('r2ot'), p('r2os'), 'h224m', q('r2nf'), c)),
        ('ud', (a, ('h225o',), 'h225s', c)),
    ]
    rows += [('ue', (first, last, c)) for first, last in
             [('hzpo', 'h224o'), ('h224o', 'h224q'), ('h224m', 'h225s'), ('h225s', 'h225o')]]
    return rows


@lru_cache(None)
def attribution_checks():
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, ['r2pn']), statements=[])
    doc = parse(format_graph(doc, 'compact') + 'q[k r2pn[]].')
    constants = ('wa', 'hzp4', 'hzp5', 'hzpo', 'h224m', 'h224o', 'h224q',
                 'h224t', 'h224u', 'h224v', 'h225s', 'h225o', 'h225p', 'h225y', 'h226d')
    people, scenes = (*constants, 'other'), ('hzp3', 'other')
    expected = expectations()
    def model(omitted=None, wrong=None):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update({n: (lambda n=n: 'other' if n == wrong else n) for n in (*constants, 'hzp3')})
        seen = set()
        def checker(name):
            def check(*args):
                if name == 'ud':
                    args = (args[0], tuple(p for p in people if args[1](p)), *args[2:])
                    row = (name, args)
                else:
                    row = (name, tuple(normalized(a) for a in args))
                if row not in expected:
                    return False
                position = expected.index(row)
                seen.add(position)
                return position != omitted
            return check
        values.update({n: checker(n) for n, _ in expected})
        return values, seen
    values, seen = model()
    assert evaluate(doc, values, people, scenes, True) == [True]
    assert seen == set(range(len(expected)))
    for position in range(len(expected)):
        values, _ = model(omitted=position)
        assert evaluate(doc, values, people, scenes, True) == [False], expected[position]
    for name in (*constants, 'hzp3'):
        values, _ = model(wrong=name)
        assert evaluate(doc, values, people, scenes, True) == [False], name
    for name in sorted({n for n, _ in expected}):
        values, _ = model()
        values[name] = unknown
        try:
            evaluate(doc, values, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(native_integrated_root='r2pn', replaced_definitions=[],
                required_relations=len(expected), omitted_relations_refused=len(expected),
                wrong_source_references_refused=len(constants) + 1,
                unknown_attribution_relations_refused=len({n for n, _ in expected}),
                world_inputs_unknown_and_unexecuted=True,
                content_internals_covered_by_separate_pinned_local_reports=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    text, start, end = unit['text'], 449, 845
    position, clauses = start, []
    for phrase, definitions, interpretation in CLAUSES:
        assert text.startswith(phrase, position), (position, phrase)
        stop = position + len(phrase)
        clauses.append(dict(range=[position, stop], text=phrase,
                            definitions=definitions, reading=interpretation))
        position = stop
    assert position == end
    paths = {FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, INDEX, *IMAGES, *PRIOR, *[p for p, _ in SENTENCES]}
    return dict(status='public_third_sentence_reviewed_under_explicit_reading',
                reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[start, end], text=text[start:end]),
                clauses=clauses, selection=selection_binding(catalog(), [59]),
                interpretation_document=DOC,
                judgment='原刊と固定原文を通読し、各句の内容・参照・条件・量化・時間・程度・描写・提示を確認した。記録した読みの下で第三文に未処理項目はない。',
                unresolved_items_under_adopted_reading=[],
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=337, preserved_first_two_sentence_characters=382,
                combined_first_three_sentence_characters=719,
                facsimile=dict(artifacts=IMAGES, pages=[483, 484], visually_collated=True,
                               differences='長いsと行末分綴。auf- / gewiegeltは頁をまたぐ。固定本文は変更しない。'),
                primary_context='https://korpora.org/Kant/aa08/036.html',
                no_independent_review=True, semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def source_checks():
    record = read(AUDIT)
    assert record == reading()
    source = record['source']
    assert len(source['text']) == 396 and len(''.join(source['text'].split())) == 337
    assert ''.join(c['text'] for c in record['clauses']) == source['text']
    reachable = {d['name'] for d in closure(catalog().document, ['r2pn'])}
    for clause in record['clauses']:
        assert set(clause['definitions']) <= reachable, clause
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == source['unit'])
    assert digest(unit['text'].encode('utf-8')) == source['unit_sha256']
    validate_hashes(ROOT, record['source_sha256'])
    return dict(source_characters=396, reviewed_nonblank_characters=337,
                consecutive_clauses=len(CLAUSES), all_named_definitions_reachable=True,
                original_images_pinned=True, judgment_is_explicit_reading_not_automatic_test_inference=True)


@lru_cache(None)
def preservation_checks():
    new = catalog()
    assert len(new.document['statements']) == 60
    assert new.document['statements'][59] == dict(kind='assert', body=dict(kind='call', symbol='r2pn', arguments=[]))
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in SENTENCES:
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_sentence_characters=382,
                prior_local_reports_hash_valid=len(PRIOR), no_language_changes_for_review=True,
                whole_unit_count_not_increased=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('attribution', attribution_checks), ('source', source_checks),
                     ('preservation', preservation_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(catalog().source_sha256) | set(read(AUDIT)['source_sha256']) | {
        AUDIT, 'scripts/check_public_third_sentence.py', 'tests/test_public_third_sentence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/check_public_reversal.py'}
    return dict(status='third_sentence_reviewed_under_explicit_reading', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=337, combined_first_three_sentence_characters=719,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
