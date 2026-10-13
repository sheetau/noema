"""Check radiation work, zero-speed ambiguity, and a bounded leading term."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

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
from scripts.check_mirror_reflection import fixture_numbers
from scripts.compose_limits import call as k, op, both, v
from scripts.compose_light_pressure import ROOT, PARENT, BUILDERS, ALL, BASE, REFLECT, FLUX, LEADING, CUT, generic_composed

REPORT = ROOT/'reports/light-pressure-v1.json'
LEDGER = ROOT/'data/light-pressure-facsimile-v1.json'


def polynomial_checks():
    V, speed, A, a, B, b, C, incoming, outgoing, P, W, P0 = map(v,
        'light speed amplitude ax finalamplitude finalax conversion incoming outgoing pressure work leading'.split())
    mul = lambda a, b: k('ad', a, b)
    add = lambda a, b: k('ab', a, b)
    neg = lambda a: k('ac', a)
    sub = lambda a, b: add(a, neg(b))
    sq = lambda a: mul(a, a)
    zero, one, two, eight = map(literal, (0, 1, 2, 8))
    le = lambda a, b: op('u', k('aa', b, a))
    callfields = lambda fn, fields: k(fn, *map(v, fields.split()))
    balance = callfields('sekf', ALL); pressure = callfields('seke', BASE+' pressure')
    leading = callfields('sekg', LEADING)
    reflection = callfields('sekb', REFLECT); flux = callfields('sekc', FLUX)
    delta = sub(sq(V), sq(speed)); entering = sub(mul(V, a), speed)
    r, rate, newrate = map(v, ('ratio', 'rate', 'finalrate'))
    bound = v('absolute'); error = mul(mul(C, V), sub(P, P0)); upper = mul(eight, mul(sq(A), bound))
    residual = mul(two, mul(sq(A), add(neg(mul(two, mul(mul(V, a), speed))), mul(add(one, sq(a)), sq(speed)))))
    stationary = [literal(x) for x in (5, 0, 2, 1, 2, -1, 8, F(5, 2), F(5, 2), 1, 0)]
    different_pressure = stationary.copy(); different_pressure[-2] = literal(2)
    claims = {
        'reflection_agrees_with_preceding_closed_form': assertion('ratio rate finalrate '+REFLECT, op('y', both(
            k('seje', r, A, a, rate, B, b, newrate), k('aa', zero, V), k('aa', zero, C), op('e', speed, mul(r, V))), reflection)),
        'incoming_side_implies_outgoing_side': assertion(REFLECT, op('y', both(reflection, le(zero, entering)), le(zero, sub(speed, mul(V, b))))),
        'flux_difference_identity': assertion(FLUX, op('y', both(reflection, flux), op('e',
            mul(mul(C, delta), sub(incoming, outgoing)), mul(two, mul(mul(sq(A), speed), sq(entering)))))),
        'nonzero_velocity_work_determines_pressure': assertion(ALL, op('y', both(balance, op('u', op('e', speed, zero))), pressure)),
        'zero_velocity_allows_two_different_pressures': assertion('', both(k('sekf', *stationary), k('sekf', *different_pressure))),
        'work_alone_fixes_stationary_pressure': assertion('', op('y', k('sekf', *different_pressure),
            k('seke', *(literal(x) for x in (5, 0, 2, 1, 8, 2))))),
        'leading_term_matches_closed_form_at_rest': assertion(BASE+' pressure leading', op('y', both(pressure, leading, op('e', speed, zero)), op('e', P, P0))),
        'exact_error_identity': assertion(BASE+' pressure leading', op('y', both(pressure, leading),
            op('e', mul(mul(C, delta), sub(P, P0)), residual))),
        'leading_error_bound_for_half_light_speed': assertion(BASE+' pressure leading absolute', op('y', both(pressure, leading,
            le(zero, bound), op('e', sq(bound), sq(speed)), le(mul(two, bound), V)), both(le(neg(upper), error), le(error, upper)))),
        'leading_term_is_exact_at_nonzero_speed': assertion('', k('sekg', *(literal(x) for x in (2, 1, 8, F(1, 4))))),
    }
    rows = {}
    for name, claim in claims.items():
        result = verify_universal(parse(generic_composed()[0]+claim), MEANINGS, timeout_ms=30000)[0]
        expected = 'invalid' if name in ('work_alone_fixes_stationary_pressure', 'leading_term_is_exact_at_nonzero_speed') else 'valid'
        if result['status'] != expected: raise ValueError('Pressure proof '+name+': '+repr(result))
        rows[name] = result
    return dict(claims=rows, rational_polynomial_proofs_only=True, all_real_cut_field_laws_proved=False,
        stationary_pressure_from_work_alone=False, approximation_bound='|P-P0| <= (8*A^2/C)*|v|/V for |v| <= V/2',
        real_continuity_and_momentum_transfer_proved=False)


FIELDS = ALL.replace('conversion', 'pi')+' leading'
SYMBOLS = {name: 'jz'+number_word(i) for i, name in enumerate(FIELDS.split())}


def numeric_checks(texts):
    extra = ''.join('r '+symbol+'[] '+CUT+'.' for symbol in SYMBOLS.values())
    for name, fields in (('seko', ALL), ('sekp', BASE+' pressure'), ('sekq', LEADING)):
        extra += 'q['+k(name, *(k(SYMBOLS[n]) for n in fields.replace('conversion', 'pi').split()))+'].'
    docs = [abstract(candidate(text, extra), OPS | {'sedi'}) for text in texts]
    def run(speed=3, ax=1, amplitude=2, *, changes=None, pi_known=True):
        V, speed, A, a, *_ = fixture_numbers(speed, ax, amplitude)
        B, b, _ = fixture_numbers(speed, ax, amplitude)[-3:]
        # Pi=3 is only a synthetic token for the abstracted integral predicate.
        pi = F(3); C = 8*pi
        incoming = A*A*(V*a-speed)/C; outgoing = B*B*(speed-V*b)/C
        P = 2*A*A*(V*a-speed)**2/(C*(V*V-speed*speed))
        config = dict(zip(FIELDS.split(), (V, speed, A, a, B, b, pi, incoming, outgoing, P, P*speed, 2*A*A*a*a/C)))
        config.update(changes or {})
        results = []
        for doc in docs:
            fixture, model = setup(doc)
            for name, symbol in SYMBOLS.items():
                model[symbol] = lambda value=F(config[name]): fixture.make(value)
            model['sedi'] = lambda value: pi_known and fixture.read(value) == pi
            used = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
            results.append(values(doc, {n: val for n, val in model.items() if n in used}, ('object',)))
        if results[0] != results[1]: raise ValueError('Extracted pressure differs')
        return results[0], config
    cases = []
    for speed, ax, amplitude in product((-3, 0, 3), (-1, F(-3, 5), 0, F(3, 5), 1), (0, 2)):
        result, config = run(speed, ax, amplitude)
        if result != [F(ax) >= F(speed, 5), True, True]: raise ValueError('Pressure fixture differs')
        cases.append(dict(speed=speed, ax=str(ax), amplitude=amplitude, results=result,
            pressure=str(config['pressure']), work=str(config['work']), incoming=str(config['incoming']), outgoing=str(config['outgoing'])))
    contrasts = {}
    def check(name, expected, **options):
        actual, _ = run(**options)
        if actual != expected: raise ValueError(name+': '+repr(actual))
        contrasts[name] = actual
    for field in ('finalamplitude', 'finalax', 'incoming', 'outgoing', 'work'):
        _, config = run(); check('wrong_'+field, [False, True, True], changes={field: config[field]+F(1, 10)})
    check('wrong_pressure', [False, False, True], changes={'pressure': 2})
    check('wrong_leading_term', [True, True, False], changes={'leading': 2})
    check('use_leading_term_as_exact_pressure', [False, False, True], changes={'pressure': F(1, 3), 'work': 1})
    check('stationary_alternate_pressure', [True, False, True], speed=0, changes={'pressure': 2})
    check('stationary_negative_pressure', [False, False, True], speed=0, changes={'pressure': -1})
    check('stationary_nonzero_work', [False, True, True], speed=0, changes={'work': 1})
    check('approaching_mirror_work_sign_reversed', [False, True, True], speed=-3, changes={'work': 4})
    check('nonnegative_fluxes_on_wrong_side_still_rejected', [False, True, True], speed=3, ax=0, amplitude=0)
    check('unknown_pi', [False]*3, pi_known=False)
    check('wrong_pi_token', [False]*3, changes={'pi': 4})
    check('zero_pi', [False]*3, changes={'pi': 0})
    for name, changes, expected in (
        ('zero_light_speed', {'light': 0}, [False, False, True]),
        ('negative_light_speed', {'light': -5}, [False, False, True]),
        ('speed_at_light_speed', {'speed': 5}, [False, False, True]),
        ('speed_beyond_negative_light_speed', {'speed': -6}, [False, False, True]),
        ('negative_amplitude', {'amplitude': -2}, [False]*3),
        ('invalid_direction_cosine', {'ax': 2}, [False]*3),
    ): check(name, expected, changes=changes)
    return dict(cases=cases, contrasts=contrasts, standalone_agrees=True,
        pi_3_is_only_an_abstract_binding_token=True, pi_integral_condition_abstracted=True,
        actual_real_arithmetic_abstracted_to_registered_rational_cuts=True,
        measurement_units_and_physical_energy_principle_proved=False)


def facsimile_check():
    ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
    for item in (ledger['pdf'], ledger['image']):
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() != item['sha256']: raise ValueError('Pressure facsimile differs')
    source = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    for mid, expected in ledger['snapshot_math_sha256'].items():
        item = next(m for m in source['math'] if m['id'] == mid)
        if item['sha256'] != expected or hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest() != expected:
            raise ValueError('Pressure source math differs')
    return ledger


def alignment():
    source = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    mapping = {'M0377': ['sekj', 'seko'], 'M0378': ['sekj', 'seko'], 'M0379': ['sekk', 'seko'],
        'M0380': ['sekk', 'sekp'], 'M0381': ['sekl', 'sekp'], 'M0382': ['sekn', 'sekq']}
    rows = []
    for mid, definitions in mapping.items():
        item = next(m for m in source['math'] if m['id'] == mid)
        unit = next(u for u in source['units'] if mid in u['math_ids'])
        rows.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], math_id=mid, math_sha256=item['sha256'],
            definitions=definitions, status='partial', review_ja='原刊915頁と照合した入出エネルギー・仕事・光圧・近似項。零速度の未決定性と近似誤差を区別する。面積・時間・単位・鏡への帰属とエネルギー原理の物理的根拠、経験との一致、談話は未完。'))
    return dict(segments=rows, semantic_completion=False, approximation_not_asserted_as_exact=True)


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored pressure document differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Pressure roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    facsimile = facsimile_check()
    paths = [*documents, PARENT, *['data/'+stem+'-basis-v1.json' for _, stem in BUILDERS],
        'data/light-pressure-facsimile-v1.json', 'scripts/compose_light_pressure.py', 'scripts/check_light_pressure.py',
        'scripts/check_mirror_reflection.py', 'scripts/check_plane_waveforms.py', 'scripts/check_tau_differential.py',
        'scripts/check_angle_composition.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/polynomial_proofs.py',
        'artifacts/written-units-v1/einstein-1905.json', facsimile['pdf']['path'], facsimile['image']['path']]
    return dict(status='partial_radiation_flux_work_pressure_and_approximation', documents=documents, sizes=sizes,
        facsimile=facsimile, polynomial=polynomial_checks(), numeric=numeric_checks(texts[1:]), alignment=alignment(),
        new_definitions=17, new_primitives=0, new_author_statements=0, parent_preserved=True, roundtrips=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Pressure report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Radiation flux, signed work, zero-speed ambiguity and leading error checked')


if __name__ == '__main__': main()
