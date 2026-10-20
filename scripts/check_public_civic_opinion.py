"""Check the integrated public opinion conditional, references and discourse."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_public_civic_opinion import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, NAMES, FIELDS, PUBLIC, DETAILS, PRIMITIVES, MEANINGS, LIMITS,
    parent, dependencies, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_levy_opinions import expression_model

INDEX = 'data/semantic-review-index-v169.json'
REPORT = 'reports/public-civic-opinion-v1.json'
AUDIT = 'data/public-civic-opinion-reading-v1.json'
DOC = 'docs/public-civic-opinion-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
EVIDENCE = 'data/officer-example-evidence-v1.json'
IMAGE = 'artifacts/officer-example-v1/page-486.jpg'
LEXICAL = 'data/levy-opinions-lexical-v1.json'
PRIOR = tuple('reports/' + n + '-v1.json' for n in ('civic-example', 'levy-opinions', 'civic-noncontravention'))
CONSTANTS = tuple(dict.fromkeys((*NAMES, *DETAILS, 'reader', 'second', 'judgment', 'other')))
DOMAIN = CONSTANTS + ('author', 'prior', 'sentence')
SCENES = ('reference', 'outcome', 'other')
EXTRA = ''.join('r z' + n + '[] a.' for n in CONSTANTS) + 'r zref[] d.r zpoint[] d.'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind, target=None):
    target = target or dict(conditional='r35g', details='r35h', cases='r35i', discourse='r35l', domain='r35g', branch='r35j')[kind]
    boundaries = dict(conditional=('r35f',), details=('r35g',), cases=('r33w', 'r35h'), domain=('r347',)).get(kind, ())
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']]); d.pop('body')
    doc.update(declarations=closure(doc, [target]), statements=[])
    names = dict(conditional=FIELDS, details=('person', 'role', 'community', 'levy'), cases=(),
                 discourse=(), domain=FIELDS, branch=PUBLIC)[kind]
    args = ' '.join('k z' + n + '[]' for n in names) + (' k zref[]' if names else '')
    call = 'k ' + target + '[' + args + ']'
    if kind != 'discourse': call = 't[' + call + '][k zpoint[]]'
    return parse(format_graph(doc, 'compact') + EXTRA + 'q[' + call + '].')


def base(doc):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in CONSTANTS: values['z' + n] = lambda n=n: n
    values.update(zref=lambda: 'reference', zpoint=lambda: 'outcome', h232v=lambda: 'reference')
    return values


def conditional_model(doc, spoken=True, conforms=True, variant='baseline'):
    v = base(doc)
    v.update({n: f for n, f in expression_model(doc, 'baseline' if spoken else 'no_own_judgment').items() if f is not unknown})
    def conformity(person, role, activity, community, reference):
        expected = ('person', 'scholar' if variant == 'scholar_as_civic_role' else 'role',
            'other' if variant == 'other_activity' else 'activity',
            'other' if variant == 'other_community' else 'community',
            'other' if variant == 'other_reference' else 'reference')
        if variant == 'other_person': expected = ('other', *expected[1:])
        return Content(SCENES, tuple(conforms and (person, role, activity, community, reference) == expected and
            point == ('other' if variant == 'other_point' else 'outcome') for point in SCENES))
    v['r35f'] = conformity
    return v


@lru_cache(None)
def conditional_checks():
    doc, rows = fixture('conditional'), []
    for spoken, conforms in product((False, True), repeat=2):
        v = conditional_model(doc, spoken, conforms)
        assert v['h245n'] is unknown and v['h245o'] is unknown
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [not spoken or conforms], (spoken, conforms, actual)
        rows.append(dict(spoken=spoken, conforms=conforms, conditional=actual[0]))
    contrasts = {}
    for variant in ('other_person', 'scholar_as_civic_role', 'other_activity', 'other_community', 'other_reference', 'other_point'):
        actual = evaluate(doc, conditional_model(doc, variant=variant), DOMAIN, SCENES, True)
        assert actual == [False], (variant, actual); contrasts[variant] = actual[0]
    return dict(cases=rows, contrasts=contrasts, native_public_expression_antecedent=True,
        conformity_typed_boundary='r35f backed by reports/civic-noncontravention-v1.json',
        same_actor_civic_role_activity_community_reference_point=True, expression_truth_not_exported=True)


@lru_cache(None)
def detail_checks():
    doc, rows = fixture('details'), {}
    for fail_second in (False, True):
        v = base(doc)
        for n in ('person', 'role', 'community', 'levy'): v['z' + n] = lambda: 'x'
        calls = set()
        def conditional(person, role, act, community, scholar, audience, levy, ref):
            assert (person, role, community, levy, ref) == ('x', 'x', 'x', 'x', 'reference')
            calls.add((act, scholar, audience))
            return Content(SCENES, tuple(not (fail_second and (act, scholar, audience, point) ==
                ('y', 'x', 'y', 'outcome')) for point in SCENES))
        v['r35g'] = conditional
        actual = evaluate(doc, v, ('x', 'y'), SCENES, True)
        assert actual == [not fail_second] and calls == set(product(('x', 'y'), repeat=3))
        rows[str(fail_second)] = actual[0]
    return dict(cases=rows, native_three_argument_quantification=True, typed_boundary='r35g checked natively in conditional_checks')


@lru_cache(None)
def case_checks():
    doc, rows = fixture('cases'), {}
    for fail_second in (False, True):
        v = base(doc); calls = set()
        # The two cases differ in person and levy while sharing the community
        # and civic role; an unrelated case must not supply their conclusion.
        cases = {('x',) * 8, ('y', 'x', 'x', 'y', 'x', 'x', 'x', 'x')}
        def levy_case(*args):
            assert args[-1] == 'reference'; calls.add(args[:-1]); return args[:-1] in cases
        def conclusion(person, role, community, levy, ref):
            assert ref == 'reference'
            return Content(SCENES, tuple(not (fail_second and (person, role, community, levy, point) ==
                ('y', 'x', 'x', 'y', 'outcome')) for point in SCENES))
        v.update(r33w=levy_case, r35h=conclusion)
        actual = evaluate(doc, v, ('x', 'y'), SCENES, True)
        assert actual == [not fail_second] and calls == set(product(('x', 'y'), repeat=8)), actual
        rows[str(fail_second)] = actual[0]
    return dict(cases=rows, all_eight_levy_arguments_quantified=True, second_case_person_and_levy_preserved=True,
        typed_boundaries=['r33w backed by civic-levy-refusal', 'r35h checked in detail_checks'])


@lru_cache(None)
def branch_checks():
    rows = {}
    for branches in ((), ('unsuitable',), ('unjust',), ('unsuitable', 'unjust')):
        actual = []
        for target in ('r35j', 'r35k', 'r347'):
            doc = fixture('branch', target); v = base(doc)
            v.update({n: f for n, f in expression_model(doc, branches=branches).items() if f is not unknown})
            actual += evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == ['unsuitable' in branches, 'unjust' in branches, bool(branches)], (branches, actual)
        rows[str(branches)] = actual
    return dict(cases=rows, native_alternatives_match_actual_antecedent=True,
        either_or_both_allowed=True, no_first_alternative_presupposed=True)


def discourse_model(doc, variant='baseline'):
    v = base(doc); v.update(h245u=lambda: 'sentence', h245f=lambda: 'prior', wa=lambda: 'author', h232o=lambda: 'reference')
    v['h236i'] = lambda node, author, code, ctx: (node, author, symbol(code), code.rank, ctx) == (
        'sentence', 'author', 'r35i', 3, 'reference')
    def pair(node, author, first, old, second, new, dimension, ctx):
        return (node, author, first, symbol(old), old.rank, second, symbol(new), new.rank,
            symbol(dimension), dimension.rank, ctx) == ('sentence', 'author', 'prior',
            'r34u' if variant == 'wrong_prior' else 'r34x', 3, 'sentence',
            'r35h' if variant == 'wrong_current' else 'r35i', 3,
            'r35j' if variant == 'wrong_dimension' else 'r2zg', 0,
            'other' if variant == 'wrong_context' else 'reference')
    v['h236k'] = pair
    v['h245v'] = lambda *args: variant != 'missing_concession' and pair(*args)
    def addition(node, author, outer, first, second, ctx):
        return (node, author, symbol(outer), outer.rank, symbol(first), first.rank, symbol(second), second.rank, ctx) == (
            'sentence', 'author', 'r35i', 3, 'r35k' if variant == 'swapped_alternatives' else 'r35j', 1,
            'r35j' if variant == 'swapped_alternatives' else 'r35k', 1, 'reference') and variant != 'missing_addition'
    v['h245w'] = addition
    v['ue'] = lambda first, second, ctx: variant != 'wrong_order' and (first, second, ctx) == ('prior', 'sentence', 'reference')
    return v


@lru_cache(None)
def discourse_checks():
    doc, rows = fixture('discourse'), {}
    for variant in ('baseline', 'wrong_prior', 'wrong_current', 'wrong_dimension', 'wrong_context',
                    'missing_concession', 'missing_addition', 'swapped_alternatives', 'wrong_order'):
        v = discourse_model(doc, variant)
        assert all(v[n] is unknown for n in ('h245s', 'h245t', 'h245n', 'h245o', 'h7a', 'h237z'))
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual); rows[variant] = actual[0]
    return dict(contrasts=rows, attribution_concession_contrast_addition_order_preserved=True,
        all_quoted_world_contents_unevaluated=True)


@lru_cache(None)
def domain_unknown_checks():
    doc = fixture('domain'); v = base(doc)
    v.update(r347=lambda *args: Content(SCENES, (True,) * 3), aa=lambda p: True,
        h237c=lambda *args: True, hzwn=lambda *args: True, h244g=lambda *args: True, h245d=lambda *args: 'issuer')
    try: evaluate(doc, v, DOMAIN, SCENES, True)
    except ValueError as error:
        assert 'Cannot finitely quantify the description domain' in str(error); refusal = str(error)
    else: raise AssertionError('Integrated conformity lost the full description domain')
    unknowns = []
    for kind, model, names in (('conditional', conditional_model, ('r35f', 'h245q')),
                               ('discourse', discourse_model, ('h245v', 'h245w'))):
        doc = fixture(kind)
        for name in names:
            v = model(doc); v[name] = unknown
            try: evaluate(doc, v, DOMAIN, SCENES, True)
            except ValueError as error: assert 'Unknown' in str(error), str(error)
            else: raise AssertionError(name)
            unknowns.append(name)
    return dict(full_domain_refused=refusal, unknown_inputs_refused=unknowns)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    parts = [
        ('Eben derselbe ', ['r33w', 'r35h', 'r35i'], 'まさに先行事例の同じ市民本人を受け、共同体・市民の立場・賦課も保持する。'),
        ('handelt demohngeachtet ', ['h236k', 'h245v', 'r35l'], '先行制約を認めても同じ人の学識者活動の不違反を退けない譲歩対照。'),
        ('der Pflicht eines Bürgers nicht entgegen, ', ['r35a', 'r35b', 'r35c', 'r35d', 'r35e', 'r35f'], '同じ活動について市民の立場で評価する全要求への不違反。生活全体の履行や許可とは別。'),
        ('wenn er, ', ['r35g', 'r35h', 'r35i'], '同じ本人の次の公的表出を前件とする条件。表出の現実の実行を別に断言しない。'),
        ('als Gelehrter, ', ['r2zi', 'r347'], '同じ本人の同じ活動を学識者として行う公的理性使用。'),
        ('wider die Unschiklichkeit ', ['r342', 'r344', 'r346', 'r35j'], '同じ賦課の事情への適合条件の不足を本人の批判的見解として表す第一の代替。'),
        ('oder auch ', ['r347', 'r35j', 'r35k', 'h245w'], '第二の批判も選言の代替として加える。両方必須や第一の成立を前提にしない。'),
        ('Ungerechtigkeit ', ['r343', 'r345', 'r346', 'r35k'], '同じ賦課の権利・権原・公平の条件の不足を本人の批判的見解として表す第二の代替。'),
        ('solcher Ausschreibungen ', ['r33w', 'r35i', 'r347'], '先行する同じ公的賦課を対象として保持する。'),
        ('öffentlich ', ['r2zi', 'cc', 'ce', 'r347'], 'その同じ活動が本来の全読者世界へ向けられる。全員の受領は不要。'),
        ('seine Gedanken äußert.', ['fa', 'h245q', 'h245r', 'h245p', 'h244n', 'r346'], '同じ本人の判断内容を同じ提示活動で表す。内容の真理や他人の判断の中立的紹介へ変えない。'),
    ]
    cursor, clauses = 2771, []
    for text, names, meaning in parts:
        assert unit['text'][cursor:cursor + len(text)] == text, (cursor, text)
        clauses.append(dict(range=[cursor, cursor + len(text)], text=text, definitions=names, reading=meaning)); cursor += len(text)
    assert cursor == 2983
    text = unit['text'][2771:2983]; count = sum(not c.isspace() for c in text)
    page = next(p for p in read(EVIDENCE)['pages'] if p['page'] == 486)
    assert digest((ROOT / IMAGE).read_bytes()) == page['sha256']
    return dict(status='public_civic_opinion_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[2771, 2983], text=text),
        selection=selection_binding(catalog(), [85]), clauses=clauses, interpretation=LIMITS, unresolved=[],
        decision='equivalent_under_stated_reading_for_public_opinion_and_civic_noncontravention',
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        newly_reviewed_sentence_characters=count, preserved_reviewed_sentence_characters=2370,
        paragraph_reviewed_sentence_characters=2370 + count, semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊486頁のEben derselbeからäußertまでを先行市民の文と次の聖職者の例の開始とともに通読した。文の全範囲を各節へ対応させた。',
            '同じ賦課事例の本人・共同体・市民役割・賦課への参照を共有する。先行の実際の拒否や出過ぎた批判・処罰は条件に追加しない。',
            '学識者としての公的表出と、市民としての同じ活動の義務適合を条件の両側で別々の役割として保持した。',
            '本人の二種の批判的判断を選言の二代替とし、本人自身の判断と実際の表出、内容の真理を分けた。auchの追加は条件内に置く。',
            '全読者世界への宛先を保持し、全員の理解・賛同や書面を追加しない。不正義という見解の現実の真理も要求しない。',
            '現在の三要求形式について完全適用範囲と全記述・全束縛域を保ち、有限の既知要求だけへの適合へ縮めない。生活全体の無過失や納付済み、積極的許可とはしない。',
            '先行する制約と現在の条件付き不違反を同じ公私使用の観点で対照し、先行内容の撤回や論理矛盾に変えない。',
            '段階3の著者帰属と談話関係を確認しても、引用内容の現実の真理を実行しない。採用解釈と形式的範囲の限界を記録した。'],
        original_page=page, source_sha256={p: digest((ROOT / p).read_bytes()) for p in (
            FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, EVIDENCE, IMAGE, LEXICAL, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:85] == old.document['statements'] and len(new.document['statements']) == 86
    assert all(new.entries[n] == e for n, e in old.entries.items())
    for lib in dependencies():
        for n, e in lib.entries.items():
            assert new.entries[n]['declaration'] == e['declaration'] and new.entries[n]['meaning_ja'] == e['meaning_ja'], n
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for p in PRIOR: validate_hashes(ROOT, read(p)['source_sha256'])
    prior = read('data/civic-example-reading-v1.json')
    assert prior['selection'] == selection_binding(new, [84]); validate_hashes(ROOT, prior['source_sha256'])
    validate_hashes(ROOT, {s['raw_archive']: s['raw_sha256'] for s in read(LEXICAL)['sources']})
    assert read(AUDIT) == reading()
    for p, s in build().items(): assert (ROOT / p).read_text(encoding='utf-8') == s, p
    for p in (FULL, CORE):
        doc = parse((ROOT / p).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation); assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=85, added_statements=1, preserved_whole_unit_reviews=len(reviews),
        new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES), new_reviewed_sentence_characters=187, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for p, s in build().items(): write_exact(ROOT / p, s)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('conditional', conditional_checks), ('details', detail_checks), ('cases', case_checks),
                     ('branches', branch_checks), ('discourse', discourse_checks), ('domains_unknown', domain_unknown_checks),
                     ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {INDEX, AUDIT, DOC, INVENTORY, EVIDENCE, IMAGE, LEXICAL, *PRIOR,
        'data/civic-example-reading-v1.json', 'scripts/compose_public_civic_opinion.py', 'scripts/check_public_civic_opinion.py',
        'tests/test_public_civic_opinion.py', 'scripts/check_levy_opinions.py', 'scripts/compose_civic_example.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='public_levy_opinion_without_civic_duty_contravention', document=FULL, **results,
        alignment=dict(**read(AUDIT)['source'], statements=[85], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
