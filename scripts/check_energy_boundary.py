"""Check boundary certificates and keep physical possibility independent."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
import hashlib, json, subprocess, sys
from noema.grammar import parse, format_graph
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_energy_boundary import ROOT, PARENT, SOURCE, LIBRARY, CORE, READING, CUT, PHYSICAL, build
from scripts.compose_limits import call as k, both, op, v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, OPS
from scripts.check_rod_setup import callbacks, guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS, assertion

REPORT = ROOT/'reports/energy-boundary-v1.json'
PEOPLE = ('particle', 'frame', 'other', 'limit', 'possible', 'author', 'scope')
SCENES = ('actual', 'alternative', 'other')


@lru_cache(None)
def text(path): return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc, model):
    return [r['value'] for r in evaluate_document(doc, individuals=PEOPLE, situations=SCENES,
        primitives={d['name']: model[d['name']] for d in doc['declarations'] if d['kind'] == 'primitive'}, max_steps=3_000_000)]


def cut(x): return k('bb', number(x))


def numeric_checks():
    rows = {}
    # Rational points on the normalization conic keep roots exact even at huge
    # bounds. This is an explicit witness family, not random float samples.
    for light, mass in [(F(5), F(2)), (F(2, 3), F(3, 7))]:
        for bound in map(F, (-10, 0, 1, 100, 10**12)):
            level = 1+max(bound, 0)/(mass*light**2)
            denominator = 2*level**2+2*level+1
            speed = light*2*level*(level+1)/denominator
            beta = denominator/(2*level+1)
            energy = mass*light**2*(beta-1)
            radius = light/(2*level**2)
            query = 'q['+k('sca', k('sesw', cut(light), cut(mass), cut(bound)), cut(radius))+'].'
            query += 'q['+k('sesx', *map(cut, (light, mass, bound, speed)))+'].'
            query += 'q['+k('sca', k('sesu', *map(cut, (light, mass, speed))), cut(energy))+'].'
            query += 'q['+k('sesz', *map(number, (light, mass, max(bound, 0), level, radius, speed, beta, energy)))+'].'
            for path in (LIBRARY, CORE):
                doc = abstract(candidate(text(path), query), OPS); _, model = setup(doc); model.update(ARITHMETIC)
                assert evaluate(doc, model) == [True]*4
            assert energy > bound and 0 <= speed < light and light-radius < speed
            rows[f'{light}/{mass}/{bound}'] = dict(radius=str(radius), speed=str(speed), energy=str(energy))
    # Exact boundary and out-of-domain points cannot be finite energy values.
    boundary = {}
    for label, values in [('light_boundary', (5, 2, 0, 5)), ('superluminal', (5, 2, 0, 6)),
                          ('zero_mass', (5, 0, 0, 4)), ('negative_mass', (5, -1, 0, 4))]:
        doc = abstract(candidate(text(CORE), 'q['+k('sesx', *map(cut, values))+'].'), OPS)
        _, model = setup(doc); model.update(ARITHMETIC)
        boundary[label] = evaluate(doc, model)[0]; assert boundary[label] is False
    query = ''.join('q['+k('sesr', *map(cut, (5, 2, point)))+'].' for point in (3, 4, 5, 6))
    doc = abstract(candidate(text(LIBRARY), query), OPS); _, model = setup(doc); model.update(ARITHMETIC)
    assert evaluate(doc, model) == [False, True, False, False]
    return dict(exact_threshold_witnesses=rows, excluded_inputs=boundary, strict_left_neighborhood=True,
                polynomial_certificate_premises_have_exact_witnesses=True)


def polynomial_checks():
    selected = extract_document(parse(text(LIBRARY)), roots=['sesz'], statement_indices=[]).document
    base = format_graph(selected, 'compact')
    names = 'light mass bound level radius speed beta energy'; values = [v(n) for n in names.split()]
    light, mass, bound, level, radius, speed, beta, energy = values
    fields = values[:5]
    claims = {
        'radius_certificate_forces_energy_above_bound': assertion(names, op('y', k('sesz', *values), k('aa', bound, energy))),
        'radius_is_at_most_half_light': assertion('light mass bound level radius', op('y', k('sesy', *fields),
            op('u', k('aa', light, k('ad', number(2), radius))))),
        'light_boundary_has_no_finite_normalized_energy': assertion('light mass beta energy',
            op('u', k('serb', light, light, beta, mass, energy))),
        'one_fixed_radius_works_for_every_bound': assertion('', op('y', both(
            k('serb', *map(number, (5, 4, F(5, 3), 2, F(100, 3)))), k('aa', number(F(5, 2)), number(4))),
            k('aa', number(100), number(F(100, 3))))),
    }
    rows = {}
    for name, claim in claims.items():
        result = verify_universal(parse(base+claim), MEANINGS, timeout_ms=20000)[0]
        assert result['status'] == ('invalid' if name.startswith('one_fixed') else 'valid'), (name, result)
        rows[name] = result
    return rows


def physical_fixture(path, source=False, speed=6):
    declarations = ''.join('r jbound'+name+'[] '+sort+'.' for name, sort in PHYSICAL)
    if source:
        doc = parse(text(path)); doc['statements'] = []
        # Only specialize the universal speed in setb. Situation quantifiers
        # and the actual particle/frame/possibility relations remain intact.
        target = next(d for d in doc['declarations'] if d['name'] == 'setb'); replacements = []
        literal_doc = candidate(text(path), 'q['+k('ba', cut(speed))+'].')
        literal = literal_doc['statements'][0]['body']['arguments'][0]
        def replace(node, name, value):
            if isinstance(node, list): return [replace(x, name, value) for x in node]
            if not isinstance(node, dict): return node
            if node.get('kind') == 'variable' and node.get('name') == name: return deepcopy(value)
            return {a: replace(b, name, value) for a, b in node.items()}
        def specialize(node):
            if isinstance(node, list): return [specialize(x) for x in node]
            if not isinstance(node, dict): return node
            if node.get('kind') == 'forall' and node.get('sort') == {'kind': 'function', 'parameters': ['number'], 'result': 'truth'}:
                replacements.append(node)
                return replace(node['body'], node['variable'], literal)
            return {a: specialize(b) for a, b in node.items()}
        # Use the actual grammar's binder fields, verified below in tests.
        target['body'] = specialize(target['body'])
        assert len(replacements) == 1, replacements
        doc = candidate(format_graph(doc, 'compact'), declarations+'q[t[k setd[]][k jboundcontext[]]].')
    else:
        doc = candidate(text(path), declarations+'q['+k('seta', *[k('jbound'+n) for n, _ in PHYSICAL], cut(speed))+'].')
    return abstract(doc, OPS)


def physical_checks():
    rows = {}; independence = []
    cases = ['denied', 'allowed_alternative', 'unreachable_only', 'other_particle_only', 'other_frame_only', 'empty_accessible']
    for path, source in [(LIBRARY, False), (CORE, True), (SOURCE, True)]:
        doc = physical_fixture(path, source); results = {}
        for variant in cases:
            cuts, model = setup(doc); model.update(ARITHMETIC)
            for name, value in [('light', cuts.make(5)), ('particle', 'particle'), ('frame', 'frame'), ('context', 'actual')]:
                model['jbound'+name] = lambda value=value: value
            def accessible(origin, outcome):
                return variant != 'empty_accessible' and origin == 'actual' and outcome in ('actual', 'alternative')
            def attainable(particle, frame, speed, outcome):
                if cuts.read(speed) != 6: return False
                return (particle, frame, outcome) == {
                    'allowed_alternative': ('particle', 'frame', 'alternative'),
                    'unreachable_only': ('particle', 'frame', 'other'),
                    'other_particle_only': ('other', 'frame', 'alternative'),
                    'other_frame_only': ('particle', 'other', 'alternative'),
                }.get(variant)
            callbacks(doc, model, {'jboundaccessible': accessible, 'jboundattainable': attainable})
            for src, dest in [('tc', 'light'), ('zramatter', 'particle'), ('ra', 'frame'),
                              ('zrjaccessible', 'accessible'), ('zrjattainable', 'attainable')]:
                model[src] = model['jbound'+dest]
            actual = evaluate(doc, model)[0]
            assert actual == (variant not in ('allowed_alternative', 'empty_accessible')), (path, variant, actual)
            results[variant] = actual
            if source and variant == 'allowed_alternative':
                separate = abstract(candidate(format_graph(doc, 'compact'),
                    'q[t[k setc[]][k jboundcontext[]]].q[t[k setd[]][k jboundcontext[]]].'), {'sesv'})
                model['sesv'] = lambda *values: True
                model['zramu'] = lambda: cuts.make(2)
                pair = evaluate(separate, model); assert pair == [True, False]
                independence.append(dict(document=path, supplied_divergence_and_actual_possibility=pair))
        rows[path] = results
    return dict(single_speed_cases=rows, independence_models=independence,
                divergence_supplied_in_independence_models=True, full_speed_domain_checked=False)


def refusal_checks():
    for root in ('sesv', 'setb'):
        if root == 'sesv':
            doc = abstract(candidate(text(CORE), 'q['+k(root, cut(5), cut(2))+'].'), OPS)
        else:
            declarations = ''.join('r jbound'+name+'[] '+sort+'.' for name, sort in PHYSICAL)
            doc = abstract(candidate(text(CORE), declarations+'q['+k(root, *[k('jbound'+n) for n, _ in PHYSICAL])+'].'), OPS)
        cuts, model = setup(doc); model.update(ARITHMETIC)
        if root == 'setb':
            model.update(jboundlight=lambda: cuts.make(5), jboundparticle=lambda: 'particle', jboundframe=lambda: 'frame', jboundcontext=lambda: 'actual')
            callbacks(doc, model, {'jboundaccessible': lambda a, b: True, 'jboundattainable': lambda *x: False})
        try: evaluate(doc, model)
        except ValueError as exc: assert any(s in str(exc).lower() for s in ('domain', 'enumerat', 'quantif', 'function', 'rational')), str(exc)
        else: raise AssertionError('Infinite domain replaced by samples')
    return dict(all_bounds_and_speeds_refused=True)


def attribution_check():
    doc = parse(text(CORE)); model = guarded(doc); seen = []
    for name, value in {'zrjlimitnode': 'limit', 'zrjpossiblenode': 'possible', 'rd': 'author', 'zrjscope': 'scope', 'ri': 'actual'}.items():
        model[name] = lambda value=value: value
    def claim(node, author, content, scope, context):
        symbol = json.loads(content.syntax)['symbol']; seen.append(symbol)
        return (node, symbol) in [('limit', 'setc'), ('possible', 'setd')] and (author, scope, context) == ('author', 'scope', 'actual')
    model['uh'] = claim
    assert evaluate(doc, model) == [True, True]
    return dict(quoted_contents=seen, limits_or_physical_relations_executed=False)


def alignment():
    work = json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit = next(x for x in work['units'] if x['id'] == 'einstein-1905:u0263'); body = unit['text']
    ranges = [(0, body.index(' also')), (body.index('für '), body.index('. ')+1),
              (body.index('Überlichtgeschwindigkeiten'), body.index(' — ')),
              (body.index('keine Existenzmöglichkeit'), len(body))]
    common = dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='partial_left_divergence_and_scoped_physical_impossibility')
    rows = [dict(common, range=[a,b], text=body[a:b], definitions=['setc'] if i<2 else ['setd']) for i,(a,b) in enumerate(ranges)]
    rows += [dict(common, math_id=m, definitions=['sesv','setc']) for m in ('M0428','M0429')]
    return {'segments': rows}


def build_report():
    files = build()
    for p, body in files.items(): assert text(p) == body, p
    old = parse(text(PARENT)); current = parse(text(SOURCE))
    assert current['statements'][:-2] == old['statements'] and len(old['statements']) == 187
    assert current['declarations'][:len(old['declarations'])] == old['declarations']
    audits = {}
    for path in (SOURCE, LIBRARY, CORE):
        doc = parse(text(path)); basis = next(json.loads(x) for p,x in files.items() if p.endswith('.json') and json.loads(x)['document']==path)
        audits[path] = {k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            rendered=format_graph(doc,notation); assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==doc
        cli=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(cli.stdout)==doc
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-electron-power-law-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_energy_boundary.py','scripts/check_energy_boundary.py','tests/test_energy_boundary.py','docs/energy-boundary-v1.md',
        'scripts/compose_electron_power_law.py','scripts/compose_electron_axis_motion.py','scripts/compose_origin_clock.py',
        'scripts/compose_limits.py','scripts/compose_situated_criticism.py','scripts/check_coordinate_correspondence.py',
        'scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py',
        'scripts/check_tau_differential.py','scripts/check_angle_composition.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_boundary_divergence_separated_from_physical_impossibility',document=SOURCE,basis_audits=audits,
        numeric=numeric_checks(),polynomial=polynomial_checks(),physical=physical_checks(),refusal=refusal_checks(),attribution=attribution_check(),
        statements_preserved=187,new_author_attributions=2,roundtrips=True,cli_parse=True,alignment=alignment(),
        all_real_cut_limit_proved=False,physical_impossibility_derived_from_divergence=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Boundary witnesses and possibility scope checked; no infinite real or physical inference rule',flush=True)


if __name__=='__main__': main()
