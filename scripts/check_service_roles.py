"""Check services as provided actions, separately from roles and competence."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts.compose_service_roles import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, PRIMITIVES, parent, build, closure
from scripts.check_clinical_roles import source_values as clinical_values, PEOPLE
from scripts.check_pastoral_roles import evaluate, SOURCE_SCENES
from scripts.check_recognizable_consequence import presentation_values
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_clinical_roles_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v54.json'
REPORT = 'reports/service-roles-v1.json'
AUDIT = 'data/service-roles-reading-v1.json'
DOC = 'docs/service-roles-v1.md'


def generic_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r jp[] a.r js[] d.r jh[a a d] c.r jf[a i[h[a] e] d] c.r jm[a i[h[a] e] d] c.
r jv[a i[h[a a] e] d] c.r jn[a i[h[a a] e] d] c.r jq[a i[h[a] e] d] c.
r ju[a d] c.r jz[a a d] c.
d jassessment[person a] e[b scene[k ju[v person v scene]]].
d jrepair[provider a recipient a] e[b scene[k jz[v provider v recipient v scene]]].
d jskill[person a] e[b scene[k ju[v person v scene]]].
q[k rqxv[k jp[] r[p jassessment] r[p jrepair] r[p jskill] k js[] p jh p jf p jm p jv p jn p jq]].''')
    answers = []
    for bits in product((False, True), repeat=12):
        sets = [{r for r, b in zip(('roleA', 'roleB'), bits[k:k+2]) if b} for k in range(0, 12, 2)]
        v = dict(jp=lambda: 'worker', js=lambda: 'now', ju=unknown, jz=unknown,
            jh=lambda p, r, s: p == 'worker' and r in sets[0] and s == 'now',
            jf=lambda r, d, s: r in sets[1] and symbol(d) == 'jassessment' and s == 'now',
            jm=lambda r, d, s: r in sets[2] and symbol(d) == 'jassessment' and s == 'now',
            jv=lambda r, d, s: r in sets[3] and symbol(d) == 'jrepair' and s == 'now',
            jn=lambda r, d, s: r in sets[4] and symbol(d) == 'jrepair' and s == 'now',
            jq=lambda r, d, s: r in sets[5] and symbol(d) == 'jskill' and s == 'now')
        actual = evaluate(doc, v, ('worker', 'roleA', 'roleB'), ('now',))[0]
        assert actual == bool(set.intersection(*sets))
        answers.append(actual)
    assert len(answers) == 4096 and sum(answers) == 127
    return dict(role_combinations=4096, true_combinations=127, result_sha256=digest(bytes(answers)),
        repair_role_reuse=True, activities_and_qualifications_not_executed=True, ordinary_evaluation=True)


@lru_cache(None)
def source_doc(previous=False, compact=False):
    c = parent() if previous else load_catalog(ROOT, BASIS); d = deepcopy(c.document)
    names = ['sr', 'su'] if compact else ['sr', 'su', 'sv', 're', 's2', 'sy', 'wh']
    d.update(declarations=closure(d, names), statements=[])
    text = '''r jp[] a.r jprovider[] a.r js[] d.
q[k sr[k jprovider[] k js[]]].q[t[k su[k jp[]]][k js[]]].'''
    if not compact:
        text += '''q[t[k sv[k jp[]]][k js[]]].
q[k re[k jp[] p sv i[scene d][k s2[k jp[] k wh[] v scene]]]].
q[t[k sy[k jp[]]][k wh[]]].'''
    return parse(format_graph(d, 'compact') + text)


def source_values(variant='baseline'):
    base = variant if variant in ('failed_goal', 'own_effort', 'shared_human_provider', 'no_access') else 'baseline'
    v = clinical_values(base)
    v.update(hzw5=unknown, hzxd=unknown, df=unknown, dg=unknown,
        hzxa=lambda r, d, s: variant != 'advice_only' and (r, symbol(d), s) == (
            'otherRole' if variant == 'split_service' else 'clinicalRole',
            'otherActivity' if variant == 'other_service' else 'hzw6', 'case'),
        hzxb=lambda r, d, s: variant != 'incidental_service' and (r, symbol(d), s) == (
            'otherRole' if variant == 'split_main_service' else 'clinicalRole',
            'otherActivity' if variant == 'other_main_service' else 'hzw6', 'case'))
    required = v['hzwp']
    v['hzwp'] = lambda r, d, s: required(r, d, s) or (variant != 'judgment_qualification_only' and (r, symbol(d), s) == (
        'otherRole' if variant == 'split_qualification' else 'clinicalRole',
        'hzw4' if variant == 'other_qualification' else 'hzxe',
        'text' if variant == 'other_context' else 'case'))
    return v


def source_checks():
    invalid = ('advice_only', 'split_service', 'other_service', 'incidental_service', 'split_main_service',
        'other_main_service', 'judgment_qualification_only', 'split_qualification', 'other_qualification', 'other_context')
    rows = {}
    for variant in ('baseline', *invalid, 'shared_human_provider', 'no_access', 'failed_goal', 'own_effort'):
        v = source_values(variant)
        actual = evaluate(source_doc(), v, PEOPLE, SOURCE_SCENES, True)
        old = evaluate(source_doc(True), v, PEOPLE, SOURCE_SCENES, True)
        role = variant not in invalid; supplied = role and variant != 'no_access'
        assert actual == [role, supplied, supplied, supplied, not supplied or variant not in ('failed_goal', 'own_effort')], (variant, actual)
        assert old == ([True] * 5 if variant in invalid else actual), (variant, old)
        rows[variant] = dict(previous=old, current=actual)
    for variant in ('baseline', 'advice_only', 'split_qualification'):
        assert evaluate(source_doc(compact=True), source_values(variant), PEOPLE, SOURCE_SCENES) == rows[variant]['current'][:2]
    for n in ('hzxa', 'hzxb', 'hzwp'):
        v = source_values(); v[n] = unknown
        try:
            evaluate(source_doc(compact=True), v, PEOPLE, SOURCE_SCENES)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(n)
    return dict(contrasts=rows, actual_actions_and_competence_unknown=True, ordinary_role_supply_checks=3,
        pure_memoization_for_full_composition=True, definitions_replaced_by_primitives=False, unknown_inputs_refused=3)


def action_doc():
    c = load_catalog(ROOT, BASIS); d = deepcopy(c.document)
    d.update(declarations=closure(d, ['hzw6']), statements=[])
    return parse(format_graph(d, 'compact') + 'r jp[] a.r jr[] a.r js[] d.q[t[k hzw6[k jp[] k jr[]]][k js[]]].')


def action_values(bits=(True, True, True, True, True), variant='baseline'):
    provider = 'patient' if variant == 'self_care' else 'provider'
    return dict(jp=lambda: provider, jr=lambda: 'patient', js=lambda: 'now',
        dg=lambda a, s: bits[0] and (a, s) == ('otherAct' if variant == 'other_occurrence' else 'act', 'now'),
        df=lambda p, a, s: bits[1] and (p, a, s) == (
            'other' if variant == 'other_participant' else provider,
            'otherAct' if variant == 'other_participation_act' else 'act', 'now'),
        hzw5=lambda a, p, r, t, s: bits[2] and (a, p, r, t, s) == ('act',
            'patient' if variant == 'reversed_parties' else provider,
            'provider' if variant == 'reversed_parties' else 'other' if variant == 'other_recipient' else 'patient',
            'topic', 'then' if variant == 'other_action_scene' else 'now'),
        sh=lambda t, r, s: bits[3] and (t, r, s) == (
            'otherTopic' if variant == 'other_health_topic' else 'topic', 'patient', 'now'),
        hzw2=lambda t, r, s: bits[4] and (t, r, s) == (
            'otherTopic' if variant == 'other_clinical_topic' else 'topic',
            'other' if variant == 'other_topic_recipient' else 'patient', 'then' if variant == 'other_topic_scene' else 'now'))


def action_checks():
    d = action_doc(); people = ('provider', 'patient', 'other', 'act', 'otherAct', 'topic', 'otherTopic'); scenes = ('now', 'then')
    rows = []
    for bits in product((False, True), repeat=5):
        actual = evaluate(d, action_values(bits), people, scenes)
        assert actual == [all(bits)]
        rows.append(dict(bits=list(bits), value=actual[0]))
    variants = ('other_occurrence', 'other_participant', 'other_participation_act', 'reversed_parties',
        'other_recipient', 'other_action_scene', 'other_health_topic', 'other_clinical_topic',
        'other_topic_recipient', 'other_topic_scene', 'self_care')
    contrasts = {}
    for variant in variants:
        contrasts[variant] = evaluate(d, action_values(variant=variant), people, scenes)
        assert contrasts[variant] == [variant == 'self_care'], (variant, contrasts[variant])
    for n in ('dg', 'df', 'hzw5', 'sh', 'hzw2'):
        v = action_values(); v[n] = unknown
        try:
            evaluate(d, v, people, scenes)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(n)
    return dict(action_combinations=rows, binding_contrasts=contrasts, unknown_inputs_refused=5,
        ordinary_evaluation=True, treatment_success_not_a_required_input=True)


def competence_checks():
    c = load_catalog(ROOT, BASIS); d = deepcopy(c.document)
    d.update(declarations=closure(d, ['sr', 'hzw4', 'hzw6', 'hzxe']), statements=[])
    doc = parse(format_graph(d, 'compact') + '''r jp[] a.r js[] d.
q[k sr[k jp[] k js[]]].q[t[k hzw4[k jp[]]][k js[]]].
q[k hzxd[k jp[] r[p hzw6] k js[]]].q[t[k hzxe[k jp[]]][k js[]]].''')
    rows = []
    for role, judgment, provision in product((False, True), repeat=3):
        v = source_values('baseline' if role else 'advice_only')
        v.update(jp=lambda: 'doctor', js=lambda: 'case',
            hzwq=lambda p, task, s: judgment and (p, symbol(task), s) == ('doctor', 'hzw3', 'case'),
            hzxd=lambda p, service, s: provision and (p, symbol(service), s) == ('doctor', 'hzw6', 'case'))
        actual = evaluate(doc, v, PEOPLE, SOURCE_SCENES)
        assert actual == [role, judgment, provision, judgment and provision]
        rows.append(dict(role=role, judgment_skill=judgment, provision_skill=provision, values=actual))
    return dict(independent_role_and_skills=rows, ordinary_evaluation=True, no_actual_action_required=True)


def attribution_checks():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8')); rows = {}
    for variant in ('baseline', 'no_presentation', 'no_marker', 'wrong_conditional', 'other_node', 'other_author',
        'other_premise', 'other_conclusion', 'reversed_scope', 'other_context', 'closed_list', 'reverse_order'):
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        v.update(presentation_values(variant))
        actual = evaluate(doc, v, ('examples', 'cause', 'author', 'other', 'payment'), ('text', 'case'))
        assert actual == [variant not in ('no_presentation', 'wrong_conditional', 'closed_list', 'reverse_order'),
            variant in ('baseline', 'closed_list', 'reverse_order')]
        rows[variant] = actual
    return dict(contrasts=rows, all_service_facts_unknown=True)


def preserved_selection(before, after):
    assert before['statements'] == after['statements']
    a, b = before['dependencies'], after['dependencies']
    assert len(a) == len(set(a)) and len(b) == len(set(b)) and set(a) == set(b)
    assert [n for n in a if n not in ('df', 'dg')] == [n for n in b if n not in ('df', 'dg')]
    assert [n for n in a if n in ('df', 'dg')] == [n for n in b if n in ('df', 'dg')]


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 43
    assert set(new.entries) - set(old.entries) == set(PRIMITIVES) | {'rqxu', 'rqxv', 'rqxw', 'hzw6', 'hzxe'}
    assert [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']] == ['sr']
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n != 'sr')
    assert [d['name'] for d in old.document['declarations'] if d['name'] not in ('df', 'dg')] == [
        d['name'] for d in new.document['declarations'] if d['name'] in old.entries and d['name'] not in ('df', 'dg')]
    prior = deepcopy(old.entries['sr']['declaration']); prior['name'] = 'rqxw'
    assert new.entries['rqxw']['declaration'] == prior
    affected = [i for i, s in enumerate(new.document['statements']) if 'sr' in {d['name'] for d in closure(new.document, _references(s))}]
    assert affected == [4, 42]
    index = json.loads((ROOT / INDEX).read_text(encoding='utf-8'))
    ids = [[s['index'] for s in json.loads((ROOT / p).read_text(encoding='utf-8'))['selection']['statements']]
        for p in index['works']['kant-1784']['reviews']]
    for selected in [*ids, [2, 3], [5], [6]]:
        a, b = selection_binding(old, selected), selection_binding(new, selected)
        preserved_selection(a, b)
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
        added_definitions=5, added_primitives=4, preserved_review_meanings=11, old_judgment_role_preserved=True,
        moved_declarations=['df', 'dg'], only_moved_dependency_positions_may_differ=True,
        first_cause_payment_convenience_meanings_unchanged=True, roundtrips=True, evidence_valid=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    phrase = 'einen Arzt der für mich die Diät beurtheilt'; start = unit['text'].index(phrase)
    paths = (PARENT, PARENT_BASIS, INDEX, inv, EVIDENCE, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'data/clinical-roles-reading-v1.json', 'data/delegation-context-reading-v1.json')
    return dict(status='clinical_judgment_and_provided_measures_connected_not_full_conditional_review', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase),
        reading='治療の知識と実践を担う役割として、判断への援助と、実施者から受け手への措置の提供を同じ役割へ結ぶ。原文の個々の仕事は依然として食事・生活の判断snであり、その場の治療の生起を追加しない。',
        decisions=['同じ役割に判断と措置の機能・主要性・両方の専門性の要求を結ぶ。',
            '実施者と受け手を順序付きの二引数で保ち、別人が処置するという内容と混同しない。',
            '措置の生起・実施者の参加・対象事項を結ぶが、処置の成功は条件に含めない。',
            '役割保持・実際の技能・現在の実行は独立に述べる。医師が全ての処置を単独で手作業するとはしない。'],
        remaining=['この用例に採る歴史的な職務範囲と、条件文全体の最終確認',
            '宗教上の配慮、刊行単位と批判的な談話の効果', '第二段落と二作品全文'],
        whole_unit_semantically_verified=False, full_source_equivalence=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('source', source_checks), ('actions', action_checks),
        ('competence', competence_checks), ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    reading = audit(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == reading
    paths = set(build()) | set(parent().source_sha256) | set(reading['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_service_roles.py', 'scripts/check_service_roles.py', 'scripts/register_service_roles.py',
        'tests/test_service_roles.py', 'scripts/fetch_clinical_roles_evidence.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_clinical_roles.py', 'scripts/check_effort_agents.py', 'scripts/check_book_form.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_written_carriers.py', 'scripts/check_role_qualifications.py',
        'scripts/check_substituted_judgment.py', 'scripts/check_recognizable_consequence.py', 'scripts/check_motive_causes.py',
        'scripts/check_designation_order.py', 'scripts/compose_falling_depiction.py', 'noema/constructed.py',
        'noema/constructed_discourse.py', 'noema/constructed_semantics.py', 'noema/meaning_catalog.py',
        'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='role_requirements_and_provided_actions_distinguished', document=FULL, **results,
        alignment=dict(**reading['source'], definitions=['rqxu', 'rqxv', 'hzw6', 'hzxe', 'sr', 'su'], status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit())); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
