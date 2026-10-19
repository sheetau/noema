"""Check personal effort separately from effort by others on the same method."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts.compose_effort_agents import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, parent, build, closure
from scripts.check_pastoral_roles import evaluate, DOMAIN, SOURCE_SCENES
from scripts.check_book_form import source_values as book_values
from scripts.check_recognizable_consequence import presentation_values
from scripts.check_motive_causes import unknown
from scripts.check_designation_order import substantive
from scripts.fetch_effort_agents_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v51.json'
REPORT = 'reports/effort-agents-v1.json'
AUDIT = 'data/effort-agents-reading-v1.json'
DOC = 'docs/effort-agents-v1.md'


def generic_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r jp[] a.r jm[] a.r js[] d.r je[] d.r jg[a] c.r jf[a a a d d] c.
q[k rqxr[k jp[] k jm[] k js[] k je[] p jg p jf]].''')
    agents = ('person', 'workerA', 'workerB'); rows = []
    for bits in product((False, True), repeat=6):
        selected = {a for a, b in zip(agents, bits[:3]) if b}
        exerting = {a for a, b in zip(agents, bits[3:]) if b}
        values = dict(jp=lambda: 'person', jm=lambda: 'method', js=lambda: 'start', je=lambda: 'end',
            jg=lambda a: a in selected,
            jf=lambda a, p, m, s, e: a in exerting and (p, m, s, e) == ('person', 'method', 'start', 'end'))
        actual = evaluate(doc, values, (*agents, 'method'), ('start', 'end'))[0]
        assert actual == bool(selected & exerting)
        rows.append(dict(bits=list(bits), selected_effort=actual))
    contrasts = {}
    for variant in ('baseline', 'other_beneficiary', 'other_method', 'other_start', 'other_end', 'outside_agent', 'empty_agents'):
        values = dict(jp=lambda: 'person', jm=lambda: 'method', js=lambda: 'start', je=lambda: 'end',
            jg=lambda a: variant != 'empty_agents' and a == 'workerA',
            jf=lambda a, p, m, s, e: (a, p, m, s, e) == (
                'workerB' if variant == 'outside_agent' else 'workerA',
                'workerB' if variant == 'other_beneficiary' else 'person',
                'otherMethod' if variant == 'other_method' else 'method',
                'elsewhere' if variant == 'other_start' else 'start',
                'elsewhere' if variant == 'other_end' else 'end'))
        contrasts[variant] = evaluate(doc, values, (*agents, 'method', 'otherMethod'), ('start', 'end', 'elsewhere'))
        assert contrasts[variant] == [variant == 'baseline']
    return dict(agent_range_combinations=rows, binding_contrasts=contrasts, empty_range_has_no_effort_witness=True)


@lru_cache(None)
def source_doc(previous=False, achievement_only=False):
    c = parent() if previous else load_catalog(ROOT, BASIS); doc = deepcopy(c.document)
    names = ['sk', 'sx'] if achievement_only else ['sk', 'sx', 'sv', 'sy', 'wh']
    if not previous:
        names += ['rqxr', 'hzwz']
    doc.update(declarations=closure(doc, names), statements=[])
    text = format_graph(doc, 'compact') + 'r jp[] a.r jm[] a.r js[] d.r je[] d.'
    text += 'q[k sk[k jp[] k jm[] k js[] k je[]]].q[t[k sx[k jp[]]][k js[]]].'
    if not achievement_only:
        text += 'q[t[k sv[k jp[]]][k js[]]].q[t[k sy[k jp[]]][k wh[]]].'
    if not previous:
        text += 'q[k rqxr[k jp[] k jm[] k js[] k je[] i[agent a][u[e[v agent][k jp[]]]] p hzwz]].'
    return parse(text)


def source_values(variant='baseline'):
    values = book_values(variant)
    values.update(jp=lambda: 'person', jm=lambda: 'plan', js=lambda: 'case', je=lambda: 'outcome')
    effort = set()
    if variant in ('own_effort', 'both_efforts'):
        effort.add(('person', 'person', 'plan', 'case', 'outcome'))
    if variant in ('other_effort', 'both_efforts'):
        effort.add(('guide', 'person', 'plan', 'case', 'outcome'))
    if variant == 'other_beneficiary':
        effort.add(('person', 'other', 'plan', 'case', 'outcome'))
    if variant == 'other_method':
        effort.add(('person', 'person', 'otherPlan', 'case', 'outcome'))
    if variant == 'other_start':
        effort.add(('person', 'person', 'plan', 'text', 'outcome'))
    if variant == 'other_end':
        effort.add(('person', 'person', 'plan', 'case', 'text'))
    values['hzwz'] = lambda a, p, m, s, e: (a, p, m, s, e) in effort
    # Interpret the former primitive from the same independently supplied agent
    # relation. Equality is claimed under this projection, not for arbitrary sk.
    values['sk'] = lambda p, m, s, e: (p, p, m, s, e) in effort
    return values


def source_checks():
    variants = ('baseline', 'own_effort', 'other_effort', 'both_efforts', 'other_beneficiary',
        'other_method', 'other_start', 'other_end', 'failed_goal', 'unavailable_plan', 'empty_results')
    rows = {}
    for variant in variants:
        values = source_values(variant)
        actual = evaluate(source_doc(), values, DOMAIN, SOURCE_SCENES, True)
        old = evaluate(source_doc(True), values, DOMAIN, SOURCE_SCENES, True)
        own = variant in ('own_effort', 'both_efforts')
        other = variant in ('other_effort', 'both_efforts')
        achievable = not own and variant not in ('failed_goal', 'unavailable_plan', 'empty_results')
        assert actual == [own, achievable, True, achievable, other], (variant, actual)
        assert old == actual[:4], (variant, old)
        rows[variant] = dict(previous=old, current=actual)
    for variant in ('other_effort', 'both_efforts'):
        assert evaluate(source_doc(), source_values(variant), DOMAIN, SOURCE_SCENES) == rows[variant]['current']
    values = source_values(); values['hzwz'] = unknown
    try:
        evaluate(source_doc(), values, DOMAIN, SOURCE_SCENES)
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown effort was filled in')
    return dict(contrasts=rows, previous_primitive_interpreted_by_same_agent_projection=True,
        pure_memoization=True, ordinary_self_other_checks_agree=True, unknown_inputs_refused=1,
        other_effort_neither_required_nor_excluded=True, definitions_replaced_by_primitives=False)


def method_checks():
    rows = {}; people = (*DOMAIN, 'idle')
    for variant in ('split_methods', 'effort_free_success', 'effort_by_other'):
        values = source_values()
        values['ae'] = lambda p, m, s: (p, s) == ('person', 'case') and m in ('plan', 'idle')
        values['af'] = lambda p, m, s, e: (p, s) == ('person', 'case') and (m, e) in (('plan', 'outcome'), ('idle', 'text'))
        values['ap'] = values['af']
        agent = 'guide' if variant == 'effort_by_other' else 'person'
        values['hzwz'] = lambda a, p, m, s, e: variant != 'effort_free_success' and (a, p, m, s, e) == (agent, 'person', 'plan', 'case', 'outcome')
        actual = evaluate(source_doc(achievement_only=True), values, people, SOURCE_SCENES)
        assert actual == [variant == 'split_methods', variant != 'split_methods', variant == 'effort_by_other']
        rows[variant] = actual
    return dict(contrasts=rows, unsuccessful_idleness_not_combined_with_effortful_success=True, ordinary_evaluation=True)


def attribution_checks():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8')); rows = {}
    for variant in ('baseline', 'no_presentation', 'no_marker', 'wrong_conditional', 'other_node', 'other_author',
                    'other_premise', 'other_conclusion', 'reversed_scope', 'other_context', 'closed_list', 'reverse_order'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(presentation_values(variant))
        actual = evaluate(doc, values, ('examples', 'cause', 'author', 'other', 'payment'), ('text', 'case'))
        expected = [variant not in ('no_presentation', 'wrong_conditional', 'closed_list', 'reverse_order'),
            variant in ('baseline', 'closed_list', 'reverse_order')]
        assert actual == expected
        rows[variant] = actual
    return dict(contrasts=rows, all_effort_facts_unknown=True, no_actual_method_execution_inferred=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 43
    assert set(new.entries) - set(old.entries) == {'hzwz', 'rqxr'}
    assert [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']] == ['sk']
    assert old.entries['sk']['kind'] == 'primitive' and new.entries['sk']['kind'] == 'definition'
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n != 'sk')
    affected = [i for i, s in enumerate(new.document['statements']) if 'sk' in {d['name'] for d in closure(new.document, _references(s))}]
    assert affected == [4, 42]
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        r = json.loads((ROOT / path).read_text(encoding='utf-8')); ids = [s['index'] for s in r['selection']['statements']]
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a == r['selection'] and a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in a['dependencies'])
    for ids in ([2, 3], [5], [6]):
        a, b = selection_binding(old, ids), selection_binding(new, ids)
        assert a['statements'] == b['statements'] and a['dependencies'] == b['dependencies']
        assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in a['dependencies'])
    for p, text in build().items():
        assert (ROOT / p).read_text(encoding='utf-8') == text
    for p in (FULL, CORE, LIBRARY):
        d = parse((ROOT / p).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(d, style)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == d
    validate(json.loads((ROOT / EVIDENCE).read_text(encoding='utf-8')))
    return dict(preserved_statements=43, changed_definitions=['sk'], affected_statements=affected,
        primitive_promoted_to_definition='sk', added_definitions=2, added_primitives=1, net_added_primitives=0,
        preserved_review_meanings=11, first_cause_payment_and_convenience_meanings_unchanged=True,
        pragmatic_declarations_unchanged=True, roundtrips=True, primary_evidence_valid=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    phrase = 'nicht selbst zu bemühen'; start = unit['text'].index(phrase)
    paths = (PARENT, PARENT_BASIS, INDEX, inv, EVIDENCE, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'docs/substituted-judgment-v1.md', 'data/recognizable-consequence-reading-v1.json')
    return dict(status='personal_effort_scope_explained_not_full_conditional_review', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase),
        reading='本人の目的に関する同じ方法で、努力を担うのが本人である条件を否定の対象へ置く。本人の努力なしで用を足せる方法があっても、他者の努力を否定せず、本人の現実の不実行とも同一視しない。',
        evidence=EVIDENCE,
        decisions=['方法の対象となる本人と、経路で努力を担う実施者を別引数で結ぶ。skでは二者を同一にする。',
            '他者による努力があっても本人の努力不要と両立する。他者の努力が必ずあるとは追加しない。',
            '同じ方法・開始・結果に成功と本人の努力の条件を要求する。別方法での成功と無為を寄せ集めない。',
            '歴史辞典の本人・他者の関与の区別を参照する。sogarに近い用法などselbstの全用法へ一般化しない。'],
        remaining=['原文に即した目的と努力の種類・方法と結果の評価範囲の最終選択', '三名詞と仕事の語義、焦点と反語の談話上の扱い',
            '条件文・第二段落全体と二作品全文'],
        whole_unit_semantically_verified=False, full_source_equivalence=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('source', source_checks), ('methods', method_checks),
                     ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    reading = audit(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == reading
    paths = set(build()) | set(parent().source_sha256) | set(reading['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_effort_agents.py', 'scripts/check_effort_agents.py', 'scripts/register_effort_agents.py',
        'scripts/fetch_effort_agents_evidence.py', 'tests/test_effort_agents.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_recognizable_consequence.py', 'scripts/check_book_form.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_written_carriers.py', 'scripts/check_role_qualifications.py', 'scripts/check_substituted_judgment.py',
        'scripts/check_motive_causes.py', 'scripts/check_designation_order.py', 'scripts/compose_falling_depiction.py',
        'noema/constructed.py', 'noema/constructed_discourse.py', 'noema/constructed_semantics.py',
        'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='personal_effort_composed_from_agent_and_beneficiary', document=FULL, **results,
        alignment=dict(**reading['source'], definitions=['rqxr', 'sk', 'rd', 'sx', 'sy'], status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit())); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
