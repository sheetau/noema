"""Countermodels for attributed danger, actual burden, and majority scope."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.check_described_explanations import symbol
from scripts.compose_described_appraisals import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/described-appraisals-v1.json'
PEOPLE = ('person', 'other', 'third', 'low', 'high', 'faculty', 'act', 'plan')
SCENES = ('actual', 'belief', 'alternative', 'loss')


def candidate(text, questions):
    doc = parse(text)
    doc['statements'] = []
    return parse(format_graph(doc, 'compact') + questions)


def values(doc, model, people=PEOPLE, scenes=SCENES):
    return [r['value'] for r in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=2_000_000, memoize_definitions=True)]


def generic_checks():
    doc = parse(generic_composed()[0] + '''
r za[] a.r zb[] d.r zc[a d] c.r zd[a d d] c.
d ze[person a] e[b scene[k zc[v person v scene]]].
q[k rn[k za[] p ze k zb[] p zd]].q[t[k ze[k za[]]][k zb[]]].
''')
    rows = []
    for first, second, first_value, second_value, actual in product((False, True), repeat=5):
        model = {'za': lambda: 'person', 'zb': lambda: 'actual',
            'zc': lambda person, scene: person == 'person' and {
                'actual': actual, 'belief': first_value, 'alternative': second_value, 'loss': False}[scene],
            'zd': lambda person, context, scene: (person, context) == ('person', 'actual') and (
                (first and scene == 'belief') or (second and scene == 'alternative'))}
        result = values(doc, model)
        expected = [(first or second) and (not first or first_value) and (not second or second_value), actual]
        if result != expected:
            raise ValueError('Non-factive judgment or empty-candidate semantics differs')
        rows.append({'candidates': [first, second], 'candidate_truths': [first_value, second_value],
                     'judgment': result[0], 'actual_truth': result[1]})
    return rows


def prospect_checks():
    doc = parse(generic_composed()[0] + '''
r za[] a.r zb[] d.r zc[a i[h[a] e] d d] c.r zd[a d] c.
r ze[a i[h[a] e] d] a.r zf[a d] c.
d zg[person a] e[b scene[e[v person][v person]]].
q[k rl[k za[] r[p zg] k zb[] p zc p zd]].
q[k rm[k za[] r[p zg] k zb[] p zc p zd p ze p zf]].
''')
    rows = {}
    for variant in ('baseline', 'wrong_person', 'wrong_activity', 'wrong_context', 'split_outcomes',
                    'wrong_adverse_person', 'empty_prospects', 'low_degree', 'wrong_degree_context',
                    'wrong_degree_activity', 'wrong_standard_context'):
        model = {
            'za': lambda: 'person', 'zb': lambda: 'actual',
            'zc': lambda person, description, context, outcome: variant != 'empty_prospects' and (
                person, symbol(description), context, outcome) == (
                'other' if variant == 'wrong_person' else 'person',
                'zh' if variant == 'wrong_activity' else 'zg',
                'belief' if variant == 'wrong_context' else 'actual', 'loss'),
            'zd': lambda person, outcome: (person, outcome) == (
                'other' if variant == 'wrong_adverse_person' else 'person',
                'alternative' if variant == 'split_outcomes' else 'loss'),
            'ze': lambda person, description, context: 'high' if variant != 'low_degree' and (
                person, symbol(description), context) == ('person',
                'zh' if variant == 'wrong_degree_activity' else 'zg',
                'belief' if variant == 'wrong_degree_context' else 'actual') else 'low',
            'zf': lambda level, context: (level, context) == ('high',
                'belief' if variant == 'wrong_standard_context' else 'actual')}
        result = values(doc, model)
        expected = [variant in ('baseline', 'low_degree', 'wrong_degree_context',
                                'wrong_degree_activity', 'wrong_standard_context'), variant == 'baseline']
        if result != expected:
            raise ValueError('Prospect, adversity and degree were mixed: ' + variant)
        rows[variant] = {'adverse_possibility': result[0], 'high_degree': result[1]}
    return rows


def source_model(doc, *, recognized=True, selected=True, actual_risk=False, believed_risk=True,
                 adverse=True, burden=True, human=True, mismatched='', judged_people=None):
    def forbidden(*args):
        raise ValueError('Appraisal evaluated an unrelated inherited primitive')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    people = {'person', 'other', 'third'}
    judged_people = people if judged_people is None else set(judged_people)
    def goal_matches(description):
        return symbol(description) == ('bm' if mismatched == 'activity' else 'up')
    def hazard(person, description, context, outcome):
        return person in people and goal_matches(description) and outcome == 'loss' and (
            context in ('belief', 'alternative') or context == 'actual')
    def degree(person, description, context):
        risk = actual_risk if context == 'actual' else believed_risk
        return 'high' if risk and person in judged_people and goal_matches(description) else 'low'
    def candidates(person, description, context, scene):
        return selected and person in people and symbol(description) == (
            'uy' if mismatched == 'candidate_description' else 'uw') and context == (
            'belief' if mismatched == 'candidate_context' else 'actual') and scene == 'belief'
    model.update(za=lambda: 'person', zb=lambda: 'actual', zc=lambda: 'belief',
        aa=lambda person: human and person in people,
        uq=hazard,
        ur=lambda person, scene: adverse and person in people and scene == 'loss',
        us=degree, ut=lambda level, context: level == 'high' and context != (
            'belief' if mismatched == 'standard_context' else 'unused'),
        uu=lambda person, description, context: Fraction(9 if burden and person in people and goal_matches(description) else 1),
        uv=lambda cost, context: cost > 5,
        u2=candidates,
        u3=lambda person, description, context: recognized and person in people and symbol(description) == (
            'uy' if mismatched == 'recognized_description' else 'uw') and context == 'actual',
        ha=lambda a, b: a+b, hb=lambda a, b: a*b, hc=lambda a, b: a<b,
        hd=lambda truth: Fraction(int(truth)), pa=lambda a, b: a/b if b else Fraction(0),
        hr=lambda population, context: set(population.items) == people and context == 'actual',
        u4=lambda ratio, context: ratio >= Fraction(4, 5) and context == 'actual')
    declared = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: value for name, value in model.items() if name in declared}


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.r zc[] d.
d zq[person a] e[k uw[v person]].
q[t[k uw[k za[]]][k zb[]]].q[t[k uw[k za[]]][k zc[]]].
q[t[k ux[k za[]]][k zb[]]].q[t[k uy[k za[]]][k zb[]]].q[t[k uz[k za[]]][k zb[]]].
q[t[k zq[k za[]]][k zb[]]].q[u[e[r[p uw]][r[p zq]]]].q[k u3[k za[] r[p zq] k zb[]]].
''')
    variants = {
        'false_but_accepted': ({}, [False, True, True, True, True]),
        'true_but_rejected': ({'actual_risk': True, 'believed_risk': False}, [True, False, False, True, False]),
        'true_and_accepted': ({'actual_risk': True}, [True, True, True, True, True]),
        'unrecognized': ({'recognized': False}, [False, True, False, True, False]),
        'empty_candidates': ({'selected': False}, [False, True, False, True, False]),
        'no_adverse_outcome': ({'adverse': False}, [False, False, False, True, False]),
        'not_burdensome': ({'burden': False}, [False, True, True, False, False]),
        'wrong_activity': ({'mismatched': 'activity'}, [False, False, False, False, False]),
        'wrong_candidate_description': ({'mismatched': 'candidate_description'}, [False, True, False, True, False]),
        'wrong_candidate_context': ({'mismatched': 'candidate_context'}, [False, True, False, True, False]),
        'wrong_recognized_description': ({'mismatched': 'recognized_description'}, [False, True, False, True, False]),
        'wrong_standard_context': ({'mismatched': 'standard_context'}, [False, False, False, True, False]),
    }
    rows = {}
    for name, (kwargs, expected) in variants.items():
        result = values(doc, source_model(doc, **kwargs))
        if result != [*expected, expected[0], True, False]:
            raise ValueError('Actual risk, attributed judgment or intensional identity differs: ' + name + repr(result))
        if name == 'false_but_accepted':
            ordinary = [r['value'] for r in evaluate_document(doc, individuals=PEOPLE, situations=SCENES,
                primitives=source_model(doc, **kwargs), max_steps=2_000_000)]
            if ordinary != result:
                raise ValueError('Ordinary and memoized appraisal evaluations differ')
        rows[name] = dict(zip(('actual_risk', 'candidate_risk', 'judgment', 'burden', 'combined',
                              'alias_actual_risk', 'descriptions_distinct', 'alias_recognized'), result))
    return rows


def majority_checks():
    doc = candidate(source_composed()[0], '''
r za[] j[a].r zb[] d.
q[t[k u5[k za[]]][k zb[]]].
''')
    rows = {}
    for name, population, selected, threshold, human in (
        ('all', ('person', 'other', 'third'), ('person', 'other', 'third'), Fraction(4, 5), True),
        ('mere_majority', ('person', 'other', 'third'), ('person', 'other'), Fraction(4, 5), True),
        ('stronger_context_accepts', ('person', 'other', 'third'), ('person', 'other'), Fraction(3, 5), True),
        ('criterion_alone_not_majority', ('person', 'other', 'third'), ('person',), Fraction(1, 4), True),
        ('duplicate', ('person', 'other', 'third', 'person'), ('person', 'other', 'third'), Fraction(4, 5), True),
        ('incomplete', ('person', 'other'), ('person', 'other'), Fraction(4, 5), True),
        ('empty', (), (), Fraction(4, 5), True),
        ('not_humans', ('person', 'other', 'third'), ('person', 'other', 'third'), Fraction(4, 5), False),
    ):
        model = source_model(doc, judged_people=selected, human=human)
        model.update(za=lambda: SequenceValue(population, '"individual"'), zb=lambda: 'actual',
                     u4=lambda ratio, context: ratio >= threshold and context == 'actual')
        result = values(doc, model)
        if result != [name in ('all', 'stronger_context_accepts')]:
            raise ValueError('Majority scope differs: ' + name)
        rows[name] = result[0]
    return rows


def target_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.q[t[k up[k za[]]][k zb[]]].
''')
    rows = {}
    for name in ('self_directed', 'guided', 'empty_selected', 'not_available', 'wrong_faculty', 'not_human'):
        model = source_model(doc, human=name != 'not_human')
        model.update(ab=lambda faculty, person, scene: (faculty, person) == (
            'act' if name == 'wrong_faculty' else 'faculty', 'person'),
            ac=lambda person, faculty, act, scene: (person, faculty, act, scene) == ('person', 'faculty', 'act', 'belief'),
            ad=lambda guide, person, act, scene: name == 'guided' and (guide, person, act, scene) == ('other', 'person', 'act', 'belief'),
            ae=lambda person, plan, start: name != 'not_available' and (person, plan, start) == ('person', 'plan', 'actual'),
            af=lambda person, plan, start, end: (person, plan, start, end) == ('person', 'plan', 'actual', 'belief'),
            ap=lambda person, plan, start, end: name != 'empty_selected' and (person, plan, start, end) == ('person', 'plan', 'actual', 'belief'))
        result = values(doc, model)
        if result != [name == 'self_directed']:
            raise ValueError('Autonomous goal did not use existing ability definition: ' + name)
        rows[name] = result[0]
    return rows


def alignment():
    source = json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'kant-1784:u0009')
    text = unit['text']
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Pinned source changed')
    opening = text.index('Daß der bei weitem')
    aside = text.index('(darunter', opening)
    resume = text.index('den Schritt', aside)
    end = text.index(': dafür', resume)
    segments = []
    for start, stop, names, status in (
        (opening, aside, ['u5'], 'partial_explicit_reading'),
        (aside, resume, [], 'pending'),
        (resume, end, ['up', 'uw', 'ux', 'uy', 'uz'], 'partial_explicit_reading'),
        (end, text.index('Nachdem', end), [], 'pending'),
    ):
        excerpt = text[start:stop].rstrip()
        segments.append({'start': start, 'end': start+len(excerpt), 'source': excerpt,
                         'definitions': names, 'status': status})
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'segments': segments,
        'full_semantic_equivalence': False,
        'remaining': ['female-group aside', 'guardian causation and agency', 'lexical basis and scale criteria',
                      'parenthetical scope and additive focus', 'step metaphor', 'rest of paragraph', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored appraisal differs')
        doc = parse(text)
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Appraisal roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/described-appraisals-basis-v1.json', 'data/kant-described-appraisals-basis-v1.json',
        'examples/v014/kant-state-convenience.noema', 'data/kant-state-convenience-basis-v1.json',
        'scripts/compose_described_appraisals.py', 'scripts/check_described_appraisals.py',
        'data/appraisal-reading-review-v1.json', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'partial_non_factive_danger_judgment_with_actual_burden', 'documents': documents,
        'judgment_candidates': generic_checks(), 'prospects': prospect_checks(),
        'source': source_checks(), 'majority': majority_checks(),
        'autonomy_goal': target_checks(), 'alignment': alignment(),
        'inherited_statements_unchanged': parse(source_composed()[0])['statements'] == parse(
            (ROOT / 'examples/v014/kant-state-convenience.noema').read_text(encoding='utf-8'))['statements'],
        'definitions_replaced_by_primitives': False, 'roundtrips': True,
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    result = build_report()
    if args.verify_only:
        if json.loads(REPORT.read_text(encoding='utf-8')) != result:
            raise ValueError('Appraisal report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('32 judgment, 11 prospect, 12 source, 8 majority and 6 autonomous-goal cases verified')


if __name__ == '__main__':
    main()
