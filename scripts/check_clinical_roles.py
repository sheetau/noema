"""Check clinical topic, principal role and qualification bindings."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts.compose_clinical_roles import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, parent, build, closure
from scripts.check_effort_agents import source_values as effort_values
from scripts.check_pastoral_roles import evaluate, DOMAIN, SOURCE_SCENES
from scripts.check_recognizable_consequence import presentation_values
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_clinical_roles_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v53.json'
REPORT = 'reports/clinical-roles-v1.json'
AUDIT = 'data/clinical-roles-reading-v1.json'
DOC = 'docs/clinical-roles-v1.md'
PEOPLE = (*DOMAIN, 'clinicalRole')


def generic_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r jp[] a.r js[] d.r jh[a a d] c.r jf[a i[h[a] e] d] c.
r jm[a i[h[a] e] d] c.r jq[a i[h[a] e] d] c.r ju[a d] c.
d jrepair[person a] e[b scene[k ju[v person v scene]]].
d jskill[person a] e[b scene[k ju[v person v scene]]].
q[k rqxs[k jp[] r[p jrepair] r[p jskill] k js[] p jh p jf p jm p jq]].''')
    rows = []
    for bits in product((False, True), repeat=8):
        sets = [{r for r, b in zip(('roleA', 'roleB'), bits[k:k+2]) if b} for k in (0, 2, 4, 6)]
        v = dict(jp=lambda: 'worker', js=lambda: 'now', ju=unknown,
            jh=lambda p, r, s: p == 'worker' and r in sets[0] and s == 'now',
            jf=lambda r, d, s: r in sets[1] and symbol(d) == 'jrepair' and s == 'now',
            jm=lambda r, d, s: r in sets[2] and symbol(d) == 'jrepair' and s == 'now',
            jq=lambda r, d, s: r in sets[3] and symbol(d) == 'jskill' and s == 'now')
        actual = evaluate(doc, v, ('worker', 'roleA', 'roleB'), ('now',))[0]
        assert actual == bool(set.intersection(*sets))
        rows.append(dict(bits=list(bits), value=actual))
    return dict(role_combinations=rows, repair_role_reuse=True, qualification_not_executed=True)


@lru_cache(None)
def source_doc(previous=False, compact=False):
    c = parent() if previous else load_catalog(ROOT, BASIS); d = deepcopy(c.document)
    names = ['sr', 'su'] if compact else ['sr', 'su', 'sv', 're', 's2', 'sy', 'wh']
    d.update(declarations=closure(d, names), statements=[])
    q = '''r jp[] a.r jprovider[] a.r js[] d.
q[k sr[k jprovider[] k js[]]].q[t[k su[k jp[]]][k js[]]].'''
    if not compact:
        q += '''q[t[k sv[k jp[]]][k js[]]].
q[k re[k jp[] p sv i[scene d][k s2[k jp[] k wh[] v scene]]]].
q[t[k sy[k jp[]]][k wh[]]].'''
    return parse(format_graph(d, 'compact') + q)


def source_values(variant='baseline'):
    base_variant = variant if variant in ('failed_goal', 'own_effort', 'shared_human_provider') else 'baseline'
    v = effort_values(base_variant)
    provider = 'guide' if variant == 'shared_human_provider' else 'doctor'
    v.update(jp=lambda: 'person', jprovider=lambda: provider, js=lambda: 'case', hzw2=unknown, hzwq=unknown)
    held, serves, principal, requires = v['hzwn'], v['hzwo'], v['hzwu'], v['hzwp']
    v['hzwn'] = lambda p, r, s: (held(p, r, s) and not (variant == 'clinical_only' and r == 'roleA')) or (
        variant != 'no_clinical_role' and (p, r, s) == (
            'other' if variant == 'other_holder' else provider, 'clinicalRole', 'case'))
    v['hzwo'] = lambda r, d, s: serves(r, d, s) or (variant != 'general_health_only' and (r, symbol(d), s) == (
        'otherRole' if variant == 'split_function' else 'clinicalRole',
        'sq' if variant == 'other_function' else 'hzw3', 'case'))
    v['hzwu'] = lambda r, d, s: principal(r, d, s) or (variant != 'incidental_function' and (r, symbol(d), s) == (
        'otherRole' if variant == 'split_principal' else 'clinicalRole',
        'sq' if variant == 'other_primary' else 'hzw3', 'case'))
    v['hzwp'] = lambda r, d, s: requires(r, d, s) or (variant != 'no_requirement' and (r, symbol(d), s) == (
        'otherRole' if variant == 'split_requirement' else 'clinicalRole',
        'rqxi' if variant == 'other_qualification' else 'hzw4',
        'text' if variant == 'other_context' else 'case'))
    if variant == 'no_access':
        access = v['sa']; v['sa'] = lambda p, w, s: access(p, w, s) and w != provider
    if variant == 'wrong_supplied_task':
        supply = v['sb']; v['sb'] = lambda w, p, task, s: supply(w, p, task, s) and w != provider
    return v


def source_checks():
    invalid = ('no_clinical_role', 'other_holder', 'general_health_only', 'split_function', 'other_function',
        'incidental_function', 'split_principal', 'other_primary', 'no_requirement', 'split_requirement',
        'other_qualification', 'other_context')
    variants = ('baseline', *invalid, 'clinical_only', 'shared_human_provider', 'no_access', 'wrong_supplied_task', 'failed_goal', 'own_effort')
    rows = {}
    for variant in variants:
        v = source_values(variant)
        actual = evaluate(source_doc(), v, PEOPLE, SOURCE_SCENES, True)
        old = evaluate(source_doc(True), v, PEOPLE, SOURCE_SCENES, True)
        role = variant not in invalid
        premise = role and variant not in ('no_access', 'wrong_supplied_task')
        assert actual == [role, premise, premise, premise, not premise or variant not in ('failed_goal', 'own_effort')], (variant, actual)
        if variant in invalid:
            assert old == [True] * 5
        elif variant == 'clinical_only':
            assert old == [False, False, False, False, True]
        else:
            assert old == actual
        rows[variant] = dict(previous=old, current=actual)
    for variant in ('baseline', 'general_health_only', 'split_requirement'):
        actual = evaluate(source_doc(compact=True), source_values(variant), PEOPLE, SOURCE_SCENES)
        assert actual == rows[variant]['current'][:2]
    for n in ('hzwn', 'hzwo', 'hzwu', 'hzwp'):
        v = source_values(); v[n] = unknown
        try:
            evaluate(source_doc(compact=True), v, PEOPLE, SOURCE_SCENES)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(n)
    return dict(contrasts=rows, ordinary_role_supply_checks=3, actual_skill_and_judgment_unknown=True,
        definitions_replaced_by_primitives=False, pure_memoization_for_full_composition=True,
        unknown_role_inputs_refused=4, no_implicit_inheritance_between_quoted_task_descriptions=True)


def task_checks():
    c = load_catalog(ROOT, BASIS); d = deepcopy(c.document)
    d.update(declarations=closure(d, ['hzw3']), statements=[])
    doc = parse(format_graph(d, 'compact') + 'r jp[] a.r js[] d.q[t[k hzw3[k jp[]]][k js[]]].')
    people = ('person', 'other', 'judgment', 'otherJudgment', 'topic', 'otherTopic'); scenes = ('now', 'then')
    def vals(bits=(True, True, True, True), variant='baseline'):
        return dict(jp=lambda: 'person', js=lambda: 'now',
            fa=lambda p, j, s: bits[0] and (p, j, s) == ('other' if variant == 'other_actor' else 'person', 'judgment', 'now'),
            fb=lambda j, t, s: bits[1] and (j, t, s) == ('otherJudgment' if variant == 'other_judgment' else 'judgment', 'topic', 'now'),
            sh=lambda t, p, s: bits[2] and (t, p, s) == ('otherTopic' if variant == 'other_health_topic' else 'topic', 'person', 'now'),
            hzw2=lambda t, p, s: bits[3] and (t, p, s) == ('otherTopic' if variant == 'other_clinical_topic' else 'topic',
                'other' if variant == 'other_patient' else 'person', 'then' if variant == 'other_scene' else 'now'))
    rows = []
    for bits in product((False, True), repeat=4):
        actual = evaluate(doc, vals(bits), people, scenes)
        assert actual == [all(bits)]
        rows.append(dict(bits=list(bits), value=actual[0]))
    variants = ('other_actor', 'other_judgment', 'other_health_topic', 'other_clinical_topic', 'other_patient', 'other_scene')
    for variant in variants:
        assert evaluate(doc, vals(variant=variant), people, scenes) == [False]
    for n in ('fa', 'fb', 'sh', 'hzw2'):
        v = vals(); v[n] = unknown
        try:
            evaluate(doc, v, people, scenes)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(n)
    return dict(judgment_combinations=rows, binding_contrasts=list(variants), unknown_inputs_refused=4, ordinary_evaluation=True)


def competence_checks():
    c = load_catalog(ROOT, BASIS); d = deepcopy(c.document)
    d.update(declarations=closure(d, ['sr', 'hzw4']), statements=[])
    doc = parse(format_graph(d, 'compact') + 'r jp[] a.r js[] d.q[k sr[k jp[] k js[]]].q[t[k hzw4[k jp[]]][k js[]]].')
    rows = []
    for role, skill in product((False, True), repeat=2):
        v = source_values('baseline' if role else 'no_clinical_role')
        v.update(jp=lambda: 'doctor', js=lambda: 'case',
            hzwq=lambda p, task, s: skill and (p, symbol(task), s) == ('doctor', 'hzw3', 'case'))
        actual = evaluate(doc, v, PEOPLE, SOURCE_SCENES)
        assert actual == [role, skill]
        rows.append(dict(role=role, actual_skill=skill, values=actual))
    for variant in ('other_person', 'general_skill', 'other_scene'):
        v = source_values(); v.update(jp=lambda: 'doctor', js=lambda: 'case',
            hzwq=lambda p, task, s: (p, symbol(task), s) == (
                'other' if variant == 'other_person' else 'doctor', 'sq' if variant == 'general_skill' else 'hzw3',
                'text' if variant == 'other_scene' else 'case'))
        assert evaluate(doc, v, PEOPLE, SOURCE_SCENES) == [True, False]
    return dict(role_skill_combinations=rows, skill_binding_contrasts=3, ordinary_evaluation=True)


def attribution_checks():
    d = parse((ROOT / CORE).read_text(encoding='utf-8')); rows = {}
    for variant in ('baseline', 'no_presentation', 'no_marker', 'wrong_conditional', 'other_node', 'other_author',
        'other_premise', 'other_conclusion', 'reversed_scope', 'other_context', 'closed_list', 'reverse_order'):
        v = {x['name']: unknown for x in d['declarations'] if x['kind'] == 'primitive'}
        v.update(presentation_values(variant))
        actual = evaluate(d, v, ('examples', 'cause', 'author', 'other', 'payment'), ('text', 'case'))
        assert actual == [variant not in ('no_presentation', 'wrong_conditional', 'closed_list', 'reverse_order'),
            variant in ('baseline', 'closed_list', 'reverse_order')]
        rows[variant] = actual
    return dict(contrasts=rows, all_clinical_facts_unknown=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 43
    assert set(new.entries) - set(old.entries) == {'rqxs', 'rqxt', 'hzw2', 'hzw3', 'hzw4'}
    assert [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']] == ['sr']
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n != 'sr')
    prior = deepcopy(old.entries['sr']['declaration']); prior['name'] = 'rqxt'
    assert new.entries['rqxt']['declaration'] == prior
    affected = [i for i, s in enumerate(new.document['statements']) if 'sr' in {d['name'] for d in closure(new.document, _references(s))}]
    assert affected == [4, 42]
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    ids = [[s['index'] for s in json.loads((ROOT / p).read_text(encoding='utf-8'))['selection']['statements']]
        for p in index['works']['kant-1784']['reviews']]
    for selected in [*ids, [2, 3], [5], [6]]:
        a, b = selection_binding(old, selected), selection_binding(new, selected)
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
    return dict(preserved_statements=43, changed_definitions=['sr'], affected_statements=affected,
        added_definitions=4, added_primitives=1, preserved_review_meanings=11, old_general_role_preserved=True,
        first_cause_payment_convenience_meanings_unchanged=True, roundtrips=True, evidence_valid=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    phrase = 'einen Arzt der für mich die Diät beurtheilt'; start = unit['text'].index(phrase)
    paths = (PARENT, PARENT_BASIS, INDEX, inv, EVIDENCE, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'data/delegation-context-reading-v1.json', 'docs/role-qualifications-v1.md')
    return dict(status='clinical_judgment_role_partially_explained_not_full_noun_equivalence', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase),
        reading='原文の健康判断の供給者を、身体の病気・損傷・不調への対応を主要な務めとし、その判断への専門性を要求する同じ役割へ結ぶ。',
        decisions=['健康一般の専門的助言役はrqxtに保存し、本文srでは治療に関する判断の役割を指定する。',
            '役割の保持・機能・主要性・資格要求を一つの役割で満たす。資格要求から実際の技能は導かない。',
            '歴史辞典の治療の知識と実践を参照するが、地域的・比喩的な全用法をこの用例へ合併しない。',
            '身体の不調への対応という話題があることと、本人が現に病気であることを区別する。'],
        remaining=['判断を援助することに加え、処置を行う実践と歴史的な職務の範囲を説明すること',
            '宗教上の配慮、刊行単位、条件文の批判的効果と全体の確認', '第二段落と二作品全文'],
        whole_unit_semantically_verified=False, full_source_equivalence=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('source', source_checks), ('tasks', task_checks),
        ('competence', competence_checks), ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    reading = audit(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == reading
    paths = set(build()) | set(parent().source_sha256) | set(reading['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_clinical_roles.py', 'scripts/check_clinical_roles.py', 'scripts/register_clinical_roles.py',
        'scripts/fetch_clinical_roles_evidence.py', 'tests/test_clinical_roles.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_effort_agents.py', 'scripts/check_book_form.py', 'scripts/check_pastoral_roles.py',
        'scripts/check_written_carriers.py', 'scripts/check_role_qualifications.py', 'scripts/check_substituted_judgment.py',
        'scripts/check_recognizable_consequence.py', 'scripts/check_motive_causes.py', 'scripts/check_designation_order.py',
        'scripts/compose_falling_depiction.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='clinical_judgment_and_general_health_roles_distinguished', document=FULL, **results,
        alignment=dict(**reading['source'], definitions=['rqxs', 'hzw3', 'hzw4', 'sr', 'su'], status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit())); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
