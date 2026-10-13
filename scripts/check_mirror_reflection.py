"""Check reflection stages while retaining the source's inconsistent last term."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json
import xml.etree.ElementTree as ET

from noema.grammar import parse, format_graph, number_word
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, OPS
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, op, both, v
from scripts.compose_mirror_reflection import ROOT, PARENT, BUILDERS, STAGES, PAIR, CUT, generic_composed

REPORT = ROOT/'reports/mirror-reflection-v1.json'
LEDGER = ROOT/'data/mirror-reflection-facsimile-v1.json'


def polynomial_checks():
    r, beta = v('ratio'), v('beta')
    stage = list(map(v, STAGES.split())); A, a, rate = stage[:3]; B, b, freq = stage[-3:]
    chain = k('sejd', r, beta, *stage)
    closed = k('seje', r, A, a, rate, B, b, freq)
    printed = k('sejf', r, A, a, rate, B, b, freq)
    mul = lambda a, b: k('ad', a, b)
    sub = lambda a, b: k('ab', a, k('ac', b))
    zero, one = literal(0), literal(1)
    claims = {
        'three_stages_imply_closed_form': assertion('ratio beta '+STAGES, op('y', chain, closed)),
        'printed_frequency_agrees_only_at_zero_speed': assertion('ratio '+PAIR, op('y', closed, op('z', printed, op('e', r, zero)))),
        'mirror_rest_reflection_is_involutive': assertion(PAIR, op('y', k('sejc', A, a, rate, B, b, freq), k('sejc', B, b, freq, A, a, rate))),
        'boost_factor_positive': assertion('ratio beta ax', op('y', k('seja', r, beta, a), k('aa', zero, mul(beta, sub(one, mul(r, a)))))),
        'closed_form_uses_same_amplitude_frequency_factor': assertion('ratio '+PAIR, op('y', closed, op('e', mul(B, rate), mul(A, freq)))),
        'printed_formula_matches_moving_example': assertion('', k('sejf', *(literal(x) for x in (F(3, 5), 2, 1, 8, F(1, 2), -1, 2)))),
        'derived_formula_matches_moving_example': assertion('', k('seje', *(literal(x) for x in (F(3, 5), 2, 1, 8, F(1, 2), -1, 2)))),
    }
    rows = {}
    for name, claim in claims.items():
        result = verify_universal(parse(generic_composed()[0]+claim), MEANINGS, timeout_ms=30000)[0]
        expected = 'invalid' if name == 'printed_formula_matches_moving_example' else 'valid'
        if result['status'] != expected: raise ValueError('Reflection proof '+name+': '+repr(result))
        rows[name] = result
    return dict(claims=rows, rational_polynomial_proofs_only=True, all_real_cut_field_laws_proved=False,
                reflection_boundary_conditions_proved=False)


def facsimile_check():
    ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
    for item in [ledger['pdf'], *ledger['images']]:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Mirror facsimile hash differs')
    source = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    for mid, expected in ledger['snapshot_math_sha256'].items():
        item = next(m for m in source['math'] if m['id'] == mid)
        if item['sha256'] != expected or hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest() != expected:
            raise ValueError('Reviewed source math differs')
    raw = next(m['mathml'] for m in source['math'] if m['id'] == 'M0376')
    ns = '{http://www.w3.org/1998/Math/MathML}'
    rows = list(ET.fromstring(raw).iter(ns+'mtr'))
    fractions = list(rows[-1].iter(ns+'mfrac'))
    # Select the unique fraction whose denominator has the whole (1-v/V)^2.
    selected = [f for f in fractions if ''.join(f[1].itertext()) == '(1−vV)2']
    if len(rows) != 3 or len(selected) != 1: raise ValueError('Printed frequency denominator changed')
    denominator = selected[0][1]
    if len(list(denominator.iter(ns+'msup'))) != 1: raise ValueError('Unexpected exponent structure')
    discrepancy = ledger['discrepancy']
    if discrepancy['is_transcription_correction'] or not discrepancy['snapshot_matches_facsimile']:
        raise ValueError('Original inconsistency mislabeled as transcription')
    return ledger


def evaluate(doc, model):
    used = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return values(doc, {name: value for name, value in model.items() if name in used}, ('object', 'x', 'y', 'z', 't'))


def fixture_numbers(speed, ax, amplitude=2, rate=8):
    V, speed, ax, amplitude, rate = map(F, (5, speed, ax, amplitude, rate))
    ratio = speed/V; beta = F(5, 4) if speed else F(1)
    factor = beta*(1-ratio*ax)
    first = (amplitude*factor, (ax-ratio)/(1-ratio*ax), rate*factor)
    second = (first[0], -first[1], first[2])
    back = beta*(1+ratio*second[1])
    final = (second[0]*back, (second[1]+ratio)/(1+ratio*second[1]), second[2]*back)
    return [V, speed, amplitude, ax, rate, *first, *second, *final]


def numeric_checks(texts):
    symbols = ['jz'+number_word(i) for i in range(14)]
    args = list(map(k, symbols))
    closedargs = args[:5]+args[-3:]
    extra = ''.join('r '+name+'[] '+CUT+'.' for name in symbols)+''.join('q['+body+'].' for body in (
        k('sejj', *args), k('sejk', *closedargs), k('sejl', *closedargs)))
    docs = [abstract(candidate(text, extra), OPS) for text in texts]
    def run(numbers):
        results = []
        for doc in docs:
            fixture, model = setup(doc)
            for symbol, value in zip(symbols, numbers, strict=True):
                model[symbol] = lambda value=F(value): fixture.make(value)
            results.append(evaluate(doc, model))
        if results[0] != results[1]: raise ValueError('Extracted reflection differs')
        return results[0]
    cases = []
    for speed, ax, amplitude in product((-3, 0, 3), (-1, F(-3, 5), 0, F(3, 5), 1), (0, 2)):
        result = run(fixture_numbers(speed, ax, amplitude))
        if result != [True, True, speed == 0]: raise ValueError('Reflection example differs')
        cases.append(dict(speed=speed, ax=str(ax), amplitude=amplitude, results=result))
    base = fixture_numbers(3, 1)
    contrasts = {}
    def check(name, numbers, expected):
        result = run(numbers)
        if result != expected: raise ValueError(name+': '+repr(result))
        contrasts[name] = result
    for index, name in ((5, 'first_amplitude'), (6, 'first_direction'), (7, 'first_frequency'),
                        (8, 'reflected_amplitude'), (9, 'reflected_direction'), (10, 'reflected_frequency')):
        numbers = base.copy(); numbers[index] += F(1, 10)
        check('wrong_'+name, numbers, [False, True, False])
    for index, name in ((11, 'final_amplitude'), (12, 'final_direction'), (13, 'final_frequency')):
        numbers = base.copy(); numbers[index] += F(1, 10)
        check('wrong_'+name, numbers, [False, False, False])
    # Keeping all other values unchanged, the actual printed last term is 8.
    numbers = base.copy(); numbers[-1] = F(8)
    check('printed_value_breaks_the_staged_result', numbers, [False, False, True])
    numbers = base.copy(); numbers[9] = numbers[6]
    check('omit_direction_reversal', numbers, [False, True, False])
    numbers = base.copy(); numbers[-3:] = numbers[2:5]
    check('returning_to_old_frame_does_not_undo_reflection', numbers, [False, False, False])
    numbers = fixture_numbers(3, 1, -2)
    check('negative_amplitude', numbers, [False, False, False])
    check('zero_frequency', fixture_numbers(3, 1, rate=0), [False, False, False])
    check('negative_frequency', fixture_numbers(3, 1, rate=-8), [False, False, False])
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True,
        actual_real_arithmetic_abstracted_to_registered_rational_cuts=True,
        physical_incidence_and_measurement_relations_verified=False)


def plane_checks(texts):
    names = ['jz'+number_word(i) for i in range(6)]
    args = list(map(k, names))
    extra = ''.join('r '+name+'[] '+CUT+'.' for name in names)+''.join('q['+k(name, *inputs)+'].' for name, inputs in (
        ('sejm', args[2:]), ('sejo', args), ('sejn', args)))
    docs = [abstract(candidate(text, extra), OPS) for text in texts]
    rows = []
    for speed, x, time in product((-3, 0, 3), (-3, 0, 3), (-1, 0, 1)):
        results = []
        for doc in docs:
            fixture, model = setup(doc)
            for name, value in zip(names, (5, speed, x, 7, -2, time), strict=True):
                model[name] = lambda value=F(value): fixture.make(value)
            results.append(evaluate(doc, model))
        if results != [[x == 0, x == 0, x == speed*time]]*2: raise ValueError('Mirror plane differs')
        rows.append(dict(speed=speed, x=x, time=time, results=results[0]))
    return dict(cases=rows, arbitrary_real_geometry_proved=False, mirror_material_properties_included=False)


def alignment():
    source = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    mapping = {'M0368': ['sejm', 'sejn', 'sejo'], 'M0372': ['sejh'], 'M0374': ['seji'], 'M0376': ['sejj', 'sejk', 'sejl']}
    rows = []
    for mid, definitions in mapping.items():
        item = next(m for m in source['math'] if m['id'] == mid)
        unit = next(u for u in source['units'] if mid in u['math_ids'])
        rows.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], math_id=mid, math_sha256=item['sha256'],
            definitions=definitions, status='partial', review_ja='原刊914–915頁と照合した平面・変換・反射の数値条件。M0376の振動数最右辺は原刊にもある不整合を別定義で保持する。鏡の物性・場の境界条件・測定と談話の接続は未完。'))
    return dict(segments=rows, semantic_completion=False, printed_and_derived_frequency_not_identified=True)


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored mirror document differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Mirror roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    facsimile = facsimile_check()
    paths = [*documents, PARENT, *['data/'+stem+'-basis-v1.json' for _, stem in BUILDERS],
        'data/mirror-reflection-facsimile-v1.json', 'scripts/compose_mirror_reflection.py', 'scripts/check_mirror_reflection.py',
        'scripts/check_plane_waveforms.py', 'scripts/check_tau_differential.py', 'scripts/check_angle_composition.py',
        'noema/finite_semantics.py', 'noema/extraction.py', 'noema/polynomial_proofs.py',
        'artifacts/written-units-v1/einstein-1905.json', facsimile['pdf']['path'], *[item['path'] for item in facsimile['images']]]
    return dict(status='partial_mirror_stages_with_original_formula_discrepancy', documents=documents, sizes=sizes,
        facsimile=facsimile, polynomial=polynomial_checks(), numeric=numeric_checks(texts[1:]), plane=plane_checks(texts[1:]),
        alignment=alignment(), new_definitions=15, new_primitives=0, new_author_statements=0,
        parent_preserved=True, roundtrips=True, verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Mirror report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Mirror stages, plane, and retained printed discrepancy checked')


if __name__ == '__main__': main()
