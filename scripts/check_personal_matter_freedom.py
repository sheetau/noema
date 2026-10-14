"""Check person-indexed universal permission without executing its action descriptions."""
import argparse
import hashlib
from itertools import product
import json
from noema.grammar import parse, format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_topical_enablement import JUDGMENT
from scripts.compose_personal_matter_freedom import ROOT, PARENT, BUILDERS, FRAME, FIELD, SOURCE_FIELD, DESCRIPTION, RULE, MEANINGS

REPORT = ROOT / 'reports/personal-matter-freedom-v1.json'
PEOPLE = ('alice', 'bob'); MATTERS = ('mattera', 'matterb')
DOMAIN = (*PEOPLE, *MATTERS, 'act', 'otheract', 'government', 'role', 'faculty', 'reason', 'examplea', 'exampleb', 'examplec')
SCENES = ('now', 'classification', 'elsewhere')
EXTRA = '''r jtsource[] a.r jtroles[a] a.r jtperson[] a.r jtactivity[] a.r jtcontext[] d.r jtmattera[] a.r jtmatterb[] a.
r jtpeople[a] c.r jttopics[a a] c.r jtactivities[a a a] c.r jtassessed[a a a d] c.r jteligible[a] c.
r jtchoice[a a a ''' + DESCRIPTION + ' ' + DESCRIPTION + '] ' + DESCRIPTION + '.\n'
EXTRA += 'r jtrequired' + RULE[1:] + '.r jtallowed' + RULE[1:] + '.'
EXTRA += ''.join('r jt' + n + t[1:] + '.' for n, t in JUDGMENT)
EXTRA += 'r jtcases[d] c.r jtselfassessment[a a d] c.'


def setup(text, source=False):
    base = parse(text); base['statements'] = []; base = parse(format_graph(base, 'compact') + EXTRA)
    actions = [k('hzgo', 'k jt' + matter + '[]') if source else k('rox', 'k jt' + matter + '[]', *['p jt' + n for n, _ in JUDGMENT]) for matter in MATTERS]
    descriptions = 'i[person a matter a activity a][k jtchoice[v person v matter v activity r[' + actions[0] + '] r[' + actions[1] + ']]]'
    topics = k('hzgq', 'p jtcases') if source else 'p jttopics'
    refs = {n: 'p jt' + n for n in ('people', 'activities', 'assessed', 'eligible', 'required', 'allowed', 'roles')}
    refs.update(source='k jtsource[]', context='k jtcontext[]', descriptions=descriptions, topics=topics)
    checked = k('roy', *(('p aa' if source and n == 'eligible' else refs[n]) for n, _ in FRAME))
    freedom = k('hzgp' if source else 'roz', *(refs[n] for n, _ in (SOURCE_FIELD if source else FIELD)))
    queries = [checked, freedom]
    queries += ['t[c[' + action + '][k jtperson[] k jtactivity[]]][k jtcontext[]]' for action in actions]
    queries += ['e[r[' + actions[0] + ']][r[' + actions[0] + ']]']
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=source, actions=actions, topics=topics,
        action_syntax=[syntax(description(base, action)) for action in actions])


def model_for(data, bits=(True,) * 6, variant='baseline', performed=False):
    selected, allowed = bits[:2], bits[2:]
    pairs = {('alice', 'mattera'), ('alice', 'matterb'), ('bob', 'matterb')} if data['source'] else set(product(PEOPLE, MATTERS))
    examples = {'examplea': ('alice', 'mattera'), 'exampleb': ('alice', 'matterb'), 'examplec': ('bob', 'matterb')}
    def judgments(person, act, point):
        return point == 'classification' and act in examples and examples[act][0] == person or performed and (person, act, point) == ('alice', 'act', 'now')
    def matters(act, matter, point):
        return point == 'classification' and act in examples and examples[act][1] == matter or performed and (act, matter, point) == ('act', 'matterb' if variant == 'other_actual_matter' else 'mattera', 'now')
    def selfassessment(act, person, point):
        return point == 'classification' and act in examples and person == ('alice' if variant == 'other_self' and act == 'examplec' else examples[act][0])
    def norm(source, person, role, act, desc, sign, point):
        if (source, role, act, point) != ('government', 'role', 'act', 'now') or person not in PEOPLE: return False
        if desc.syntax not in data['action_syntax'] or variant == 'other_norm_description': return False
        index = data['action_syntax'].index(desc.syntax)
        if variant == 'outside_denial' and (person, index) == ('bob', 0): return False
        if variant == 'negative_missing' and person == 'bob' and index == 1 and not sign: return False
        return allowed[2 * PEOPLE.index(person) + index]
    def activities(person, matter, act):
        return (person, matter) in pairs and act == 'act' and not (variant == 'empty_activities' and person == 'bob' and matter == 'matterb')
    def owned(faculty, person, point):
        return performed and (faculty, person, point) == ('faculty', 'bob' if variant == 'foreign_faculty' else 'alice', 'now')
    model = guarded(data['document'])
    model.update(jtsource=lambda: 'government', jtroles=lambda person: 'role', jtperson=lambda: 'alice', jtactivity=lambda: 'act', jtcontext=lambda: 'now',
        jtmattera=lambda: 'mattera', jtmatterb=lambda: 'matterb', jtpeople=lambda person: person in PEOPLE and selected[PEOPLE.index(person)],
        jttopics=lambda person, matter: (person, matter) in pairs, jtactivities=activities,
        jtassessed=lambda person, matter, act, point: (person, matter) in pairs and (act, point) == ('act', 'now') and not (variant == 'unassessed' and person == 'bob'),
        jteligible=lambda person: person in PEOPLE and not (variant == 'ineligible' and person == 'bob'),
        jtchoice=lambda person, matter, act, first, second: first if matter == 'mattera' else second,
        jtrequired=lambda source, person, role, act, desc, sign, point: variant == 'opposing_requirement' and (source, person, role, act, point) == ('government', 'bob', 'role', 'act', 'now') and desc.syntax == data['action_syntax'][1] and sign,
        jtallowed=norm, jtowned=owned, jtuse=lambda person, faculty, act, point: performed and (person, faculty, act, point) == ('alice', 'faculty', 'act', 'now'),
        jtjudgments=judgments, jtmatters=matters,
        jtreasons=lambda act, reason, point: performed and (act, reason, point) == ('otheract' if variant == 'other_reason' else 'act', 'reason', 'now'),
        jtsupport=lambda reason, act, point: performed and (reason, act, point) == ('reason', 'act', 'now'),
        jtguidance=lambda guide, person, act, point: variant == 'guided' and (guide, person, act, point) == ('bob', 'alice', 'act', 'now'),
        jtcases=lambda point: point == 'classification' and variant != 'empty_cases', jtselfassessment=selfassessment)
    if data['source']:
        model.update(aa=model['jteligible'], h7a=model['jtrequired'], h7b=norm, ab=owned, ac=model['jtuse'], fa=judgments, fb=matters,
            fc=model['jtreasons'], fd=model['jtsupport'], ad=model['jtguidance'], se=selfassessment)
    return model


def values(data, model):
    return [r['value'] for r in evaluate_document(data['document'], primitives=model, individuals=DOMAIN, situations=SCENES, max_steps=30_000_000)]


def select(data, indices):
    from copy import deepcopy
    result = dict(data); result['document'] = deepcopy(data['document'])
    result['document']['statements'] = [result['document']['statements'][i] for i in indices]
    return result


def checks(texts):
    data = select(setup(texts[0]), (0, 1)); grid = []
    for bits in product((False, True), repeat=6):
        selected, grants = bits[:2], bits[2:]
        expected = [any(selected), any(selected) and all(not selected[i] or all(grants[2 * i:2 * i + 2]) for i in range(2))]
        result = values(data, model_for(data, bits))
        if result != expected: raise ValueError('Personal scope matrix differs: ' + repr((bits, result, expected)))
        grid.append(dict(bits=list(bits), result=result))
    print('64 person and matter permission profiles passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = setup(text, True); profiles = []; cases = {}
        for grants in product((False, True), repeat=4):
            expected = [True, grants[0] and grants[1] and grants[3], False, False, True]
            result = values(data, model_for(data, (True, True, *grants)))
            if result != expected: raise ValueError('Source person/matter profile differs: ' + repr((grants, result, expected)))
            profiles.append(dict(grants=list(grants), result=result))
        for variant in ('outside_denial', 'negative_missing', 'opposing_requirement', 'unassessed', 'empty_activities', 'empty_cases', 'other_self', 'ineligible', 'other_norm_description'):
            checked = variant not in ('unassessed', 'empty_activities', 'empty_cases', 'other_self', 'ineligible')
            expected = [checked, variant == 'outside_denial', False, False, True]
            result = values(data, model_for(data, variant=variant))
            if result != expected: raise ValueError('Source scope contrast differs: ' + repr((variant, result, expected)))
            cases[variant] = result
        for variant in ('baseline', 'foreign_faculty', 'other_reason', 'guided', 'other_actual_matter'):
            expected = [True, True, variant == 'baseline', variant == 'other_actual_matter', True]
            result = values(data, model_for(data, variant=variant, performed=True))
            if result != expected: raise ValueError('Own judgment contrast differs: ' + repr((variant, result, expected)))
            cases['performed_' + variant] = result
        rows.append(dict(profiles=profiles, cases=cases)); print('Source personal freedom and actual judgment contrasts passed', flush=True)
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Personal matter freedom artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Personal matter freedom roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']: raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = 'Jedem frei ließ, sich in allem, was Gewissensangelegenheit ist, seiner eigenen Vernunft zu bedienen'
    start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_personal_matter_freedom.py', 'scripts/check_personal_matter_freedom.py', 'scripts/compose_topical_enablement.py', 'scripts/compose_described_norms.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/grammar.py', 'noema/meaning_basis.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_person_indexed_matter_freedom_and_conscience_classification', documents=documents, sizes=sizes, interpretation=checks(texts), parent_preserved=True, roundtrips=True,
        new_definitions=7, new_primitives=0, new_author_statements=0, alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args(); result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Personal matter freedom record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print('Each person and matter remains bound; permission does not execute judgment')


if __name__ == '__main__': main()
