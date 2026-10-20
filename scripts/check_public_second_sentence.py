"""Bind the sentence review to actual witnesses, source roles and attribution."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_second_sentence import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, build, closure,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_self_formed_course import source_values, CONSTANTS, PEOPLE, SCENES

INDEX = 'data/semantic-review-index-v123.json'
AUDIT = 'data/public-second-sentence-reading-v1.json'
REPORT = 'reports/public-second-sentence-v1.json'
DOC = 'docs/public-second-sentence-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/future-dissemination-reading-v1/page-483.jpg'
LEXICAL = 'artifacts/public-second-sentence-reading-v1/haufen-fwb.html'
FIRST = 'data/public-first-sentence-reading-v1.json'
PRIOR = ['reports/guardian-forecast-v1.json', 'reports/dissemination-content-v1.json',
         'reports/dissemination-opportunities-v1.json', 'reports/yoke-depiction-v1.json',
         'reports/self-formed-course-v1.json']


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, text, boundaries=()):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + text)


def calls(node, name):
    result = []
    if isinstance(node, list):
        for x in node:
            result.extend(calls(x, name))
    elif isinstance(node, dict):
        if node.get('kind') == 'call' and node['symbol'] == name:
            result.append(node)
        for x in node.values():
            result.extend(calls(x, name))
    return result


def single(node, name):
    rows = calls(node, name)
    assert len(rows) == 1, (name, len(rows))
    return rows[0]


def variable(name):
    return dict(kind='variable', name=name)


def parameters(d):
    return [variable(p['name']) for p in d['parameters']]


def unbind(node):
    binders = []
    while node['kind'] == 'exists':
        binders.append(variable(node['variable']))
        node = node['body']
    return binders, node


def witness_chain(entries):
    """A checked syntactic certificate of the local existential introduction.

    This proves the shared role/witness connection, not the truth of the
    prediction or the equivalence of German and Noema.
    """
    declaration = lambda n: entries[n]['declaration']
    d = declaration('h4q')
    assert d['body']['kind'] == 'content'
    witnesses, claim = unbind(d['body']['body'])
    assert len(witnesses) == 3 and claim['kind'] == 'call' and claim['symbol'] == 'h4p'
    assert claim['arguments'] == parameters(d) + witnesses + [variable(d['body']['variable'])]
    d = declaration('hzod'); p = parameters(d)
    assert d['body']['kind'] == 'and'
    assert single(d, 'h4p') == d['body']['arguments'][0]
    assert single(d, 'h4p')['arguments'] == [p[i] for i in (0, 1, 2, 3, 5)]
    assert single(d, 'rqtg')['arguments'][-3:] == [p[i] for i in (3, 4, 5)]
    d = declaration('hzoe'); p = parameters(d)
    assert d['body']['kind'] == 'and' and single(d, 'hzod') == d['body']['arguments'][0]
    assert single(d, 'hzod')['arguments'] == [
        p[2], p[15], p[16], p[17], dict(kind='apply', function=p[14], arguments=[p[0]]), p[10]]
    d = declaration('hzr3'); p = parameters(d)
    witnesses, body = unbind(d['body'])
    assert len(witnesses) == 9
    assert single(body, 'hzoe')['arguments'] == [
        witnesses[4], witnesses[5], *p[:5], witnesses[6], witnesses[7], witnesses[8], p[7],
        *witnesses[:4], *p[8:11]]
    d = declaration('hzr4'); p = parameters(d)
    spread = single(d, 'rqsw')
    assert spread['arguments'][1]['kind'] == 'lambda'
    recipient = variable(spread['arguments'][1]['parameters'][0]['name'])
    assert single(spread['arguments'][1], 'hzr3')['arguments'] == [p[1], recipient, *p[2:11]]
    d = declaration('hzr5'); p = parameters(d)
    witnesses, body = unbind(d['body'])
    assert len(witnesses) == 3 and body['symbol'] == 'hzr4'
    assert body['arguments'] == [*p[:8], *witnesses, *p[8:]]
    d = declaration('r2lu'); p = parameters(d)
    witnesses, body = unbind(d['body'])
    assert len(witnesses) == 2 and body['kind'] == 'and'
    assert single(body, 'hzr5')['arguments'] == [*p[:2], *witnesses, *p[2:8]]
    assert single(body, 'hzq3')['arguments'][0] == p[1]
    d = declaration('r2lv')
    qualified = single(d, 'rqti')['arguments'][3]
    assert qualified['kind'] == 'lambda'
    assert single(qualified, 'r2lu')['arguments'][1] == variable(qualified['parameters'][0]['name'])
    # The source projection specifically supplies the plural spread criterion.
    assert any(x == dict(kind='function_ref', symbol='rqsy')
               for x in nodes(declaration('r2m3')))
    assert single(declaration('hzpp'), 'qh')['arguments'][2:4] == [
        dict(kind='quote', body=dict(kind='function_ref', symbol=n)) for n in ('h4q', 'hzpn')]
    return dict(chain=['r2lv', 'r2lu', 'hzr5', 'hzr4', 'hzr3', 'hzoe', 'hzod', 'h4p', 'h4q'],
                shared_roles=['origin', 'departure', 'prior', 'attained', 'anchor'],
                h4q_witnesses='the same departure, prior and attained used by every successful route',
                first_send='point(first), not a later relay or final receipt',
                physical_and_intellectual_processes_not_identified=True,
                scope='local implication by conjunction elimination and existential introduction')


def nodes(node):
    if isinstance(node, dict):
        yield node
        for x in node.values():
            yield from nodes(x)
    elif isinstance(node, list):
        for x in node:
            yield from nodes(x)


@lru_cache(None)
def binding_checks():
    result = witness_chain(catalog().entries)
    # Each mutation remains a same-sort candidate but breaks the role certificate.
    cases = [('hzoe', 'hzod', 0, 3), ('hzoe', 'hzod', 3, 16),
             ('hzod', 'h4p', 0, 1), ('hzod', 'h4p', 3, 2),
             ('hzr3', 'hzoe', 2, 1), ('hzr4', 'hzr3', 0, 2),
             ('r2lu', 'hzr5', 1, 3)]
    for owner, name, argument, wrong_parameter in cases:
        entries = deepcopy(catalog().entries)
        d = entries[owner]['declaration']
        single(d, name)['arguments'][argument] = parameters(d)[wrong_parameter]
        try:
            witness_chain(entries)
        except AssertionError:
            pass
        else:
            raise AssertionError((owner, argument))
    return dict(**result, wrong_role_mutations_refused=len(cases))


@lru_cache(None)
def achievement_checks():
    doc = fixture(['hzod', 'h4q'], CONSTANTS +
                  'q[k hzod[k zp[] k zw[] k zbefore[] k zattained[] k zcompleted[] k zanchor[]]].'
                  'q[t[k h4q[k zp[]]][k zanchor[]]].', ('bf', 'h4l'))
    rows = {}
    variants = ('baseline', 'other_worker', 'other_mind', 'no_self_work', 'no_autonomy_cause',
                'other_worker_also_participates', 'simultaneous', 'course_before_achievement')
    for variant in variants:
        values = source_values(doc, variant)
        actual = evaluate(doc, values, PEOPLE, SCENES, True)
        achieved = variant in ('baseline', 'other_worker_also_participates', 'simultaneous', 'course_before_achievement')
        expected = [achieved and variant not in ('simultaneous', 'course_before_achievement'), achieved]
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    for missing in ('h4m', 'h4n', 'g3', 'ic'):
        values = source_values(doc)
        values[missing] = unknown
        try:
            evaluate(doc, values, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(cases=rows, same_native_h4p_h4q_and_hzod=True, unknown_inputs_refused=4,
                ability_contents_are_explicit_boundary=True, no_physical_yoke_inputs_needed=True,
                existential_achievement_alone_does_not_prove_first_send_order=True)


@lru_cache(None)
def attribution_checks():
    doc = fixture(['r2mi'], 'q[k r2mi[]].')
    people = ('first', 'second', 'metaphor', 'crowdword', 'author', 'foreground', 'background', 'other')
    scenes = ('text', 'other')
    count = 0
    for fg, bg, metaphor, reason, tone in product((False, True), repeat=5):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(
            hzp4=lambda: 'first', hzp5=lambda: 'second', hzpo=lambda: 'metaphor',
            h223m=lambda: 'crowdword', wa=lambda: 'author', hzp3=lambda: 'text',
            hzpz=lambda: 'foreground', hzq2=lambda: 'background',
            hznreport=lambda n, a, c, s, r: fg and (n, a, s, r) == ('second', 'author', 'foreground', 'text')
                and c.rank == 3 and json.loads(c.syntax) == dict(kind='call', symbol='r2md', arguments=[]),
            hzrbgreport=lambda n, a, f, b, fs, bs, r: bg and
                (n, a, fs, bs, r) == ('second', 'author', 'foreground', 'background', 'text') and
                f.rank == b.rank == 3 and
                [json.loads(x.syntax)['symbol'] for x in (f, b)] == ['r2md', 'r2me'],
            qa=lambda n, a, target, picture, r: metaphor and (n, a, r) == ('metaphor', 'author', 'text')
                and (symbol(target), symbol(picture)) == ('h4q', 'hzpn'),
            ud=lambda a, premises, n, r: reason and (a, n, r) == ('author', 'first', 'text')
                and {p for p in people if premises(p)} == {'second'},
            ue=lambda earlier, later, r: (earlier, later, r) == ('first', 'second', 'text'),
            h223l=lambda n, a, scope, family, r: tone and (n, a, r) == ('crowdword', 'author', 'text')
                and scope.rank == family.rank == 1 and (symbol(scope), symbol(family)) == ('h222e', 'h223i'),
        )
        actual = evaluate(doc, values, people, scenes, True)
        assert actual == [fg and bg and metaphor and reason and tone]
        count += 1
    for name in ('hzp5', 'hzpo', 'h223m', 'wa', 'hzp3'):
        wrong = dict(values)
        wrong[name] = lambda: 'other'
        assert evaluate(doc, wrong, people, scenes, True) == [False]
    for name in ('qa', 'h223l', 'ud'):
        missing = dict(values)
        missing[name] = unknown
        try:
            evaluate(doc, missing, people, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(attribution_combinations=count, mismatched_source_roles_refused=5,
                world_physical_and_forecast_inputs_unexecuted=True, tone_separate_from_claim_and_background=True,
                unknown_attributions_refused=3, reason_is_presentation_not_logical_entailment=True)


@lru_cache(None)
def portability_checks():
    doc = fixture(['h223l'], '''
r zscope[a d] c.r zfamily[a d] a.r znode[] a.r zauthor[] a.r zcontext[] d.
q[k h223l[k znode[] k zauthor[] r b[p zscope] r b[p zfamily] k zcontext[]]].
''')
    values = dict(zscope=unknown, zfamily=unknown, znode=lambda: 'label', zauthor=lambda: 'speaker',
                  zcontext=lambda: 'debate',
                  h223l=lambda n, a, scope, family, c: (n, a, c) == ('label', 'speaker', 'debate')
                  and (symbol(scope), symbol(family)) == ('zscope', 'zfamily'))
    assert evaluate(doc, values, ('label', 'speaker'), ('debate',), True) == [True]
    return dict(other_discourse_and_referent_family=True, no_kant_or_crowd_symbols_needed=True)


CLAUSES = [
    ('Denn ', ['hzp6'], '同じ著者がこの文を第一文の理由として提示する。真理や論理的含意とは別。'),
    ('da ', ['r2ly', 'rqtp'], '先行文と同じ公衆に自由が残される場合。候補・期間・起点を共有する。'),
    ('werden sich ', ['r2lv', 'r2lp'], '同じ条件内の将来予測。findenと合わせ存在を述べ、探索者は補わない。'),
    ('immer ', ['r2lp', 'h223f'], '非空の全評価機会。成功を見て機会を選別せず、将来点と後続点を要求する。'),
    ('einige Selbstdenkende, ', ['rqti', 'hzq3', 'r2lu'], '異なる二人以上の独立判断への性向。全員でないという条件は加えない。'),
    ('sogar ', ['hzpw', 'r2mc', 'r2me'], '任用された後見役にも該当者がいる焦点と、より見込みにくいという背景を分ける。'),
    ('unter den eingesetzten Vormündern ', ['hzhb', 'h223k', 'r2m5', 'r2m6'], '同じ対象集団への責務、過去の任用行為、現在の職務委任を持つ人の中に該当者がいる。'),
    ('des großen Haufens, ', ['h223i', 'r2m7', 'r2mh'], '大勢の被指導者を一括する参照・人数・低く扱う呼称を分ける。'),
    ('finden, ', ['rqti', 'r2lv'], '見出されるとは該当者の存在の読み。全機会で同じ人であることは要求しない。'),
    ('welche, ', ['r2lu', 'hzr5'], '先行する自己思考者と自己離脱・伝播の発信者が同じ人。'),
    ('nachdem sie ', ['hzoe', 'hzod', 'rqtg'], '同じ本人の離脱完了が、その人の最初の発信より厳密に先。'),
    ('das Joch der Unmündigkeit ', ['hzpp', 'h4q', 'hzpn', 'hzpk'], '知的未成熟の自己離脱を、牽引用の頚木を身体から除く描写で提示する。'),
    ('selbst abgeworfen haben, ', ['h4p', 'h4o', 'hzpm', 'hzod'], '本人の活動と因果関与による完了。助力は排除せず、別人の離脱や将来の未完了で代用しない。'),
    ('den Geist ', ['r2lz', 'hzq6'], '伝わる内容は後続の判断への性向。実際の一回の判断そのものではない。'),
    ('einer vernünftigen Schätzung ', ['hznu', 'h222v'], '本人の価値を理由に基づいて評定する性向。高い評点を補わない。'),
    ('des eigenen Werths ', ['hznu', 'h222v'], '受け手本人の人としての価値・長所。発信者だけの価値や金銭価格へ取り替えない。'),
    ('und des Berufs jedes Menschen ', ['hznq', 'h222w', 'h222x', 'h222y'], '全ての人に、人として自ら考える課題があることを認める。特定職業へ限定しない。'),
    ('selbst zu denken ', ['hznq', 'hznu'], '各人本人が思考する規範内容。同じ人の判断と使命承認を結ぶ。'),
    ('um sich ', ['hzom', 'rqth'], '発信者を中心とする社会的接点。本人を除き、全読者や地理的近傍とは同一視しない。'),
    ('verbreiten werden.', ['hzr3', 'hzr4', 'rqsy', 'hzob', 'r2lv'], '受領・理解・因果を伴う取得が周囲の二人以上へ将来成立する。任意長の有限経路を許し、状態の持続も保つ。'),
]


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    text = unit['text']; start, end = 129, 448
    anchors = [text.index(phrase, start, end) for phrase, _, _ in CLAUSES]
    assert anchors == sorted(anchors) and anchors[0] == start
    clauses = [dict(range=[a, b], text=text[a:b], definitions=defs, reading=reason)
               for a, b, (_, defs, reason) in zip(anchors, anchors[1:] + [end], CLAUSES)]
    paths = {FULL, BASIS, DOC, INVENTORY, IMAGE, LEXICAL, FIRST, *PRIOR}
    return dict(status='public_second_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, end], text=text[start:end]),
                clauses=clauses, selection=selection_binding(catalog(), [58]),
                interpretation=LIMITS, witness_connection=witness_chain(catalog().entries),
                judgment='全語句の内容・照応・量化・時間・条件・比喩・語調・理由提示を通読し、上記の明示した読みの下で第二文に未処理項目はないと判断する。',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=274, preserved_first_sentence_characters=108,
                combined_first_two_sentence_characters=382,
                facsimile=dict(artifact=IMAGE, page=483, visually_collated=True,
                               differences='長いs、行末の分綴、Werths等の歴史的綴り。固定本文は変更しない。'),
                lexical=dict(artifact=LEXICAL, url='https://fwb-online.de/go/haufen.s.0m_1709340534',
                             sections=[5, 6], accessed='2026-10-20',
                             use='集団用法と低く扱う語調の根拠。時代範囲が異なるため、この原文での唯一の読解を証明するものではない。'),
                primary_context='https://korpora.org/Kant/aa08/036.html',
                no_independent_review=True, semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert new.document['statements'][:-1] == old.document['statements']
    assert len(new.document['statements']) == 59
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    assert read(FIRST)['selection'] == selection_binding(new, [55, 56])
    validate_hashes(ROOT, read(FIRST)['source_sha256'])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    record = read(AUDIT)
    assert record == reading()
    source = record['source']
    assert len(''.join(source['text'].split())) == 274
    assert ''.join(c['text'] for c in record['clauses']) == source['text']
    for clause in record['clauses']:
        assert set(clause['definitions']) <= set(new.entries)
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == source['unit'])
    assert digest(unit['text'].encode('utf-8')) == source['unit_sha256']
    assert unit['text'][218:236] == 'des großen Haufens'
    assert source['range'][0] <= 254 < 315 <= source['range'][1]
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(added_definitions=len(MEANINGS), added_semantic_primitives=1, added_source_references=1,
                added_statement_index=58, source_clauses=len(CLAUSES), preserved_whole_unit_reviews=len(reviews),
                preserved_first_sentence_characters=108, reviewed_second_sentence_characters=274, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('binding', binding_checks), ('achievement', achievement_checks),
                     ('attribution', attribution_checks), ('portability', portability_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, IMAGE, LEXICAL, FIRST, *PRIOR, 'scripts/compose_public_second_sentence.py',
        'scripts/check_public_second_sentence.py', 'tests/test_public_second_sentence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/check_self_formed_course.py',
    }
    source = read(AUDIT)['source']
    return dict(status='second_sentence_reviewed_under_explicit_reading', document=FULL, **results,
                alignment=dict(**source, definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=274, combined_first_two_sentence_characters=382,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
