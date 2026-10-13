"""Verify light-ball slices and conditional volume/energy algebra."""
import argparse
from fractions import Fraction as F
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import encode, decode
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, evaluate, OPS
from scripts.check_angle_composition import model_arithmetic
from scripts.check_parallel_composition import transform
from scripts.check_real_products import MEANINGS, assertion
from scripts.check_moving_light_trip import literal
from scripts.compose_limits import call as k, op, both, v
from scripts.compose_light_complex import ROOT, PARENT, BUILDERS, CUT, generic_composed, source_composed, core_composed

REPORT = ROOT / 'reports/light-complex-v1.json'
LEDGER = ROOT / 'data/light-complex-facsimile-v1.json'


def polynomial_checks():
    mul = lambda a, b: k('ad', a, b)
    add = lambda a, b: k('ab', a, b)
    sub = lambda a, b: add(a, k('ac', b))
    sq = lambda a: mul(a, a)
    zero, one = literal(0), literal(1)
    V, a, b, c, x, y, z, t, delta = map(v, 'light ax ay az x y z time delta'.split())
    beta, r = map(v, ('beta', 'ratio'))
    D = k('sebf', beta, r, a)
    domain = both(k('aa', zero, beta), k('aa', sq(r), one), op('u', k('aa', one, sq(a))))
    factor, p, newp, S, newS, C, E, newE = map(v, 'factor power newpower volume newvolume conversion energy newenergy'.split())
    premise = k('sebh', factor, p, newp, S, newS, C, E, newE)
    residual = add(sub(mul(C, newE), mul(newp, newS)), add(k('ac', mul(factor, sub(mul(C, E), mul(p, S)))),
        add(mul(sub(newp, mul(p, sq(factor))), newS), mul(mul(p, factor), sub(mul(factor, newS), S)))))
    f, newf = map(v, ('rate', 'newrate'))
    claims = {
        'moving_center_translation': assertion('light ax ay az x y z time delta', op('e',
            k('sebd', V, a, b, c, *[add(pos, mul(mul(V, direction), delta)) for pos, direction in ((x, a), (y, b), (z, c))], add(t, delta)),
            k('sebd', V, a, b, c, x, y, z, t))),
        'zero_new_time_inverse_slice': assertion('beta ratio ax ay az x y z', op('e',
            k('sebd', one, a, b, c, mul(beta, x), y, z, mul(mul(beta, r), x)),
            k('sebe', beta, r, a, b, c, x, y, z))),
        'volume_coefficient_positive': assertion('beta ratio ax', op('y', domain, k('aa', zero, D))),
        'parallel_positive_root': assertion('beta ratio', op('y', both(k('aa', zero, beta), k('aa', sq(r), one),
            op('e', mul(sq(beta), sub(one, sq(r))), one)), op('e', mul(sq(k('sebf', beta, r, one)), add(one, r)), sub(one, r)))),
        'energy_residual_identity': assertion('factor power newpower volume newvolume conversion energy newenergy',
            op('e', mul(C, sub(newE, mul(factor, E))), residual)),
        'energy_factor_from_density_and_volume': assertion('factor power newpower volume newvolume conversion energy newenergy',
            op('y', premise, op('e', newE, mul(factor, E)))),
        'shared_factor_preserves_energy_frequency_ratio': assertion('factor energy newenergy rate newrate', op('y',
            both(op('e', newE, mul(factor, E)), op('e', newf, mul(factor, f))), op('e', mul(newE, f), mul(E, newf)))),
        'unchanged_volume_counterexample': assertion('', k('sebg', *(literal(n) for n in (F(5,4), F(3,5), 0, 1, 1)))),
        'square_energy_factor_counterexample': assertion('', k('sebh', *(literal(n) for n in (2, 1, 4, 2, 1, 1, 2, 8)))),
        'negative_beta_counterexample': assertion('', k('sebg', *(literal(n) for n in (F(-5,4), F(3,5), 0, 1, F(-4,5))))),
    }
    rows = {}
    for name, claim in claims.items():
        result = verify_universal(parse(generic_composed()[0] + claim), MEANINGS, timeout_ms=20000)[0]
        expected = 'invalid' if name.endswith('counterexample') else 'valid'
        if result['status'] != expected:
            raise ValueError('Light complex algebra differs: ' + name + repr(result))
        rows[name] = result
    return {'claims': rows, 'rational_polynomial_proofs_only': True, 'volume_measure_law_proved': False,
        'all_real_cut_laws_proved': False}


def evaluate_numbers(doc, names, numbers, undefined_value=0):
    fixture, model = setup(doc)
    if undefined_value:
        model_arithmetic(fixture, model, undefined_value)
        model['ba'] = lambda value: isinstance(fixture.read(value), F)
        model['sjd'] = lambda value: fixture.make(1/fixture.read(value) if fixture.read(value)>0 else undefined_value)
    for name, number in zip(names, numbers, strict=True):
        model[name] = lambda number=number: fixture.make(number)
    return evaluate(doc, model)


def geometry_checks(texts):
    names = tuple('j' + n for n in 'abcdefghijklm')
    args = list(map(k, names))
    # V, v, a,b,c,R, xi,eta,zeta, oldx,oldy,oldz,oldt.
    surface = [args[0], *args[2:6], *args[9:13]]
    query = ''.join('q[' + k(name, *values) + '].' for name, values in (
        ('sece', args[:9]), ('secg', args[:9]), ('secb', surface), ('secc', surface)))
    docs = [abstract(candidate(text, ''.join('r ' + n + '[] ' + CUT + '.' for n in names) + query), OPS) for text in texts]
    directions = ((1,0,0), (-1,0,0), (0,1,0), (F(3,5),F(4,5),0), (F(1,3),F(2,3),F(2,3)))
    offsets = ((5,0,0), (3,4,0), (0,0,5), (0,0,0), (6,0,0))
    rows = []
    for speed, direction, offset in product((-3,0,3), directions, offsets):
        beta = F(5,4) if speed else F(1)
        ratio = F(speed,5)
        a,b,c = direction
        D = beta * (1-a*ratio)
        xi = F(offset[0]) / D
        newpoint = (xi, offset[1]+b*beta*ratio*xi, offset[2]+c*beta*ratio*xi, F(0))
        old = transform(newpoint, -speed, F(5))
        norm = sum(F(n)**2 for n in offset)
        expected = [norm == 25]*3 + [norm <= 25]
        numbers = (5,speed,*direction,5,*newpoint[:3],*old)
        actual = [evaluate_numbers(doc, names, numbers) for doc in docs]
        if any(row != expected for row in actual):
            raise ValueError('Moving ball/simultaneous slice differs: ' + str((numbers, actual, expected)))
        old_zero_norm = sum((old[i])**2 for i in range(3))
        rows.append({'speed': speed, 'direction': list(map(str, direction)), 'offset': list(offset),
            'old_time': str(old[3]), 'results': actual[0], 'wrong_old_zero_time_surface': old_zero_norm == 25})
    # Select the original queries only for the new-time slice; the old-point
    # queries intentionally have no dependence on the frame speed.
    contrasts = {}
    for label, index, value in (('zero_radius',5,0), ('negative_radius',5,-5), ('nonunit_direction',2,2),
                                ('zero_light',0,0), ('light_speed',1,5), ('superluminal',1,6)):
        numbers = [5,3,1,0,0,5,10,0,0,F(25,2),0,0,F(3,2)]
        numbers[index] = value
        actual = []
        for doc in docs:
            selected = {**doc, 'statements': doc['statements'][:2]}
            actual.append(evaluate_numbers(selected, names, numbers))
            if evaluate_numbers(selected, names, numbers, 17) != [False,False]:
                raise ValueError('Shape domain relies on undefined oracle result: '+label)
        if actual != [[False,False]]*2:
            raise ValueError('Invalid light-ball parameters accepted: ' + label + repr(actual))
        contrasts[label] = actual[0]
    return {'cases': rows, 'contrasts': contrasts, 'standalone_agrees': True,
        'surface_and_interior_distinguished': True, 'zero_new_time_is_not_zero_old_time': True,
        'domain_rejection_independent_of_two_undefined_oracle_values': True}


def energy_checks(texts):
    names = tuple('j' + n for n in 'abcdefghijkl')
    args = list(map(k, names))
    query = ''.join('q[' + k(name, *values) + '].' for name, values in (
        ('seci', args[:10]), ('secj', args[:3]+args[8:10]), ('seck', args[:3]+args[8:12])))
    docs = [abstract(candidate(text, ''.join('r '+n+'[] '+CUT+'.' for n in names)+query), OPS) for text in texts]
    def run(numbers):
        rows = [evaluate_numbers(doc, names, numbers) for doc in docs]
        if rows[0] != rows[1]:
            raise ValueError('Standalone energy conditions differ')
        return rows[0]
    rows = []
    for speed, a, conversion in product((-3,0,3), (-1,0,1,F(3,5),F(1,3)), (1,8)):
        beta = F(5,4) if speed else F(1)
        D = beta*(1-a*F(speed,5))
        E,S,rate = F(10),F(4),F(7)
        p = conversion*E/S
        numbers = (5,speed,a,p,p*D**2,S,S/D,conversion,E,E*D,rate,rate*D)
        actual = run(numbers)
        if actual != [True]*3:
            raise ValueError('Energy ratio from volume and density failed')
        rows.append({'speed': speed, 'ax': str(a), 'conversion': conversion, 'factor': str(D), 'results': actual})
    base = [5,3,0,F(5,2),F(125,32),4,F(16,5),1,10,F(25,2),7,F(35,4)]
    fixtures = {
        'unchanged_volume': ({6:4}, [False,True,True]),
        'changed_conversion': ({7:2}, [False,True,True]),
        'wrong_squared_amplitude': ({4:F(25,8)}, [False,True,True]),
        'squared_energy_factor': ({9:F(125,8)}, [False,False,False]),
        'wrong_frequency': ({11:7}, [True,True,False]),
        'zero_energy': ({8:0,9:0}, [False,False,False]),
        'negative_energy': ({8:-10,9:F(-25,2)}, [False,False,False]),
        'zero_power': ({3:0,4:0}, [False,True,True]),
        'zero_volume': ({5:0,6:0}, [False,True,True]),
        'negative_conversion': ({7:-1}, [False,True,True]),
        'out_of_range_direction': ({2:2}, [False,False,False]),
        'light_speed': ({1:5}, [False,False,False]),
        'superluminal': ({1:6}, [False,False,False]),
    }
    contrasts = {}
    for label, (changes, expected) in fixtures.items():
        numbers = base.copy()
        for i,value in changes.items():
            numbers[i] = value
        actual = run(numbers)
        if actual != expected:
            raise ValueError('Energy contrast failed: '+label+repr(actual))
        if label in ('light_speed','superluminal'):
            for doc in docs:
                if evaluate_numbers(doc,names,numbers,17) != expected:
                    raise ValueError('Energy domain relies on undefined oracle result')
        contrasts[label] = actual
    return {'cases': rows, 'contrasts': contrasts, 'standalone_agrees': True,
        'common_conversion_is_parameter_not_pi_definition': True}


def parallel_checks(text):
    names = ('ja','jb','jc','jd')
    doc = abstract(candidate(text, ''.join('r '+n+'[] '+CUT+'.' for n in names)+'q['+k('secl',*map(k,names))+'].'),OPS)
    rows = {}
    for speed, energy in ((-3,4),(0,2),(3,1)):
        for sign in (1,-1):
            actual = evaluate_numbers(doc,names,(5,speed,2,sign*energy))
            if actual != [sign == 1]:
                raise ValueError('Positive parallel root differs')
            rows[str((speed,sign))] = actual
    return rows


def finite_refusal(text):
    query = 'q['+k('secg',*(k('bb',literal(n)) for n in (5,0,1,0,0,5,5,0,0)))+'].'
    doc = candidate(text,query)
    fixture,model = setup(doc)
    model.update(aa=lambda a,b:a<b, ab=lambda a,b:a+b, ac=lambda a:-a, ad=lambda a,b:a*b)
    try:
        evaluate(doc,model)
    except ValueError as exc:
        if 'Cannot finitely quantify the rational number domain' not in str(exc):
            raise
        return {'refused':True,'reason':str(exc)}
    raise ValueError('Full cut semantics were replaced by finite samples')


def alignment():
    source = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    mapping = {'M0355':['secb','secc'], 'M0359':['sece','secg'], 'M0362':['sech'],
        'M0365':['seci','secj'], 'M0367':['secl']}
    rows = []
    for mid,definitions in mapping.items():
        item = next(m for m in source['math'] if m['id']==mid)
        unit = next(u for u in source['units'] if mid in u['math_ids'])
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:
            raise ValueError('Math snapshot differs')
        rows.append({'unit':unit['id'],'unit_sha256':unit['text_sha256'],'math_id':mid,'math_sha256':item['sha256'],
            'definitions':definitions,'status':'partial','review_ja':'原刊913–914頁の式を照合。球面・断面・正の体積比・エネルギー比の部分記述。M0365の8πの構成、空間測度、同じ光の集合と観測への帰属、全文の意味確認は未完。'})
    unit = next(u for u in source['units'] if u['id']=='einstein-1905:u0214')
    excerpt = 'die Energie und die Frequenz eines Lichtkomplexes sich nach demselben Gesetze'
    if unit['text'].count(excerpt)!=1:
        raise ValueError('Ambiguous energy/frequency excerpt')
    start = unit['text'].index(excerpt)
    rows.append({'unit':unit['id'],'unit_sha256':unit['text_sha256'],'range':[start,start+len(excerpt)],'text':excerpt,
        'definitions':['seck'],'status':'partial','review_ja':'同じ速度・方向に依存する係数をエネルギーと周波数に共用する条件。観測者の運動、同じ光の集合、著者の評価の意味は未完。'})
    return {'segments':rows,'semantic_completion':False,'new_source_ranges':True}


def facsimile_check():
    ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
    for item in [ledger['pdf'],*ledger['images']]:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Facsimile differs')
    if ledger['reviewed_math_ids'] != ['M0355','M0359','M0362','M0365','M0367']:
        raise ValueError('Review range differs')
    snapshot = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    for mid, expected in ledger['snapshot_math_sha256'].items():
        item = next(m for m in snapshot['math'] if m['id'] == mid)
        if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest() != expected:
            raise ValueError('Reviewed math tokens differ from snapshot')
    return ledger


def build_report():
    documents,sizes,texts = {},{},[]
    for builder,stem in BUILDERS:
        text,basis = builder();doc = parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored light complex differs')
        for notation in ('compact','full'):
            form = format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:
                raise ValueError('Light complex roundtrip differs')
        documents[basis['document']] = audit_basis(doc,basis)
        sizes[stem] = {'characters':len(text),'statements':len(doc['statements'])}
    source,parent = parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if source['declarations'][:len(parent['declarations'])]!=parent['declarations'] or source['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    facsimile = facsimile_check()
    paths = [*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'data/light-complex-facsimile-v1.json','scripts/compose_light_complex.py','scripts/check_light_complex.py',
        'scripts/check_plane_waveforms.py','scripts/check_tau_differential.py','scripts/check_angle_composition.py',
        'scripts/check_parallel_composition.py','noema/extraction.py','noema/polynomial_proofs.py','noema/finite_semantics.py',
        'artifacts/written-units-v1/einstein-1905.json',facsimile['pdf']['path'],*[item['path'] for item in facsimile['images']]]
    return json.loads(json.dumps({'status':'partial_moving_ball_volume_energy_conditions_not_physical_completion',
        'documents':documents,'sizes':sizes,'facsimile':facsimile,'polynomial':polynomial_checks(),
        'geometry':geometry_checks(texts[1:]),'energy':energy_checks(texts[1:]),'parallel':parallel_checks(texts[2]),
        'finite_refusal':finite_refusal(texts[2]),'alignment':alignment(),'parent_preserved':True,'roundtrips':True,
        'new_primitives':0,'new_author_statements':0,'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Light complex report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Moving ball slices and conditional volume/energy factors checked')


if __name__=='__main__':
    main()
