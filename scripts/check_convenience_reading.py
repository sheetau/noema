"""Review convenience with the current opportunity-normalized capacity."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_falling_depiction import ROOT, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.fetch_convenience_reading_evidence import PATH as EVIDENCE, validate

FULL = 'examples/v016/kant-appointed-roles.noema'
BASIS = 'data/appointed-roles-basis-v1.json'
INDEX = 'data/semantic-review-index-v58.json'
CORE = 'examples/v016/convenience-reading-core.noema'
AUDIT = 'data/convenience-reading-v1.json'
REPORT = 'reports/convenience-reading-v1.json'
DOC = 'docs/convenience-reading-v1.md'
PEOPLE = ('person', 'other', 'plan', 'assessment', 'faculty', 'act')
SCENES = ('text', 'case', 'result', 'profileCase', 'profileResult', 'failure', 'success')


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def core():
    d = deepcopy(catalog().document); d['statements'] = [d['statements'][6]]
    d['declarations'] = closure(d, _references(d['statements']))
    return format_graph(d, 'compact') + '\n'


@lru_cache(None)
def questions():
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, ['bf', 'ul', 'un', 'wh']), statements=[])
    return parse(format_graph(d, 'compact') + '''r jp[] a.r ja[] d.r jb[] d.
q[t[k bf[k jp[]]][k ja[]]].q[t[k bf[k jp[]]][k jb[]]].
q[t[k ul[k jp[]]][k wh[]]].q[t[k un[]][k wh[]]].''')


def values(variant='baseline'):
    v = {d['name']: unknown for d in questions()['declarations'] if d['kind'] == 'primitive'}
    profiles = {('case', 'profileCase'), ('result', 'profileResult')}
    paths = {('assessment', 'profileCase', 'success' if variant == 'not_immature' else 'failure'),
        ('assessment', 'profileResult', 'success' if variant in ('not_immature', 'state_changes') else 'failure')}
    if variant != 'no_method':
        paths.add(('plan', 'case', 'result'))
    v.update(jp=lambda: 'person', ja=lambda: 'case', jb=lambda: 'result', wh=lambda: 'text',
        aa=lambda p: variant != 'not_human' and (p == 'person' or p == 'other' and variant in ('extra_person', 'outside_person')),
        ab=lambda f, p, s: (f, p) == ('faculty', 'person'),
        ac=lambda p, f, a, s: (p, f, a, s) == ('person', 'faculty', 'act', 'success'),
        ad=lambda *args: False,
        ae=lambda p, m, s: p == 'person' and any((m, s) == x[:2] for x in paths),
        af=lambda p, m, s, e: p == 'person' and (m, s, e) in paths and not (variant == 'outside_result' and m == 'plan'),
        ap=lambda p, m, s, e: p == 'person' and (m, s, e) in paths and not (variant == 'empty_results' and m == 'plan'),
        hzsc=lambda p, a, s: variant != 'empty_profile' and p == 'person' and (a, s) in profiles,
        hzsd=lambda p, a, s: p == 'person' and (a, s) in profiles,
        hzse=lambda p, s: p == 'person' and s in ('profileCase', 'profileResult'),
        hzsf=lambda *args: False,
        hzsg=lambda p, m, a, s: p == 'person' and m == 'assessment' and (a, s) in profiles,
        hzsh=lambda p, m, a, s: variant != 'unclassified_profile' and p == 'person' and (a, s) in profiles,
        sj=lambda p, s: variant != 'failed_goal' and (p, s) == ('person', 'result'),
        oc=lambda *args: Fraction(9 if variant == 'high_burden' else 1),
        uj=lambda p, c, s: variant != 'empty_cases' and (p, c, s) == (
            'other' if variant == 'wrong_case_person' else 'person',
            'case' if variant == 'wrong_case_context' else 'text', 'case'),
        uk=lambda b, c: b <= 2 and c == ('case' if variant == 'wrong_standard_context' else 'text'),
        um=lambda p, c: variant != 'empty_people' and c == 'text' and (p == 'person' or p == 'other' and variant == 'extra_person'))
    return v


def source_checks():
    rows = {}
    variants = ('baseline', 'high_burden', 'failed_goal', 'no_method', 'not_immature', 'state_changes',
        'not_human', 'empty_results', 'outside_result', 'empty_cases', 'empty_people',
        'wrong_case_person', 'wrong_case_context', 'wrong_standard_context', 'empty_profile', 'unclassified_profile',
        'extra_person', 'outside_person')
    for variant in variants:
        actual = evaluate(questions(), values(variant), PEOPLE, SCENES, True)
        invalid = variant in ('not_immature', 'not_human', 'empty_profile', 'unclassified_profile')
        expected = [not invalid, not invalid and variant != 'state_changes',
            variant in ('baseline', 'empty_people', 'extra_person', 'outside_person'), variant in ('baseline', 'outside_person')]
        assert actual == expected, (variant, actual, expected)
        rows[variant] = actual
    return dict(contrasts=rows, current_capacity_definitions_executed=True,
        definitions_replaced_by_primitives=False, pure_memoization=True)


def generic_checks():
    d = deepcopy(catalog().document); d.update(declarations=closure(d, ['rj', 'nd']), statements=[])
    doc = parse(format_graph(d, 'compact') + '''r jp[] a.r js[] d.r ji[d] c.r jg[d] c.
r ja[a a d] c.r jo[a a d d] c.r je[a a d d] c.r jb[a a d] b.r jt[b] c.
q[k rj[k jp[] b scene[k ji[v scene]] b scene[k jg[v scene]] k js[] p ja p jo p je p jb p jt]].
q[k nd[k jp[] b scene[k jg[v scene]] k js[] p ja p jo p je p jb p jt]].''')
    answers = []
    for initial, final, goal, available, selected, cheap in product((False, True), repeat=6):
        v = dict(jp=lambda: 'person', js=lambda: 'start',
            ji=lambda s: initial if s == 'start' else final, jg=lambda s: goal and s == 'end',
            ja=lambda p, m, s: available and (p, m, s) == ('person', 'plan', 'start'),
            jo=lambda p, m, s, e: (p, m, s, e) == ('person', 'plan', 'start', 'end'),
            je=lambda p, m, s, e: selected and (p, m, s, e) == ('person', 'plan', 'start', 'end'),
            jb=lambda *args: Fraction(1 if cheap else 9), jt=lambda b: b <= 2)
        actual = evaluate(doc, v, ('person', 'plan'), ('start', 'end'))
        assert actual == [initial and final and goal and available and selected and cheap,
            goal and available and selected and cheap]
        answers.append(actual)
    contrasts = {}
    for variant in ('split_state_goal', 'split_burden_success', 'combined', 'outside_outcomes'):
        def path(p, m, s, e):
            return (p, s) == ('person', 'start') and (m, e) in (('first', 'one'), ('second', 'two'))
        v = dict(jp=lambda: 'person', js=lambda: 'start',
            ji=lambda s: s in ('start', 'one') or variant != 'split_state_goal' and s == 'two',
            jg=lambda s: s == 'two', ja=lambda p, m, s: (p, s) == ('person', 'start') and m in ('first', 'second'),
            jo=lambda *args: variant != 'outside_outcomes' and path(*args), je=path,
            jb=lambda p, m, s: Fraction(9 if variant == 'split_burden_success' and m == 'second' else 1),
            jt=lambda b: b <= 2)
        actual = evaluate(doc, v, ('person', 'first', 'second'), ('start', 'one', 'two'))
        expected = {'split_state_goal': [False, True], 'split_burden_success': [False, False],
            'combined': [True, True], 'outside_outcomes': [False, False]}[variant]
        assert actual == expected
        contrasts[variant] = actual
    return dict(combinations=64, answers=answers, method_contrasts=contrasts,
        current_generic_definitions=True, ordinary_evaluation=True)


def ordinary_and_unknown_checks():
    d = deepcopy(questions()); d['statements'] = d['statements'][:1]
    d['declarations'] = closure(d, _references(d['statements']))
    # The actual shared incapacity definition, not a replacement state flag.
    ordinary = evaluate(d, values(), PEOPLE, SCENES)
    assert ordinary == evaluate(d, values(), PEOPLE, SCENES, True) == [True]
    for name in ('uj', 'uk', 'um', 'hzsh'):
        v = values(); v[name] = unknown
        try:
            evaluate(questions(), v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(actual_incapacity_ordinary_agrees=True, unknown_inputs_refused=4,
        full_composition_uses_pure_memoization=True)


def attribution_checks():
    doc = parse(core()); rows = {}
    for variant in ('baseline', 'other_author', 'other_node', 'other_content', 'other_context', 'reversed_before', 'reversed_after'):
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        v.update(uo=lambda: 'convenience', mw=lambda: 'cause', s3=lambda: 'examples', wa=lambda: 'author', wh=lambda: 'text',
            uc=lambda n, a, d, s: (n, a, symbol(d), s) == (
                'other' if variant == 'other_node' else 'convenience',
                'other' if variant == 'other_author' else 'author',
                'mx' if variant == 'other_content' else 'un',
                'case' if variant == 'other_context' else 'text'),
            ue=lambda a, b, s: s == 'text' and (a, b) in {
                ('convenience', 'cause') if variant == 'reversed_before' else ('cause', 'convenience'),
                ('examples', 'convenience') if variant == 'reversed_after' else ('convenience', 'examples')})
        actual = evaluate(doc, v, ('convenience', 'cause', 'examples', 'author', 'other'), ('text', 'case'))
        assert actual == [variant == 'baseline']
        rows[variant] = actual
    return dict(contrasts=rows, content_facts_and_liking_not_asserted=True)


def reading():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    text = 'Es ist so bequem, unmündig zu sein.'; start = unit['text'].index(text)
    parts = [('assertion', 'Es ist ', ['uc', 'un'], '選定した人と仮定場面に対する便宜の評価を著者の主張として帰属する。'),
        ('degree', 'so ', ['uk'], '文脈で示される「これほど便利」という負担の水準。原文へ固定数値や比較対象を追加しない。'),
        ('convenience', 'bequem, ', ['rj', 'rk', 'ul'], '同じ方法で、評価結果における状態と実用上の目的を満たし、本人の負担が文脈基準内である。'),
        ('immaturity', 'unmündig ', ['bf', 'bc'], '第一段落で定義された、自分の理解力を他者の指導なしに行使する能力の不足という状態。'),
        ('being', 'zu sein.', ['rj'], 'その状態にある場合を評価する。状態へ入る容易さや、その状態を好むことへ置き換えない。')]
    clauses = []; pos = start
    for name, phrase, definitions, meaning in parts:
        clauses.append(dict(id=name, range=[pos, pos+len(phrase)], text=phrase,
            definitions=definitions, interpretation_ja=meaning, status='reviewed_under_stated_reading'))
        pos += len(phrase)
    paths = (inv, FULL, BASIS, INDEX, EVIDENCE, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'data/delegation-context-reading-v1.json', 'data/delegation-reading-v1.json',
        'data/exercise-capacity-reading-v1.json', 'reports/exercise-capacity-v1.json',
        'reports/state-convenience-v1.json', 'docs/state-convenience-v1.md')
    return dict(status='convenience_sentence_reviewed_with_current_capacity', reviewer='assistant_review',
        decision='equivalent_under_stated_reading_for_this_sentence', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start+len(text)], text=text,
            nonblank_characters=sum(not ch.isspace() for ch in text)), clauses=clauses,
        selection=selection_binding(catalog(), [6]),
        context=dict(people='一般化の対象となる人々を先に定め、成功した本人だけを結果から選び直さない。全人類への無条件の断言とはしない。',
            cases='その本人が未成熟である場合の、実際上の用事を評価する仮定場面。前後の文の場面範囲と自動的に同一視しない。',
            goal='代行例と同じswの実用上の用事。自分で判断することを目的自体へ組み込まない。',
            burden='本人に必要な取組みの負担。同じ方法・本人へ結び、評価の水準ukを元の文脈へ固定する。',
            horizon='その状態で用を足す評価範囲の開始と結果に状態を求める。全生涯の継続や、その後の成熟不能を含めない。',
            capacity='現行bcの、既有の判断基盤を保ち通常の機会を与えた場面での行使能力の不足。現在の実行機会の欠如だけと区別する。'),
        findings=['原刊482頁と歴史辞典の目的達成のための労を軽くする用法を照合した。',
            '未成熟・便宜・程度・一般化・著者帰属を現在の定義本体で区別できる。',
            '目的や方法の条件と能力の評価範囲を保った上で、この短文は採用した読みの下で対応すると判断する。'],
        interpretation_limits=['アシスタントによる採用読解であり、独立査読や自動証明ではない。',
            'Bequemの全用法を低負担へ還元せず、この目的相対的な読みを採る。本人の好みや道徳的な推奨を追加しない。',
            '評価する人・場面・目的・結果・負担尺度と基準は文脈入力であり、原文に具体的数値や測定手法を加えない。',
            '結果で状態を保持することから、経路の全瞬間や一生の状態維持を推論しない。',
            'この固定版の一文への判断を、別文脈・後続版・段落全体へ自動継承しない。'],
        remaining=['支払いの文の語義と限定・見込みの働き', '後見人の働きかけを含む第二段落全体', '二作品全文'],
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        semantic_equivalence_automatically_proved=False, new_whole_unit_reviews=0,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def integrity_checks():
    r = reading(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == r
    validate_hashes(ROOT, r['source_sha256'])
    assert ''.join(c['text'] for c in r['clauses']) == r['source']['text']
    for clause in r['clauses']:
        a, b = clause['range']; start = r['source']['range'][0]
        assert clause['text'] == r['source']['text'][a-start:b-start]
        assert all(n in catalog().entries for n in clause['definitions'])
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document'] == FULL and index['works']['kant-1784']['meaning_basis'] == BASIS
    assert (ROOT / CORE).read_text(encoding='utf-8') == core()
    d = parse(core())
    for style in ('compact', 'full'):
        text = format_graph(d, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    return dict(current_selection_bound=True, clause_partition=5, reviewed_sentence_characters=r['source']['nonblank_characters'],
        manuscripts_unchanged=True, roundtrips=True, semantic_equivalence_automatically_proved=False)


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('source', source_checks), ('ordinary', ordinary_and_unknown_checks),
        ('attribution', attribution_checks), ('integrity', integrity_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    r = reading(); source = r['source']
    paths = set(r['source_sha256']) | set(catalog().source_sha256) | {CORE, AUDIT, DOC,
        'scripts/check_convenience_reading.py', 'scripts/register_convenience_reading.py', 'tests/test_convenience_reading.py',
        'scripts/fetch_convenience_reading_evidence.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'scripts/compose_falling_depiction.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='convenience_sentence_reviewed_under_explicit_source_reading', document=CORE, **results,
        alignment=dict(unit=source['unit'], unit_sha256=source['unit_sha256'], range=source['range'], source=source['text'],
            definitions=['rj', 'rk', 'bf', 'ul', 'un', 'uk'], status='explicit_interpretive_annotation'),
        review_decision=r['decision'], reviewer='assistant_review', whole_sentence_semantically_verified=True,
        new_verified_sentence_characters=source['nonblank_characters'], semantic_equivalence_automatically_proved=False,
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
