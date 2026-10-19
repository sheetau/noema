"""Fix the interpretation context of the delegated-judgment conditional."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_falling_depiction import ROOT, closure
from scripts.check_effort_agents import source_values, attribution_checks
from scripts.check_pastoral_roles import evaluate, DOMAIN
from scripts.check_motive_causes import unknown

FULL = 'examples/v016/kant-effort-agents.noema'
BASIS = 'data/effort-agents-basis-v1.json'
INDEX = 'data/semantic-review-index-v52.json'
CORE = 'examples/v016/delegation-context-core.noema'
AUDIT = 'data/delegation-context-reading-v1.json'
REPORT = 'reports/delegation-context-v1.json'
DOC = 'docs/delegation-context-v1.md'
SCENES = ('text', 'case', 'outcome', 'caseB', 'outcomeB', 'failure')
PEOPLE = (*DOMAIN, 'planB')


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def core():
    doc = deepcopy(catalog().document)
    doc['statements'] = [doc['statements'][i] for i in (4, 42)]
    doc['declarations'] = closure(doc, _references(doc['statements']))
    return format_graph(doc, 'compact') + '\n'


@lru_cache(None)
def questions():
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, ['sv', 'sx', 'sy', 're', 's2', 'wh']), statements=[])
    return parse(format_graph(doc, 'compact') + '''
r jp[] a.r ja[] d.r jb[] d.
q[t[k sv[k jp[]]][k ja[]]].q[t[k sx[k jp[]]][k ja[]]].
q[t[k sv[k jp[]]][k jb[]]].q[t[k sx[k jp[]]][k jb[]]].
q[t[k sy[k jp[]]][k wh[]]].
q[k re[k jp[] p sv i[scene d][k s2[k jp[] k wh[] v scene]]]].''')


def values(variant='baseline'):
    # Instantiate the existing source predicates in two hypothetical cases.
    # No production definition is replaced. Only primitive interpretations vary.
    aliases = {'caseB': 'case', 'outcomeB': 'outcome', 'planB': 'plan'}
    fold = lambda arg: aliases.get(arg, arg) if isinstance(arg, str) else arg
    v = {name: (lambda *args, fn=fn: fn(*(fold(a) for a in args)))
         for name, fn in source_values().items()}
    v.update(jp=lambda: 'person', ja=lambda: 'case', jb=lambda: 'caseB')
    cases = set() if variant == 'empty_cases' else {'case', 'caseB'}
    if variant == 'first_case_only':
        cases = {'case'}
    v['s2'] = lambda p, anchor, case: p == 'person' and anchor == (
        'outcome' if variant == 'other_anchor' else 'text') and case in cases
    access = v['sa']
    v['sa'] = lambda p, w, s: access(p, w, s) and variant != 'no_premise' and not (
        variant == 'second_premise_absent' and s == 'caseB')
    paths = {('person', 'plan', 'case', 'outcome'), ('person', 'planB', 'caseB', 'outcomeB')}
    if variant in ('failure_selected', 'failure_excluded'):
        paths.add(('person', 'plan', 'case', 'failure'))
    selected = set(paths)
    if variant == 'failure_excluded':
        selected.remove(('person', 'plan', 'case', 'failure'))
    if variant == 'empty_second_results':
        selected = {x for x in selected if x[2] != 'caseB'}
    v['ae'] = lambda p, m, s: any(x[:3] == (p, m, s) for x in paths) and not (
        variant == 'missing_second_method' and s == 'caseB')
    v['af'] = lambda p, m, s, e: (p, m, s, e) in paths and not (
        variant == 'outside_results' and s == 'caseB')
    v['ap'] = lambda p, m, s, e: (p, m, s, e) in selected
    # Goal identity is fixed by the reading, not chosen after seeing outcomes.
    goals = {('person', 'delegated_practical_use', 'outcome'),
             ('person', 'delegated_practical_use', 'outcomeB')}
    if variant in ('second_goal_fails', 'first_case_only', 'second_premise_absent'):
        goals.remove(('person', 'delegated_practical_use', 'outcomeB'))
    if variant == 'other_person_goal':
        goals = {('other', task, scene) for _, task, scene in goals}
    if variant == 'other_goal':
        goals = {(p, 'unrelated_goal', scene) for p, _, scene in goals}
    v['sj'] = lambda p, s: (p, 'delegated_practical_use', s) in goals
    efforts = set()
    if variant == 'second_own_effort':
        efforts.add(('person', 'person', 'planB', 'caseB', 'outcomeB'))
    if variant == 'other_effort':
        efforts |= {('guide', *x) for x in paths}
    v['hzwz'] = lambda a, p, m, s, e: (a, p, m, s, e) in efforts
    return v


def scope_checks():
    shifted = values('other_anchor')['s2']
    assert shifted('person', 'outcome', 'case') and not shifted('person', 'text', 'case')
    expected = {
        'baseline': [True, True, True, True, True, True],
        'second_goal_fails': [True, True, True, False, False, True],
        'second_own_effort': [True, True, True, False, False, True],
        'other_person_goal': [True, False, True, False, False, True],
        'other_goal': [True, False, True, False, False, True],
        'other_effort': [True, True, True, True, True, True],
        'first_case_only': [True, True, True, False, True, True],
        'empty_cases': [True, True, True, True, False, False],
        'other_anchor': [True, True, True, True, False, False],
        'no_premise': [False, True, False, True, True, False],
        'second_premise_absent': [True, True, False, False, True, True],
        'missing_second_method': [True, True, True, False, False, True],
        'outside_results': [True, True, True, False, False, True],
        'empty_second_results': [True, True, True, False, False, True],
        'failure_selected': [True, False, True, True, False, True],
        'failure_excluded': [True, True, True, True, True, True],
    }
    rows = {}
    for variant, wanted in expected.items():
        actual = evaluate(questions(), values(variant), PEOPLE, SCENES, True)
        assert actual == wanted, (variant, actual, wanted)
        rows[variant] = actual
    return dict(query_order=['premise_A', 'conclusion_A', 'premise_B', 'conclusion_B', 'conditional', 'applicable'],
        contrasts=rows, definitions_replaced_by_primitives=False, pure_memoization=True,
        excluded_failure_is_not_a_universal_success_guarantee=True)


def ordinary_checks():
    # Evaluate the actual result-selection/goal/effort definitions without memoization.
    doc = deepcopy(questions()); doc['statements'] = doc['statements'][1:2]
    doc['declarations'] = closure(doc, _references(doc['statements']))
    rows = {}
    for variant in ('baseline', 'other_goal', 'failure_selected', 'failure_excluded'):
        actual = evaluate(doc, values(variant), PEOPLE, SCENES)
        assert actual == [variant in ('baseline', 'failure_excluded')]
        assert actual == evaluate(doc, values(variant), PEOPLE, SCENES, True)
        rows[variant] = actual
    for name in ('sj', 'hzwz', 'ap'):
        v = values(); v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, ordinary_matches_memoized=True, unknown_inputs_refused=3)


def reading():
    inventory = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inventory).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    start, end = unit['text'].index('Habe ich'), unit['text'].index('Ich habe nicht nöthig')
    while unit['text'][end - 1].isspace():
        end -= 1
    sources = (inventory, FULL, BASIS, INDEX, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'data/delegation-reading-review-v1.json', 'data/effort-agents-reading-v1.json',
        'data/recognizable-consequence-reading-v1.json', 'docs/substituted-judgment-v1.md',
        'docs/role-qualifications-v1.md', 'docs/book-form-v1.md', 'docs/conscience-reading-v1.md')
    return dict(status='purpose_relative_context_fixed_with_remaining_lexical_limits', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, end], text=unit['text'][start:end]),
        selection=selection_binding(catalog(), [4, 42]),
        context=dict(
            person='仮定例の一人称の位置。同じ本人を前件・後件・仕事の受け手へ通す。著者の実生活の断言ではない。',
            purpose='この仮定例で、理解・行為の道徳的評価・身体の生活調整に関わる本人の実際上の用事を処理できること。自ら判断することを達成条件には含めず、無関係な満足や別人の成功で代用しない。',
            effort='その用事に必要な判断を本人が自分で行うための取組み。あらゆる身体活動、支払い、指示に従う動作まで不要だとは読まない。',
            methods='本人が仮定状況で利用可能な、その用事を処理する方法。現実の選択や実行は要求しない。供給元が成功方法を因果的に生むという追加主張もしない。',
            results='同じ方法に属する非空の評価結果。日常の実用的な可能性を扱う文脈の選択範囲であり、論理的に可能な全結果への保証ではない。反例となる結果を後から削除して成功を作る操作は、この固定した解釈の変更になる。',
            cases='提示文脈を基準に本人を置く非空の仮定範囲。同じ前件が成り立つ各場合で後件を要求し、前件の成立候補があるかを別に検査する。'),
        facsimile_observations=['原刊482頁に三例、非網羅的な列挙、条件の帰結、jaとselbstが続く。',
            '次の思考・支払い・他者による引受けの文が、問題の努力を自ら判断する仕事として読む文脈を与える。次文そのものを今回の対象範囲へ加えない。'],
        interpretation_limits=['目的と努力の限定は文脈に基づく読解であり、原文に目的語の明示的な列挙があるとはしない。',
            '供給される判断の正しさや、実世界の達成を保証せず、著者がこの態度を推奨するとも読まない。',
            '有限モデルは条件の結合を検査する。語義の妥当性を自動的に証明しない。'],
        remaining=['医師と他の健康専門職の歴史的な境界、宗教上の配慮を判断の援助として読む範囲、書物の刊行単位の慣習',
            '三例の名詞・仕事と談話上の批判的効果を含む条件文全体の最終確認', '第二段落全体と二作品全文'],
        whole_unit_semantically_verified=False, full_conditional_equivalence=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sources})


def integrity_checks():
    r = reading()
    assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == r
    validate_hashes(ROOT, r['source_sha256'])
    assert (ROOT / CORE).read_text(encoding='utf-8') == core()
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document'] == FULL
    assert index['works']['kant-1784']['meaning_basis'] == BASIS
    d = parse(core())
    for style in ('compact', 'full'):
        text = format_graph(d, style)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    return dict(current_selection_bound=True, source_statements=2, manuscripts_unchanged=True,
        context_fields=6, roundtrips=True, semantic_equivalence_automatically_proved=False)


def build_report():
    results = {}
    for name, fn in [('scope', scope_checks), ('ordinary', ordinary_checks), ('attribution', attribution_checks), ('integrity', integrity_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    review = reading(); source = review['source']
    paths = set(review['source_sha256']) | set(catalog().source_sha256) | {CORE, AUDIT, DOC,
        'scripts/check_delegation_context.py', 'scripts/register_delegation_context.py', 'tests/test_delegation_context.py',
        'scripts/check_effort_agents.py', 'scripts/check_book_form.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_written_carriers.py', 'scripts/check_role_qualifications.py', 'scripts/check_substituted_judgment.py',
        'scripts/check_recognizable_consequence.py', 'scripts/check_motive_causes.py', 'scripts/compose_falling_depiction.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='delegation_interpretation_context_fixed', document=CORE, **results,
        alignment=dict(**source, definitions=['rd', 'rc', 're', 'sv', 'sx', 'sy', 'hzwy'], status='explicit_interpretive_annotation'),
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
