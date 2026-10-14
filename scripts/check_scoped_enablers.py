"""Check scoped passive enablement and assessment of every possible result."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, SequenceValue
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.check_topical_enablement import EXTRA, REFS, DOMAIN as SOURCE_DOMAIN, SCENES as SOURCE_SCENES, model_for as old_model
from scripts.compose_limits import call as k, app, op
from scripts.compose_topical_enablement import CHECKED, CAPABLE, COLLECTIVE, SOURCE
from scripts.compose_scoped_enablers import ROOT, PARENT, BUILDERS, SCOPE_CHECK, SCOPE_POSSIBLE, SCOPED_SOURCE, GROUP_SOURCE

REPORT = ROOT / 'reports/scoped-enablers-v1.json'
PEOPLE = ('alice', 'bob')
ACTORS = ('teacher', 'mentor')
DOMAIN = (*PEOPLE, *ACTORS, 'matter', 'plan')
SCENES = ('now', 'ready', 'bad', 'done')
ADDED = 'r jleligible[a a] c.r jlagents[a a d] c.r jlgoals[a a] e.'
FIELDS = {**REFS, 'eligible': 'p jleligible', 'agents': 'p jlagents', 'goals': 'p jlgoals'}


def expressions(source=False):
    fields = [('hzeq', SOURCE), ('hzer', SOURCE), ('hzev', SCOPED_SOURCE), ('hzew', SCOPED_SOURCE)] if source else [
        ('rll', CHECKED), ('rlm', CAPABLE), ('rlr', SCOPE_CHECK), ('rls', SCOPE_POSSIBLE)]
    result = {}
    for field, (name, params) in zip(('assessed', 'capable', 'enableassessed', 'enableable'), fields, strict=True):
        if source:
            result[field] = k(name, *(FIELDS[n] for n, _ in params))
        else:
            refs = {**FIELDS, 'person': 'v person', 'context': 'v point'}
            result[field] = 'i[person a][b point[' + k(name, *(refs[n] for n, _ in params)) + ']]'
    return result


def setup(text, source=False):
    functions = expressions(source)
    queries = [op('t', app(function, 'k jkperson[]'), 'k jkcontext[]') for function in functions.values()]
    refs = {**FIELDS, **functions}
    group = k('hzex' if source else 'rlp', *(refs[n] for n, _ in (GROUP_SOURCE if source else COLLECTIVE)))
    return candidate(text, EXTRA + ADDED + ''.join('q[' + expr + '].' for expr in (*queries, group)))


def generic_model(doc, success=(True, False, False, True), eligible=ACTORS, variant='baseline', current=(False, False)):
    model = guarded(doc)
    model.update({n: fn for n, fn in arithmetic().items() if n in model})
    def member(actor, person):
        return actor in (eligible.get(person, ()) if isinstance(eligible, dict) else eligible) and person in PEOPLE
    def available(person, matter, plan, point):
        return person in PEOPLE and matter == 'matter' and plan == 'plan' and (
            point == 'ready' or point == 'now' and current[PEOPLE.index(person)])
    def outcomes(person, matter, plan, start, end):
        return available(person, matter, plan, start) and end == 'done'
    def selected(person, matter, plan, start, end):
        return outcomes(person, matter, plan, start, end) and not (
            variant == 'future_unassessed' and start == 'ready')
    def enabling(actor, person, plan, point):
        return actor in ACTORS and person in PEOPLE and plan == 'plan' and point == 'now' and not (
            variant == 'no_methods' or variant == 'teacher_absent' and actor == 'teacher')
    def effects(actor, person, plan, start, end):
        if not enabling(actor, person, plan, start): return False
        if variant == 'teacher_no_effects' and actor == 'teacher': return False
        index = ACTORS.index(actor) * 2 + PEOPLE.index(person)
        return end == ('ready' if success[index] else 'bad')
    model.update(jkperson=lambda: 'alice', jkcontext=lambda: 'now', jktopic=lambda: 'faith', jkanchor=lambda: 'now',
        jkenabler=lambda: 'teacher', jkpopulation=lambda: SequenceValue(PEOPLE, '"individual"'),
        jkscope=lambda person: person in PEOPLE, jkcurrentupper=lambda: Fraction(2), jkenableupper=lambda: Fraction(2),
        jkrelevant=lambda person, matter: person in PEOPLE and matter == 'matter', jkavailable=available,
        jkoutcomes=outcomes, jkselected=selected, jkenabling=enabling, jkeffects=effects,
        jleligible=member, jlagents=lambda actor, person, anchor: anchor == 'now' and member(actor, person),
        jlgoals=lambda person, matter: Content(SCENES, tuple(person in PEOPLE and matter == 'matter' and point == 'done' for point in SCENES)))
    return model


def source_model(doc, scenario='baseline'):
    model = old_model(doc, (False, False, True, True))
    def agents(actor, person, anchor):
        scope = ('teacher',) if scenario == 'teacher_only' else ACTORS
        return actor in scope and person in PEOPLE and anchor == 'now'
    def enabling(actor, person, plan, point):
        return actor in ACTORS and person in PEOPLE and plan == 'plan' and point == 'now'
    def effects(actor, person, plan, start, end):
        if not enabling(actor, person, plan, start): return False
        if scenario == 'teacher_no_effects' and actor == 'teacher': return False
        return end == ('trained' if actor == 'mentor' else 'failed')
    model.update(jlagents=agents, jleligible=lambda actor, person: agents(actor, person, 'now'),
        jkenabling=enabling, jkeffects=effects,
        jlgoals=lambda person, matter: Content(SOURCE_SCENES, tuple(False for _ in SOURCE_SCENES)))
    if scenario == 'future_unassessed':
        original = model['jkselected']
        model['jkselected'] = lambda person, matter, plan, start, end: start != 'trained' and original(person, matter, plan, start, end)
    if scenario == 'guided':
        model['ad'] = model['jkguidance'] = lambda other, person, act, point: other == 'teacher' and person in PEOPLE and point == 'judged'
    return model


def values(doc, model, source=False, statistics=None):
    rows = evaluate_document(doc, primitives=model, individuals=(*SOURCE_DOMAIN, 'mentor') if source else DOMAIN,
        situations=SOURCE_SCENES if source else SCENES, max_steps=16_000_000, statistics=statistics)
    return [row['value'] for row in rows]


def generic_checks(text):
    doc = setup(text); rows = []
    for success in product((False, True), repeat=4):
        possible = [success[0] or success[2], success[1] or success[3]]
        expected = [True, False, True, possible[0], not all(possible)]
        actual = values(doc, generic_model(doc, success))
        if actual != expected: raise ValueError('Scoped existential mismatch: ' + repr((success, actual)))
        rows.append(dict(success=list(success), result=actual))
    contrasts = []
    for eligible, variant, expected in (
        (('teacher',), 'baseline', [True, False, True, True, True]),
        (('mentor',), 'baseline', [True, False, True, False, True]),
        ((), 'baseline', [True, False, True, False, True]),
        (ACTORS, 'no_methods', [True, False, True, False, True]),
        (ACTORS, 'teacher_absent', [True, False, True, False, True]),
        (ACTORS, 'teacher_no_effects', [True, False, False, False, False]),
        (ACTORS, 'future_unassessed', [True, False, False, False, False]),
        ({'alice': ('mentor',), 'bob': ('teacher',)}, 'baseline', [True, False, True, False, True]),
    ):
        actual = values(doc, generic_model(doc, eligible=eligible, variant=variant))
        if actual != expected: raise ValueError('Scoped contrast mismatch: ' + repr((eligible, variant, actual)))
        contrasts.append(dict(eligible=eligible, variant=variant, result=actual))
    # A known successful actor remains a witness even if another actor lacks an effect assessment.
    actual = values(doc, generic_model(doc, (False, False, True, True), variant='teacher_no_effects'))
    if actual != [True, False, False, True, False]: raise ValueError('Known witness conflated with total assessment')
    print('Generic actor grid and assessment contrasts passed', flush=True)
    return dict(cases=rows, contrasts=contrasts, known_witness_with_incomplete_scope=actual)


def source_checks(texts):
    rows = []
    expected = {'baseline': [True, False, True, True, False], 'teacher_only': [True, False, True, False, True],
        'teacher_no_effects': [True, False, False, True, False], 'future_unassessed': [True, False, False, False, False],
        'guided': [True, False, True, False, True]}
    for text in texts:
        doc = setup(text, True); cases = {}
        for scenario, answer in expected.items():
            stats = {}; actual = values(doc, source_model(doc, scenario), True, stats)
            if actual != answer: raise ValueError('Source scope mismatch: ' + repr((scenario, actual)))
            cases[scenario] = dict(result=actual, steps=stats['steps'])
            print('Source scoped enablement:', scenario, 'passed', flush=True)
        # Quotation must not evaluate unknown abilities or unknown membership.
        base = setup(text, True); base['statements'] = []
        refs = {**FIELDS, 'context': 'v point'}
        body = 'b point[' + k('hzex', *(refs[n] for n, _ in GROUP_SOURCE)) + ']'
        quoted = parse(format_graph(base, 'compact') + 'q[e[r[' + body + ']][r[' + body + ']]].')
        quote_result = values(quoted, guarded(quoted), True)
        if quote_result != [True]: raise ValueError('Scoped quotation executed unknown inputs')
        rows.append(dict(cases=cases, quotation=quote_result))
    return rows


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Scoped enabler artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Scoped enabler roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    previous = json.loads((ROOT / 'reports/topical-enablement-v1.json').read_text(encoding='utf-8'))
    segment = {**previous['alignment']['segments'][0], 'definitions': ['rlq', 'rlr', 'rls', 'hzev', 'hzew', 'hzex']}
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_scoped_enablers.py', 'scripts/check_scoped_enablers.py', 'scripts/compose_topical_enablement.py',
        'scripts/check_topical_enablement.py', 'scripts/check_scoped_counts.py', 'scripts/check_described_appraisals.py',
        'scripts/check_rod_setup.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json', 'reports/topical-enablement-v1.json'}
    return dict(status='partial_scoped_passive_enablement', documents=documents, sizes=sizes,
        generic=generic_checks(texts[0]), source=source_checks(texts[1:]), parent_preserved=True, roundtrips=True,
        new_definitions=6, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[segment]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Scoped enablers report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Scoped actors, future assessments and source connections checked')


if __name__ == '__main__': main()
