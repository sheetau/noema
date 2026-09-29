"""Verify finite ratio witnesses and evaluate both source results without stubs."""
import argparse
from fractions import Fraction
import hashlib
import json

from noema.finite_semantics import SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.compose_finite_ratios import ROOT, generic_composed, source_composed
from scripts.compose_limits import v, call, op, both, quant
from scripts.check_described_explanations import symbol

REPORT = ROOT / 'reports/finite-ratios-v1.json'


def arithmetic_proofs():
    zero, one = 'n p a b', 'n p b b'
    n, c, r, s = [v(name) for name in ('size', 'count', 'ratio', 'other')]
    mul = lambda a, b: call('aa', a, b)
    lt = lambda a, b: call('ab', a, b)
    le = lambda a, b: op('u', lt(b, a))
    eq = lambda a, b: op('e', a, b)
    claims = {
        'positive_size_has_at_most_one_ratio': (('size', 'count', 'ratio', 'other'), op('y', both(lt(zero, n), eq(mul(n, r), c), eq(mul(n, s), c)), eq(r, s))),
        'bounded_count_gives_ratio_in_unit_interval': (('size', 'count', 'ratio'), op('y', both(lt(zero, n), le(zero, c), le(c, n), eq(mul(n, r), c)), both(le(zero, r), le(r, one)))),
        'any_other_candidate_equals_computed_quotient': (('size', 'count', 'ratio', 'other'), op('y', both(lt(zero, n), eq(mul(n, s), c)), op('z', eq(mul(n, r), c), eq(r, s)))),
    }
    rows = {}
    for name, (names, body) in claims.items():
        for variable in reversed(names):
            body = quant('f', variable, 'b', body)
        text = 'n:r aa[b b] b.r ab[b b] c.s[' + body + '].'
        result = verify_universal(parse(text), {'aa': 'multiply', 'ab': 'less'})[0]
        if result['status'] != 'valid':
            raise ValueError('Ratio arithmetic unresolved: ' + name)
        rows[name] = result
    return rows


def finite_checks():
    doc = parse(generic_composed()[0] + '''
r za[] j[a].r zb[a] c.r zc[a] c.r zd[b] c.r ze[] b.
q[e[k pb[k za[] p zb]][k ze[]]].q[k pc[k za[] p zb]].q[k pd[k za[] p zc p zb p zd]].
''')
    def run(population, selected, *, quotient_bad=False, outsider=None, indicator_bad=False):
        expected = Fraction(len([p for p in population if p in selected]), len(population)) if population else Fraction(0)
        model = {'ha': lambda a, b: a+b, 'hb': lambda a, b: a*b, 'hc': lambda a, b: a<b,
            'hd': lambda truth: Fraction(2 if indicator_bad and truth else int(truth)),
            'pa': lambda a, b: Fraction(99) if quotient_bad else a/b if b else Fraction(0),
            'za': lambda: SequenceValue(tuple(population), '"individual"'), 'zb': lambda p: p in selected,
            'zc': lambda p: p != outsider, 'zd': lambda ratio: ratio >= Fraction(3, 5), 'ze': lambda: expected}
        return [r['value'] for r in evaluate_document(doc, individuals=tuple(dict.fromkeys((*population, 'other'))), situations=('text',), primitives=model)]
    rows = []
    for size in range(9):
        population = tuple('p'+str(i) for i in range(size))
        for count in range(size+1):
            actual = run(population, set(population[:count]))
            expected = [True, bool(size), bool(size) and Fraction(count, size) >= Fraction(3, 5)]
            if actual != expected:
                raise ValueError('Computed finite ratio differs')
            rows.append({'size': size, 'count': count, 'quotient_matches': actual[0], 'valid': actual[1], 'large': actual[2]})
    contrasts = {}
    for name, population, selected, kwargs, expected in (
        ('duplicate', ('a', 'a', 'b'), {'a'}, {}, [True, False, False]),
        ('outsider', ('a', 'b'), {'a', 'b'}, {'outsider': 'b'}, [True, True, False]),
        ('bad_quotient', ('a', 'b'), {'a'}, {'quotient_bad': True}, [False, False, False]),
        ('bad_indicator', ('a', 'b'), {'a'}, {'indicator_bad': True}, [False, False, False]),
        ('empty', (), set(), {}, [True, False, False])):
        actual = run(population, selected, **kwargs)
        if actual != expected:
            raise ValueError('Invalid ratio accepted: ' + name)
        contrasts[name] = actual
    return {'cases': rows, 'contrasts': contrasts}


def source_candidate(legacy=False):
    text = (ROOT / 'examples/v014/kant-easy-guardians.noema').read_text(encoding='utf-8') if legacy else source_composed()[0]
    doc = parse(text)
    doc['statements'] = []
    return parse(format_graph(doc, 'compact') + '\nq[t[k ms[k mv[]]][k wh[]]].q[t[k ok[k mv[]]][k wh[]]].')


def source_values(doc, *, expensive=False):
    scenes = ('child', 'adult', 'text', 'expected')
    domain = ('change', 'reader', 'guide', 'faculty', 'group')
    model = {d['name']: (lambda *args: False) for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update({
        'aa': lambda p: p in ('reader', 'guide'),
        'ab': lambda faculty, person, scene: (faculty, person) == ('faculty', 'reader'),
        'ac': lambda person, faculty, act, scene: (person, faculty, act) == ('reader', 'faculty', 'change'),
        'ae': lambda person, plan, scene: plan == 'change' and ((person == 'reader' and scene != 'text') or (person == 'guide' and scene == 'text')),
        'af': lambda person, plan, start, end: plan == 'change' and ((person == 'reader' and start == end) or (person == 'guide' and start == 'text' and end == 'expected')),
        'ap': lambda person, plan, start, end: plan == 'change' and ((person == 'reader' and start == end) or (person == 'guide' and start == 'text' and end == 'expected')),
        'ag': lambda process, start, end: (process, start, end) == ('change', 'child', 'adult'),
        'la': lambda person, process, start, end: (person, process, start, end) == ('reader', 'change', 'child', 'adult'),
        'ha': lambda a, b: a+b, 'hb': lambda a, b: a*b, 'hc': lambda a, b: a<b, 'hd': lambda b: Fraction(int(b)),
        'hr': lambda pop, context: pop.items == ('reader',) and context == 'text',
        'hs': lambda ratio, context: ratio >= Fraction(3, 5) and context == 'text',
        'ia': lambda person, ctx, point: person == 'reader' and ctx in ('text', 'expected') and point in ('child', 'adult', ctx),
        'ib': lambda person, ctx, point: person == 'reader' and ctx in ('text', 'expected') and point == ctx,
        'ic': lambda a, b, ctx: scenes.index(a) < scenes.index(b),
        'id': lambda person, desc, point: person == 'reader' and symbol(desc) == 'bf' and point == 'text',
        'ka': lambda person, point: person == 'reader' and point != 'child',
        'kb': lambda person, other, point: (person, other, point) == ('reader', 'guide', 'child'),
        'kd': lambda *args: True,
        'ke': lambda judge, person, desc, ctx, alt: (judge, person, symbol(desc), ctx, alt) == ('guide', 'reader', 'kf', 'text', 'expected'),
        'mp': lambda group: SequenceValue(('reader',) if group == 'group' else (), '"individual"'),
        'mv': lambda: 'group', 'wa': lambda: 'guide', 'wh': lambda: 'text',
        'oa': lambda actor, act, scene: (actor, act, scene) == ('guide', 'change', 'expected'),
        'ob': lambda act, actor, target, scene: (act, actor, target, scene) == ('change', 'guide', 'reader', 'expected'),
        'oc': lambda *args: Fraction(9 if expensive else 1),
        'oe': lambda burden, ctx: burden <= 2 and ctx == 'text',
        'of': lambda group, actor, ctx: (group, actor, ctx) == ('group', 'guide', 'text')})
    if 'pa' in model:
        model['pa'] = lambda a, b: a/b if b else Fraction(0)
    return [r['value'] for r in evaluate_document(doc, individuals=domain, situations=scenes, primitives=model,
        max_steps=50000000, memoize_definitions=True)]


def source_checks():
    doc = source_candidate()
    rows = {}
    for name, expensive in (('baseline', False), ('high_role_burden', True)):
        actual = source_values(doc, expensive=expensive)
        if actual != [True, not expensive]:
            raise ValueError('Integrated source results differ: ' + name)
        rows[name] = {'first_result': actual[0], 'second_result': actual[1]}
    try:
        source_values(source_candidate(legacy=True))
    except ValueError as error:
        if 'rational number domain' not in str(error):
            raise
        refused = str(error)
    else:
        raise ValueError('Legacy unbounded rational quantification unexpectedly ran')
    return {'cases': rows, 'semantic_definitions_stubbed': False, 'pure_definition_memoization': True, 'legacy_refusal': refused,
        'meaning': 'Finite interpretations exercise real definitions of both results; no real-world or full source equivalence is proved.'}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored finite ratio differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            canonical = format_graph(doc, notation)
            if parse(canonical) != doc or parse(decode(encode(canonical, 'v2'))) != doc:
                raise ValueError('Finite ratio roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/finite-ratios-basis-v1.json', 'data/kant-finite-ratio-basis-v1.json',
        'examples/v014/kant-easy-guardians.noema', 'data/kant-easy-guardians-basis-v1.json',
        'scripts/compose_finite_ratios.py', 'scripts/check_finite_ratios.py', 'noema/discourse.py', 'noema/finite_semantics.py', 'noema/polynomial_proofs.py']
    return {'status': 'unique_finite_ratio_and_integrated_source_results', 'documents': documents,
        'arithmetic': arithmetic_proofs(), 'finite': finite_checks(), 'source': source_checks(), 'roundtrips': True,
        'verified_full_units': {'einstein-1905': 0, 'kant-1784': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Finite ratio report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('3 rational lemmas, 45 finite counts, 5 invalid inputs and 2 integrated source cases checked')


if __name__ == '__main__':
    main()
