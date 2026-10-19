"""Check self-assessment and its quoted substitution in the current manuscript."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_pastoral_roles import ROOT, FULL, BASIS, closure
from scripts.check_pastoral_roles import evaluate, source_values, DOMAIN, SOURCE_SCENES, attribution_checks
from scripts.check_motive_causes import unknown, symbol
from scripts.fetch_conscience_evidence import PATH as EVIDENCE, URL, validate

INDEX = 'data/semantic-review-index-v48.json'
CORE = 'examples/v016/conscience-delegation.noema'
AUDIT = 'data/conscience-reading-v1.json'
REPORT = 'reports/conscience-reading-v1.json'
DOC = 'docs/conscience-reading-v1.md'


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def core():
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, ['sm', 'st']), statements=[])
    return format_graph(doc, 'compact') + '\n'


@lru_cache(None)
def query(mode):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, ['sm'] if mode == 'task' else ['sm', 'st']), statements=[])
    text = format_graph(doc, 'compact') + 'r jperson[] a.r jscene[] d.'
    if mode in ('task', 'both'):
        text += 'q[t[k sm[k jperson[]]][k jscene[]]].'
    if mode in ('supply', 'both'):
        text += 'q[t[k st[k jperson[]]][k jscene[]]].'
    return parse(text)


def task_checks():
    rows = []
    judgments = ('judgmentA', 'judgmentB', 'judgmentC')
    for bits in product((False, True), repeat=6):
        performed = {j for j, b in zip(judgments, bits[:3]) if b}
        assessed = {j for j, b in zip(judgments, bits[3:]) if b}
        values = dict(jperson=lambda: 'person', jscene=lambda: 'case',
            fa=lambda p, j, s: p == 'person' and j in performed and s == 'case',
            se=lambda j, p, s: j in assessed and p == 'person' and s == 'case')
        result = evaluate(query('task'), values, ('person', *judgments), ('case',))[0]
        assert result == bool(performed & assessed)
        rows.append(dict(bits=list(bits), self_assessment=result))
    contrasts = {}
    for variant in ('baseline', 'other_actor', 'other_subject', 'other_judgment',
                    'other_performance_scene', 'other_assessment_scene', 'no_judgment', 'no_moral_assessment'):
        values = dict(jperson=lambda: 'person', jscene=lambda: 'case',
            fa=lambda p, j, s: variant != 'no_judgment' and (p, j, s) == (
                'other' if variant == 'other_actor' else 'person', 'judgmentA',
                'elsewhere' if variant == 'other_performance_scene' else 'case'),
            se=lambda j, p, s: variant != 'no_moral_assessment' and (j, p, s) == (
                'judgmentB' if variant == 'other_judgment' else 'judgmentA',
                'other' if variant == 'other_subject' else 'person',
                'elsewhere' if variant == 'other_assessment_scene' else 'case'))
        result = evaluate(query('task'), values, ('person', 'other', *judgments), ('case', 'elsewhere'))
        assert result == [variant == 'baseline']
        contrasts[variant] = result
    for name in ('fa', 'se'):
        values = dict(jperson=lambda: 'person', jscene=lambda: 'case', fa=lambda *a: True, se=lambda *a: True)
        values[name] = unknown
        try:
            evaluate(query('task'), values, ('person', 'judgmentA'), ('case',))
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(same_judgment_combinations=rows, contrasts=contrasts, unknown_inputs_refused=2,
        moral_assessment_is_an_interpreted_primitive=True,
        truth_of_moral_verdict_and_feeling_not_tested=True)


def independence_checks():
    rows = []
    people = (*DOMAIN, 'judgmentA')
    for performed, supplied in product((False, True), repeat=2):
        values = source_values('baseline')
        supply = values['sb']
        values.update(fa=lambda p, j, s: performed and (p, j, s) == ('person', 'judgmentA', 'case'),
            se=lambda j, p, s: (j, p, s) == ('judgmentA', 'person', 'case'),
            sb=lambda w, p, t, s: supplied and supply(w, p, t, s))
        actual = evaluate(query('both'), values, people, SOURCE_SCENES)
        assert actual == [performed, supplied]
        rows.append(dict(self_performed=performed, supplied_as_substitute=supplied, actual=actual))
    values = source_values('baseline')
    values.update(fa=unknown, se=unknown)
    assert evaluate(query('supply'), values, people, SOURCE_SCENES) == [True]
    return dict(cases=rows,unknown_self_assessment_does_not_prevent_quoted_supply=True,
        no_actual_self_performance_or_its_negation_inferred=True,
        literal_transmission_of_a_mental_state_not_asserted=True)


def substitution_checks():
    rows = {}
    variants = ('baseline', 'wrong_task', 'wrong_beneficiary', 'other_supply_scene',
        'other_access_scene', 'split_provider', 'no_supply', 'no_access', 'no_role', 'incidental_function')
    for variant in variants:
        values = source_values(variant if variant in ('no_supply', 'no_access', 'no_role', 'incidental_function') else 'baseline')
        if variant in ('wrong_task', 'wrong_beneficiary', 'other_supply_scene', 'split_provider'):
            values['sb'] = lambda w, p, t, s: (w, p, symbol(t), s) == (
                'other' if variant == 'split_provider' else 'guide',
                'other' if variant == 'wrong_beneficiary' else 'person',
                'sn' if variant == 'wrong_task' else 'sm',
                'text' if variant == 'other_supply_scene' else 'case')
        if variant == 'other_access_scene':
            values['sa'] = lambda p, w, s: (p, w, s) == ('person', 'guide', 'text')
        values.update(fa=unknown, se=unknown)
        actual = evaluate(query('supply'), values, DOMAIN, SOURCE_SCENES)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual
    for name in ('sa', 'sb'):
        values = source_values('baseline'); values[name] = unknown
        try:
            evaluate(query('supply'), values, DOMAIN, SOURCE_SCENES)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, unknown_inputs_refused=2,
        definitions_replaced_by_primitives=False, ordinary_evaluation=True,
        self_assessment_content_never_executed=True)


def reading():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    phrase = 'der für mich Gewissen hat'
    start = unit['text'].index(phrase)
    paths = (inv, FULL, BASIS, INDEX, EVIDENCE, 'data/pastoral-role-evidence-v1.json',
        'artifacts/first-cause-reading-v1/page-482.jpg', 'docs/substituted-judgment-v1.md')
    return dict(status='functional_conscience_reading_checked_with_open_lexical_limits',
        reviewer='assistant_review', decision='existing_functional_description_supported_for_this_use',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase),
        document=FULL, meaning_basis=BASIS, selection=selection_binding(catalog(), [4]),
        scope='Self-assessment content and its substitution only; not the complete provider noun or conditional sentence.',
        interpretation_ja='自分の行為を道徳的要求に照らして自ら判断する仕事について、助言者の判断・指示を本人の用に供するという機能上の代行として読む。',
        decisions=[
            dict(topic='self_reference', definitions=['sm', 'fa', 'se'],
                reading='判断主体と、その行為が評価される本人を同一にし、同じ判断と状況に結ぶ。'),
            dict(topic='substitution', definitions=['st', 'rb', 'sa', 'sb'],
                reading='同じ供給元の利用と、本人に代わる同じ仕事の供給を結ぶ。本人の実際の判断や判断しなかった事実は追加しない。'),
            dict(topic='quotation', definitions=['s4', 'sy', 'st', 'sm'],
                reading='自己判断の記述を代行の対象として参照する。助言者自身の行為への良心や、感情の移転へ変えない。著者の仮定例の提示から実際の代行を断定しない。'),
        ],
        lexical_evidence=dict(url=URL, stored=EVIDENCE,
            support='道徳上の通常の語義では自己の行為と法の関係への意識・確信を述べ、誤る良心の用例も区別する。',
            counterweight='同じ項目に罪責感・ためらい等の用法もあり、smがそれらを全て定義したことにはならない。'),
        original_print=dict(page=482, image='artifacts/first-cause-reading-v1/page-482.jpg',
            url='https://www.digitale-sammlungen.de/de/view/bsb10926843?page=522',
            observation='書物の例の後にSeelsorgerとこの関係節が続き、その後にArztとDiätの例が続く。für michは助言者の自己評価ではなく仮定例の本人への代行にかかると読む。'),
        limits=['機能上の読みの根拠と参照結合を確認した。Gewissen全語義の必要十分な定義、唯一の著者意図、独立査読の証明ではない。',
            '道徳的要求と判断の内面性は既存の意味規約による。形式的な有限モデルはその哲学的妥当性や判断の正しさを証明しない。',
            'spの宗教上の職務条件、良心の能力・感情としての定義、他の名詞、便宜・反語と条件文全体は別に確認を要する。',
            '役割を持つことから本人の信仰や教義の真理、助言の正しさを補わない。後年の良心論をこの1784年の一節へそのまま移さない。'],
        whole_unit_semantically_verified=False, full_noun_equivalence=False,
        new_whole_unit_reviews=0, new_covered_characters=0,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def integrity_checks():
    review = reading()
    assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == review
    validate_hashes(ROOT, review['source_sha256'])
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    assert index['works']['kant-1784']['document'] == FULL
    assert index['works']['kant-1784']['meaning_basis'] == BASIS
    assert (ROOT / CORE).read_text(encoding='utf-8') == core()
    doc = parse(core())
    assert not doc['statements']
    assert all(d == catalog().entries[d['name']]['declaration'] for d in doc['declarations'])
    for style in ('compact', 'full'):
        text = format_graph(doc, style)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(current_selection_bound=True, current_definitions_unchanged=True,
        primary_evidence_valid=True, roundtrips=True, new_whole_unit_reviews=0,
        semantic_equivalence_automatically_proved=False)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / CORE, core())
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('task', task_checks), ('independence', independence_checks),
                     ('substitution', substitution_checks), ('attribution', attribution_checks), ('integrity', integrity_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    review = reading()
    paths = set(catalog().source_sha256) | set(review['source_sha256']) | {
        CORE, AUDIT, DOC, 'scripts/check_conscience_reading.py', 'scripts/fetch_conscience_evidence.py',
        'scripts/register_conscience_reading.py', 'tests/test_conscience_reading.py',
        'scripts/fetch_pastoral_role_evidence.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_written_carriers.py', 'scripts/check_role_qualifications.py',
        'scripts/check_substituted_judgment.py', 'scripts/check_motive_causes.py',
        'scripts/compose_pastoral_roles.py', 'scripts/compose_falling_depiction.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='functional_conscience_reading_checks_not_full_noun_or_sentence', document=CORE,
        **results, alignment=dict(**review['source'], definitions=['sm', 'st', 'rb', 'sa', 'sb'],
            status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    prepare()
    write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
