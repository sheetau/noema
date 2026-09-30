"""Check usual deterrence with exceptions and universal scope inside each case."""
import argparse
from fractions import Fraction
import hashlib
from itertools import product
import json

from noema.finite_semantics import SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate, source_model as appraisal_model
from scripts.check_described_explanations import symbol
from scripts.compose_example_deterrence import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/example-deterrence-v1.json'
DOMAIN = ('experiencer', 'person', 'other', 'third', 'casea', 'caseb', 'casec', 'example', 'differentexample',
          'futureone', 'futuretwo', 'pastact', 'nowact', 'unrelated', 'high', 'low', 'population', 'author', 'node', 'learning')
SCENES = ('past', 'actual', 'future', 'belief', 'loss')
CASES = ('casea', 'caseb', 'casec')
PEOPLE = ('person', 'other', 'third')


def values(doc, model, people=DOMAIN, scenes=SCENES):
    return [row['value'] for row in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=20_000_000, memoize_definitions=True)]


def arithmetic():
    return {'ha': lambda a, b: a+b, 'hb': lambda a, b: a*b, 'hc': lambda a, b: a<b,
            'hd': lambda truth: Fraction(int(truth)), 'pa': lambda a, b: a/b if b else Fraction(0)}


def scope_checks():
    doc = parse(generic_composed()[0] + '''
r za[] a.r zb[a] c.r zc[] d.r zd[a a d] c.q[k r6[k za[] p zb k zc[] p zd]].
''')
    rows = []
    for first, second, first_holds, second_holds in product((False, True), repeat=4):
        model = arithmetic() | {'za': lambda: 'person', 'zb': lambda act: act == 'one' and first or act == 'two' and second,
            'zc': lambda: 'now', 'zd': lambda person, act, scene: (person, scene) == ('person', 'now')
                and (act == 'one' and first_holds or act == 'two' and second_holds)}
        result = values(doc, model, ('person', 'one', 'two'), ('now',))
        expected = (first or second) and (not first or first_holds) and (not second or second_holds)
        if result != [expected]:
            raise ValueError('Nonempty universal scope differs')
        rows.append({'selected': [first, second], 'holds': [first_holds, second_holds], 'all': result[0]})
    return rows


def usual_checks():
    doc = parse(generic_composed()[0] + '''
r za[] j[a].r zb[a] c.r zc[a] c.r zd[b] c.r ze[] b.
q[k r7[k za[] p zb p zc p zd]].q[e[k pb[k za[] p zc]][k ze[]]].
''')
    people = ('a', 'b', 'c', 'd', 'e')
    checked, exceptions = 0, 0
    for count in range(6):
        for mask in product((False, True), repeat=count):
            selected = dict(zip(people[:count], mask))
            for threshold in (Fraction(3, 5), Fraction(4, 5)):
                model = arithmetic() | {'za': lambda: SequenceValue(people[:count], '"individual"'),
                    'zb': lambda case: True, 'zc': lambda case: selected.get(case, False),
                    'zd': lambda ratio: ratio >= threshold, 'ze': lambda: ratio}
                ratio = Fraction(sum(mask), count) if count else Fraction(0)
                result = values(doc, model, people, ('now',))
                expected = bool(count) and ratio > Fraction(1, 2) and ratio >= threshold
                if result != [expected, True]:
                    raise ValueError('Usual fraction differs from independent count')
                checked += 1
                exceptions += expected and sum(mask) < count
    invalid = {}
    for variant in ('duplicate', 'ineligible', 'minority_with_permissive_criterion', 'half', 'invalid_indicator'):
        population = ('a', 'a', 'b') if variant == 'duplicate' else ('a', 'b') if variant == 'half' else ('a', 'b', 'c')
        selected = ('a',) if variant in ('minority_with_permissive_criterion', 'half') else population
        model = arithmetic() | {'za': lambda: SequenceValue(population, '"individual"'),
            'zb': lambda case: not (variant == 'ineligible' and case == 'a'), 'zc': lambda case: case in selected,
            'zd': lambda ratio: True, 'ze': lambda: Fraction(0)}
        if variant == 'invalid_indicator':
            model['hd'] = lambda truth: Fraction(0)
        result = values(doc, model, people, ('now',))
        if result[0]:
            raise ValueError('Invalid frequency accepted: ' + variant)
        invalid[variant] = result[0]
    return {'enumerated_cases': checked, 'accepted_with_exceptions': exceptions, 'invalid': invalid}


def source_model(doc, variant='baseline'):
    model = appraisal_model(doc)
    def observer(case):
        return dict(zip(CASES, PEOPLE)).get(case, 'person')
    def scope(context):
        if context != 'actual' or variant == 'empty_cases':
            return ()
        return ('casea', 'caseb') if variant == 'omit_exception' else ('casea', 'casea', 'caseb', 'casec') if variant == 'duplicate_cases' else CASES[::-1] if variant == 'reordered_cases' else CASES
    def fear(person, act, context):
        return person in PEOPLE and context == 'actual' and act in ('futureone', 'futuretwo') and not (
            variant == 'no_fear_for_exception' and person == 'third')
    def avoiding(person, act, context):
        return fear(person, act, context) and person != 'third' and variant != 'mere_nonexecution' and not (
            variant == 'one_attempt_not_avoided' and (person, act) == ('person', 'futuretwo'))
    def explanation(subject, cause, target, effect, context):
        return (subject in CASES and target == ('casec' if variant == 'wrong_effect_subject' else subject)
            and context == 'actual' and symbol(cause) == ('gs' if variant == 'wrong_factor' else 'gr')
            and symbol(effect) in ('gs', 'gt') and not (variant == 'no_fear_explanation' and symbol(effect) == 'gs'))
    model.update(za=lambda: 'casea', zb=lambda: 'actual', zc=lambda: 'person',
        aa=lambda person: person in (*PEOPLE, 'experiencer') and not (variant == 'nonhuman_observer' and person == 'person'),
        mv=lambda: 'population', mp=lambda group: SequenceValue(PEOPLE if group == 'population' else (), '"individual"'),
        ab=lambda *args: False, ac=lambda *args: False,
        ad=lambda guide, person, act, context: guide != person,
        al=lambda person, goal, context: variant == 'courage_present' and person == 'person',
        f5=lambda person, event, description, point: (person, event, point) == ('experiencer', 'example', 'past')
            and symbol(description) == ('bm' if variant == 'wrong_task' else 'bb'),
        f6=lambda event, outcome: variant != 'unknown_example_result' and (event, outcome) == ('example', 'loss'),
        f7=lambda event: 'past', gd=observer, ge=lambda case: 'example',
        gg=lambda person, example, context: person in PEOPLE and example == (
            'differentexample' if variant == 'wrong_recognized_example' else 'example') and context == 'actual',
        gj=lambda case, context: case in CASES and context == 'actual' and not (
            variant == 'ineligible_case' and case == 'caseb'),
        gk=lambda context: SequenceValue(scope(context), '"individual"'),
        hr=lambda cases, context: set(cases.items) == set(CASES) and context == 'actual',
        gl=lambda ratio, context: context == 'actual' and ratio >= (Fraction(4, 5) if variant == 'strict_criterion' else Fraction(3, 5)),
        dd=lambda earlier, later: SCENES.index(earlier) < SCENES.index(later),
        ma=lambda person, act, context: variant != 'empty_attempts' and person in PEOPLE and context == 'actual'
            and act in ('futureone', 'futuretwo', 'pastact', 'nowact', 'unrelated'),
        go=lambda act: 'past' if act == 'pastact' else 'actual' if act == 'nowact' else 'future',
        gp=lambda act, description, context: act != 'unrelated' and symbol(description) == 'bb' and context == 'actual',
        mc=fear, md=avoiding,
        me=lambda person, act, description, context: symbol(description) == ('mb' if variant == 'wrong_avoidance_reason' else 'mc')
            and fear(person, act, context), ea=explanation)
    if variant == 'outside_current_group':
        model['u3'] = lambda *args: False
    declared = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: callback for name, callback in model.items() if name in declared}


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.r zc[] a.r ze[] b.
q[t[k gu[k za[]]][k zb[]]].q[t[k gv[k za[]]][k zb[]]].
q[e[k pb[k gk[k zb[]] i[case a][t[k gv[v case]][k zb[]]]]][k ze[]]].q[t[k gx[]][k zb[]]].
''')
    rows = {}
    for variant in ('baseline', 'reordered_cases', 'omit_exception', 'duplicate_cases', 'empty_cases', 'strict_criterion',
                    'ineligible_case', 'outside_current_group', 'nonhuman_observer', 'empty_attempts', 'unknown_example_result',
                    'wrong_task', 'wrong_recognized_example', 'courage_present', 'no_fear_for_exception',
                    'mere_nonexecution', 'one_attempt_not_avoided', 'wrong_avoidance_reason', 'wrong_effect_subject',
                    'wrong_factor', 'no_fear_explanation'):
        fear_false = ('empty_attempts', 'unknown_example_result', 'wrong_task', 'wrong_recognized_example',
                      'courage_present', 'wrong_effect_subject', 'wrong_factor', 'no_fear_explanation')
        deterrence_false = ('empty_attempts', 'unknown_example_result', 'wrong_task', 'wrong_recognized_example',
                           'mere_nonexecution', 'one_attempt_not_avoided', 'wrong_avoidance_reason',
                           'wrong_effect_subject', 'wrong_factor')
        ratio = Fraction(0) if variant in (*deterrence_false[:5], 'wrong_avoidance_reason', 'wrong_factor', 'empty_cases') else (
            Fraction(1) if variant == 'omit_exception' else Fraction(3, 4) if variant == 'duplicate_cases' else
            Fraction(1, 3) if variant == 'one_attempt_not_avoided' else Fraction(0) if variant == 'wrong_effect_subject' else Fraction(2, 3))
        model = source_model(doc, variant)
        model['ze'] = lambda: ratio
        result = values(doc, model)
        expected = [variant not in fear_false, variant not in deterrence_false, True, variant in ('baseline', 'reordered_cases')]
        if result != expected:
            raise ValueError('Example, timidity, deterrence or frequency differs: ' + variant + repr(result))
        rows[variant] = {'fear_with_example': result[0], 'deterrence_with_example': result[1],
                         'deterrence_fraction': str(ratio), 'fraction_matches_independent_count': result[2],
                         'scoped_usual_claim': result[3]}
    return rows


def future_scope_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.r zc[] a.r zd[] a.
q[k gq[k zc[] k zd[] k zb[]]].
''')
    rows = {}
    for act in ('futureone', 'futuretwo', 'pastact', 'nowact', 'unrelated'):
        model = source_model(doc)
        model['zd'] = lambda: act
        result = values(doc, model)
        if result != [act in ('futureone', 'futuretwo')]:
            raise ValueError('Future contemplated attempts differ')
        rows[act] = result[0]
    return rows


def attribution_checks():
    doc = candidate(source_composed()[0], 'q[k gy[]].')
    rows = {}
    def forbidden(*args):
        raise ValueError('Attribution evaluated fear or deterrence')
    for variant in ('baseline', 'wrong_author', 'wrong_content', 'wrong_node', 'reversed_text'):
        model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
        model.update(g2=lambda: 'node', fv=lambda: 'learning', wa=lambda: 'author', wh=lambda: 'actual',
            uc=lambda node, author, description, context: (node, author, context) == (
                'learning' if variant == 'wrong_node' else 'node', 'person' if variant == 'wrong_author' else 'author', 'actual')
                and json.loads(description.syntax) == {'kind': 'call', 'symbol': 'gs' if variant == 'wrong_content' else 'gx', 'arguments': []},
            ue=lambda a, b, context: (a, b, context) == (
                'node' if variant == 'reversed_text' else 'learning', 'learning' if variant == 'reversed_text' else 'node', 'actual'))
        result = values(doc, model)
        if result != [variant == 'baseline']:
            raise ValueError('Source attribution differs')
        rows[variant] = {'attribution': result[0], 'contents_evaluated': False}
    return rows


def alignment():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
                if u['id'] == 'kant-1784:u0009')
    text = unit['text']
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Pinned source differs')
    start = text.index('allein ein Beispiel')
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': len(text), 'source': text[start:],
        'definitions': ['gq', 'gr', 'gs', 'gt', 'gu', 'gv', 'gw', 'gx', 'gy'], 'status': 'partial_explicit_reading',
        'full_semantic_equivalence': False,
        'remaining': ['concession and focus', 'literal falling and walking', 'cognitive mechanism and timidity meaning',
            'generic scope and case representativeness', 'facsimile review']}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored example deterrence differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Example deterrence roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/example-deterrence-basis-v1.json', 'data/kant-example-deterrence-basis-v1.json',
        'examples/v014/kant-experience-acquisition.noema', 'data/kant-experience-acquisition-basis-v1.json',
        'scripts/compose_example_deterrence.py', 'scripts/check_example_deterrence.py',
        'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'example_fear_and_usual_deterrence_with_exceptions', 'documents': documents,
        'scope': scope_checks(), 'usual': usual_checks(), 'source': source_checks(), 'future_scope': future_scope_checks(),
        'attribution': attribution_checks(), 'alignment': alignment(), 'roundtrips': True,
        'definitions_replaced_by_primitives': False,
        'inherited_statements_unchanged': parse(source_composed()[0])['statements'] == parse(
            (ROOT / 'examples/v014/kant-experience-acquisition.noema').read_text(encoding='utf-8'))['statements'],
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Example deterrence report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('16 scope, 126 fraction, 5 invalid, 21 source, 5 future and 5 attribution cases verified')


if __name__ == '__main__':
    main()
