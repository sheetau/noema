"""Expand actual derivative definitions in an explicit standard scalar model."""
from copy import deepcopy
from functools import lru_cache
import argparse
import hashlib
import json
import subprocess
import sys
import z3
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_affine_field_witness import ROOT, FULL, DOCUMENT, BASIS, REVIEW, ROLES, FORMULA, build

REPORT = ROOT/'reports/affine-field-witness-v1.json'


def flatten(node):
    return flatten(node['arguments'][0])+flatten(node['arguments'][1]) if node.get('kind') == 'and' else [node]


def strip_prefix(node):
    parameters = []
    while node['kind'] == 'forall':
        parameters.append((node['variable'], node['sort'])); node = node['body']
    return parameters, node


def require(condition, message):
    if not condition: raise ValueError(message)


class ScalarModel:
    """CUT is projected to R; no cut representation theorem is asserted."""
    EXPAND = {'sexw', 's5t', 'sjs', 'sjr', 'sjq', 'sjp', 'sjo', 'shn', 'shm', 'shx'}

    def __init__(self, doc, zero_reciprocal=0, *, witnesses=True, cluster_step=True, delta=1):
        self.declarations = {d['name']: d for d in doc['declarations']}
        self.cut = self.declarations['sjs']['parameters'][2]['sort']
        self.serial = 0; self.steps = 0; self.executed = set(); self.stack = []
        self.witnesses = witnesses; self.cluster_step = cluster_step; self.delta = delta
        self.instantiated = []; self.universal_symbols = []
        def collect(node, kind):
            if isinstance(node, list): return sum((collect(x, kind) for x in node), [])
            if not isinstance(node, dict): return []
            return ([node] if node.get('kind') == kind else [])+sum((collect(x, kind) for x in node.values()), [])
        self.existentials = {}
        for name in ('sjq', 'sjr'):
            nodes = collect(self.declarations[name]['body'], 'exists')
            require(len(nodes) == 1, 'Expected one explicit witness in '+name)
            self.existentials[name] = nodes[0]
        self.cluster_epsilon = self.declarations['sjq']['body']['arguments'][1]['variable']
        filler = zero_reciprocal if z3.is_arith(zero_reciprocal) else z3.RealVal(zero_reciprocal)
        self.meanings = {
            'ba': lambda x: z3.BoolVal(True), 'bb': lambda x: x,
            'bg': lambda x, y: x < y, 'bd': lambda x, y: x+y,
            'bf': lambda x, y: x-y, 'shv': lambda x, y: x*y,
            'sjt': lambda x: z3.If(x == 0, filler, 1/x),
            'szi': lambda condition, x, y: z3.If(condition, x, y),
        }
        for i, n in enumerate(ROLES): self.meanings[n] = lambda i=i: z3.IntVal(i)

    def named(self, name, args, positive=True):
        self.executed.add(name)
        if name in self.meanings: return z3.simplify(self.meanings[name](*args))
        require(name in self.EXPAND, 'Unsupported scalar boundary: '+name)
        d = self.declarations[name]; require(d['kind'] == 'definition', 'Expected a saved definition')
        self.stack.append(name)
        try: return self.expr(d['body'], {p['name']: a for p, a in zip(d['parameters'], args, strict=True)}, positive)
        finally: self.stack.pop()

    def expr(self, node, env, positive=True):
        self.steps += 1; require(self.steps <= 100000, 'Scalar expansion budget exceeded')
        kind = node['kind']
        if kind == 'variable': return env[node['name']]
        if kind == 'number': return z3.RealVal(str(node['numerator'])+'/'+str(node['denominator']))
        if kind == 'call': return self.named(node['symbol'], [self.expr(a, env, None) for a in node['arguments']], positive)
        if kind == 'function_ref': return lambda *args: self.named(node['symbol'], args, None)
        if kind == 'lambda':
            return lambda *args: self.expr(node['body'], env | {p['name']: a for p, a in zip(node['parameters'], args, strict=True)}, None)
        if kind == 'apply': return self.expr(node['function'], env)(*[self.expr(a, env) for a in node['arguments']])
        if kind == 'sequence': return [self.expr(x, env) for x in node['items']]
        if kind == 'length': return z3.RealVal(len(self.expr(node['sequence'], env)))
        if kind == 'fold':
            state = self.expr(node['initial'], env); step = self.expr(node['step'], env)
            for item in self.expr(node['sequence'], env): state = step(state, item)
            return state
        if kind in ('forall', 'exists'):
            require(node['sort'] == self.cut or node['sort'] == 'individual', 'Unsupported scalar quantifier sort')
            self.serial += 1
            var = z3.Const('bound_'+str(self.serial), z3.RealSort() if node['sort'] == self.cut else z3.IntSort())
            if self.witnesses and positive is True:
                if kind == 'exists':
                    owner = self.stack[-1]
                    require(owner in self.existentials and node is self.existentials[owner], 'Unknown existential witness')
                    if owner == 'sjq':
                        point = env[self.declarations[owner]['parameters'][1]['name']]
                        var = point+(env[self.cluster_epsilon]/2 if self.cluster_step else 0)
                    else: var = z3.RealVal(self.delta)
                    self.instantiated.append(owner)
                else: self.universal_symbols.append(str(var))
                # Positive existential substitution strengthens the claim. Fresh
                # arbitrary symbols retain the universal obligation over R/Int;
                # these are not finite sample values.
                return self.expr(node['body'], env | {node['variable']: var}, positive)
            body = self.expr(node['body'], env | {node['variable']: var}, positive)
            return z3.simplify((z3.ForAll if kind == 'forall' else z3.Exists)([var], body))
        require(kind in ('and', 'or', 'not', 'implies', 'iff', 'equal'), 'Unsupported scalar syntax: '+kind)
        polarities = [positive]*len(node['arguments'])
        if kind in ('not', 'implies'): polarities[0] = None if positive is None else not positive
        if kind in ('iff', 'equal'): polarities = [None]*len(node['arguments'])
        values = [self.expr(a, env, p) for a, p in zip(node['arguments'], polarities, strict=True)]
        return z3.simplify({'and': lambda: z3.And(*values), 'or': lambda: z3.Or(*values),
            'not': lambda: z3.Not(values[0]), 'implies': lambda: z3.Implies(*values),
            'iff': lambda: values[0] == values[1], 'equal': lambda: values[0] == values[1]}[kind]())


def fixture(doc=None, zero_reciprocal=0, **options):
    doc = doc or parse((ROOT/DOCUMENT).read_text(encoding='utf-8'))
    model = ScalarModel(doc, zero_reciprocal, **options)
    coefficient = {(i, j): z3.Real('coefficient_'+str(i)+'_'+str(j)) for i in range(3) for j in range(4)}
    offsets = [z3.Real('offset_'+str(i)) for i in range(3)]
    coordinates = [z3.Real('coordinate_'+str(i)) for i in range(4)]
    # Total functions, with arbitrary symbolic values at all observed roles.
    # Unobserved roles may be extended by zero; no derivative clause reads them.
    def select(entries, indices):
        value = z3.RealVal(0)
        for keys, item in reversed(list(entries.items())):
            value = z3.If(z3.And(*(index == key for index, key in zip(indices, keys, strict=True))), item, value)
        return z3.simplify(value)
    table = lambda i, j: select(coefficient, (i, j))
    constant = lambda i: select({(j,): x for j, x in enumerate(offsets)}, (i,))
    point = lambda i: select({(j,): x for j, x in enumerate(coordinates)}, (i,))
    parameters, body = strip_prefix(doc['statements'][0]['body'])
    require(len(parameters) == 3 and body['kind'] == 'implies', 'Expected affine derivative theorem')
    clauses = flatten(body['arguments'][1])
    require(len(clauses) == 12 and all(c['kind'] == 'call' and c['symbol'] == 's5t' for c in clauses), 'Expected all twelve partials')
    env = dict(zip((n for n, _ in parameters), (table, constant, point), strict=True))
    return model, coefficient, offsets, coordinates, env, clauses, body


def partial_formula(component=0, axis=0, *, doc=None, zero_reciprocal=0, wrong_value=False, **options):
    model, coefficient, offsets, coordinates, env, clauses, body = fixture(doc, zero_reciprocal, **options)
    clause = deepcopy(clauses[component*4+axis])
    if wrong_value:
        clause['arguments'][-1] = dict(kind='call', symbol='bd', arguments=[clause['arguments'][-1],
            dict(kind='call', symbol='bb', arguments=[dict(kind='number', numerator=1, denominator=1)])])
    formula = model.expr(clause, env)
    return formula, model


def has_quantifier(formula):
    return z3.is_quantifier(formula) or any(has_quantifier(c) for c in formula.children())


def solve(formula):
    require(not has_quantifier(formula), 'Unresolved quantified scalar obligation')
    solver = z3.Solver(); solver.set(timeout=10000); solver.add(z3.Not(formula))
    status = solver.check()
    require(status != z3.unknown, 'Scalar proof unknown: '+solver.reason_unknown())
    return str(status)


@lru_cache(None)
def derivative_checks():
    rows = {}; used = set()
    for component in range(3):
        for axis in range(4):
            formula, model = partial_formula(component, axis, zero_reciprocal=z3.Real('arbitrary_zero_reciprocal'))
            result = solve(formula); require(result == 'unsat', 'Affine derivative witness failed')
            require(model.instantiated == ['sjq', 'sjr'], 'Accumulation and limit witnesses missing')
            used.update(model.executed)
            rows[ROLES[component]+':'+ROLES[axis]] = dict(counterexample_status=result,
                accumulation_witness='point + epsilon / 2', limit_radius='1', universal_symbols=model.universal_symbols)
    variants = {}
    for label, options in [('wrong_derivative', {'wrong_value': True}), ('zero_delta', {'delta': 0}),
        ('same_point_as_accumulation_witness', {'cluster_step': False})]:
        formula, _ = partial_formula(**options); result = solve(formula)
        require(result == 'sat', 'Wrong derivative certificate was accepted: '+label); variants[label] = result
    return dict(partials=rows, refused_certificates=variants, executed_symbols=sorted(used),
        derivative_oracle_used=False, scalar_interpretation_only=True, cut_representation_proved=False,
        arbitrary_zero_reciprocal_irrelevant=True)


def connection_checks(doc=None):
    doc = doc or parse((ROOT/DOCUMENT).read_text(encoding='utf-8'))
    first_params, first = strip_prefix(doc['statements'][0]['body'])
    second_params, second = strip_prefix(doc['statements'][1]['body'])
    labels = [n for n, _ in FORMULA if n != 'newelectricjet']+['coefficients', 'offsets', 'point']
    def rename(node, mapping):
        if isinstance(node, list): return [rename(n, mapping) for n in node]
        if not isinstance(node, dict): return node
        if node.get('kind') == 'variable' and node['name'] in mapping: return deepcopy(mapping[node['name']])
        return {k: rename(v, mapping) for k, v in node.items()}
    variable = lambda n: dict(kind='variable', name=n)
    # Only the quantified parameter names change; local lambda binders are
    # retained and normalized below when comparing complete temporary bodies.
    first = rename(first, {n: variable(label) for (n, _), label in zip(first_params, ['coefficients', 'offsets', 'point'], strict=True)})
    second = rename(second, {n: variable(label) for (n, _), label in zip(second_params, labels, strict=True)})
    require(second['kind'] == 'implies' and second['arguments'][0]['kind'] == 'and', 'Expected conditional connection')
    validity, numeric = second['arguments'][0]['arguments']
    require(validity == first['arguments'][0], 'Coordinate/field validity changed')
    conclusion = second['arguments'][1]
    require(conclusion['kind'] == 'call' and conclusion['symbol'] == 'sent', 'Expected the actual sent condition')
    sent = next(d for d in doc['declarations'] if d['name'] == 'sent')
    expanded = rename(sent['body'], {p['name']: a for p, a in zip(sent['parameters'], conclusion['arguments'], strict=True)})
    clauses = flatten(expanded)
    require(clauses[0] == numeric and numeric['symbol'] == 'sens', 'Numerical condition or shared table changed')
    # Alpha-normalize local slice lambdas by parsing closed helper assertions.
    def canonical(node):
        from noema.discourse import normalize_document
        declarations = deepcopy(doc['declarations'])
        for n, (_, sort) in zip(labels, second_params, strict=True):
            node = dict(kind='forall', variable=n, sort=sort, body=node)
        return normalize_document(dict(schema_version='0.14', lexicon_version='0.14', declarations=declarations,
            statements=[dict(kind='assert', body=node)]))['statements'][0]
    diagonal = [flatten(first['arguments'][1])[i*4+i] for i in range(3)]
    require([canonical(x) for x in clauses[1:]] == [canonical(x) for x in diagonal], 'Different field/point/region in the diagonal connection')
    return dict(actual_sent_unfolded=True, sens_preserved_with_same_arguments=True,
        same_field_region_point=True, all_three_diagonal_partials_match=True,
        additional_field_equations_required=False)


def build_report():
    files = build()
    for p, body in files.items(): require((ROOT/p).read_text(encoding='utf-8') == body, 'Stored artifact differs: '+p)
    doc = parse(files[DOCUMENT]); full = parse((ROOT/FULL).read_text(encoding='utf-8'))
    old = {d['name']: d for d in full['declarations']}
    require(all(d == old[d['name']] for d in doc['declarations'] if d['name'] != 'sexw'), 'Historical declaration changed')
    audit = audit_basis(doc, json.loads(files[BASIS])); audit.pop('definition_dependencies')
    for notation in ('full', 'compact'):
        formatted = format_graph(doc, notation)
        require(parse(formatted) == parse(transcribe(formatted, alphabet='v2')) == doc, 'Roundtrip changed')
    cli = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'noema', 'parse', '-i', str(ROOT/DOCUMENT)],
        check=True, capture_output=True, encoding='utf-8')
    require(json.loads(cli.stdout) == doc, 'CLI parse changed')
    source = json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'einstein-1905:u0236')
    math = next(m for m in source['math'] if m['id'] == 'M0390')
    paths = set(files) | {FULL, 'data/einstein-density-origins-basis-v1.json', 'data/density-formula-review-v12.json',
        'artifacts/written-units-v1/einstein-1905.json', 'docs/affine-field-witness-v1.md',
        'scripts/compose_affine_field_witness.py', 'scripts/check_affine_field_witness.py',
        'scripts/compose_field_equations.py', 'scripts/compose_density_formula.py', 'scripts/compose_limits.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_situated_criticism.py', 'tests/test_affine_field_witness.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar', 'language', 'discourse', 'semantics', 'meaning_basis', 'extraction', 'script'))
    return dict(status='affine_field_derivatives_in_explicit_scalar_interpretation', document=DOCUMENT, source_document=FULL,
        audit=audit, derivatives=derivative_checks(), connection=connection_checks(),
        scalar_boundaries=['ba', 'bb', 'bg', 'bd', 'bf', 'shv', 'sjt', 'szi', *ROLES],
        new_primitives=0, new_definitions=1, derived_statements=2, new_author_statements=0,
        roundtrips=True, cli_parse=True, solver_version=z3.get_version_string(),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        alignment=dict(segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'], math_id='M0390', math_sha256=math['sha256'],
            status='partial_scalar_affine_field_witness', definitions=['sexw', 's5t', 'sjs', 'sent'])]),
        source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli = argparse.ArgumentParser(); cli.add_argument('--verify-only', action='store_true'); options = cli.parse_args()
    report = build_report()
    if options.verify_only: require(json.loads(REPORT.read_text(encoding='utf-8')) == report, 'Stored report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('Actual derivative definitions checked for constructed affine fields in the scalar model')


if __name__ == '__main__': main()
