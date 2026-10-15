"""Check signed substitution using exact, explicitly registered polynomials."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import subprocess
import sys

from noema.grammar import parse, format_graph
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_integral_substitution import ROOT, PARENT, LIBRARY, BASIS, CUT, SCALAR, build
from scripts.compose_limits import call as k
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup, OPS
from scripts.check_rod_setup import callbacks
from scripts.check_quantities import ARITHMETIC
from scripts.check_phi_normalization import number
from scripts.check_material_acceleration import trim, derivative, poly_value, unwrap, free

REPORT = ROOT/'reports/integral-substitution-v1.json'


def add(a, b):
    return trim((a[i] if i < len(a) else 0)+(b[i] if i < len(b) else 0) for i in range(max(len(a), len(b))))


def multiply(a, b):
    out = [F(0)]*max(0, len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b): out[i+j] += x*y
    return trim(out)


def compose(a, b):
    out = ()
    for coefficient in reversed(a): out = add(multiply(out, b), (coefficient,))
    return out


def primitive(poly): return (F(0),)+tuple(a/F(i+1) for i, a in enumerate(poly))


def integral(poly, lower, upper):
    antiderivative = primitive(poly)
    return poly_value(antiderivative, upper)-poly_value(antiderivative, lower)


def text(): return (ROOT/LIBRARY).read_text(encoding='utf-8')


def evaluate(doc, model):
    names = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return [row['value'] for row in evaluate_document(doc, individuals=('object',), situations=('actual',),
        primitives={n: model[n] for n in names}, max_steps=2_000_000)]


class PolynomialIntegrals:
    """Interpret only retained callbacks and the lambda arithmetic actually read.

    Unknown callbacks are never sampled. This is an analytical test model for
    sede/sjs, not a proof of their all-cut definitions.
    """
    def __init__(self, doc):
        self.doc = doc
        self.cuts, self.model = setup(doc)
        self.model.update(ARITHMETIC)
        self.registered = {}
        self.model['sede'] = self.positive_integral
        self.model['sjs'] = self.differentiate

    def register(self, symbol, polynomial):
        polynomial = trim(polynomial)
        def function(x): return self.cuts.make(poly_value(polynomial, self.cuts.read(x)))
        self.registered[function] = polynomial
        callbacks(self.doc, self.model, {symbol: function})

    def polynomial(self, function):
        function = unwrap(function)
        if function.implementation in self.registered: return self.registered[function.implementation]
        closure = free(function)
        node, captured = closure.get('node'), closure.get('captured')
        if node and captured is not None and len(node.get('parameters', [])) == 1:
            variable = node['parameters'][0]['name']
            return self.expression(node['body'], captured, variable)
        raise ValueError('Unregistered analytical integrand')

    def expression(self, node, captured, variable):
        kind = node.get('kind')
        if kind == 'variable':
            if node['name'] == variable: return (F(0), F(1))
            return trim((self.cuts.read(captured[node['name']]),))
        if kind == 'apply' and len(node['arguments']) == 1:
            ref = node['function']
            if ref.get('kind') != 'variable' or ref['name'] not in captured:
                raise ValueError('Unregistered function reference')
            return compose(self.polynomial(captured[ref['name']]), self.expression(node['arguments'][0], captured, variable))
        if kind == 'call' and node.get('symbol') in ('shv', 'bd', 'bf') and len(node['arguments']) == 2:
            left, right = [self.expression(n, captured, variable) for n in node['arguments']]
            if node['symbol'] == 'shv': return multiply(left, right)
            return add(left, tuple(-x for x in right) if node['symbol'] == 'bf' else right)
        raise ValueError('Unregistered polynomial expression')

    def positive_integral(self, lower, upper, function, value):
        lo, hi = self.cuts.read(lower), self.cuts.read(upper)
        return lo < hi and integral(self.polynomial(function), lo, hi) == self.cuts.read(value)

    def differentiate(self, domain, function, time, value):
        # The derivative is computed symbolically. The domain is evaluated only
        # for this local query, not used to certify interval coverage.
        return domain(time) and poly_value(derivative(self.polynomial(function)), self.cuts.read(time)) == self.cuts.read(value)


CASES = {
    'increasing': ((0, 0, 1), (0, 2), (0, 3), 0, 1, F(3, 2), True),
    'decreasing': ((2, -1), (-1,), (0, 3), 0, 1, F(-9, 2), True),
    'constant': ((2,), (), (0, 3), 0, 1, F(0), True),
    'folded_same_endpoints': ((0, 1, -1), (1, -2), (1, 2), 0, 1, F(0), True),
    'folded_different_endpoints': ((0, 1, -1), (1, -2), (1, 2), 0, F(3, 4), F(57, 256), True),
    'cubic_composition': ((0, 1, 0, 1), (1, 0, 3), (0, 0, 3), 0, 1, F(8), True),
    'wrong_reverse_sign': ((2, -1), (-1,), (0, 3), 0, 1, F(9, 2), False),
    'absolute_derivative_is_wrong': ((2, -1), (1,), (0, 3), 0, 1, F(-9, 2), False),
    'wrong_derivative': ((0, 0, 1), (0, 3), (0, 3), 0, 1, F(3, 2), False),
    # The perturbation t(t-1/2)(t-1) vanishes at three common probes and
    # integrates to zero. Matching endpoint integrals do not certify g'=rate.
    'wrong_rate_same_integral': ((0, 0, 1), (0, F(5, 2), F(-3, 2), 1), (1,), 0, 1, F(1), True),
    'zero_bounds_nonzero_value': ((2,), (), (0, 3), 0, 1, F(1), False),
}


def fixture(query, abstract_integrals=True):
    declarations = ''.join('r jsub'+n+'[] '+SCALAR+'.' for n in ('transform', 'rate', 'integrand'))
    doc = candidate(text(), declarations+query)
    return abstract(doc, OPS | ({'sede', 'sjs'} if abstract_integrals else set()))


def arguments(lo, hi, rlo=-10, rhi=10):
    return [k('bb', number(x)) for x in (lo, hi, rlo, rhi)]+[k('jsub'+n) for n in ('transform', 'rate', 'integrand')]


def substitution_checks():
    rows = {}
    for name, (g, rate, f, lo, hi, value, expected) in CASES.items():
        query = 'q['+k('sesm', *arguments(lo, hi), k('bb', number(value)))+'].'
        doc = fixture(query); model = PolynomialIntegrals(doc)
        for symbol, poly in zip(('transform', 'rate', 'integrand'), (g, rate, f)): model.register('jsub'+symbol, poly)
        actual = evaluate(doc, model.model)[0]
        assert actual == expected, (name, actual)
        # Coefficient identity covers the whole polynomial, not a sample grid.
        transformed = multiply(compose(trim(f), trim(g)), trim(rate))
        potential = compose(primitive(trim(f)), trim(g))
        identity = derivative(potential) == transformed
        if name not in ('absolute_derivative_is_wrong', 'wrong_derivative', 'wrong_rate_same_integral'): assert identity, name
        else: assert not identity, name
        rows[name] = dict(joint_integrals=actual, polynomial_chain_identity=identity,
            transformed_coefficients=list(map(str, transformed)),
            spatial_integral=str(integral(trim(f), poly_value(g, F(lo)), poly_value(g, F(hi)))),
            time_integral=str(integral(transformed, F(lo), F(hi))))
    return rows


def local_checks():
    rows = {}
    # Wrong range and wrong derivative are visible in the actual local Noema
    # condition. The polynomial has an interior excursion despite equal ends.
    cases = [('baseline', (0, 1, -1), (1, -2), 1, F(1, 2), True),
             ('range_misses_interior', (0, 1, -1), (1, -2), F(1, 8), F(1, 2), False),
             ('wrong_rate', (0, 1, -1), (1,), 1, F(1, 2), False),
             ('stopped', (0,), (), 1, F(1, 2), True),
             ('alias_at_midpoint', (0, 0, 1), (0, F(5, 2), F(-3, 2), 1), 1, F(1, 2), True),
             ('alias_at_quarter', (0, 0, 1), (0, F(5, 2), F(-3, 2), 1), 1, F(1, 4), False)]
    for name, g, rate, upper, time, expected in cases:
        doc = fixture('q['+k('sesj', *arguments(0, 1, 0, upper), k('bb', number(time)))+'].')
        model = PolynomialIntegrals(doc)
        for symbol, poly in zip(('transform', 'rate', 'integrand'), (g, rate, (1,))): model.register('jsub'+symbol, poly)
        actual = evaluate(doc, model.model)[0]; assert actual == expected, name
        rows[name] = actual
    return rows


def refusal_checks():
    doc = fixture('q['+k('sesm', *arguments(0, 1), k('bb', number(F(3, 2))))+'].')
    model = PolynomialIntegrals(doc)
    model.register('jsubtransform', (0, 0, 1)); model.register('jsubrate', (0, 2))
    called = []
    def unknown(x):
        called.append(x)
        return model.cuts.make(0)
    callbacks(doc, model.model, {'jsubintegrand': unknown})
    try: evaluate(doc, model.model)
    except ValueError as exc: assert 'Unregistered' in str(exc)
    else: raise AssertionError('Unknown function was fitted')
    assert not called
    for root in ('sesk', 'sesn', 'sesm'):
        inputs = arguments(0, 1)+([k('bb', number(F(3, 2)))] if root == 'sesm' else [])
        doc = fixture('q['+k(root, *inputs)+'].', abstract_integrals=root != 'sesm')
        model = PolynomialIntegrals(doc)
        for symbol, poly in zip(('transform', 'rate', 'integrand'), ((0, 0, 1), (0, 2), (0, 3))): model.register('jsub'+symbol, poly)
        try: evaluate(doc, model.model)
        except ValueError as exc: assert any(s in str(exc).lower() for s in ('domain', 'enumerat', 'function', 'quantif', 'rational'))
        else: raise AssertionError('All-cut condition decided by finite samples')
    return dict(unknown_function_refused_without_sampling=True, all_cut_regularity_and_theorem_refused=True,
                all_partition_integral_refused=True)


def structure_checks():
    doc = parse(text()); old = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lookup = {d['name']: d for d in doc['declarations']}
    for d in old['declarations']:
        if d['name'] in lookup: assert lookup[d['name']] == d, d['name']
    assert not doc['statements']
    def calls(node, symbol):
        if isinstance(node, list): return sum((calls(x, symbol) for x in node), [])
        if not isinstance(node, dict): return []
        return ([node] if node.get('kind') == 'call' and node.get('symbol') == symbol else [])+sum((calls(x, symbol) for x in node.values()), [])
    source = lookup['sesq']['body']
    regular = calls(source, 'seso')[0]['arguments']; claim = calls(source, 'sesp')[0]['arguments']
    assert regular == claim
    fixed = [x['symbol'] for x in regular[:17] if x.get('kind') == 'call']
    assert fixed == ['zramatter', 'ra', 'zrhdomain', 'zrhcurve', 'zrgstart', 'zraevent',
                     'zrhstartpoint', 'zrhendpoint', 'zrgposition', 'zb7', 'zrivelocity',
                     'zriacceleration', 'zrgprofile', 'tc', 'zramu', 'zrgcharge']
    for symbol in ('seso', 'sesp'):
        definitions = calls(lookup[symbol]['body'], 'sere')
        mass = lookup[symbol]['parameters'][15]['name']
        assert definitions and all(x['arguments'][1] == dict(kind='variable', name=mass) for x in definitions)
    assert len(calls(lookup['sesp']['body'], 'sesn')) == 2
    assert not any(calls(lookup[n]['body'], s) for n in ('sesl', 'seso', 'sesp') for s in ('sjt', 'sjd', 'cd'))
    return dict(parent_definitions_unchanged=True, source_references_shared=True,
        two_substitutions=True, no_division_by_speed=True, new_author_attributions=0)


def build_report():
    for path, body in build().items(): assert (ROOT/path).read_text(encoding='utf-8') == body, path
    doc = parse(text()); basis = json.loads((ROOT/BASIS).read_text(encoding='utf-8'))
    audit = audit_basis(doc, basis)
    for notation in ('full', 'compact'):
        rendered = format_graph(doc, notation)
        assert parse(rendered) == parse(transcribe(rendered, alphabet='v2')) == doc
    cli = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'noema', 'parse', '-i', str(ROOT/LIBRARY)],
        check=True, capture_output=True, encoding='utf-8')
    assert json.loads(cli.stdout) == doc
    paths = [PARENT, LIBRARY, BASIS, 'data/einstein-electron-power-law-basis-v1.json',
        'scripts/compose_integral_substitution.py', 'scripts/check_integral_substitution.py',
        'tests/test_integral_substitution.py', 'docs/integral-substitution-v1.md',
        'scripts/compose_electron_power_law.py', 'scripts/compose_electron_axis_motion.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/check_material_acceleration.py', 'scripts/check_coordinate_correspondence.py',
        'scripts/check_described_appraisals.py', 'scripts/check_plane_waveforms.py',
        'scripts/check_rod_setup.py', 'scripts/check_quantities.py', 'scripts/check_phi_normalization.py',
        'scripts/check_tau_differential.py', 'scripts/check_angle_composition.py']
    paths += ['noema/'+n+'.py' for n in ('grammar', 'language', 'discourse', 'semantics', 'finite_semantics', 'extraction', 'meaning_basis', 'script')]
    return dict(status='oriented_substitution_statement_and_registered_polynomial_checks', document=LIBRARY,
        basis_audit={k: v for k, v in audit.items() if k != 'definition_dependencies'},
        substitution=substitution_checks(), local=local_checks(), refusal=refusal_checks(), structure=structure_checks(),
        roundtrips=True, cli_parse=True, all_cut_theorem_proved=False, source_coverage_added=False,
        source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli = argparse.ArgumentParser(); cli.add_argument('--verify-only', action='store_true'); options = cli.parse_args()
    report = build_report()
    if options.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8')) == report
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: stream.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('Oriented substitution checked on registered polynomials; all-cut theorem remains unproved', flush=True)


if __name__ == '__main__': main()
