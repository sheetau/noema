"""Verify opportunities to pursue ability without asserting effort or success."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.check_topical_enablement import EXTRA as CAPACITY_EXTRA, REFS as CAPACITY_REFS, DOMAIN as SOURCE_DOMAIN, SCENES as SOURCE_SCENES
from scripts.compose_limits import call as k, app, op
from scripts.compose_free_pursuit import ROOT, PARENT, BUILDERS, OPPORTUNITY, SOURCE, GROUP, CAPACITY, TRUE

REPORT = ROOT / 'reports/free-pursuit-v1.json'
PEOPLE = ('alice', 'bob')
DOMAIN = (*PEOPLE, 'authority', 'role', 'plan', 'other', 'part')
SCENES = ('now', 'later', 'elsewhere')
EXTRA = '''r jmsource[] a.r jmperson[] a.r jmrole[] a.r jmactivity[] a.r jmcontext[] d.
r jmavailable[a a d] c.r jmoutcomes[a a d d] c.r jmoccurs[a d] c.r jmparticipates[a a d] c.r jmwork[a a d] c.
r jmaims[a a i[h[j[a]] e] j[a] d] c.r jmgoals[a] e.r jmscope[a] c.r jmroles[a] a.
r jmrequired[a a a a i[h[a a] e] c d] c.r jmallow[a a a a i[h[a a] e] c d] c.'''
REFS = {n: 'k jm' + n + '[]' for n in ('source', 'person', 'role', 'activity', 'context')}
REFS.update({n: 'p jm' + n for n in ('available', 'outcomes', 'required', 'scope', 'roles')})
REFS['allowed'] = 'p jmallow'


def setup(text, source=False):
    base = candidate(text, EXTRA + (CAPACITY_EXTRA if source else ''))
    goal = k('hzey', *(CAPACITY_REFS[n] for n, _ in CAPACITY)) if source else k('rlu', 'p jmgoals')
    goal_syntax = syntax(description(base, goal))
    work = k('hzez', 'r[' + goal + ']', 'p jmaims') if source else k('rlt', 'r[' + goal + ']',
        'p jmaims', 'p jmoccurs', 'p jmparticipates', 'p jmwork')
    work_syntax = syntax(description(base, work)); refs = {**REFS, 'description': 'r[' + work + ']'}
    norms = ['p h7a', 'p h7b'] if source else ['p jmrequired', 'p jmallow']
    permitted = k('rdm', *(refs[n] for n in ('source', 'person', 'role', 'activity', 'description')), TRUE, refs['context'], *norms)
    opportunities = []
    for name in (('hze2', 'hze3') if source else ('rlv', 'rlw')):
        opportunities.append(k(name, *(refs[n] for n, _ in (SOURCE if source else OPPORTUNITY))))
    actual = op('t', app('s[' + refs['description'] + ']', refs['person'], refs['activity']), refs['context'])
    if source:
        group = k('hze4', *(refs[n] for n, _ in GROUP))
    else:
        fields = {**refs, 'person': 'v person', 'activity': 'v activity', 'context': 'v point', 'role': app('p jmroles', 'v person')}
        content = 'i[person a][b point[g activity a[' + k('rlw', *(fields[n] for n, _ in OPPORTUNITY)) + ']]]'
        group = k('rlx', refs['scope'], content, refs['context'])
    expressions = [permitted, *opportunities, actual, group]
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + expr + '].' for expr in expressions))
    return dict(document=doc, source=source, goal=goal, goal_syntax=goal_syntax, work=work, work_syntax=work_syntax)


def model_for(data, bits=(True, True, True, True), variant='baseline', actual=False):
    doc, source = data['document'], data['source']; model = guarded(doc)
    scenes = SOURCE_SCENES if source else SCENES
    future = 'trained' if source else 'later'; authority = 'teacher' if source else 'authority'
    role = 'faith' if source else 'role'; other = 'actone' if source else 'other'; part = 'reason' if source else 'part'
    allow, abstain, available, execution = bits
    def at(point): return execution and (point == future or actual and point == 'now')
    def occurs(activity, point): return activity == ('plan' if variant != 'wrong_activity' else other) and at(point)
    def participates(person, activity, point): return person in PEOPLE and activity == 'plan' and at(point)
    def work(person, activity, point): return participates(person, activity, point) and variant != 'no_selfwork'
    def aims(person, activity, desc, bindings, point):
        return person in PEOPLE and activity == 'plan' and desc.syntax == data['goal_syntax'] and (
            variant != 'goal_alias') and bindings.items == ((other,) if variant == 'other_goal_person' else (person,)) and at(point)
    def norm(src, person, job, activity, desc, sign, point, permission):
        if (src, job, activity, point) != (authority, role, 'plan', 'now') or person not in PEOPLE: return False
        if desc.syntax != data['work_syntax'] or variant == 'permission_alias': return False
        if permission: return allow if sign else abstain
        return (variant == 'ban' and not sign) or (variant == 'compulsory' and sign)
    model.update(jmsource=lambda: authority, jmperson=lambda: 'alice', jmrole=lambda: role, jmactivity=lambda: 'plan', jmcontext=lambda: 'now',
        jmavailable=lambda person, activity, point: available and person in PEOPLE and activity == 'plan' and point == 'now',
        jmoutcomes=lambda person, activity, start, end: person in PEOPLE and activity == 'plan' and start == 'now' and end == future and variant != 'no_outcome',
        jmoccurs=occurs, jmparticipates=participates, jmwork=work, jmaims=aims,
        jmrequired=lambda *a: norm(*a, False), jmallow=lambda *a: norm(*a, True),
        jmscope=lambda person: person in PEOPLE, jmroles=lambda person: role,
        jmgoals=lambda person: Content(scenes, tuple(False for _ in scenes)))
    if source:
        model.update(aa=lambda person: person in PEOPLE, ae=model['jmavailable'], af=model['jmoutcomes'],
            dg=occurs, df=participates, h7a=model['jmrequired'], h7b=model['jmallow'],
            h4m=lambda item, person, point: item == part and person in PEOPLE and at(point),
            h4n=lambda person, item, activity, point: item == part and work(person, activity, point))
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model,
        individuals=SOURCE_DOMAIN if data['source'] else DOMAIN,
        situations=SOURCE_SCENES if data['source'] else SCENES, max_steps=5_000_000)]


def checks(texts):
    generic = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=4):
        allow, abstain, available, execution = bits; opportunity = allow and available and execution
        expected = [allow, opportunity, opportunity and abstain, False, opportunity and abstain]
        actual = values(generic, model_for(generic, bits))
        if actual != expected: raise ValueError('Pursuit opportunity collapsed: ' + repr((bits, actual)))
        grid.append(dict(bits=list(bits), result=actual))
    rows = []
    for text, source in ((texts[0], False), (texts[1], True), (texts[2], True)):
        data = setup(text, source); results = {}
        for variant in ('baseline', 'wrong_activity', 'no_selfwork', 'goal_alias', 'other_goal_person', 'permission_alias', 'no_outcome', 'ban', 'compulsory'):
            actual = values(data, model_for(data, variant=variant))
            expected = [True, True, True, False, True] if variant == 'baseline' else (
                [True, True, False, False, False] if variant == 'compulsory' else
                [False, False, False, False, False] if variant in ('ban', 'permission_alias') else [True, False, False, False, False])
            if actual != expected: raise ValueError('Pursuit reference contrast: ' + repr((source, variant, actual)))
            results[variant] = actual
        # Actual work and the opportunity to work are independently expressible.
        actual = values(data, model_for(data, (False, False, False, True), actual=True))
        if actual != [False, False, False, True, False]: raise ValueError('Actual effort inferred permission')
        results['actual_without_opportunity'] = actual
        rows.append(results); print('Pursuit contrasts passed:', 'source' if source else 'generic', flush=True)
    return dict(grid=grid, document_checks=rows, unknown_goal_not_evaluated=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Free pursuit artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Free pursuit roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0014')
    phrase = 'daß jetzt ihnen doch das Feld geöffnet wird, sich dahin frei zu bearbeiten'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_free_pursuit.py', 'scripts/check_free_pursuit.py', 'scripts/check_topical_enablement.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_described_appraisals.py',
        'scripts/check_rod_setup.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_permission_and_opportunity_for_self_development', documents=documents, sizes=sizes,
        interpretation=checks(texts), parent_preserved=True, roundtrips=True, new_definitions=10, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase,
            definitions=['rlt', 'rlu', 'rlv', 'rlw', 'rlx', 'hzey', 'hzez', 'hze2', 'hze3', 'hze4'])]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Free pursuit report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Permission, available self-development, actual effort and goals separated')


if __name__ == '__main__': main()
