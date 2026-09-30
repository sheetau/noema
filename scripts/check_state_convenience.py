"""Check state-preserving low burden without inferring liking or choice."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import decode, encode
from scripts.compose_state_convenience import ROOT, generic_composed, source_composed
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/state-convenience-v1.json'


def candidate(text, questions):
    doc = parse(text)
    doc['statements'] = []
    return parse(format_graph(doc, 'compact') + '\n' + questions)


def values(doc, model, people, scenes, memoize=False, budget=5_000_000):
    return [r['value'] for r in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=budget, memoize_definitions=memoize)]


def state_checks():
    doc = candidate(generic_composed()[0], '''
r qa[] a.r qb[] d.r qc[d] c.r qd[d] c.r qe[a a d] c.r qf[a a d d] c.
r qg[a a d d] c.r qh[a a d] b.r qi[b] c.
q[k rj[k qa[] b scene[k qc[v scene]] b scene[k qd[v scene]] k qb[] p qe p qf p qg p qh p qi]].
q[k nd[k qa[] b scene[k qd[v scene]] k qb[] p qe p qf p qg p qh p qi]].
''')
    rows = []
    for initial, final, goal, available, selected, cheap in product((False, True), repeat=6):
        model = {'qa': lambda: 'person', 'qb': lambda: 'start',
            'qc': lambda scene: initial if scene == 'start' else final,
            'qd': lambda scene: goal and scene == 'end',
            'qe': lambda person, plan, start: available and (person, plan, start) == ('person', 'plan', 'start'),
            'qf': lambda person, plan, start, end: (person, plan, start, end) == ('person', 'plan', 'start', 'end'),
            'qg': lambda person, plan, start, end: selected and (person, plan, start, end) == ('person', 'plan', 'start', 'end'),
            'qh': lambda *args: Fraction(1 if cheap else 9), 'qi': lambda burden: burden <= 2}
        actual = values(doc, model, ('person', 'plan'), ('start', 'end'))
        expected = [initial and final and goal and available and selected and cheap,
                    goal and available and selected and cheap]
        if actual != expected:
            raise ValueError('State convenience was reduced to easy attainment')
        rows.append({'initial_state': initial, 'result_state': final, 'goal': goal, 'available': available,
            'selected': selected, 'cheap': cheap, 'state_convenience': actual[0], 'easy_goal': actual[1]})
    contrasts = {}
    for variant in ('split_state_and_goal', 'split_burden_and_success', 'combined', 'outside_outcomes'):
        def outcome(person, plan, start, end):
            return (person, start) == ('person', 'start') and (plan, end) in (('first', 'one'), ('second', 'two'))
        model = {'qa': lambda: 'person', 'qb': lambda: 'start',
            'qc': lambda scene: scene in ('start', 'one') or (variant != 'split_state_and_goal' and scene == 'two'),
            'qd': lambda scene: scene == 'two',
            'qe': lambda person, plan, start: (person, start) == ('person', 'start') and plan in ('first', 'second'),
            'qf': lambda *args: variant != 'outside_outcomes' and outcome(*args), 'qg': outcome,
            'qh': lambda person, plan, start: Fraction(9 if variant == 'split_burden_and_success' and plan == 'second' else 1),
            'qi': lambda burden: burden <= 2}
        actual = values(doc, model, ('person', 'first', 'second'), ('start', 'one', 'two'))
        expected = {'split_state_and_goal': [False, True], 'split_burden_and_success': [False, False],
                    'combined': [True, True], 'outside_outcomes': [False, False]}[variant]
        if actual != expected:
            raise ValueError('Convenience mixed different methods: ' + variant)
        contrasts[variant] = actual
    return {'cases': rows, 'contrasts': contrasts}


PEOPLE = ('person', 'other', 'plan', 'faculty', 'act')
SCENES = ('text', 'case', 'result', 'autonomous')


def source_model(doc, variant):
    def forbidden(*args):
        raise ValueError('Convenience evaluated liking, motives or actual choice')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    def method(person, plan, start):
        return variant != 'no_method' and (person, plan) == ('person', 'plan') and (
            start == 'case' or (variant in ('not_immature', 'state_changes') and start == 'result'))
    def outcome(person, plan, start, end):
        return (person, plan) == ('person', 'plan') and ((start, end) == ('case', 'result') or (
            variant in ('not_immature', 'state_changes') and (start, end) == ('result', 'autonomous')))
    model.update(za=lambda: 'person', zb=lambda: 'case', zc=lambda: 'result', wh=lambda: 'text',
        aa=lambda person: variant != 'not_human' and person in ('person', 'other'),
        ab=lambda faculty, person, scene: (faculty, person) == ('faculty', 'person'),
        ac=lambda person, faculty, act, scene: (person, faculty, act) == ('person', 'faculty', 'act') and (
            (variant == 'not_immature' and scene in ('result', 'autonomous')) or (variant == 'state_changes' and scene == 'autonomous')),
        ad=lambda *args: False, ae=method, af=outcome,
        ap=lambda *args: variant != 'empty_results' and outcome(*args),
        oc=lambda *args: Fraction(9 if variant == 'high_burden' else 1),
        sj=lambda person, scene: variant != 'failed_goal' and (person, scene) == ('person', 'result'),
        uj=lambda person, context, scene: variant != 'empty_cases' and (person, context, scene) == (
            'other' if variant == 'wrong_case_person' else 'person', 'case' if variant == 'wrong_case_context' else 'text', 'case'),
        uk=lambda burden, context: burden <= 2 and context == ('case' if variant == 'wrong_standard_context' else 'text'),
        um=lambda person, context: variant != 'empty_people' and (person, context) == ('person', 'text'))
    return model


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.r zc[] d.
q[t[k bf[k za[]]][k zb[]]].q[t[k bf[k za[]]][k zc[]]].
q[t[k ul[k za[]]][k wh[]]].q[t[k un[]][k wh[]]].
''')
    rows = {}
    variants = ('baseline', 'high_burden', 'failed_goal', 'no_method', 'not_immature', 'state_changes',
        'not_human', 'empty_results', 'empty_cases', 'empty_people', 'wrong_case_person', 'wrong_case_context', 'wrong_standard_context')
    for variant in variants:
        actual = values(doc, source_model(doc, variant), PEOPLE, SCENES, True)
        expected = [variant not in ('not_immature', 'not_human', 'empty_results'),
                    variant not in ('not_immature', 'not_human', 'state_changes'),
                    variant in ('baseline', 'empty_people'), variant == 'baseline']
        if actual != expected:
            raise ValueError('Integrated convenience differs: ' + variant + ' ' + repr(actual))
        rows[variant] = dict(zip(('state_at_case', 'state_at_result', 'person_convenience', 'scoped_general_claim'), actual))
    ordinary = values(doc, source_model(doc, 'baseline'), PEOPLE, SCENES, budget=50_000_000)
    if ordinary != list(rows['baseline'].values()):
        raise ValueError('Ordinary and memoized convenience evaluations differ')
    return {'cases': rows, 'definitions_replaced_by_primitives': False, 'ordinary_baseline_agrees': True,
        'pure_definition_memoization': True, 'liking_motive_or_choice_evaluated': False}


def attribution_checks():
    from scripts.check_kant_discourse import base_model, DOMAIN, NODES
    doc = parse(source_composed()[0])
    rows = {}
    for variant in ('baseline', 'wrong_node', 'wrong_author', 'wrong_content', 'wrong_context', 'reversed_before', 'reversed_after'):
        model = base_model(doc)
        def forbidden(*args):
            raise ValueError('Attribution endorsed the convenience claim or evaluated a state')
        for name in ('uj', 'uk', 'um', 'ae', 'af', 'ap', 'oc', 'id', 'me', 'oa'):
            model[name] = forbidden
        def claim(node, author, description, context):
            if node in ('conclusion', 'explanation'):
                return True
            syntax = json.loads(description.syntax)
            return (node, author, syntax, context) == ('other' if variant == 'wrong_node' else 'convenience',
                'other' if variant == 'wrong_author' else 'author',
                {'kind': 'call', 'symbol': 'mx' if variant == 'wrong_content' else 'un', 'arguments': []},
                'other' if variant == 'wrong_context' else 'text')
        def before(a, b, context):
            edges = [('conclusion', 'explanation'), ('explanation', 'illustration'), ('illustration', 'payment'),
                ('convenience', 'explanation') if variant == 'reversed_before' else ('explanation', 'convenience'),
                ('illustration', 'convenience') if variant == 'reversed_after' else ('convenience', 'illustration')]
            return context == 'text' and ((a in NODES and b in NODES and NODES.index(a) < NODES.index(b)) or (a, b) in edges)
        model.update(mw=lambda: 'explanation', s3=lambda: 'illustration', t4=lambda: 'payment', uo=lambda: 'convenience',
            ua=lambda *args: True, ub=lambda *args: True, uc=claim, ud=lambda *args: True,
            uf=lambda *args: True, qa=lambda *args: True, s4=lambda *args: True, s5=lambda *args: True, ue=before)
        actual = values(doc, model, (*DOMAIN, 'explanation', 'illustration', 'payment', 'convenience', 'other'), ('text',))
        if actual != [True, True, True, True, True, variant == 'baseline']:
            raise ValueError('Convenience attribution or source order differs: ' + variant)
        rows[variant] = {'statements': actual, 'underlying_contents_evaluated': False}
    return rows


def alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0009')
    digest = hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()
    if digest != unit['text_sha256'] or digest != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Original source differs')
    starts = ('Faulheit und Feigheit', 'Es ist so bequem, unmündig zu sein.', 'Habe ich ein Buch,',
              'Ich habe nicht nöthig zu denken,', 'Daß der bei weitem größte Theil')
    if any(unit['text'].count(start) != 1 for start in starts):
        raise ValueError('Paragraph prefix boundaries are missing or ambiguous')
    boundaries = [unit['text'].index(start) for start in starts]
    if boundaries[0] != 0 or boundaries != sorted(boundaries):
        raise ValueError('Paragraph prefix order differs')
    entries = (('causal_explanation', 'mw', 'mx'), ('state_convenience', 'uo', 'un'),
               ('three_examples', 's3', 'sy'), ('payment_expectation', 't4', 't3'))
    segments, covered = [], set()
    for (name, node, definition), start, next_start in zip(entries, boundaries, boundaries[1:]):
        excerpt = unit['text'][start:next_start].rstrip()
        end = start + len(excerpt)
        covered.update(i for i in range(start, end) if not unit['text'][i].isspace())
        segments.append({'id': name, 'node': node, 'definition': definition, 'start': start, 'end': end,
            'source': excerpt, 'status': 'partial_explicit_reading'})
    expected = {i for i in range(boundaries[-1]) if not unit['text'][i].isspace()}
    if covered != expected:
        raise ValueError('A source character in the first four sentences was left unassigned')
    return {'unit': unit['id'], 'unit_sha256': digest, 'segments': segments,
        'all_nonblank_prefix_characters_assigned': True, 'prefix_end': boundaries[-1],
        'remaining_source_characters': len(unit['text']) - boundaries[-1],
        'full_semantic_equivalence': False, 'remaining': ['general semantic basis', 'convenience degree and scope',
            'irony and discourse effects', 'rest of paragraph', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored state convenience differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('State convenience roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/state-convenience-basis-v1.json', 'data/kant-state-convenience-basis-v1.json',
        'examples/v014/kant-payment-expectation.noema', 'data/kant-payment-expectation-basis-v1.json',
        'scripts/compose_state_convenience.py', 'scripts/check_state_convenience.py', 'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'state_convenience_and_four_sentence_partial_prefix', 'documents': documents,
        'state': state_checks(), 'source': source_checks(), 'attribution': attribution_checks(),
        'alignment': alignment(), 'roundtrips': True, 'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('State convenience report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('64 state cases, 4 method contrasts, 13 source and 7 attribution cases; four source sentences assigned')


if __name__ == '__main__':
    main()
