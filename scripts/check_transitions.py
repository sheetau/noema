"""Check process-bound state transitions and reject merely earlier states."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.compose_transitions import ROOT, generic_composed, source_composed
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/transitions-v1.json'


def generic_checks():
    doc = parse(generic_composed()[0] + '''
r za[d] c.r zb[d d] c.r zc[a d d] c.r zd[] a.r ze[] d.r zf[] d.r zg[] e.
q[k tg[p za p zb k zd[] k ze[] k zf[] p zc]].
q[k th[p za p zb k zd[] k ze[] k zf[] p zc k zg[]]].
''')
    scenes = ('before', 'after', 'outside')
    def run(pre=False, post=True, process=True, variant='baseline'):
        start = 'after' if variant == 'reverse' else 'before'
        end = 'before' if variant == 'same_point' else 'outside' if variant == 'outside' else 'after'
        model = {'za': lambda point: point in scenes[:2],
            'zb': lambda a, b: (a, b) == ('before', 'after') or (variant == 'cycle' and (a, b) == ('after', 'before')),
            'zc': lambda event, a, b: process and (event, a, b) == ('other' if variant == 'wrong_process' else 'event', 'before', 'after'),
            'zd': lambda: 'event', 'ze': lambda: start, 'zf': lambda: end,
            'zg': lambda: Content(scenes, (pre, post, False))}
        return [r['value'] for r in evaluate_document(doc, individuals=('event', 'other'), situations=scenes, primitives=model)]
    rows = []
    for pre, post, process in product((False, True), repeat=3):
        actual = run(pre, post, process)
        if actual != [process, process and not pre and post]:
            raise ValueError('Transition truth table differs')
        rows.append({'before': pre, 'after': post, 'process_exists': process, 'linked': actual[0], 'became_true': actual[1]})
    invalid = {}
    for variant in ('reverse', 'same_point', 'outside', 'cycle', 'wrong_process'):
        actual = run(variant=variant)
        if actual != [False, False]:
            raise ValueError('Invalid transition accepted: ' + variant)
        invalid[variant] = actual
    return {'truth_cases': rows, 'invalid_bindings': invalid}


def source_candidate(mode='witness'):
    doc = parse(source_composed()[0])
    doc['statements'] = []
    # Keep the old prior-state condition in this diagnostic only.
    old = parse((ROOT / 'examples/v014/kant-prior-concession.noema').read_text(encoding='utf-8'))
    legacy = deepcopy(next(d for d in old['declarations'] if d['name'] == 'kf'))
    legacy['name'] = 'lo'
    doc['declarations'].append(legacy)
    text = format_graph(doc, 'compact') + '\nr za[] a.r zb[] a.r zc[] d.r zd[] d.r ze[] d.r zf[] j[a].\n'
    if mode == 'witness':
        text += 'q[k km[k za[] k zb[] k zc[] k zd[] k ze[]]].q[t[k kc[k za[]]][k zd[]]].'
    elif mode == 'prior':
        text += 'q[t[k kf[k za[]]][k ze[]]].q[t[k lo[k za[]]][k ze[]]].'
    else:
        text += 'q[k ki[k zf[] n p b b k ze[]]].'
    return parse(text)


def source_values(doc, variant='baseline'):
    scenes = ('child', 'adult', 'text', 'expected')
    domain = ('change', 'reader', 'guide', 'faculty')
    def history(person, context, point):
        return person == 'reader' and context in ('text', 'expected') and point in ('child', 'adult', context)
    def dependency(person, other, point):
        if variant == 'no_prior_dependence':
            return False
        expected_person = 'guide' if variant == 'other_person_dependent' else 'reader'
        expected_guide = 'reader' if variant == 'self_guidance_only' else 'guide'
        return person == expected_person and other == expected_guide and (point == 'child' or (variant == 'still_dependent' and point == 'adult'))
    model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update({
        'aa': lambda p: p == 'reader',
        'ab': lambda faculty, person, scene: (faculty, person) == ('faculty', 'reader'),
        'ac': lambda person, faculty, act, scene: (person, faculty, act) == ('reader', 'faculty', 'change'),
        'ae': lambda person, plan, scene: (person, plan) == ('reader', 'change') and scene != 'text',
        'af': lambda person, plan, start, end: (person, plan) == ('reader', 'change') and start == end,
        'ap': lambda person, plan, start, end: (person, plan) == ('reader', 'change') and start == end,
        'ag': lambda process, start, end: variant != 'no_process' and (process, start, end) == (
            'guide' if variant == 'wrong_process' else 'change', 'child', 'adult'),
        'la': lambda person, process, start, end: variant != 'no_affected_subject' and (person, process, start, end) == (
            'guide' if variant == 'wrong_affected_subject' else 'reader', 'change', 'child', 'adult'),
        'ha': lambda a, b: a+b, 'hb': lambda a, b: a*b, 'hc': lambda a, b: a<b, 'hd': lambda b: Fraction(int(b)),
        'hr': lambda pop, context: pop.items == ('reader',) and context == 'text',
        'hs': lambda ratio, context: ratio >= Fraction(3, 5) and context == 'text',
        'ia': history,
        'ib': lambda person, context, point: person == 'reader' and context in ('text', 'expected') and point == context,
        'ic': lambda a, b, context: scenes.index(a) < scenes.index(b),
        'id': lambda person, desc, point: person == 'reader' and symbol(desc) == 'bf' and point == 'text',
        'ka': lambda person, point: person == 'reader' and point != 'child' and variant != 'not_mature_after',
        'kb': dependency, 'kd': lambda a, b, context: variant != 'not_long_ago',
        'ke': lambda judge, person, desc, context, alternative: (judge, person, symbol(desc), context, alternative) ==
              ('guide', 'reader', 'kf', 'text', 'expected'),
        'wa': lambda: 'guide', 'za': lambda: 'reader', 'zb': lambda: 'change',
        'zc': lambda: 'child', 'zd': lambda: 'adult', 'ze': lambda: 'text',
        'zf': lambda: SequenceValue(('reader',), '"individual"')})
    if variant == 'outside_history':
        model['ia'] = lambda person, context, point: history(person, context, point) and point != 'child'
    return [r['value'] for r in evaluate_document(doc, individuals=domain, situations=scenes,
        primitives=model, max_steps=100000000)]


def source_checks():
    doc = source_candidate()
    variants = ('baseline', 'no_process', 'wrong_process', 'no_affected_subject', 'wrong_affected_subject',
        'no_prior_dependence', 'other_person_dependent', 'self_guidance_only', 'still_dependent',
        'not_mature_after', 'not_long_ago', 'outside_history')
    rows = {}
    for variant in variants:
        actual = source_values(doc, variant)
        expected = [variant == 'baseline', variant not in ('still_dependent', 'not_mature_after')]
        if actual != expected:
            raise ValueError('Release witness differs: ' + variant)
        rows[variant] = {'transition': actual[0], 'later_state': actual[1]}
    comparisons = {}
    prior = source_candidate('prior')
    for variant in ('baseline', 'no_process', 'no_prior_dependence'):
        actual = source_values(prior, variant)
        if actual != [variant == 'baseline', True]:
            raise ValueError('State-only comparison differs: ' + variant)
        comparisons[variant] = {'new_transition_prior': actual[0], 'old_state_only_prior': actual[1]}
    integrated = source_values(source_candidate('population'))
    if integrated != [True]:
        raise ValueError('Transition prior disconnected from concession and population')
    return {'witnesses': rows, 'old_vs_new': comparisons, 'population_and_concession_baseline': True}


def source_alignment():
    units = json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
    unit = next(u for u in units if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Kant source differs')
    phrase = 'nachdem sie die Natur längst von fremder Leitung frei gesprochen (naturaliter majorennes)'
    if unit['text'].count(phrase) != 1:
        raise ValueError('Release clause missing or ambiguous')
    start = unit['text'].index(phrase)
    return {'unit': unit['id'], 'unit_sha256': digest, 'start': start, 'end': start+len(phrase), 'source': phrase,
        'definitions': ['kl', 'km', 'kf'], 'status': 'transition_reading_partial_source_clause',
        'previous_dependence_is_an_explicit_reading': True,
        'remaining': ['natural maturation mechanism', 'personification and declaration metaphor', 'independent Latin reading',
            'causes', 'guardians clause', 'rest of paragraph', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored transitions differ')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Transition roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/transitions-basis-v1.json', 'data/kant-release-transition-basis-v1.json',
        'examples/v014/kant-prior-concession.noema', 'data/kant-prior-concession-basis-v1.json',
        'scripts/compose_transitions.py', 'scripts/check_transitions.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'process_and_affected_subject_partial_source_connection', 'documents': documents,
        'generic': generic_checks(), 'source': source_checks(), 'alignment': source_alignment(), 'roundtrips': True,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Transition report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('8 transition states, 5 invalid bindings, 12 source witnesses and 3 old/new comparisons checked')


if __name__ == '__main__':
    main()
