"""Verify appointment, role, community and activity bindings independently."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts.compose_appointed_roles import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, PRIMITIVES, parent, build, closure
from scripts.check_service_roles import source_values as previous_values, PEOPLE, preserved_selection
from scripts.check_pastoral_roles import evaluate, SOURCE_SCENES
from scripts.check_recognizable_consequence import presentation_values
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_appointed_roles_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v56.json'
REPORT = 'reports/appointed-roles-v1.json'
AUDIT = 'data/appointed-roles-reading-v1.json'
DOC = 'docs/appointed-roles-v1.md'
DOMAIN = (*PEOPLE, 'community', 'otherCommunity')


def generic_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''r jp[] a.r js[] d.
r jh[a a d] c.r jf[a i[h[a] e] d] c.r jm[a i[h[a] e] d] c.
r ja[a a a d] c.r jr[a i[h[a a] e] a d] c.r ju[a d] c.r jv[a a d] c.
d jtask[person a] e[b scene[k ju[v person v scene]]].
d jservice[person a community a] e[b scene[k jv[v person v community v scene]]].
q[k rqxx[k jp[] r[p jtask] r[p jservice] k js[] p jh p jf p jm p ja p jr]].''')
    answers = []
    for bits in product((False, True), repeat=10):
        sets = [{r for r, bit in zip(('roleA', 'roleB'), bits[i:i+2]) if bit} for i in range(0, 10, 2)]
        v = dict(jp=lambda: 'teacher', js=lambda: 'now', ju=unknown, jv=unknown,
            jh=lambda p, r, s: p == 'teacher' and r in sets[0] and s == 'now',
            jf=lambda r, d, s: r in sets[1] and symbol(d) == 'jtask' and s == 'now',
            jm=lambda r, d, s: r in sets[2] and symbol(d) == 'jtask' and s == 'now',
            ja=lambda p, r, c, s: p == 'teacher' and r in sets[3] and c == 'school' and s == 'now',
            jr=lambda r, d, c, s: r in sets[4] and symbol(d) == 'jservice' and c == 'school' and s == 'now')
        actual = evaluate(doc, v, ('teacher', 'roleA', 'roleB', 'school'), ('now',))[0]
        assert actual == bool(set.intersection(*sets))
        answers.append(actual)
    assert len(answers) == 1024 and sum(answers) == 63
    return dict(combinations=1024, true_combinations=63, result_sha256=digest(bytes(answers)),
        educational_appointment_fixture=True, activities_not_executed=True, ordinary_evaluation=True)


@lru_cache(None)
def source_doc(previous=False, compact=False):
    c = parent() if previous else load_catalog(ROOT, BASIS); d = deepcopy(c.document)
    names = ['sp', 'st'] if compact else ['sp', 'st', 'sv', 're', 's2', 'sy', 'wh']
    d.update(declarations=closure(d, names), statements=[])
    text = '''r jp[] a.r jg[] a.r js[] d.
q[k sp[k jg[] k js[]]].q[t[k st[k jp[]]][k js[]]].'''
    if not compact:
        text += '''q[t[k sv[k jp[]]][k js[]]].
q[k re[k jp[] p sv i[scene d][k s2[k jp[] k wh[] v scene]]]].
q[t[k sy[k jp[]]][k wh[]]].'''
    return parse(format_graph(d, 'compact') + text)


def source_values(variant='baseline'):
    v = previous_values(variant if variant in ('failed_goal', 'own_effort') else 'baseline')
    if variant == 'no_access':
        access = v['sa']
        v['sa'] = lambda p, w, s: w != 'guide' and access(p, w, s)
    v.update(jp=lambda: 'person', jg=lambda: 'guide', js=lambda: 'case', hzxh=unknown,
        hzxf=lambda p, r, c, s: variant != 'no_appointment' and (p, r, c, s) == (
            'other' if variant == 'other_appointee' else 'guide',
            'otherRole' if variant == 'other_appointed_role' else 'pastoral',
            'otherCommunity' if variant == 'other_appointing_community' else 'community',
            'text' if variant == 'other_appointment_scene' else 'case'),
        hzxg=lambda r, d, c, s: variant != 'no_responsibility' and (r, symbol(d), c, s) == (
            'otherRole' if variant == 'other_responsible_role' else 'pastoral',
            'hzw6' if variant == 'other_service' else 'hzxi',
            'otherCommunity' if variant == 'other_responsible_community' else 'community',
            'text' if variant == 'other_responsibility_scene' else 'case'))
    return v


def source_checks():
    invalid = ('no_appointment', 'other_appointee', 'other_appointed_role', 'other_appointing_community',
        'other_appointment_scene', 'no_responsibility', 'other_responsible_role', 'other_service',
        'other_responsible_community', 'other_responsibility_scene')
    rows = {}
    for variant in ('baseline', *invalid, 'no_access', 'failed_goal', 'own_effort'):
        v = source_values(variant)
        actual = evaluate(source_doc(), v, DOMAIN, SOURCE_SCENES, True)
        old = evaluate(source_doc(True), v, DOMAIN, SOURCE_SCENES, True)
        role = variant not in invalid; supplied = role and variant != 'no_access'
        wanted = [role, supplied, supplied, supplied, not supplied or variant not in ('failed_goal', 'own_effort')]
        assert actual == wanted, (variant, actual)
        assert old == ([True] * 5 if variant in invalid else actual), (variant, old)
        rows[variant] = dict(previous=old, current=actual)
    for variant in ('baseline', 'no_appointment', 'other_responsible_community'):
        assert evaluate(source_doc(compact=True), source_values(variant), DOMAIN, SOURCE_SCENES) == rows[variant]['current'][:2]
    for n in ('hzxf', 'hzxg'):
        v = source_values(); v[n] = unknown
        try:
            evaluate(source_doc(compact=True), v, DOMAIN, SOURCE_SCENES)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(n)
    return dict(contrasts=rows, ordinary_comparisons=3, unknown_inputs_refused=2,
        current_activity_and_skill_unknown=True, pure_memoization=True,
        definitions_replaced_by_primitives=False, previous_nonappointed_countermodel_rejected=True)


def sentence_checks():
    answers = []
    for book, guide, doctor, goal, effort_free in product((False, True), repeat=5):
        v = source_values(); access, attainment = v['sa'], v['sj']
        available = {w for w, bit in zip(('book', 'guide', 'doctor'), (book, guide, doctor)) if bit}
        v['sa'] = lambda p, w, s: w in available and access(p, w, s)
        v['sj'] = lambda p, s: goal and attainment(p, s)
        v['hzwz'] = lambda a, p, m, s, e: not effort_free and (a, p, m, s, e) == ('person', 'person', 'plan', 'case', 'outcome')
        actual = evaluate(source_doc(), v, DOMAIN, SOURCE_SCENES, True)
        premise = book and guide and doctor
        assert actual == [True, guide, premise, premise, not premise or goal and effort_free]
        answers.append(dict(bits=[book, guide, doctor, goal, effort_free], values=actual))
    return dict(combinations=answers, all_current_definitions_executed=True, pure_memoization=True,
        semantic_equivalence_automatically_proved=False)


def activity_checks():
    c = load_catalog(ROOT, BASIS); d = deepcopy(c.document)
    d.update(declarations=closure(d, ['hzxi']), statements=[])
    doc = parse(format_graph(d, 'compact') + 'r jp[] a.r jc[] a.r js[] d.q[t[k hzxi[k jp[] k jc[]]][k js[]]].')
    def values(bits=(True, True, True), variant='baseline'):
        return dict(jp=lambda: 'guide', jc=lambda: 'community', js=lambda: 'now',
            dg=lambda a, s: bits[0] and (a, s) == ('act', 'now'),
            df=lambda p, a, s: bits[1] and (p, a, s) == (
                'other' if variant == 'other_person' else 'guide',
                'otherAct' if variant == 'other_participation_act' else 'act', 'now'),
            hzxh=lambda a, c, s: bits[2] and (a, c, s) == (
                'otherAct' if variant == 'other_content_act' else 'act',
                'otherCommunity' if variant == 'other_community' else 'community',
                'then' if variant == 'other_scene' else 'now'))
    people = ('guide', 'other', 'act', 'otherAct', 'community', 'otherCommunity')
    for bits in product((False, True), repeat=3):
        assert evaluate(doc, values(bits), people, ('now', 'then')) == [all(bits)]
    variants = ('baseline', 'other_person', 'other_participation_act', 'other_content_act', 'other_community', 'other_scene')
    for variant in variants:
        assert evaluate(doc, values(variant=variant), people, ('now', 'then')) == [variant == 'baseline']
    for n in ('dg', 'df', 'hzxh'):
        v = values(); v[n] = unknown
        try:
            evaluate(doc, v, people, ('now', 'then'))
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(n)
    # Appointment and actual participation can vary independently in one model.
    d = deepcopy(c.document); d.update(declarations=closure(d, ['sp', 'hzxi']), statements=[])
    combined = parse(format_graph(d, 'compact') + 'r jp[] a.r jc[] a.r js[] d.q[k sp[k jp[] k js[]]].q[t[k hzxi[k jp[] k jc[]]][k js[]]].')
    rows = []
    for appointed, active in product((False, True), repeat=2):
        v = source_values('baseline' if appointed else 'no_appointment')
        v.update(jp=lambda: 'guide', jc=lambda: 'community', js=lambda: 'case',
            dg=lambda a, s: active and (a, s) == ('act', 'case'),
            df=lambda p, a, s: (p, a, s) == ('guide', 'act', 'case'),
            hzxh=lambda a, c, s: (a, c, s) == ('act', 'community', 'case'))
        actual = evaluate(combined, v, (*DOMAIN, 'act'), SOURCE_SCENES)
        assert actual == [appointed, active]
        rows.append(dict(appointed=appointed, active=active, values=actual))
    return dict(combinations=8, binding_contrasts=6, unknown_inputs_refused=3, independent_status_and_action=rows)


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
    return dict(contrasts=rows, institutional_and_action_facts_unknown=True)


def structure():
    old, new = parent(), load_catalog(ROOT, BASIS)
    assert old.document['statements'] == new.document['statements'] and len(new.document['statements']) == 43
    assert set(new.entries) - set(old.entries) == set(PRIMITIVES) | {'rqxx', 'rqxy', 'hzxi'}
    assert [n for n in old.entries if old.entries[n]['declaration'] != new.entries[n]['declaration']] == ['sp']
    assert all(substantive(old.entries[n]) == substantive(new.entries[n]) for n in old.entries if n != 'sp')
    assert [d['name'] for d in old.document['declarations'] if d['name'] not in ('df', 'dg')] == [
        d['name'] for d in new.document['declarations'] if d['name'] in old.entries and d['name'] not in ('df', 'dg')]
    saved = deepcopy(old.entries['sp']['declaration']); saved['name'] = 'rqxy'
    assert new.entries['rqxy']['declaration'] == saved
    affected = [i for i, s in enumerate(new.document['statements']) if 'sp' in {d['name'] for d in closure(new.document, _references(s))}]
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
    return dict(preserved_statements=43, changed_definitions=['sp'], affected_statements=affected,
        added_definitions=3, added_primitives=3, preserved_review_meanings=11, old_role_preserved=True,
        moved_declarations=['df', 'dg'], only_moved_dependency_positions_may_differ=True,
        first_cause_payment_convenience_meanings_unchanged=True, roundtrips=True, evidence_valid=True)


def audit():
    inv = 'artifacts/written-units-v1/kant-1784.json'
    unit = next(u for u in json.loads((ROOT / inv).read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    phrase = 'einen Seelsorger, der für mich Gewissen hat'; start = unit['text'].index(phrase)
    paths = (PARENT, PARENT_BASIS, INDEX, inv, EVIDENCE, 'artifacts/first-cause-reading-v1/page-482.jpg',
        'data/pastoral-role-evidence-v1.json', 'data/delegation-sentence-reading-v1.json',
        'data/delegation-context-reading-v1.json', 'reports/delegation-sentence-v1.json')
    return dict(status='appointed_public_religious_responsibility_connected', reviewer='assistant_review',
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, start + len(phrase)], text=phrase),
        reading='宗教上の援助を主要な務めとし、公の宗教的奉仕の責務を持つ同じ役割に共同体から任じられた者として読む。',
        decisions=['Geistlichの広い歴史的用法を選ぶ。狭義の秘跡の資格・教派固有の叙任を一律の条件にしない。',
            '任用・援助機能・主要性・公的責務を同じ役割と共同体へ結ぶ。',
            '役割と技能・現在の活動・成功を区別する。共同体の制度の正当性も追加しない。',
            '旧spはrqxyとして保存する。非任用の援助者を表す能力を失わない。'],
        remaining=['公的な宗教行為hzxhの内部構成は基本関係の解釈に残る',
            '修正した条件文の通し読解、第二段落と二作品全文の意味確認'],
        whole_unit_semantically_verified=False, full_source_equivalence=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in paths})


def build_report():
    results = {}
    for name, fn in [('generic', generic_checks), ('source', source_checks), ('sentence', sentence_checks),
        ('activity', activity_checks), ('attribution', attribution_checks), ('structure', structure)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    reading = audit(); assert json.loads((ROOT / AUDIT).read_text(encoding='utf-8')) == reading
    paths = set(build()) | set(parent().source_sha256) | set(reading['source_sha256']) | {AUDIT, DOC,
        'scripts/compose_appointed_roles.py', 'scripts/check_appointed_roles.py', 'scripts/register_appointed_roles.py',
        'tests/test_appointed_roles.py', 'scripts/fetch_appointed_roles_evidence.py', 'scripts/fetch_pastoral_role_evidence.py',
        'scripts/check_service_roles.py', 'scripts/check_clinical_roles.py', 'scripts/check_effort_agents.py',
        'scripts/check_book_form.py', 'scripts/check_pastoral_roles.py', 'scripts/check_written_carriers.py',
        'scripts/check_role_qualifications.py', 'scripts/check_substituted_judgment.py',
        'scripts/check_recognizable_consequence.py', 'scripts/check_motive_causes.py', 'scripts/check_designation_order.py',
        'scripts/compose_falling_depiction.py', 'noema/constructed.py', 'noema/constructed_discourse.py',
        'noema/constructed_semantics.py', 'noema/meaning_catalog.py', 'noema/semantic_reviews.py', 'noema/script.py'}
    return dict(status='appointment_and_community_duty_distinguished_from_activity', document=FULL, **results,
        alignment=dict(**reading['source'], definitions=['rqxx', 'rqxy', 'hzxi', 'sp', 'st'], status='explicit_interpretive_annotation'),
        new_covered_characters=0, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT / AUDIT, encoded(audit())); write_exact(ROOT / REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
