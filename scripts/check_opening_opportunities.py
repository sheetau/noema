"""Verify opportunity gains, retained alternatives and actual change witnesses."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, FunctionValue
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_described_appraisals import candidate
from scripts.check_assessed_payments import description
from scripts.check_rod_setup import guarded
from scripts import check_enlightening_epoch as epoch
from scripts.compose_limits import call as k
from scripts.compose_opening_opportunities import ROOT, PARENT, BUILDERS, FRAME, FAMILY, PROCESS, SOURCE, SOURCE_PROCESS, COMBINED, MEANINGS

REPORT = ROOT / 'reports/opening-opportunities-v1.json'
PEOPLE = ('alice', 'bob')
DOMAIN = (*PEOPLE, 'plan', 'other', 'opening', 'unrelated')
SCENES = ('before', 'middle', 'now')
EXTRA = '''r jrhistory[d] c.r jrbefore[d d] c.r jrstart[] d.r jrend[] d.
r jrpeople[a] c.r jractivities[a a] c.r jrassessed[a a d] c.r jropportunities[a a] e.
r jrprocesses[a a] a.r jrtransitions[a d d] c.r jraffected[a a d d] c.r jroccurs[a d] c.'''
REFS = {n: 'k jr' + n + '[]' for n in ('start', 'end')}
REFS.update({n: 'p jr' + n for n in ('history', 'before', 'people', 'activities', 'assessed', 'opportunities', 'processes', 'transitions', 'affected', 'occurs')})
SOURCE_DOMAIN = (*epoch.SOURCE_DOMAIN, 'opening')


def setup(text):
    queries = [k(name, *(REFS[n] for n, _ in fields)) for name, fields in (
        ('rmo', FRAME), ('rmq', FAMILY), ('rmr', FAMILY), ('rms', FAMILY), ('rmt', PROCESS))]
    return dict(document=candidate(text, EXTRA + ''.join('q[' + q + '].' for q in queries)), source=False)


def generic_model(data, bits=(False, True, False, True), variant='baseline'):
    model = guarded(data['document'])
    def opportunities(person, activity):
        index = PEOPLE.index(person) * 2 if person in PEOPLE else 0
        a, b = bits[index:index + 2]
        return Content(SCENES, (a, a, b) if person in PEOPLE and activity == 'plan' else (False,) * 3)
    model.update(jrhistory=lambda point: point in SCENES,
        jrbefore=lambda a, b: SCENES.index(a) < SCENES.index(b), jrstart=lambda: 'before', jrend=lambda: 'now',
        jrpeople=lambda person: person in PEOPLE and variant != 'empty_people',
        jractivities=lambda person, activity: person in PEOPLE and activity == 'plan' and variant != 'empty_activities',
        jrassessed=lambda person, activity, point: not (variant == 'unassessed' and person == 'alice' and point == 'before'),
        jropportunities=opportunities, jrprocesses=lambda person, activity: 'opening',
        jrtransitions=lambda process, a, b: (process, a, b) == ('opening', 'before', 'now') and variant != 'no_process',
        jraffected=lambda person, process, a, b: person in PEOPLE and (process, a, b) == ('opening', 'before', 'now') and variant != 'wrong_person',
        jroccurs=lambda process, point: (process, point) == ('opening', 'now') and variant != 'ended')
    return model


def source_setup(text):
    old = epoch.source_setup(text); base = old['document']; base['statements'] = []
    base = parse(format_graph(base, 'compact') + EXTRA)
    signs = epoch.indications
    goal = k('hzey', *(signs.CAPACITY_REFS[n] for n, _ in signs.CAPACITY))
    work = k('hzez', 'r[' + goal + ']', 'p jmaims')
    refs = {**signs.decline.REFS, 'end': 'k jqcontext[]', 'authority': 'k jmsource[]', 'roles': 'p jmroles',
        'execution': 'r[' + work + ']', 'activities': 'p jractivities', 'assessed': 'p jrassessed', 'processes': 'p jrprocesses'}
    specialized = specialize_definition(base, 'hzfi', 'jropening', {
        next(i for i, (name, _) in enumerate(COMBINED) if name == 'execution'): description(base, work)})
    base = specialized.document
    target = k('jropening', *(refs[n] for n, _ in COMBINED if n != 'execution'))
    context = 'k jqcontext[]'
    answer_refs = {**old['refs'], 'progress': target}
    answer = k('hzfc', *(answer_refs[n] for n, _ in epoch.SOURCE_ANSWER))
    group = k('hze4', refs['authority'], refs['people'], refs['roles'], refs['execution'], context)
    queries = [k('rmo', *(refs[n] for n, _ in FRAME)), k('hzfg', *(refs[n] for n, _ in SOURCE)),
        k('hzfh', *(refs[n] for n, _ in SOURCE_PROCESS)), group, 't[' + target + '][' + context + ']',
        't[' + answer + '][' + context + ']']
    # Evaluate actual practice separately from the opportunity and its opening.
    queries.append('t[c[s[' + refs['execution'] + ']][k jmperson[] k jmactivity[]]][' + context + ']')
    queries.append('t[k h4l[k jmperson[]]][' + context + ']')
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=True, old=old, target=target, answer=answer, question=old['question'],
        disquotations_removed=specialized.disquotations_removed)


def source_model(data, variant='baseline'):
    model = epoch.source_model(data['old']); old_allow = model['h7b']; old_occurs = model['dg']
    def permission(source, person, role, activity, desc, sign, point):
        available = point == 'first' if variant == 'lost' else point in ('first', 'last') if variant == 'stable' else point == 'last'
        return available and old_allow(source, person, role, activity, desc, sign, point)
    model.update({n: f for n, f in guarded(data['document']).items() if n not in model})
    model.update(h7b=permission, jmperson=lambda: 'person', jmactivity=lambda: 'practice',
        jractivities=lambda person, activity: (person, activity) == ('person', 'practice'),
        jrassessed=lambda person, activity, point: not (variant == 'unassessed' and point == 'first'),
        jrprocesses=lambda person, activity: 'opening',
        ag=lambda process, a, b: (process, a, b) == ('opening', 'first', 'last') and variant != 'no_process',
        la=lambda person, process, a, b: (person, process, a, b) == ('person', 'opening', 'first', 'last') and variant != 'wrong_person',
        dg=lambda activity, point: old_occurs(activity, point) or (activity, point) == ('opening', 'last') and variant != 'ended')
    if variant == 'no_decline':
        model['jnequations'] = lambda obstacle, point: FunctionValue(('individual', epoch.indications.decline.STATE_SORT), 'truth',
            lambda variable, state: False if variable == obstacle else not state(obstacle))
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model,
        individuals=SOURCE_DOMAIN if data['source'] else DOMAIN,
        situations=epoch.indications.SOURCE_SCENES if data['source'] else SCENES, max_steps=32_000_000)]


def checks(texts):
    generic = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=4):
        a, b, c, d = bits; gains = (not a and b, not c and d)
        retained = (not a or b) and (not c or d)
        expected = [True, all(gains), retained and any(gains), all(gains) and retained, all(gains)]
        actual = values(generic, generic_model(generic, bits))
        if actual != expected: raise ValueError('Opportunity gains collapsed: ' + repr((bits, actual)))
        grid.append(dict(bits=list(bits), result=actual))
    for variant in ('unassessed', 'empty_people', 'empty_activities'):
        if values(generic, generic_model(generic, variant=variant)) != [False] * 5:
            raise ValueError('Incomplete opportunity frame accepted')
    print('16 fixed-person endpoint profiles passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = source_setup(text); cases = {}
        for variant, expected in (
            ('baseline', [True, True, True, True, True, True, False, False]),
            ('stable', [True, False, False, True, False, False, False, False]),
            ('lost', [True, False, False, False, False, False, False, False]),
            ('unassessed', [False, False, False, True, False, False, False, False]),
            ('no_process', [True, True, False, True, False, False, False, False]),
            ('wrong_person', [True, True, False, True, False, False, False, False]),
            ('ended', [True, True, False, True, False, False, False, False]),
            ('no_decline', [True, True, True, True, False, False, False, False])):
            actual = values(data, source_model(data, variant))
            if actual != expected: raise ValueError('Opening process contrast failed: ' + repr((variant, actual)))
            cases[variant] = actual; print('Opportunity opening:', variant, 'passed', flush=True)
        quoted, question, answer = epoch.discourse_setup(data)
        for variant in ('baseline', 'wrong_answer', 'unrelated_response'):
            if values(quoted, epoch.discourse_model(quoted, question, answer, variant)) != [variant == 'baseline']:
                raise ValueError('Opening answer attribution changed')
        rows.append(dict(cases=cases, disquotations_removed=data['disquotations_removed'], quotation_checked=True))
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Opening opportunities artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Opening opportunities roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0014')
    phrase = 'daß jetzt ihnen doch das Feld geöffnet wird, sich dahin frei zu bearbeiten'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_opening_opportunities.py', 'scripts/check_opening_opportunities.py', 'scripts/check_enlightening_epoch.py',
        'scripts/check_clear_indications.py', 'scripts/check_declining_hindrances.py', 'scripts/check_free_pursuit.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_scoped_counts.py',
        'scripts/check_described_appraisals.py', 'scripts/check_rod_setup.py', 'noema/higher_order_semantics.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py', 'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_assessed_opportunity_onset_and_process', documents=documents, sizes=sizes,
        interpretation=checks(texts), parent_preserved=True, roundtrips=True, new_definitions=10, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Opening opportunities report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Opportunity onset, current opening process and unchanged ability separated')


if __name__ == '__main__': main()
