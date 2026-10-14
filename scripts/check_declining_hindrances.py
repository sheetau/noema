"""Test fixed-catalogue declines and intervention-grounded capability obstacles."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import FunctionValue, SequenceValue
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_scoped_counts import arithmetic
from scripts.compose_limits import call as k
from scripts.compose_declining_hindrances import ROOT, PARENT, BUILDERS, CHECKED, DECLINE, GRADUAL, SOURCE, SOURCE_CAUSAL

REPORT = ROOT / 'reports/declining-hindrances-v1.json'
OBSTACLES = ('one', 'two', 'three')
TIMES = ('first', 'second', 'third', 'last')
SCENES = (*TIMES, 'high', 'low')
DOMAIN = (*OBSTACLES, 'y', 'person', 'faculty', 'plan', 'act', 'guide')
STATE_SORT = {'kind': 'function', 'parameters': ['individual'], 'result': 'truth'}
EXTRA = '''r jnhistory[d] c.r jnbefore[d d] c.r jnstart[] d.r jnend[] d.r jnobstacles[] j[a].
r jnscope[a] c.r jnassessed[a d] c.r jnhindering[a d] c.r jnbound[] b.
r jnvariables[a] j[a].r jnequations[a d] h[a h[a] c] c.r jnfactors[a] a.
r jnworlds[a d h[a] c] d.r jnpopulation[] j[a].r jnpeople[a] c.r jnexpected[d] b.'''
REFS = {n: 'k jn' + n + '[]' for n in ('start', 'end', 'obstacles', 'bound', 'population')}
REFS.update({n: 'p jn' + n for n in ('history', 'before', 'scope', 'assessed', 'hindering', 'variables', 'equations', 'factors', 'worlds', 'people')})


def setup(text, source=False):
    refs = dict(REFS)
    if source:
        refs['assessed'] = k('hze5', *(refs[n] for n, _ in SOURCE_CAUSAL))
        refs['hindering'] = k('hze6', *(refs[n] for n, _ in SOURCE_CAUSAL))
    expressions = [k(name, *(refs[n] for n, _ in fields)) for name, fields in (
        ('rl2', CHECKED), ('rl3', DECLINE), ('hze7' if source else 'rl4', SOURCE if source else GRADUAL), ('rl6', GRADUAL))]
    counts = 'f point d[y[k jnhistory[v point]][e[' + k('rly', refs['obstacles'], refs['hindering'], 'v point') + '][k jnexpected[v point]]]]'
    return candidate(text, EXTRA + ''.join('q[' + expr + '].' for expr in (*expressions, counts)))


def generic_model(doc, profile=(3, 3, 2, 1), variant='baseline', bound=1, membership=None):
    model = guarded(doc); model.update({n: f for n, f in arithmetic().items() if n in model})
    def hindering(obstacle, point):
        if obstacle not in OBSTACLES or point not in TIMES: return False
        return obstacle in membership[TIMES.index(point)] if membership is not None else OBSTACLES.index(obstacle) < profile[TIMES.index(point)]
    def before(first, last):
        ordered = first in TIMES and last in TIMES and TIMES.index(first) < TIMES.index(last)
        return ordered or variant == 'cycle' and (first, last) == ('last', 'first')
    population = ('one', 'two') if variant == 'omitted' else ('one', 'one', 'two', 'three') if variant == 'duplicate' else OBSTACLES
    expected = lambda point: Fraction(sum(hindering(o, point) for o in population))
    model.update(jnhistory=lambda point: point in TIMES, jnbefore=before,
        jnstart=lambda: 'first', jnend=lambda: 'last', jnobstacles=lambda: SequenceValue(population, '"individual"'),
        jnscope=lambda obstacle: obstacle in OBSTACLES,
        jnassessed=lambda obstacle, point: not (variant == 'unassessed' and obstacle == 'two' and point == 'third'),
        jnhindering=hindering, jnbound=lambda: Fraction(bound), jnexpected=expected)
    return model


def source_model(doc, variant='baseline'):
    model = generic_model(doc)
    profile = (3, 3, 2, 1)
    def active(obstacle, point):
        return obstacle in OBSTACLES and point in TIMES and OBSTACLES.index(obstacle) < profile[TIMES.index(point)]
    def equations(obstacle, point):
        def equation(variable, state):
            if variable == obstacle: return False
            if variant == 'no_solution' and point == 'third': return not state('y')
            return not state(obstacle) if active(obstacle, point) else True
        return FunctionValue(('individual', STATE_SORT), 'truth', equation)
    def available(person, plan, point): return person == 'person' and plan == 'plan'
    def outcomes(person, plan, start, end): return available(person, plan, start) and start == end
    def selected(person, plan, start, end):
        return outcomes(person, plan, start, end) and not (variant == 'unassessed' and start == 'low')
    raw_counts = (0, 0, 0, 0) if variant in ('wrong_worlds', 'guided') else (3, 3, 0, 1) if variant == 'no_solution' else profile
    model.update(jnvariables=lambda obstacle: SequenceValue((obstacle, 'y') if obstacle != 'y' else ('y',), '"individual"'),
        jnequations=equations, jnfactors=lambda obstacle: obstacle,
        jnworlds=lambda obstacle, point, state: 'high' if variant == 'wrong_worlds' or state('y') else 'low',
        jnpopulation=lambda: SequenceValue(('person', 'person') if variant == 'duplicate_people' else ('person',), '"individual"'),
        jnpeople=lambda person: person == 'person', jnexpected=lambda point: Fraction(raw_counts[TIMES.index(point)] if point in TIMES else 0),
        aa=lambda person: person == 'person', ae=available, af=outcomes, ap=selected,
        ab=lambda faculty, person, point: (faculty, person) == ('faculty', 'person'),
        ac=lambda person, faculty, act, point: (person, faculty, act, point) == ('person', 'faculty', 'act', 'high'),
        ad=lambda other, person, act, point: variant == 'guided' and (other, person, act, point) == ('guide', 'person', 'act', 'high'))
    return model


def values(doc, model, source=False):
    return [row['value'] for row in evaluate_document(doc, primitives=model, individuals=DOMAIN if source else OBSTACLES,
        situations=SCENES if source else TIMES, max_steps=12_000_000)]


def checks(texts):
    doc = setup(texts[0]); cases = []
    for profile in product(range(4), repeat=4):
        decreases = profile[-1] < profile[0] and all(a >= b for a, b in zip(profile, profile[1:]))
        gradual = decreases and all(a - b <= 1 for a, b in zip(profile, profile[1:])) and any(profile[-1] < n < profile[0] for n in profile[1:-1])
        expected = [True, decreases, gradual, gradual, True]
        actual = values(doc, generic_model(doc, profile))
        if actual != expected: raise ValueError('Temporal decline differs: ' + repr((profile, actual)))
        cases.append(dict(profile=list(profile), result=actual))
    contrasts = {}
    for variant in ('unassessed', 'omitted', 'duplicate', 'cycle'):
        actual = values(doc, generic_model(doc, variant=variant))
        if actual != [False, False, False, False, True]: raise ValueError('Invalid assessment certified decline: ' + variant)
        contrasts[variant] = actual
    print('256 temporal profiles and assessment contrasts passed', flush=True)
    source_rows = []
    for text in texts[1:]:
        source_doc = setup(text, True); rows = {}
        for variant, expected in (
            ('baseline', [True, True, True, True, True]), ('unassessed', [False, False, False, False, True]),
            ('duplicate_people', [False, False, False, False, True]), ('no_solution', [False, False, False, False, True]),
            ('wrong_worlds', [True, False, False, False, True]), ('guided', [True, False, False, False, True])):
            actual = values(source_doc, source_model(source_doc, variant), True)
            if actual != expected: raise ValueError('Causal decline differs: ' + repr((variant, actual)))
            rows[variant] = actual; print('Intervention-grounded decline:', variant, 'passed', flush=True)
        source_rows.append(rows)
    return dict(profiles=cases, contrasts=contrasts, source=source_rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Declining hindrance artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Declining hindrance roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0014')
    phrase = 'die Hindernisse der allgemeinen Aufklärung, oder des Ausganges aus ihrer selbst verschuldeten Unmündigkeit, allmälig weniger werden'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_declining_hindrances.py', 'scripts/check_declining_hindrances.py',
        'scripts/check_scoped_counts.py', 'scripts/check_described_appraisals.py', 'scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_assessed_multistep_decline_of_potential_hindrances', documents=documents, sizes=sizes,
        interpretation=checks(texts), parent_preserved=True, roundtrips=True, new_definitions=12, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase,
            definitions=['rly', 'rlz', 'rl2', 'rl3', 'rl4', 'rl5', 'rl6', 'rl7', 'rma', 'hze5', 'hze6', 'hze7'])]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Declining hindrances report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Fixed temporal scope, gradual count decline and intervention assessments checked')


if __name__ == '__main__': main()
