"""Check the whole clerical sentence, same-case explanation and attribution."""
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
from scripts.compose_clerical_obligation import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, NAMES, PRIMITIVES, MEANINGS, LIMITS, parent, dependencies, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v170.json'
REPORT = 'reports/clerical-obligation-v1.json'
AUDIT = 'data/clerical-obligation-reading-v1.json'
DOC = 'docs/clerical-obligation-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
EVIDENCE = 'data/officer-example-evidence-v1.json'
IMAGE = 'artifacts/officer-example-v1/page-486.jpg'
LEXICAL = 'data/clerical-teaching-lexical-v1.json'
PRIOR = tuple('reports/' + n + '-v1.json' for n in (
    'public-civic-opinion', 'clerical-audiences', 'confessional-teaching', 'ranked-appointment', 'teaching-policy'))
DOMAIN = ('x', 'y')
SCENES = ('past', 'reference', 'outcome')
DISCOURSE_DOMAIN = ('author', 'prior', 'priorpublic', 'sentence', 'main', 'reason', 'other')


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(target='r36k', boundaries=('r35t',)):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']]); d.pop('body')
    doc.update(declarations=closure(doc, [target]), statements=[])
    query = 'k ' + target + '[]'
    if target != 'r36l': query = 't[' + query + '][k zpoint[]]'
    return parse(format_graph(doc, 'compact') + 'r zpoint[] d.q[' + query + '].')


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(h232v=lambda: 'reference', zpoint=lambda: 'outcome')
    return v


def native_model(doc, required=True, appointed=True, variant='baseline'):
    v = base(doc); case = ('x',) * len(NAMES)
    v['r35t'] = lambda *args: variant != 'no_case' and args == (*case, 'reference')
    def target(code, bindings, ref, positive, prefix):
        wanted = tuple('y' if variant == prefix + '_binding_' + n else 'x' for n in NAMES)
        return (symbol(code), code.rank, tuple(bindings.items), ref, positive) == (
            'r35w' if variant == prefix + '_target' else 'r36e', 1, wanted,
            'past' if variant == prefix + '_reference' else 'reference', variant != prefix + '_polarity')
    v.update(h237z=lambda source, person, role, code, bindings, ref, sign, point: required and
        (source, person, role, point) == ('x', 'x', 'x', 'outcome') and target(code, bindings, ref, sign, 'duty'),
        h223k=lambda event, source, person, role, point: appointed and (event, source, person, role, point) == ('x', 'x', 'x', 'x', 'past'),
        h246m=lambda event, code, bindings, ref, sign, point: (event, point) == ('x', 'past') and target(code, bindings, ref, sign, 'terms'),
        ia=lambda person, anchor, point: person == 'x' and anchor in SCENES and point in SCENES,
        ic=lambda first, last, anchor: first in SCENES and last in SCENES and anchor in SCENES and SCENES.index(first) < SCENES.index(last),
        dg=lambda event, point: (event, point) == ('x', 'past'),
        cf=lambda person, role, point: (person, role, point) == ('x', 'x', 'past'))
    return v


@lru_cache(None)
def native_checks():
    rows = []
    for required, appointed in product((False, True), repeat=2):
        values = []
        for target in ('r36i', 'r36j', 'r36k'):
            doc = fixture(target); v = native_model(doc, required, appointed)
            assert all(v[n] is unknown for n in ('h246n', 'h246o', 'h246p', 'h246j', 'h246l'))
            values += evaluate(doc, v, DOMAIN, SCENES, True)
        assert values == [required, appointed, required and appointed], (required, appointed, values)
        rows.append(dict(required=required, appointed=appointed, results=values))
    return dict(cases=rows, native_policy_requirement_and_past_appointment_evaluated=True,
        quoted_policy_and_teaching_not_executed=True,
        boundary='r35t is the fixed case boundary; its native clerical, institutional and audience definitions are checked in the pinned dependencies.')


@lru_cache(None)
def identity_checks():
    rows = {}
    for prefix, target in [('duty', 'r36i'), ('terms', 'r36j')]:
        doc = fixture(target)
        for field in ('target', 'reference', 'polarity', *('binding_' + n for n in NAMES)):
            variant = prefix + '_' + field
            actual = evaluate(doc, native_model(doc, variant=variant), DOMAIN, SCENES, True)
            assert actual == [False], (variant, actual); rows[variant] = actual[0]
    return dict(contrasts=rows, same_nine_individuals_reference_and_positive_policy_in_both_clauses=True,
        individual_activity_target_cannot_replace_standing_policy=True)


@lru_cache(None)
def scope_checks():
    doc = fixture('r36k', ('r35t', 'r36f', 'r36g')); rows = {}
    for position in range(len(NAMES)):
        second = tuple('y' if i == position else 'x' for i in range(len(NAMES)))
        cases = {('x',) * len(NAMES), second}
        for fail in ('none', 'duty', 'appointment'):
            v = base(doc); calls = set()
            def case(*args):
                assert args[-1] == 'reference'; calls.add(args[:-1]); return args[:-1] in cases
            def conclusion(kind):
                return lambda *args: Content(SCENES, tuple(args[-1] == 'reference' and
                    not (fail == kind and args[:-1] == second and point == 'outcome') for point in SCENES))
            v.update(r35t=case, r36f=conclusion('duty'), r36g=conclusion('appointment'))
            actual = evaluate(doc, v, DOMAIN, SCENES, True)
            assert actual == [fail == 'none'] and calls == set(product(DOMAIN, repeat=len(NAMES))), (position, fail, actual)
            rows[NAMES[position] + '_' + fail] = actual[0]
    v = base(doc); absent = lambda *args: Content(SCENES, (False,) * len(SCENES))
    v.update(r35t=lambda *args: False, r36f=absent, r36g=absent)
    assert evaluate(doc, v, DOMAIN, SCENES, True) == [True]
    return dict(contrasts=rows, all_nine_case_fields_quantified=True, no_existential_unique_person_added=True,
        boundaries=['r35t is checked in prior native dependencies.', 'r36f/r36g are evaluated natively in native_checks.'])


def discourse_model(doc, variant='baseline'):
    v = base(doc)
    v.update(h246q=lambda: 'sentence', h246r=lambda: 'main', h246s=lambda: 'reason',
        h245f=lambda: 'prior', h245u=lambda: 'priorpublic', wa=lambda: 'author', h232o=lambda: 'reference')
    def claim(node, author, code, ctx):
        expected = {'sentence': 'r36k', 'main': 'r36i', 'reason': 'r36j'}
        if variant == 'swapped_clause_contents': expected.update(main='r36j', reason='r36i')
        return node in expected and (author, symbol(code), code.rank, ctx) == (
            'other' if variant == 'other_author' else 'author', expected[node], 3,
            'outcome' if variant == 'other_context' else 'reference') and not (variant == 'missing_reason_claim' and node == 'reason')
    def explanation(author, premises, conclusion, ctx):
        return variant != 'no_explanation' and (author, conclusion, ctx) == ('author', 'main', 'reference') and {
            n for n in DISCOURSE_DOMAIN if premises(n)} == ({'main'} if variant == 'reversed_explanation' else {'reason'})
    def parallel(node, author, prior, first, current, ctx):
        return variant != 'no_parallel' and (node, author, prior, symbol(first), first.rank,
            symbol(current), current.rank, ctx) == ('sentence', 'author', 'prior',
            'r35i' if variant == 'public_opinion_as_constraint' else 'r34x', 3,
            'r36i' if variant == 'only_main_as_whole' else 'r36k', 3, 'reference')
    def order(first, last, ctx):
        pairs = {('priorpublic', 'sentence'), ('main', 'reason')}
        if variant == 'wrong_predecessor': pairs.remove(('priorpublic', 'sentence'))
        if variant == 'reversed_clause_order': pairs.remove(('main', 'reason'))
        return (first, last) in pairs and ctx == 'reference'
    v.update(h236i=claim, ud=explanation, h245m=parallel, ue=order)
    return v


@lru_cache(None)
def discourse_checks():
    doc, rows = fixture('r36l', ()), {}
    for variant in ('baseline', 'swapped_clause_contents', 'other_author', 'other_context', 'missing_reason_claim',
        'no_explanation', 'reversed_explanation', 'no_parallel', 'public_opinion_as_constraint',
        'only_main_as_whole', 'wrong_predecessor', 'reversed_clause_order'):
        v = discourse_model(doc, variant)
        assert all(v[n] is unknown for n in ('h237z', 'h246m', 'h246n', 'h246j'))
        actual = evaluate(doc, v, DISCOURSE_DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual); rows[variant] = actual[0]
    # Even permissive attribution callbacks cannot merge the clause nodes.
    v = discourse_model(doc); v.update(h246s=lambda: 'main', h236i=lambda *args: True,
        ud=lambda *args: True, h245m=lambda *args: True, ue=lambda *args: True)
    assert evaluate(doc, v, DISCOURSE_DOMAIN, SCENES, True) == [False]
    return dict(contrasts=rows, separate_attribution_reason_parallelism_and_order=True,
        exact_single_reason_node=True, clause_nodes_remain_distinct=True, quoted_world_content_not_executed=True)


@lru_cache(None)
def unknown_checks():
    rows = []
    for target, names, model, domain in [('r36k', ('h237z', 'h246m', 'h223k'), native_model, DOMAIN),
        ('r36l', ('h236i', 'ud', 'h245m'), discourse_model, DISCOURSE_DOMAIN)]:
        doc = fixture(target, () if target == 'r36l' else ('r35t',))
        for name in names:
            v = model(doc); v[name] = unknown
            try: evaluate(doc, v, domain, SCENES, True)
            except ValueError as error: assert 'Unknown' in str(error), str(error)
            else: raise AssertionError(name)
            rows.append(name)
    return dict(unknown_relations_refused=rows, full_description_domain_preserved_by_pinned_teaching_policy=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    parts = [
        ('Eben so ', ['h245m', 'r36l'], '先行する市民の役割上の制約の例に並べて聖職者の職務を提示する。'),
        ('ist ein Geistlicher verbunden, ', ['r35m', 'r35t', 'r36f', 'r36i'], '同じ聖職者の一般的職務事例について、教示方針への制度上の要求を述べる。'),
        ('seinen Katechismusschülern ', ['r35n', 'r35o', 'r35q', 'r36d'], '同じ本人・職務・教会の初歩的な宗教問答の生徒全体への教示担当を保持する。'),
        ('und seiner Gemeine ', ['r35p', 'r35q', 'r36d'], '同じ本人に同じ職務で配慮が委ねられた会衆を加え、両方の宛先の担当網羅を保つ。'),
        ('nach dem Symbol der Kirche, ', ['r35r', 'r35s', 'r356', 'r36a', 'r36b'], '同じ教会が採用した信条に沿う同じNoema条件列を、実行教示の基準として用いる。'),
        ('der er dient, ', ['h246k', 'r35t', 'r356', 'r36a'], '信条を採用する同じ教会に同じ本人・職務で仕える関係。'),
        ('seinen Vortrag zu thun; ', ['r356', 'r357', 'r36c', 'r36d', 'r36e', 'r36f'], '本人による説明・教示を職務上の全担当機会に求める。実際の履行・信仰・教義の真理とは別。'),
        ('denn ', ['ud', 'r36l'], '同じ条件での任用を、著者が教示義務の理由として提示する。'),
        ('er ist auf diese Bedingung ', ['r36f', 'r36g', 'r36j'], '本人・役割・教会と、義務の同じ一般方針記述・九個体列・基準・正極性を受ける。'),
        ('angenommen worden.', ['r35x', 'r35y', 'r36g', 'r36j'], '同じ過去時点に生起した同じ任用行為と、その条件を結ぶ。採用前の履行や現在の義務を任用だけから導かない。'),
    ]
    cursor, clauses = 2984, []
    for text, names, meaning in parts:
        assert unit['text'][cursor:cursor + len(text)] == text, (cursor, text)
        clauses.append(dict(range=[cursor, cursor + len(text)], text=text, definitions=names, reading=meaning)); cursor += len(text)
    assert cursor == 3185
    text = unit['text'][2984:3185]; count = sum(not c.isspace() for c in text); assert count == 171
    page = next(p for p in read(EVIDENCE)['pages'] if p['page'] == 486)
    assert digest((ROOT / IMAGE).read_bytes()) == page['sha256']
    return dict(status='clerical_obligation_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[2984, 3185], text=text),
        selection=selection_binding(catalog(), [86]), clauses=clauses, interpretation=LIMITS, unresolved=[],
        decision='equivalent_under_stated_reading_for_teaching_obligation_and_appointment_explanation',
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        newly_reviewed_sentence_characters=count, preserved_reviewed_sentence_characters=2557,
        paragraph_reviewed_sentence_characters=2557 + count, semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊486頁で先行市民の制約と公的見解、Eben soからangenommen wordenまで、次のAber als Gelehrterの開始を通読した。今回の全文範囲を連続した各節に対応させた。',
            '聖職者・役割・教会を同じ任用・奉仕の組へ結び、二つの宛先をそれぞれ完全な生徒・会衆範囲として保持した。Symbolを信条、Kircheを共同の立場と宗教的実践を持つ組織として読む。',
            '一般的な職務教示を一回の講義へ狭めず、全担当機会と全宛先の割当を方針内に置いた。生徒と会衆が別の機会に教えられることを許し、代替活動全ての実行は要求しない。',
            '各担当期間に少なくとも一つの適合した提示を求め、実際の追加教示も同じ基準に適合させる。未実行、不適合の発言、担当漏れを成功例だけで隠さない。',
            '同じ信条・主題・条件列を採用と基準評価に共有し、内容の真理・本人の確信・受け手の理解を自動条件にしない。本文の要求を評価しても教示を実行しない。',
            '同じ一般方針記述・九個体束縛・基準・正極性を、現在の要求と過去任用の条件の両方へ渡す。任用行為と過去時点は同じ一組であり、別条件へのすり替えを許さない。',
            '主節と任用節を独立した内容として保持し、dennは著者が後者を前者の根拠として提示する関係とする。両者の併存だけで説明を補わず、普遍的な論理導出や正当性の証明にも変えない。',
            'Eben soの並列先は市民の役割上の制約の例であり、直前の公的見解の不違反を義務の根拠にしない。本文順序は直前文から保持する。',
            '全文と両節の段階3の帰属を確認しても引用内容の真理を実行しない。有限診断例、型付き境界、全発話記述域の拒否と、明示解釈による通読判断を区別した。'],
        original_page=page, source_sha256={p: digest((ROOT / p).read_bytes()) for p in (
            FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, EVIDENCE, IMAGE, LEXICAL, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:86] == old.document['statements'] and len(new.document['statements']) == 87
    assert all(new.entries[n] == e for n, e in old.entries.items())
    for lib in dependencies():
        for n, e in lib.entries.items():
            assert new.entries[n]['declaration'] == e['declaration'] and new.entries[n]['meaning_ja'] == e['meaning_ja'], n
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for p in PRIOR: validate_hashes(ROOT, read(p)['source_sha256'])
    prior = read('data/public-civic-opinion-reading-v1.json')
    assert prior['selection'] == selection_binding(new, [85]); validate_hashes(ROOT, prior['source_sha256'])
    validate_hashes(ROOT, {s['raw_archive']: s['raw_sha256'] for s in read(LEXICAL)['sources']})
    assert read(AUDIT) == reading()
    for p, s in build().items(): assert (ROOT / p).read_text(encoding='utf-8') == s, p
    for p in (FULL, CORE):
        doc = parse((ROOT / p).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation); assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=86, added_statements=1, preserved_whole_unit_reviews=len(reviews),
        new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES), new_reviewed_sentence_characters=171, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for p, s in build().items(): write_exact(ROOT / p, s)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('native', native_checks), ('identity', identity_checks), ('scope', scope_checks),
        ('discourse', discourse_checks), ('unknown', unknown_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {INDEX, AUDIT, DOC, INVENTORY, EVIDENCE, IMAGE, LEXICAL, *PRIOR,
        'data/public-civic-opinion-reading-v1.json', 'scripts/compose_clerical_obligation.py', 'scripts/check_clerical_obligation.py',
        'tests/test_clerical_obligation.py', 'scripts/compose_civic_example.py', 'scripts/compose_confessional_teaching.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='clerical_teaching_duty_with_same_appointment_explanation', document=FULL, **results,
        alignment=dict(**read(AUDIT)['source'], statements=[86], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
