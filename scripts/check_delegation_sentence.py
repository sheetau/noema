"""Audit the whole delegation conditional and expose its remaining lexical gap."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_falling_depiction import ROOT, closure
from scripts.check_service_roles import source_values, attribution_checks, PEOPLE
from scripts.check_pastoral_roles import evaluate, SOURCE_SCENES
from scripts.check_motive_causes import unknown, symbol
from scripts.fetch_delegation_sentence_evidence import PATH as EVIDENCE, validate

FULL = 'examples/v016/kant-service-roles.noema'
BASIS = 'data/service-roles-basis-v1.json'
INDEX = 'data/semantic-review-index-v55.json'
CORE = 'examples/v016/delegation-sentence-core.noema'
AUDIT = 'data/delegation-sentence-reading-v1.json'
REPORT = 'reports/delegation-sentence-v1.json'
DOC = 'docs/delegation-sentence-v1.md'


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def core():
    d = deepcopy(catalog().document)
    d['statements'] = [d['statements'][i] for i in (4, 42)]
    d['declarations'] = closure(d, _references(d['statements']))
    return format_graph(d, 'compact') + '\n'


@lru_cache(None)
def questions():
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, ['ss', 'st', 'su', 'sv', 'sx', 're', 's2', 'sy', 'wh']), statements=[])
    text = format_graph(d, 'compact') + 'r jp[] a.r js[] d.'
    for n in ('ss', 'st', 'su', 'sv', 'sx'):
        text += 'q[t[k ' + n + '[k jp[]]][k js[]]].'
    text += 'q[k re[k jp[] p sv i[scene d][k s2[k jp[] k wh[] v scene]]]].q[t[k sy[k jp[]]][k wh[]]].'
    return parse(text)


def composition_checks():
    rows = []
    for book, pastoral, physician, goal, effort_free in product((False, True), repeat=5):
        v = source_values(); access = v['sa']; attainment = v['sj']
        available = {w for w, bit in zip(('book', 'guide', 'doctor'), (book, pastoral, physician)) if bit}
        v['sa'] = lambda p, w, s: w in available and access(p, w, s)
        v['sj'] = lambda p, s: goal and attainment(p, s)
        v['hzwz'] = lambda a, p, m, s, e: not effort_free and (a, p, m, s, e) == ('person', 'person', 'plan', 'case', 'outcome')
        actual = evaluate(questions(), v, PEOPLE, SOURCE_SCENES, True)
        premise = book and pastoral and physician; conclusion = goal and effort_free
        wanted = [book, pastoral, physician, premise, conclusion, premise, not premise or conclusion]
        assert actual == wanted, (book, pastoral, physician, goal, effort_free, actual)
        rows.append(dict(book=book, pastoral=pastoral, physician=physician, goal=goal, effort_free=effort_free, values=actual))
    return dict(query_order=['book_example', 'pastoral_example', 'medical_example', 'premise', 'conclusion', 'applicable', 'conditional'],
        combinations=rows, definitions_replaced_by_primitives=False, pure_memoization=True,
        current_role_record_carrier_and_effort_definitions_executed=True)


def supply_checks():
    base = {('book', 'person', 'bm', 'case'), ('guide', 'person', 'sm', 'case'), ('doctor', 'person', 'sn', 'case')}
    variants = ('baseline', 'wrong_book_task', 'wrong_guide_recipient', 'wrong_doctor_scene', 'swap_tasks', 'self_provider')
    expected = {
        'baseline': [True, True, True], 'wrong_book_task': [False, True, True],
        'wrong_guide_recipient': [True, False, True], 'wrong_doctor_scene': [True, True, False],
        'swap_tasks': [False, False, True], 'self_provider': [False, True, True],
    }
    rows = {}
    for variant in variants:
        facts = set(base)
        if variant == 'wrong_book_task':
            facts.remove(('book', 'person', 'bm', 'case')); facts.add(('book', 'person', 'sm', 'case'))
        if variant == 'wrong_guide_recipient':
            facts.remove(('guide', 'person', 'sm', 'case')); facts.add(('guide', 'other', 'sm', 'case'))
        if variant == 'wrong_doctor_scene':
            facts.remove(('doctor', 'person', 'sn', 'case')); facts.add(('doctor', 'person', 'sn', 'text'))
        if variant == 'swap_tasks':
            facts = {('book', 'person', 'sm', 'case'), ('guide', 'person', 'bm', 'case'), ('doctor', 'person', 'sn', 'case')}
        if variant == 'self_provider':
            facts.remove(('book', 'person', 'bm', 'case')); facts.add(('person', 'person', 'bm', 'case'))
        v = source_values(); v['sb'] = lambda w, p, task, s: (w, p, symbol(task), s) in facts
        if variant == 'self_provider':
            # Give the person every book/access predicate of the old provider,
            # so exclusion is not merely caused by a missing provider kind.
            fold = lambda x: 'book' if x == 'person' else x
            for n in ('sc',):
                fn = v[n]; v[n] = lambda p, s, fn=fn: fn(fold(p), s)
            fn = v['hzwr']; v['hzwr'] = lambda r, w, s, fn=fn: fn(r, fold(w), s)
            fn = v['sa']; v['sa'] = lambda p, w, s, fn=fn: fn(p, fold(w), s)
        actual = evaluate(questions(), v, PEOPLE, SOURCE_SCENES, True)
        assert actual[:3] == expected[variant], (variant, actual)
        assert actual[3:] == [all(expected[variant]), True, all(expected[variant]), True]
        rows[variant] = actual
    # Ordinary evaluation of the same composite premise, including all roles.
    d = deepcopy(questions()); d['statements'] = d['statements'][:4]
    d['declarations'] = closure(d, _references(d['statements']))
    assert evaluate(d, source_values(), PEOPLE, SOURCE_SCENES) == [True] * 4
    for name in ('sa', 'sb'):
        v = source_values(); v[name] = unknown
        try:
            evaluate(d, v, PEOPLE, SOURCE_SCENES)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, ordinary_full_premise_agrees=True, unknown_inputs_refused=2,
        substituted_tasks_not_performed_by_recipient=True)


def lexical_gap_checks():
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, ['sp', 'st']), statements=[])
    # jclerical is an independent criterion used only in this audit fixture.
    # It is deliberately not a new production lexical definition.
    assert 'jclerical' not in catalog().entries
    doc = parse(format_graph(d, 'compact') + '''r jp[] a.r jr[] a.r js[] d.r jclerical[a d] c.
q[k sp[k jp[] k js[]]].q[t[k st[k jr[]]][k js[]]].q[k jclerical[k jp[] k js[]]].''')
    rows = []
    for clerical in (False, True):
        v = source_values(); v.update(jp=lambda: 'guide', jr=lambda: 'person', js=lambda: 'case',
            jclerical=lambda p, s: clerical and (p, s) == ('guide', 'case'))
        actual = evaluate(doc, v, PEOPLE, SOURCE_SCENES)
        assert actual == [True, True, clerical]
        rows.append(dict(clerical_status=clerical, values=actual))
    return dict(countermodels=rows, clergy_criterion_is_fixture_only=True,
        source_requires_review_of_clerical_status=True, current_sp_does_not_distinguish_status=True,
        all_sentence_semantics_verified=False,
        limitation='This countermodel witnesses a distinction absent from the declared predicates, under the stated historical clerical reading; it is not an empirical claim about a named counselor.')


def reading():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    start, end = unit['text'].index('Habe ich'), unit['text'].index('Ich habe nicht nöthig')
    while unit['text'][end-1].isspace():
        end -= 1
    text = unit['text'][start:end]
    markers = ('ein Buch', 'das für mich', 'einen Seelsorger', 'der für mich Gewissen', 'einen Arzt',
        'der für mich die Diät', 'u. s. w.', 'so brauche ich', 'ja nicht', 'nicht selbst')
    marks = [0] + [text.index(s) for s in markers] + [len(text)]
    rows = [
        ('hypothetical_first_person', ['s4', 'sy', 'sa'], '同じ本人を置く仮定例での利用可能性。著者自身の所持・生活の断言にはしない。'),
        ('written_work', ['sl', 'rqxp', 'rqxo'], '参照可能な書かれた作品を、その実際または予定された葉の集合の形と結ぶ。巻の区分・紙の数量単位の読みは採らない。'),
        ('substituted_understanding', ['ss', 'sb', 'bm'], '書物から供される表現が本人の理解力の使用に代わる。本を実際に思考する人とはしない。'),
        ('pastoral_provider', ['sp', 'rqxl'], '宗教上の援助を主要な務めとする継続的役割はあるが、歴史資料のGeistlicherという身分の条件は未表現。'),
        ('substituted_conscience', ['st', 'sm', 'se'], '本人自身の行為を道徳的要求に照らす判断の代行。感情・罪責の痛みなど全用法をこの箇所へ合併しない。'),
        ('medical_provider', ['sr', 'rqxv', 'hzxe'], '治療の判断と措置の提供を主要な務めとし、その専門性を要求する同じ役割として読む。その場の処置や本人の無誤謬性は追加しない。'),
        ('regimen_judgment', ['su', 'sn', 'sf'], '本人の食事と日々の生活の調整を判断する。Diätを現代の減量だけに狭めない。'),
        ('open_enumeration', ['sz', 's5'], '三例の原文順を保ち、網羅的な一覧とはしない。第四の供給元や例を特定して追加しない。'),
        ('consequence', ['rc', 'sv', 'sx', 'rd'], '同じ仮定上の本人について、三例を前件、選択できる同じ方法での目的達成と努力不要を後件へ結ぶ。'),
        ('recognizable_consequence', ['hzwy', 'hzwx'], '帰結を仮定の下で認めやすいものとして示す。現実の真理・読者全員の同意・態度への推奨は含めない。'),
        ('own_effort_not_needed', ['sx', 'sk', 'hzwz'], '問題となる判断の取組みについて、実施者が本人である努力を不要とする。他者の努力や本人の全活動を否定しない。'),
    ]
    clauses = [dict(id=n, range=[start+a, start+b], text=text[a:b], definitions=names, interpretation_ja=meaning,
        status='unresolved_clerical_status' if n == 'pastoral_provider' else 'mapped_under_stated_reading')
        for (n, names, meaning), a, b in zip(rows, marks[:-1], marks[1:], strict=True)]
    context_path = 'data/delegation-context-reading-v1.json'
    paths = (inv, FULL, BASIS, INDEX, context_path, EVIDENCE, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'data/book-form-evidence-v1.json', 'data/pastoral-role-evidence-v1.json', 'data/conscience-evidence-v1.json',
        'data/clinical-roles-evidence-v1.json', 'data/effort-agents-evidence-v1.json', 'data/recognizable-consequence-evidence-v1.json',
        'reports/book-form-v1.json', 'reports/conscience-reading-v1.json', 'reports/service-roles-v1.json',
        'data/delegation-reading-review-v1.json')
    return dict(status='whole_sentence_audited_with_an_explicit_remaining_lexical_gap', reviewer='assistant_review',
        decision='not_yet_equivalent_under_the_historical_clerical_reading',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, end], text=text,
            nonblank_characters=sum(not c.isspace() for c in text)), clauses=clauses,
        document=FULL, meaning_basis=BASIS, selection=selection_binding(catalog(), [4, 42]),
        context=json.loads((ROOT / context_path).read_text(encoding='utf-8'))['context'],
        references=[dict(page=482, image='artifacts/first-cause-reading-v1/page-482.jpg',
            url='https://www.digitale-sammlungen.de/de/view/bsb10926843?page=522')],
        findings=['一人称・三例・仕事の受け手・列挙順・条件・否定・jaの範囲を十一範囲へ分け、現行宣言へ照合した。',
            'Diätの生活秩序という読みを歴史資料で裏付けた。目的と努力は固定済みの文脈指定を使う。',
            'Seelsorgerの歴史資料はGeistlicherと記す。主要な宗教上の助言役だけでは、その身分の区別を保持したことにならない。'],
        interpretation_limits=['歴史辞典は語義選択の資料であり、作者の唯一の意図を証明しない。',
            '書物の全境界や全教派・時代の職制、医療制度をこの用例へ無制限に要求するものではない。必要な聖職身分の違いと語の全用法を分ける。',
            '批判的な談話の働きは前後の議論でも照合する。jaや一人称だけから著者の推奨や後件の偽を追加しない。'],
        remaining=['聖職者としての身分・職務を既存の宗教上の援助機能へ結ぶ', 'その修正後の条件文全体と第二段落の意味確認', '二作品全文'],
        whole_unit_semantically_verified=False, whole_sentence_semantically_verified=False,
        new_verified_sentence_characters=0, new_whole_unit_reviews=0,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def integrity_checks():
    r = reading(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == r
    validate_hashes(ROOT, r['source_sha256'])
    assert r['source']['range'] == [326, 518] and len(r['clauses']) == 11
    assert ''.join(c['text'] for c in r['clauses']) == r['source']['text']
    for c in r['clauses']:
        a, b = c['range']; assert c['text'] == r['source']['text'][a-326:b-326]
        assert all(n in catalog().entries for n in c['definitions'])
    assert [c['id'] for c in r['clauses'] if c['status'].startswith('unresolved')] == ['pastoral_provider']
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document'] == FULL and index['works']['kant-1784']['meaning_basis'] == BASIS
    assert (ROOT / CORE).read_text(encoding='utf-8') == core()
    d = parse(core())
    for style in ('compact', 'full'):
        text = format_graph(d, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    return dict(clause_partition=11, current_selection_bound=True, unresolved_semantic_gates=1,
        manuscripts_unchanged=True, roundtrips=True, semantic_equivalence_automatically_proved=False)


def build_report():
    results = {}
    for name, fn in [('composition', composition_checks), ('supply', supply_checks), ('lexical_gap', lexical_gap_checks),
        ('attribution', attribution_checks), ('integrity', integrity_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading(); source = r['source']
    paths = set(r['source_sha256']) | set(catalog().source_sha256) | {CORE, AUDIT, DOC,
        'scripts/check_delegation_sentence.py', 'scripts/register_delegation_sentence.py', 'scripts/fetch_delegation_sentence_evidence.py',
        'scripts/fetch_pastoral_role_evidence.py', 'tests/test_delegation_sentence.py', 'scripts/check_service_roles.py',
        'scripts/check_clinical_roles.py', 'scripts/check_effort_agents.py', 'scripts/check_book_form.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_written_carriers.py', 'scripts/check_role_qualifications.py',
        'scripts/check_substituted_judgment.py', 'scripts/check_recognizable_consequence.py', 'scripts/check_motive_causes.py',
        'scripts/compose_falling_depiction.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='whole_conditional_audit_retains_clerical_status_gap', document=CORE, **results,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'], source=source['text'],
            definitions=['ss', 'st', 'su', 'sv', 'sx', 'sy', 'hzwy'], status='explicit_interpretive_annotation'),
        review_decision=r['decision'], whole_sentence_semantically_verified=False, new_verified_sentence_characters=0,
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / CORE, core()); write_exact(ROOT / AUDIT, encoded(reading()))


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
