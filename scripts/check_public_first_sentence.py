"""Check clause factoring and discourse roles; preserve the separate reading judgment."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_first_sentence import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS,
    parent, build, closure, extracted,
)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_public_comparison_claim import seq, predicate
from scripts.check_scoped_counts import arithmetic

INDEX = 'data/semantic-review-index-v119.json'
REPORT = 'reports/public-first-sentence-v1.json'
AUDIT = 'data/public-first-sentence-reading-v1.json'
DOC = 'docs/public-first-sentence-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/future-dissemination-reading-v1/page-483.jpg'
PRIOR = ['reports/public-comparison-claim-v1.json', 'reports/prospective-comparison-v1.json',
         'reports/prospective-liberty-v1.json']

# Authored after rereading the fixed sentence, original page and later liberty
# explanation. These reasons are not inferred from the finite tests below.
REASONS = [
    '固定原文u0011の[0,128)と原刊483頁を照合した。第一文の全語・句読点を連続区間へ割り付け、綴りの変更は加えない。',
    '公衆の自己啓蒙、個人との可能性比較、自由を残す条件、ほぼ必然という留保、対比・強調・条件の取り立てを区別した。r2lfを維持し、前後半r2lj・r2llと提示関係r2loを追加した。',
    'esは同じ自己啓蒙の内容、ihmは同じ公衆へ接続した。manの出所はh222f、比較個人はhzzq・whの範囲、公衆・期間・起点・尺度は同じ入力を共用する。',
    'Daß節の内容を閉じた内容として著者waへ帰属する。aberは前段落との対比、jaは条件付きの言い方への強め方、nurは自由の条件を足りるものとして提示する働きとした。',
    'beinaheの例外余地を保つ。nurを必要条件・唯一原因・例外のない成功保証へ強めず、jaから数値確率の大小を推論しない。範囲・比率・規範的自由の具体化は採用解釈として明記した。',
    '自己啓蒙は内部の人の活動による自立的使用の能力変化として既存の因果・時間・人の分類へ展開する。三つの提示関係は引数と意味規約を公開した一般的な基本概念であり、原文一文を返す記号ではない。',
    '有限の反例検査は量化・共有入力・帰属の保持を調べる。既存の様相検査は依存内容とハッシュを固定して再利用する。これらは原文との自動同義性証明でも独立査読でもない。',
    '第一文を前段落の個人の難しさと後続の公的理性使用の限定を含めて再読した。明示した読みの下で第一文の未処理項目はないと判断する。第四段落の残りをこの判断に含めない。',
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
def factoring_checks():
    doc = fixture(['r2lf', 'r2lj', 'r2ll'], 'r zr[] d.'
                  'q[t[k r2lf[]][k zr[]]].q[t[k r2lj[]][k zr[]]].q[t[k r2ll[]][k zr[]]].',
                  ('r2la', 'r2ld', 'r2lh', 'r2lk'))
    groups, people = ('g', 'h'), ('p', 'q')
    pairs = tuple(product(groups, people))
    domain = (*groups, *people, 'node', 'object')

    def model(selected, persons, comparisons, near):
        values = unknowns(doc)
        values.update(
            zr=lambda: 'now', wh=lambda: 'earlier', hzzq=lambda: 'node',
            h222e=lambda g, r: g in selected and r == 'now',
            hzzn=lambda n, p, r: (n, r) == ('node', 'earlier') and p in persons,
            aa=lambda p: p in people,
            r2la=lambda g, r: g in groups and r == 'now',
            r2ld=lambda g, p, r: r == 'now' and (g, p) in comparisons and g in near,
            r2lh=lambda g, p, r: r == 'now' and (g, p) in comparisons,
            r2lk=lambda g, r: r == 'now' and g in near,
        )
        return values

    count = 0
    for bits in product((False, True), repeat=10):
        selected = {x for x, b in zip(groups, bits[:2]) if b}
        persons = {x for x, b in zip(people, bits[2:4]) if b}
        comparisons = {x for x, b in zip(pairs, bits[4:8]) if b}
        near = {x for x, b in zip(groups, bits[8:]) if b}
        actual = evaluate(doc, model(selected, persons, comparisons, near), domain, ('now', 'earlier'), True)
        comparative = bool(selected and persons) and set(product(selected, persons)) <= comparisons
        conditioned = bool(selected) and selected <= near
        assert actual == [comparative and conditioned, comparative, conditioned], (bits, actual)
        count += 1
    for selected, persons in [({'g', 'object'}, {'p'}), ({'g'}, {'p', 'object'})]:
        actual = evaluate(doc, model(selected, persons, set(product(selected, persons)), selected),
                          domain, ('now', 'earlier'), True)
        assert actual[:2] == [False, False]
    for name in ('h222e', 'hzzn', 'r2lh', 'r2lk'):
        values = model({'g'}, {'p'}, {('g', 'p')}, {'g'})
        values[name] = unknown
        try:
            evaluate(doc, values, domain, ('now', 'earlier'), True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(scope_comparison_and_conditional_combinations=count, same_combined_claim=True,
                empty_scopes_and_ineligible_selections_refused=True, unknown_inputs_refused=4,
                modal_bodies_are_explicit_test_boundaries=True)


@lru_cache(None)
def family_checks():
    doc = fixture(['r2lk', 'r2lm', 'r2ln'], 'r zg[] a.r zr[] d.r zb[] d.'
                  'q[k r2lk[k zg[] k zr[]]].'
                  'q[t[k r2lm[k zg[] k zr[]]][k zb[]]].'
                  'q[t[k r2ln[k zg[] k zr[]]][k zb[]]].', ('hznh', 'hznf', 'hzng'))
    domain = ('g', 'h', 'p', 'q', 'low', 'mid', 'high', 'source', 'frame')
    scenes = ('reference', 'other', 'branch', 'alternate', 'start')
    count = 0
    for audience, reference, branch in product(('g', 'h'), ('reference', 'other'), ('branch', 'alternate')):
        seen = set()
        values = unknowns(doc)
        values.update(arithmetic())

        def field(name, g, r, result):
            assert (g, r) == (audience, reference), (name, g, r)
            seen.add(name)
            return result

        values.update(zg=lambda: audience, zr=lambda: reference, zb=lambda: branch,
                      aa=lambda p: p in ('p', 'q'))
        for name, result in [('h222f', 'source'), ('h222g', 'frame'), ('h222i', seq(('p', 'q'))),
                             ('h222l', seq(('low', 'mid', 'high'))), ('h222p', 'mid')]:
            values[name] = lambda g, r, name=name, result=result: field(name, g, r, result)
        from fractions import Fraction
        values.update(pa=lambda n, d: n / d if d else Fraction(0),
                      h222j=lambda g, r: field('h222j', g, r, Fraction(1, 3)),
                      h222h=lambda g, r, b: field('h222h', g, r, 'start' if b == branch else 'other'),
                      h222k=lambda g, r, b: field('h222k', g, r, b == branch),
                      h222m=lambda g, r, v: field('h222m', g, r, v == 'mid'))

        def extent_check(extent):
            assert extent(predicate({'p', 'q'}), predicate({'p'}))
            assert not extent(predicate({'p'}), predicate({'p'}))
            assert not extent(predicate({'p', 'q'}), predicate({'source'}))

        def conditional(g, r, source, frame, origins, extent, cases, scale, less, near, low, high, degree):
            assert (g, r, source, frame) == (audience, reference, 'source', 'frame')
            assert origins(branch) == 'start' and origins('start') == 'other'
            assert [s for s in scenes if cases(s)] == [branch]
            assert [p for p in domain if scale(p)] == ['low', 'mid', 'high']
            assert less('low', 'mid') and less('mid', 'high') and not less('mid', 'low')
            assert near('mid') and not near('high')
            assert (low, high, degree) == ('low', 'high', 'mid')
            extent_check(extent)
            return True

        def condition(g, r, source, frame, origin, candidate):
            return (g, r, source, frame, origin, candidate) == (
                audience, reference, 'source', 'frame', 'start', branch)

        def goal(g, r, frame, origin, extent, candidate):
            extent_check(extent)
            return (g, r, frame, origin, candidate) == (audience, reference, 'frame', 'start', branch)

        values.update(hznh=conditional, hznf=condition, hzng=goal)
        assert evaluate(doc, values, domain, scenes, True) == [True, True, True]
        assert {'h222f', 'h222g', 'h222h', 'h222i', 'h222j', 'h222k', 'h222l', 'h222m', 'h222p'} <= seen
        invalid = dict(values, h222l=lambda *args: seq(('low', 'mid', 'mid', 'high')),
                       hznh=lambda *args: True)
        assert evaluate(doc, invalid, domain, scenes, True) == [False, True, True]
        count += 1
    return dict(audience_reference_candidate_combinations=count, shared_condition_goal_and_qualification=True,
                real_extent_and_scale_guards_executed=True, selected_person_not_in_conditional_family=True)


def quoted_call(value, name):
    return value.rank == 1 and json.loads(value.syntax) == dict(kind='call', symbol=name, arguments=[])


@lru_cache(None)
def discourse_checks():
    doc = fixture(['r2lo'], 'q[k r2lo[]].')
    domain = ('whole', 'author', 'prior', 'first', 'second', 'other')
    scenes = ('text', 'other')

    def model(flags):
        values = unknowns(doc)
        values.update(hzp4=lambda: 'whole', wa=lambda: 'author', hzp3=lambda: 'text',
                      hzzq=lambda: 'prior', h222t=lambda: 'first', h222u=lambda: 'second')

        def assertion(node, author, content, context):
            return (author, context) == ('author', 'text') and (
                node == 'first' and flags[0] and quoted_call(content, 'r2lj') or
                node == 'second' and flags[1] and quoted_call(content, 'r2ll'))

        def pair(expected, enabled, node, author, first, content1, second, content2, axis, context):
            n1, c1, n2, c2 = expected
            return enabled and (node, author, first, second, context) == ('whole', 'author', n1, n2, 'text') \
                and quoted_call(content1, c1) and quoted_call(content2, c2) and symbol(axis) == 'h4l'

        def sufficient(node, author, scope, condition, goal, qualification, context):
            return flags[4] and (node, author, context) == ('second', 'author', 'text') \
                and [symbol(v) for v in (scope, condition, goal, qualification)] == ['h222e', 'r2lm', 'r2ln', 'r2lk'] \
                and [v.rank for v in (scope, condition, goal, qualification)] == [0, 1, 1, 1]

        values.update(hzon=assertion,
                      h222q=lambda *args: pair(('prior', 'r2ec', 'first', 'r2lj'), flags[2], *args),
                      h222r=lambda *args: pair(('first', 'r2lj', 'second', 'r2ll'), flags[3], *args),
                      h222s=sufficient,
                      ue=lambda a, b, c: flags[5] and (a, b, c) == ('first', 'second', 'text'))
        return values

    for flags in product((False, True), repeat=6):
        assert evaluate(doc, model(flags), domain, scenes, True) == [all(flags)], flags
    for name in ('hzp4', 'wa', 'hzp3', 'hzzq', 'h222t', 'h222u'):
        values = model((True,) * 6)
        values[name] = lambda: 'other'
        assert evaluate(doc, values, domain, scenes, True) == [False], name
    values = model((True,) * 6)
    values['h222u'] = lambda: 'first'
    assert evaluate(doc, values, domain, scenes, True) == [False]
    for name in ('h222q', 'h222r', 'h222s'):
        values = model((True,) * 6)
        values[name] = unknown
        try:
            evaluate(doc, values, domain, scenes, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    # Mutations check the actual quote wiring, not only absent primitive facts.
    from scripts.compose_public_first_sentence import replace_calls
    for mapping in ({'r2lk': 'r2la'}, {'r2lm': 'r2ln', 'r2ln': 'r2lm'}, {'r2lj': 'r2ll'}, {'h4l': 'bf'}):
        changed = deepcopy(doc)
        target = next(d for d in changed['declarations'] if d['name'] == 'r2lo')
        target['body'] = replace_calls(target['body'], mapping)
        assert evaluate(changed, model((True,) * 6), domain, scenes, True) == [False], mapping
    return dict(presentation_fact_combinations=64, all_world_inputs_unexecuted=True,
                clause_order_author_axis_and_qualification_preserved=True, quote_mutations_refused=4,
                unknown_inputs_refused=3)


@lru_cache(None)
def portability_checks():
    primitives = ''.join('r ' + n + PRIMITIVES[n][0] + '.' for n in ('h222q', 'h222r', 'h222s'))
    # Heating and entry permission use the same generic presentation signatures.
    doc = parse('p:\n' + primitives + '''
r zn[] a.r za[] a.r zf[] a.r zs[] a.r zc[] d.
r zcold[d] c.r zwarm[d] c.r zhot[d] c.r ztemperature[a] e.
r zvisitors[a d] c.r zticket[a d d] c.r zentry[a d d] c.r zlikely[a d] c.
d zfirst[] e[b point[k zcold[v point]]].
d zsecond[] e[b point[k zwarm[v point]]].
d zthird[] e[b point[k zhot[v point]]].
d zcondition[person a reference d] e[b candidate[k zticket[v person v reference v candidate]]].
d zgoal[person a reference d] e[b candidate[k zentry[v person v reference v candidate]]].
q[k h222q[k zn[] k za[] k zf[] r b[k zfirst[]] k zs[] r b[k zsecond[]] r[p ztemperature] k zc[]]].
q[k h222r[k zn[] k za[] k zf[] r b[k zsecond[]] k zs[] r b[k zthird[]] r[p ztemperature] k zc[]]].
q[k h222s[k zn[] k za[] r[p zvisitors] r b[p zcondition] r b[p zgoal] r b[p zlikely] k zc[]]].
''')
    values = unknowns(doc)
    values.update(zn=lambda: 'note', za=lambda: 'speaker', zf=lambda: 'one', zs=lambda: 'two', zc=lambda: 'text')

    def pair(first_name, second_name, node, author, first, c1, second, c2, axis, context):
        return (node, author, first, second, context) == ('note', 'speaker', 'one', 'two', 'text') \
            and quoted_call(c1, first_name) and quoted_call(c2, second_name) and symbol(axis) == 'ztemperature'

    values.update(h222q=lambda *args: pair('zfirst', 'zsecond', *args),
                  h222r=lambda *args: pair('zsecond', 'zthird', *args),
                  h222s=lambda n, a, s, c, g, q, r: (n, a, r) == ('note', 'speaker', 'text') and
                  [symbol(v) for v in (s, c, g, q)] == ['zvisitors', 'zcondition', 'zgoal', 'zlikely'])
    assert evaluate(doc, values, ('note', 'speaker', 'one', 'two'), ('text',), True) == [True] * 3
    for truth in (False, True):
        modified = dict(values)
        for name in ('zcold', 'zwarm', 'zhot', 'zticket', 'zentry', 'zlikely'):
            modified[name] = lambda *args, truth=truth: truth
        assert evaluate(doc, modified, ('note', 'speaker', 'one', 'two'), ('text',), True) == [True] * 3
    return dict(non_kant_heating_and_admission_contents=True, world_truth_independent=True,
                basic_meaning_conventions_not_psychological_derivations=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0011')
    text = unit['text'][:128]
    pieces = [
        ('Daß ', ['r2lf', 'r2lg'], '後続の内容を著者の主張として帰属する。'),
        ('aber ', ['r2lo', 'h222q', 'r2ec'], '個人の離脱の難しさと、公衆の可能性を対比する。'),
        ('ein Publikum ', ['r2la', 'r2le', 'h222e'], '話題の各公衆を、公的議論の宛先となる読者集団として読む。'),
        ('sich selbst aufkläre, ', ['hzng', 'hzmy', 'r2lc'], '同じ公衆内部の人の働きによって、自立的使用の能力変化が広がる。'),
        ('ist eher möglich; ', ['r2kv', 'r2lh', 'r2li', 'r2lj'], '前段落の各個人と同じ候補・尺度で将来の達成可能性を比較する。'),
        ('ja ', ['r2lo', 'h222r'], '条件付きのほぼ必然という強い言い方へ進む。'),
        ('es ist, ', ['r2ll', 'r2lk'], '前半と同じ公衆の同じ自己啓蒙を後半の対象にする。'),
        ('wenn man ihm ', ['h222f', 'r2lm', 'hznh'], '未特定の許可主体と同じ公衆に束縛した条件を置く。'),
        ('nur ', ['h222s', 'r2lo'], '限定付き帰結のために自由を残しておけば足りると提示する。'),
        ('Freiheit läßt, ', ['hznf', 'hzna', 'r2lm'], '同じ期間・起点に、公的理性使用の規範的許可を残し維持する。'),
        ('beinahe unausbleiblich.', ['hznh', 'rqsu', 'r2lk', 'r2ll'], '条件付き程度を必然の端点近傍とし、端点自体と同一視しない。'),
    ]
    clauses, start = [], 0
    for phrase, definitions, interpretation in pieces:
        assert text[start:start + len(phrase)] == phrase
        clauses.append(dict(range=[start, start + len(phrase)], text=phrase,
                            definitions=definitions, reading=interpretation))
        start += len(phrase)
    assert start == len(text) == 128
    assert sum(not c.isspace() for c in text) == 108
    paths = {FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, IMAGE, *PRIOR}
    return dict(status='public_first_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[0, 128], text=text),
                clauses=clauses, selection=selection_binding(catalog(), [55, 56]),
                requirements=[dict(number=i, reason=reason) for i, reason in enumerate(REASONS, 1)],
                interpretation=LIMITS, unresolved=[],
                decision='equivalent_under_stated_reading_for_this_sentence',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=108, newly_reviewed_sentence_characters=108,
                paragraph_reviewed_sentence_characters=108,
                semantic_equivalence_automatically_proved=False,
                original_page=dict(path=IMAGE, page=483, visually_inspected=True),
                references=[dict(url='https://korpora.org/Kant/aa08/036.html', accessed='2026-10-20',
                                 use='個人との対比、第一文と後続する公的理性使用の自由の限定。'),
                            dict(url='https://korpora.org/Kant/aa08/037.html', accessed='2026-10-20',
                                 use='学識者の公的な理性使用、読者世界、職務内での私的使用。')],
                remaining_unit_work='第二文以降の理由、扇動、漸進性、革命の限界を全体として確認する。',
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:len(old.document['declarations'])] == old.document['declarations']
    assert new.document['statements'][:-1] == old.document['statements']
    assert len(new.document['statements']) == 57
    assert all(new.entries[n] == e for n, e in old.entries.items())
    # Canonicalize the extracted declarations in context to account for alpha naming.
    expected = deepcopy(old.document)
    expected['declarations'].extend(extracted())
    expected = parse(format_graph(expected, 'compact'))
    for declaration in expected['declarations'][-3:]:
        assert declaration == new.entries[declaration['name']]['declaration']
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
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
    return dict(added_definitions=len(MEANINGS), added_discourse_primitives=3, added_source_references=2,
                authored_statements=57, added_statement_index=56,
                preserved_whole_unit_reviews=len(reviews), sentence_nonblank_characters=108, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('factoring', factoring_checks), ('families', family_checks),
                     ('discourse', discourse_checks), ('portability', portability_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, IMAGE, *PRIOR, 'scripts/compose_public_first_sentence.py',
        'scripts/check_public_first_sentence.py', 'tests/test_public_first_sentence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'scripts/check_public_comparison_claim.py', 'scripts/check_scoped_counts.py',
    }
    source = read(AUDIT)['source']
    return dict(status='first_sentence_reviewed_under_explicit_reading', document=FULL, **results,
                alignment=dict(**source, definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=108, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                semantic_equivalence_automatically_proved=False,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
