"""Verify fallible diagnostic signs and their concrete two-clause target."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, FunctionValue, SequenceValue
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_described_appraisals import candidate
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts import check_declining_hindrances as decline
from scripts.check_free_pursuit import EXTRA as WORK_EXTRA, CAPACITY_EXTRA, CAPACITY_REFS
from scripts.compose_free_pursuit import CAPACITY
from scripts.compose_limits import call as k
from scripts.compose_clear_indications import ROOT, PARENT, BUILDERS, INDICATIONS, RECOGNIZED, SOURCE

REPORT = ROOT / 'reports/clear-indications-v1.json'
ITEMS = ('signone', 'signtwo')
DOMAIN = ('observer', *ITEMS)
SCENES = ('actual', 'positiveone', 'positivetwo', 'negativeone', 'negativetwo')
EXTRA = '''r jppoints[] j[d].r jpscope[d] c.r jpweight[d] b.r jpthreshold[] b.
r jpclassifications[a d] c.r jpcontents[a] e.r jplinked[a i[e] d] c.r jpaccessible[a a d] c.
r jprecognized[a i[e] d] c.r jpobserver[] a.r jpcontext[] d.r jptarget[] e.'''
REFS = {n: 'k jp' + n + '[]' for n in ('points', 'threshold', 'observer', 'context')}
REFS.update({n: 'p jp' + n for n in ('scope', 'weight', 'classifications', 'contents', 'linked', 'accessible', 'recognized')})


def finish(base, target, source=False, **extra):
    refs = {**REFS, 'target': 'r[' + target + ']'}
    queries = [k(name, *(refs[n] for n, _ in fields)) for name, fields in (
        ('rmd', INDICATIONS), ('rme', INDICATIONS), ('rmf', RECOGNIZED), ('rmg', INDICATIONS))]
    queries.append('t[' + target + '][k jpcontext[]]')
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + expr + '].' for expr in queries))
    return dict(document=doc, target=target, target_syntax=syntax(description(base, target)), source=source, **extra)


def setup(text): return finish(candidate(text, EXTRA), 'k jptarget[]')


def source_setup(text):
    base = candidate(text, EXTRA + WORK_EXTRA + CAPACITY_EXTRA + decline.EXTRA)
    goal = k('hzey', *(CAPACITY_REFS[n] for n, _ in CAPACITY))
    work = k('hzez', 'r[' + goal + ']', 'p jmaims')
    specialized = specialize_definition(base, 'hzfa', 'jpcombined',
        {next(i for i, (name, _) in enumerate(SOURCE) if name == 'execution'): description(base, work)})
    refs = {**decline.REFS, 'authority': 'k jmsource[]', 'roles': 'p jmroles'}
    target = k('jpcombined', *(refs[n] for n, _ in SOURCE if n != 'execution'))
    return finish(specialized.document, target, True, goal_syntax=syntax(description(base, goal)),
        work_syntax=syntax(description(base, work)), disquotations_removed=specialized.disquotations_removed)


def evidence_model(data, scenes, hypothesis, signal, observer='observer', context=None, variant='baseline', threshold=2, weight=1):
    model = guarded(data['document']); model.update({n: f for n, f in arithmetic().items() if n in model})
    context = scenes[0] if context is None else context
    def access(owner, item, point):
        return owner == observer and item in (ITEMS[:1] if variant == 'single' else ITEMS) and point == context
    model.update(jppoints=lambda: SequenceValue(scenes, '"situation"'), jpscope=lambda point: point in scenes,
        jpweight=lambda point: Fraction(weight), jpthreshold=lambda: Fraction(threshold), jpclassifications=lambda item, point: True,
        jpcontents=lambda item: Content(scenes, tuple(bool(flag and item in ITEMS) for flag in signal)),
        jplinked=lambda item, target, point: item in ITEMS and target.syntax == data['target_syntax'] and point == context and variant != 'wrong_target',
        jpaccessible=access, jprecognized=lambda owner, target, point: owner == observer and target.syntax == data['target_syntax'] and point == context and variant != 'unrecognized',
        jpobserver=lambda: observer, jpcontext=lambda: context,
        jptarget=lambda: Content(scenes, tuple(hypothesis)))
    return model


def generic_model(data, signal=(True, True, True, False, False), **kwargs):
    return evidence_model(data, SCENES, (False, True, True, False, False), signal, **kwargs)


SOURCE_SCENES = (*decline.SCENES, 'work')
SOURCE_DOMAIN = (*decline.DOMAIN, 'practice', *ITEMS)


def source_model(data, variant='baseline'):
    doc = data['document']; model = decline.source_model(doc)
    extra = evidence_model(data, SOURCE_SCENES, (False,) * len(SOURCE_SCENES),
        tuple(point in ('first', 'last') for point in SOURCE_SCENES), observer='person',
        context='last' if variant == 'true_target' else 'first', variant=variant)
    model.update({name: callback for name, callback in extra.items() if name.startswith('jp')})
    old_available, old_outcomes = model['ae'], model['af']
    model['ae'] = lambda person, plan, point: (person == 'person' and point in decline.TIMES and variant != 'no_opportunity') if plan == 'practice' else old_available(person, plan, point)
    model['af'] = lambda person, plan, start, end: (person == 'person' and start in decline.TIMES and end == 'work') if plan == 'practice' else old_outcomes(person, plan, start, end)
    model.update(jmsource=lambda: 'guide', jmroles=lambda person: 'faculty',
        h7a=lambda *args: False,
        h7b=lambda source, person, role, act, desc, sign, point: (source, person, role, act) == ('guide', 'person', 'faculty', 'practice') and desc.syntax == data['work_syntax'] and point in decline.TIMES,
        dg=lambda act, point: (act, point) == ('practice', 'work'),
        df=lambda person, act, point: (person, act, point) == ('person', 'practice', 'work'),
        h4m=lambda part, person, point: (part, person, point) == ('faculty', 'person', 'work'),
        h4n=lambda person, part, act, point: (person, part, act, point) == ('person', 'faculty', 'practice', 'work'),
        jmaims=lambda person, act, goal, bindings, point: (person, act, point) == ('person', 'practice', 'work') and goal.syntax == data['goal_syntax'] and bindings.items == ('person',))
    if variant == 'no_decline':
        model['jnequations'] = lambda obstacle, point: FunctionValue(('individual', decline.STATE_SORT), 'truth',
            lambda variable, state: False if variable == obstacle else not state(obstacle))
    return model


def values(data, model, statistics=None):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model,
        individuals=SOURCE_DOMAIN if data['source'] else DOMAIN, situations=SOURCE_SCENES if data['source'] else SCENES,
        max_steps=32_000_000, statistics=statistics)]


def checks(texts):
    generic = setup(texts[0]); grid = []
    for signal in product((False, True), repeat=5):
        positive = sum(signal[1:3]); negative = int(signal[0]) + sum(signal[3:])
        strong = 3 * positive > 2 * negative * 2
        indication = signal[0] and strong
        expected = [indication, indication, indication, False, False]
        actual = values(generic, generic_model(generic, signal))
        if actual != expected: raise ValueError('Diagnostic sign mismatch: ' + repr((signal, actual)))
        grid.append(dict(signal=list(signal), result=actual))
    print('32 diagnostic profiles passed', flush=True)
    rows = []
    for text in texts[1:]:
        data = source_setup(text); cases = {}
        for variant, expected in (
            ('baseline', [True, True, True, False, False]), ('true_target', [True] * 5),
            ('no_opportunity', [False] * 5), ('no_decline', [False] * 5),
            ('single', [True, False, False, False, False]), ('unrecognized', [True, True, False, False, False]),
            ('wrong_target', [False] * 5)):
            stats = {}; actual = values(data, source_model(data, variant), stats)
            if actual != expected: raise ValueError('Concrete indication target mismatch: ' + repr((variant, actual)))
            cases[variant] = dict(result=actual, steps=stats['steps'])
            print('Two-clause indication:', variant, 'passed', flush=True)
        rows.append(dict(cases=cases, disquotations_removed=data['disquotations_removed']))
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Clear indication artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Clear indication roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0014')
    phrase = 'davon haben wir doch deutliche Anzeigen'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_clear_indications.py', 'scripts/check_clear_indications.py', 'scripts/check_declining_hindrances.py',
        'scripts/check_free_pursuit.py', 'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py',
        'scripts/check_scoped_counts.py', 'scripts/check_described_appraisals.py', 'scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_model_relative_clear_indications_of_opportunity_and_decline', documents=documents, sizes=sizes,
        interpretation=checks(texts), parent_preserved=True, roundtrips=True, new_definitions=7, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase,
            definitions=['rmb', 'rmc', 'rmd', 'rme', 'rmf', 'rmg', 'hzfa'])]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Clear indications report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Fallible signs, reference identity and concrete combined target checked')


if __name__ == '__main__': main()
