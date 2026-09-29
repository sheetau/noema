"""Check prior time and concessive expectations without asserting default truth."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.compose_concession import ROOT, generic_composed, source_composed
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/concession-v1.json'


def expectation_checks():
    doc = parse(generic_composed()[0] + '''
r za[] e.r zb[] e.r zc[a i[h[a] e] d d] c.r zd[] a.r ze[] d.
d zf[person a] e[k za[]].
q[k ja[k zd[] k za[] r[p zf] k zb[] k ze[] p zc]].
q[k jb[k zd[] k za[] r[p zf] k zb[] k ze[] p zc]].
''')
    scenes = ('actual', 'first', 'second')
    rows = []
    for premise, conclusion, chosen in product(product((False, True), repeat=3), product((False, True), repeat=3), product((False, True), repeat=2)):
        selected = {s for s, on in zip(scenes[1:], chosen) if on}
        model = {'za': lambda: Content(scenes, premise), 'zb': lambda: Content(scenes, conclusion),
            'zc': lambda person, desc, context, alt: (person, symbol(desc), context) == ('reader', 'zf', 'actual') and alt in selected,
            'zd': lambda: 'reader', 'ze': lambda: 'actual'}
        actual = [r['value'] for r in evaluate_document(doc, individuals=('reader',), situations=scenes, primitives=model)]
        expected = bool(selected) and all(premise[i] and not conclusion[i] for i, s in enumerate(scenes) if s in selected)
        if actual != [expected, premise[0] and conclusion[0] and expected]:
            raise ValueError('Concessive condition differs from explicit candidate evaluation')
        rows.append({'premise': list(premise), 'conclusion': list(conclusion), 'candidates': list(chosen),
            'contrary_expectation': actual[0], 'concession': actual[1]})
    # An actual true conclusion cannot also be a candidate where it is false.
    model['za'] = lambda: Content(scenes, (True, True, True))
    model['zb'] = lambda: Content(scenes, (True, False, False))
    model['zc'] = lambda person, desc, context, alt: alt == 'actual'
    actual = [r['value'] for r in evaluate_document(doc, individuals=('reader',), situations=scenes, primitives=model)]
    if actual != [False, False]:
        raise ValueError('Actual fact was forced into a contrary expectation')
    return {'cases': rows, 'actual_conclusion_cannot_be_contrary_candidate': True}


def prior_checks():
    doc = parse(generic_composed()[0] + '''
r za[d] c.r zb[d] c.r zc[d d] c.r zd[] d.r ze[d d] c.
q[k te[p za p zb p zc k zd[]]].q[k tf[p za p zb p zc k zd[] p ze]].
''')
    scenes = ('prior', 'start', 'end', 'outside')
    cases = (
        ('baseline', 'prior', ('start', 'end'), True, True, True),
        ('not_long_ago', 'prior', ('start', 'end'), False, True, False),
        ('at_start', 'start', ('start', 'end'), True, False, False),
        ('after_start', 'end', ('start', 'end'), True, False, False),
        ('outside_history', 'outside', ('start', 'end'), True, False, False),
        ('empty_scope', 'prior', (), True, False, False),
        ('gap_in_scope', 'prior', ('prior', 'end'), True, False, False),
    )
    rows = {}
    for name, point, scope, long_ago, ordered, expected in cases:
        model = {'za': lambda s: s in scenes[:3], 'zb': lambda s: s in scope,
            'zc': lambda a, b: scenes.index(a) < scenes.index(b), 'zd': lambda: point,
            'ze': lambda a, b: long_ago}
        actual = [r['value'] for r in evaluate_document(doc, individuals=('person',), situations=scenes, primitives=model)]
        if actual != [ordered, expected]:
            raise ValueError('Prior and elapsed distinction differs: ' + name)
        rows[name] = {'prior': actual[0], 'sufficiently_earlier': actual[1]}
    return rows


def source_candidate(population=False):
    doc = parse(source_composed()[0])
    doc['statements'] = []
    text = format_graph(doc, 'compact') + '\nr za[] a.r zb[] d.r zc[] j[a].\n'
    text += 'q[k ki[k zc[] n p b b k zb[]]].' if population else 'q[t[k kg[k za[]]][k zb[]]].'
    return parse(text)


def source_value(doc, variant):
    scenes = ('text', 'expected', 'prior', 'during', 'after')
    domain = ('reader', 'other', 'author', 'plan', 'faculty', 'act')
    model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    def history(person, context, point):
        return person == 'reader' and point in ({'prior', 'during'} if context == 'text' else {'prior', 'after'} if context == 'expected' else set())
    def scope(person, context, point):
        return person == 'reader' and (context, point) in {('text', 'during'), ('expected', 'after')}
    def order(a, b, context):
        if variant == 'release_later' and context == 'text':
            return (a, b) == ('during', 'prior')
        return a == 'prior' and b in ('during', 'after')
    model.update({
        'aa': lambda person: person == 'reader',
        'ab': lambda organ, person, scene: organ == 'faculty' and person == 'reader',
        'ac': lambda person, organ, act, scene: (person, organ, act) == ('reader', 'faculty', 'act'),
        'ae': lambda person, plan, scene: person == 'reader' and plan == 'plan' and scene != 'during',
        'af': lambda person, plan, start, end: person == 'reader' and plan == 'plan' and start == end,
        'ap': lambda person, plan, start, end: person == 'reader' and plan == 'plan' and start == end,
        'ha': lambda a, b: a+b, 'hb': lambda a, b: a*b, 'hc': lambda a, b: a<b, 'hd': lambda b: Fraction(int(b)),
        'hr': lambda pop, context: pop.items == ('reader',) and context == 'text',
        'hs': lambda ratio, context: ratio >= Fraction(3, 5) and context == 'text',
        'ia': history, 'ib': scope, 'ic': order,
        'id': lambda person, desc, point: person == 'reader' and symbol(desc) == 'bf' and point == 'during',
        'ka': lambda person, point: person == ('other' if variant == 'other_person_mature' else 'reader') and point == 'prior',
        'kb': lambda person, other, point: variant == 'still_developmentally_dependent' and (person, other, point) == ('reader', 'other', 'prior'),
        'kd': lambda a, b, context: variant != 'not_long_ago',
        'ke': lambda judge, person, desc, context, alt: variant != 'no_candidates' and
              (judge, person, symbol(desc), context, alt) == (
                  'other' if variant == 'wrong_perspective' else 'author',
                  'other' if variant == 'wrong_subject' else 'reader',
                  'kc' if variant == 'wrong_premise_description' else 'kf', 'text',
                  'text' if variant == 'actual_is_expected' else 'during' if variant == 'candidate_lacks_premise' else 'expected'),
        'wa': lambda: 'author', 'za': lambda: 'reader', 'zb': lambda: 'text',
        'zc': lambda: SequenceValue(('reader',), '"individual"')})
    if variant == 'no_actual_persistence':
        model['id'] = lambda *args: False
    result = evaluate_document(doc, individuals=domain, situations=scenes, primitives=model, max_steps=100000000)
    return result[0]['value']


def source_checks():
    doc = source_candidate()
    variants = ('baseline', 'other_person_mature', 'still_developmentally_dependent', 'release_later', 'not_long_ago',
        'no_candidates', 'wrong_perspective', 'wrong_subject', 'wrong_premise_description', 'actual_is_expected',
        'candidate_lacks_premise', 'no_actual_persistence')
    rows = {}
    for variant in variants:
        actual = source_value(doc, variant)
        if actual != (variant == 'baseline'):
            raise ValueError('Prior/concessive source binding differs: ' + variant)
        rows[variant] = actual
    population = source_candidate(population=True)
    integrated = {v: source_value(population, v) for v in ('baseline', 'still_developmentally_dependent')}
    if integrated != {'baseline': True, 'still_developmentally_dependent': False}:
        raise ValueError('Concession disconnected from population quantifier')
    return {'cases': rows, 'population_connection': integrated,
        'note': 'Singleton temporal scopes are finite binding tests, not a reconstruction of a real lifespan.'}


def source_alignment():
    units = json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
    unit = next(u for u in units if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Kant source changed')
    fragments = []
    for phrase, names in (('nachdem sie die Natur längst von fremder Leitung frei gesprochen (naturaliter majorennes)', ['kc', 'kf']),
                          ('dennoch gerne Zeitlebens unmündig bleiben', ['kg', 'ie'])):
        if unit['text'].count(phrase) != 1:
            raise ValueError('Source fragment missing or ambiguous')
        start = unit['text'].index(phrase)
        fragments.append({'start': start, 'end': start+len(phrase), 'source': phrase, 'definitions': names})
    return {'unit': unit['id'], 'unit_sha256': digest, 'fragments': fragments, 'status': 'partial_interpretive_clause',
        'developmental_maturity_is_not_actual_intellectual_independence': True,
        'remaining': ['developmental grounding', 'personification and declaration metaphor', 'independent Latin reading',
            'causes', 'guardians clause', 'rest of paragraph', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored concession document differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Concession roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/concession-basis-v1.json', 'data/kant-prior-concession-basis-v1.json',
        'examples/v014/kant-lifelong-state.noema', 'data/kant-lifelong-state-basis-v1.json',
        'scripts/compose_concession.py', 'scripts/check_concession.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'prior_conditions_and_concession_partial_source_connection', 'documents': documents,
        'expectations': expectation_checks(), 'prior': prior_checks(), 'source': source_checks(),
        'alignment': source_alignment(), 'roundtrips': True,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Concession report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('256 expectation combinations, 7 temporal contrasts, 12 source cases and 2 population bindings checked')


if __name__ == '__main__':
    main()
