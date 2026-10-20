"""Check shared goal bindings, nonfactive institutional purpose and sentence reading."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import FunctionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_purpose_mechanism import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, library, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v163.json'
REPORT = 'reports/public-purpose-mechanism-v1.json'
AUDIT = 'data/public-purpose-mechanism-reading-v1.json'
EVIDENCE = 'data/public-purpose-mechanism-evidence-v1.json'
DOC = 'docs/public-purpose-mechanism-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/answer-discourse-v1/page-485.jpg'
PRIOR = ('reports/mechanism-requirements-v1.json', 'reports/institutional-coordination-v1.json')
DOMAIN = ('one', 'two', 'third', 'roleone', 'roletwo', 'work', 'otherwork', 'community',
          'government', 'mechanism', 'arrangement', 'other')
SCENES = ('reference', 'future', 'other')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    roots = {'target': ['r3a', 'r3e', 'r3f'], 'means': ['r3b'],
             'purpose': ['r3c', 'r3d'], 'discourse': ['r3g']}[kind]
    if kind == 'purpose':
        for d in doc['declarations']:
            if d['name'] == 'r2zx':
                d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
                d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    text = format_graph(doc, 'compact')
    extra = 'r zwork[] a.r zreference[] d.r zpoint[] d.r zperson[] a.'
    if kind in ('target', 'purpose'):
        start = text.index('r h237k[')
        end = text.index('.', start) + 1
        text = text[:start] + text[end:]
        adapter = '''
r zgoal[] e.r zothergoal[] e.
r zgoalcode[a d i[e] i[e]] i[e].
d h237k[work a reference d] i[e][k zgoalcode[v work v reference r[k zgoal[]] r[k zothergoal[]]]].
'''
        start = text.index('d r3a[')
        text = text[:start] + adapter + text[start:]
    args = 'k zwork[] k zreference[]'
    if kind == 'target':
        query = ('q[t[k r3a[' + args + ']][k zpoint[]]].'
                 'q[t[k r3e[k zwork[] k zperson[] k zreference[]]][k zpoint[]]].'
                 'q[t[k r3f[k zwork[] k zperson[] k zreference[]]][k zpoint[]]].')
    elif kind == 'means':
        query = 'q[t[k r3b[' + args + ']][k zpoint[]]].'
    elif kind == 'purpose':
        query = 'q[k r3c[' + args + ']].q[t[k r3d[]][k zpoint[]]].'
    else:
        extra, query = '', 'q[k r3g[]].'
    return parse(text + extra + query)


def base(doc, variant='baseline'):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    people = set() if variant == 'empty_group' else {'one', 'two'}
    if variant == 'extra_member':
        people.add('third')
    roles = dict(one='roleone', two='roletwo')
    values.update(zwork=lambda: 'work', zreference=lambda: 'reference', zpoint=lambda: 'future',
        zperson=lambda: 'one', h232v=lambda: 'reference',
        aa=lambda p: p in {'one', 'two', 'third'},
        h237h=lambda w, r: 'mechanism', h237i=lambda w, r: 'community',
        h237d=lambda m, w, r: FunctionValue(('individual',), 'truth',
            lambda p: p in people and (m, w, r) == ('mechanism', 'work', 'reference')),
        h237e=lambda p, m, w, r: roles.get(p, 'other'),
        h237f=lambda p, role, m, w, r: p in roles and (role, m, w, r) == (
            'other' if variant == 'other_assigned_role' else roles.get(p),
            'mechanism', 'work', 'reference'),
        h237c=lambda p, c, r: p in {'one', 'two', 'third'} and (c, r) == (
            'other' if variant == 'other_membership_community' else 'community', 'reference'),
        h237m=lambda w, r: 'government',
        h237o=lambda m, w, r: 'arrangement' if (m, w, r) == ('mechanism', 'work', 'reference') else 'other',
        zgoalcode=lambda w, r, goal, other: other if variant == 'other_goal_provider' else goal,
        h237n=lambda g, c, r: (g, c, r) == ('government',
            'other' if variant == 'other_governed_community' else 'community', 'reference'))
    return values


def target_model(flags=(True, False, False, True), variant='baseline'):
    values = base(fixture('target'), variant)
    def outcome(side, government, person, work, arrangement, goal, point):
        offset = {'one': 0, 'two': 2}.get(person)
        return offset is not None and flags[offset + side] and (
            government, work, arrangement, symbol(goal), point) == (
            'other' if variant == 'other_directing_government' else 'government',
            'otherwork' if variant == 'other_effect_work' else 'work',
            'other' if variant == 'other_effect_arrangement' else 'arrangement',
            'zothergoal' if variant == 'other_prevention_goal' and side == 1 else 'zgoal',
            'reference' if variant == 'other_effect_point' else 'future')
    def coordinated(arrangement, people, work, point):
        actual = {p for p in DOMAIN if people(p)}
        expected = {'one'} if variant == 'coordinated_subset' else {'one', 'two'}
        return variant != 'no_coordination' and actual == expected and (
            arrangement, work, point) == ('arrangement', 'work', 'future')
    values.update(h237s=lambda *args: outcome(0, *args), h237t=lambda *args: outcome(1, *args),
        h237p=coordinated,
        h237q=lambda a, w, p: variant != 'spontaneous_only' and (a, w, p) == ('arrangement', 'work', 'future'),
        h237r=lambda m, a, w, p: (m, a, w, p) == (
            'other' if variant == 'other_supplying_mechanism' else 'mechanism',
            'other' if variant == 'other_supplied_arrangement' else 'arrangement', 'work', 'future'))
    return values


@lru_cache(None)
def target_checks():
    doc, combinations = fixture('target'), []
    for flags in product((False, True), repeat=4):
        actual = evaluate(doc, target_model(flags), DOMAIN, SCENES, True)
        expected = [(flags[0] or flags[1]) and (flags[2] or flags[3]), flags[0], flags[1]]
        assert actual == expected, (flags, actual)
        combinations.append(dict(flags=list(flags), target_direction_prevention=actual))
    contrasts = {}
    for variant in ('empty_group', 'extra_member', 'other_goal_provider', 'other_membership_community',
                    'other_governed_community', 'other_directing_government', 'other_effect_work',
                    'other_effect_arrangement', 'other_prevention_goal', 'other_effect_point',
                    'coordinated_subset', 'no_coordination', 'spontaneous_only',
                    'other_supplying_mechanism', 'other_supplied_arrangement'):
        actual = evaluate(doc, target_model(variant=variant), DOMAIN, SCENES, True)
        assert actual[0] is False, (variant, actual)
        contrasts[variant] = actual
    for name in ('h237s', 'h237t', 'h237p', 'h237q', 'h237r'):
        values = target_model(); values[name] = unknown
        try:
            evaluate(doc, values, DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(combinations=combinations, contrasts=contrasts, unknown_inputs_refused=5,
                goal_truth_not_executed=True, mixed_and_both_outcomes_allowed=True,
                same_goal_and_instrument_preserved=True)


@lru_cache(None)
def means_checks():
    doc, rows = fixture('means'), []
    for executing_one, revising_one, executing_two, revising_two in product((False, True), repeat=4):
        values = base(doc)
        values.update(
            h237a=lambda p, r, w, s: (p, r, w, s) in (
                {('one', 'roleone', 'work', 'future')} if executing_one else set()) |
                ({('two', 'roletwo', 'work', 'future')} if executing_two else set()),
            h237b=lambda p, r, w, s: (p, r, w, s) in (
                {('one', 'roleone', 'work', 'future')} if revising_one else set()) |
                ({('two', 'roletwo', 'work', 'future')} if revising_two else set()))
        actual = evaluate(doc, values, DOMAIN, SCENES, True)
        expected = executing_one and not revising_one and executing_two and not revising_two
        assert actual == [expected]
        rows.append(dict(flags=[executing_one, revising_one, executing_two, revising_two], value=actual[0]))
    for variant in ('empty_group', 'other_assigned_role', 'other_membership_community'):
        values = base(doc, variant)
        values.update(h237a=lambda *args: True, h237b=lambda *args: False)
        assert evaluate(doc, values, DOMAIN, SCENES, True) == [False]
    return dict(combinations=rows, native_passive_content=True, fixed_roles_and_group=True)


def purpose_model(variant='baseline'):
    doc = fixture('purpose')
    values = base(doc)
    values.update(
        r2zx=lambda w, r: variant != 'missing_requirements' and (w, r) == ('work', 'reference'),
        h237l=lambda code, c, w, r: variant != 'private_goal_only' and (
            symbol(code), c, w, r) == (
                'zgoal', 'other' if variant == 'public_goal_other_community' else 'community',
                'otherwork' if variant == 'public_goal_other_work' else 'work', 'reference'),
        h237u=lambda mechanism, work, means, end, reference: variant != 'missing_purpose' and (
            mechanism, work, symbol(means), means.rank, symbol(end), end.rank, reference) == (
            'other' if variant == 'purpose_other_mechanism' else 'mechanism',
            'otherwork' if variant == 'purpose_other_work' else 'work',
            'r3a' if variant == 'purpose_reversed' else 'r3b', 1,
            'r3b' if variant == 'purpose_reversed' else 'r3a', 1,
            'future' if variant == 'purpose_other_reference' else 'reference'))
    return values


@lru_cache(None)
def purpose_checks():
    doc, rows = fixture('purpose'), {}
    for variant in ('baseline', 'missing_requirements', 'private_goal_only', 'public_goal_other_community',
                    'public_goal_other_work', 'missing_purpose', 'purpose_other_mechanism',
                    'purpose_other_work', 'purpose_reversed', 'purpose_other_reference'):
        actual = evaluate(doc, purpose_model(variant), DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'] * 2, (variant, actual)
        rows[variant] = actual
    values = purpose_model(); values['zpoint'] = lambda: 'other'
    assert evaluate(doc, values, DOMAIN, SCENES, True) == [True, True]
    values = purpose_model(); values['h232v'] = lambda: 'other'
    assert evaluate(doc, values, DOMAIN, SCENES, True) == [True, False]
    for name in ('h237l', 'h237n', 'h237u'):
        values = purpose_model(); values[name] = unknown
        try:
            evaluate(doc, values, DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    assert all(purpose_model()[n] is unknown for n in ('h237a', 'h237b', 'h237s', 'h237t', 'zgoal'))
    return dict(contrasts=rows, unknown_inputs_refused=3, fixed_reference=True,
                means_end_and_goal_truth_not_executed=True,
                semantic_boundaries=['r2zx is a typed fixture boundary; its unchanged native check is pinned.',
                                     'Purpose and public-goal relations are explicit model inputs.',
                                     'No individual psychological intention is inferred.'])


@lru_cache(None)
def discourse_checks():
    doc, rows = fixture('discourse'), {}
    for variant in ('baseline', 'wrong_content', 'reversed_alternatives', 'other_enclosing_goal',
                    'missing_explanation', 'reversed_explanation', 'wrong_order', 'wrong_context'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(wa=lambda: 'author', h237w=lambda: 'sentence', h236s=lambda: 'definition',
            h232o=lambda: 'presentation',
            h236i=lambda n, a, code, ctx: (n, a, symbol(code), code.rank, ctx) == (
                'sentence', 'author', 'r2zy' if variant == 'wrong_content' else 'r3d', 3, 'presentation'),
            h237v=lambda n, a, end, primary, fallback, ctx: (
                n, a, symbol(end), end.rank, symbol(primary), primary.rank,
                symbol(fallback), fallback.rank, ctx) == (
                'sentence', 'author', 'r3b' if variant == 'other_enclosing_goal' else 'r3a', 1,
                'r3f' if variant == 'reversed_alternatives' else 'r3e', 1,
                'r3e' if variant == 'reversed_alternatives' else 'r3f', 1,
                'reference' if variant == 'wrong_context' else 'presentation'),
            uf=lambda a, first, second, ctx: variant != 'missing_explanation' and (
                a, first, second, ctx) == ('author',
                'sentence' if variant == 'reversed_explanation' else 'definition',
                'definition' if variant == 'reversed_explanation' else 'sentence', 'presentation'),
            ue=lambda first, second, ctx: (first, second, ctx) == (
                'sentence' if variant == 'wrong_order' else 'definition', 'sentence', 'presentation'))
        actual = evaluate(doc, values, DOMAIN + ('author', 'definition', 'sentence'),
                          SCENES + ('presentation',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    return dict(contrasts=rows, attribution_does_not_execute_content=True,
                lesser_alternative_is_not_logical_entailment=True)


def evidence():
    return dict(status='mechanism_sentence_facsimile_and_explicit_interpretation',
                checked_date='2026-10-21',
                facsimile=dict(path=IMAGE, page=485, visually_inspected=True,
                    url='https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00525/full/full/0/default.jpg',
                    finding_ja='必要な機構・受動的な振る舞い・umによる目的節・künstliche Einhelligkeit・Regierung・öffentlichen Zwekken・oder wenigstens・dieser Zwekkeへの照応を一文として確認した。直後の服従と同じ人の学識者としての議論も同頁で確認した。'),
                adopted_reading=LIMITS,
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (
                    IMAGE, INVENTORY, 'data/use-definitions-evidence-v1.json')})


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    parts = [
        ('Nun ', ['uf', 'ue', 'r3g'], '先行私的使用定義に続く説明への移行。'),
        ('ist zu manchen Geschäften, ', ['r3d', 'r2zt'], '不特定の事務についての非全称・非空の存在読み。具体件数は固定しない。'),
        ('die in das Interesse des gemeinen Wesens laufen, ', ['h236w', 'h237i', 'r3c'], '同じ共同体の共通の利害に関わる事務。'),
        ('ein gewisser Mechanism nothwendig, ', ['h236y', 'h237h', 'r2zx', 'r2zw'], '同じ事務に必要な制度的仕組みとその利用可能性。'),
        ('vermittelst dessen ', ['h237f', 'r3b', 'h237u'], '同じ機構の役割割当てと目的への仕方を保つ。'),
        ('einige Glieder des gemeinen Wesens ', ['h237d', 'h237c', 'r2zn'], '同じ共同体に属する固定した非空の人々。全員への一般化や特定人数は加えない。'),
        ('sich bloß passiv verhalten müssen, ', ['r2zu', 'r2zv', 'r2zs', 'r3b'], '職務上の受動的遂行を求める。要求と実際の遂行を分ける。'),
        ('um ', ['h237u', 'r3c'], '同じ遂行内容を後続の目的へ向けた仕方として引用する。'),
        ('durch eine künstliche Einhelligkeit ', ['h237o', 'h237p', 'h237q', 'h237r', 'r3a'], '同じ機構が支える人為的な実務上の協調を手段とする。'),
        ('von der Regierung ', ['h237m', 'h237n', 'h237s', 'h237t'], '同じ共同体の公的運営を指揮する政府を両代替の主体とする。'),
        ('zu öffentlichen Zwekken gerichtet, ', ['h237k', 'h237l', 'h237s', 'r3e'], '同じ事務の公的目的へ本人の振る舞いを方向付ける。'),
        ('oder wenigstens ', ['r2zo', 'h237v', 'r3g'], '包含的な代替として、第二を控えめな最低限に位置付ける。'),
        ('von der Zerstörung dieser Zwekke abgehalten zu werden.', ['h237k', 'h237t', 'r3f'], '同じ目的を本人が破壊することを抑止する。達成や破壊の実行を含意しない。'),
    ]
    cursor, clauses = 1294, []
    for text, names, meaning in parts:
        assert unit['text'][cursor:cursor + len(text)] == text, (cursor, text)
        assert all(n in catalog().entries for n in names)
        clauses.append(dict(range=[cursor, cursor + len(text)], text=text, definitions=names, reading=meaning))
        cursor += len(text)
    assert cursor == 1660
    text = unit['text'][1294:1660]
    count = sum(not c.isspace() for c in text)
    validate_hashes(ROOT, read(EVIDENCE)['source_sha256'])
    return dict(status='public_purpose_mechanism_sentence_reviewed_under_explicit_reading',
                reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[1294, 1660], text=text),
                selection=selection_binding(catalog(), [79]), clauses=clauses,
                interpretation=LIMITS, unresolved=[],
                decision='equivalent_under_stated_reading_for_the_mechanism_sentence',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=count, newly_reviewed_sentence_characters=count,
                preserved_reviewed_sentence_characters=1106,
                paragraph_reviewed_sentence_characters=1106 + count,
                semantic_equivalence_automatically_proved=False,
                holistic_review=[
                    '主節の必要性・成員の要求を保持したまま、目的節を同じ事務・人々・役割・機構へ束縛した。',
                    '人為的協調の同じ配置を、機構の作用と政府による二つの効果へ渡している。',
                    '目的の公共性と政府の管轄を保持し、閉じた同じ目的記述がdieser Zwekkeの照応先になっている。',
                    'umの内側を実際の成功へ交換せず、要求・目的・履行・帰属の作用域を分けた。',
                    'wenigstensの最低限の提示とNunの説明への移行を、単なる併置だけに落としていない。',
                    '人数・事務数を特定しない存在読み、職務上の受動性、分配的な包含選言を採用解釈として明記した。',
                ],
                original_page=dict(path=IMAGE, page=485, visually_inspected=True),
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (
                    FULL, BASIS, ANNOTATIONS, DOC, EVIDENCE, INVENTORY, IMAGE, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:79] == old.document['statements']
    assert len(new.document['statements']) == 80
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    for n in ('r2zo', 'r2zp', 'r2zq', 'r2zr'):
        assert new.entries[n]['declaration'] == library().entries[n]['declaration']
        assert new.entries[n]['meaning_ja'] == library().entries[n]['meaning_ja']
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    assert read(EVIDENCE) == evidence()
    assert read(AUDIT) == reading()
    prior = read('data/use-definitions-reading-v1.json')
    assert prior['selection'] == selection_binding(new, [76, 77])
    validate_hashes(ROOT, prior['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=79, added_statements=1,
                preserved_whole_unit_reviews=len(reviews), old_meanings_unchanged=True,
                new_reviewed_sentence_characters=read(AUDIT)['newly_reviewed_sentence_characters'],
                roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / EVIDENCE, encoded(evidence()))
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('target', target_checks), ('means', means_checks), ('purpose', purpose_checks),
                     ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, EVIDENCE, DOC, INVENTORY, IMAGE, *PRIOR,
        'data/use-definitions-reading-v1.json', 'scripts/compose_public_purpose_mechanism.py',
        'scripts/check_public_purpose_mechanism.py', 'tests/test_public_purpose_mechanism.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='public_purpose_mechanism_sentence_under_explicit_reading', document=FULL,
                **results, alignment=dict(**read(AUDIT)['source'], statements=[79],
                    definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
