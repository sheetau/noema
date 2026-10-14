"""Prove coordinate coherence from projections of actual Noema conditions.

This is a restricted logical proof, not a general higher-order Noema prover.
The solver receives weaker conjuncts/instances of the real premises. Validity
of cuts is left arbitrary; cut equality is justified separately by extensionality.
"""
import argparse
from copy import deepcopy
import hashlib
import json

import z3

from noema.discourse import normalize_document
from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.script import encode, decode
from scripts.compose_origin_clock import ROOT
from scripts.compose_density_time import FULL, PARENT, INDEX, TIME
from scripts.compose_material_velocity import AT, TRACK, valid, equalpoints
from scripts.compose_local_density import BOUND, ROLES
from scripts.compose_additive_charge import CLOCK, POINT
from scripts.compose_limits import call as k, v, both, op, quant
from scripts.compose_situated_criticism import args
from scripts.check_density_time import structural_checks as time_structure
from scripts.check_material_velocity import structural_checks as velocity_structure
from scripts.check_local_density import structural_checks as density_structure

REPORT = ROOT / 'reports/coordinate-witnesses-v1.json'
THEOREM = 'examples/v014/coordinate-witness-coherence.noema'
BASIS = 'data/coordinate-witness-coherence-basis-v1.json'
REVIEW = 'data/density-formula-review-v5.json'


def theorem_artifacts():
    source = parse((ROOT / FULL).read_text(encoding='utf-8'))
    doc = deepcopy(source)
    doc['statements'] = []
    premise = both(k('seoc', *args(AT)), k('seox', *args(TIME)), valid(v('target')),
        k('zpb', v('matter'), v('frame'), v('event'), v('target'), v('context')))
    claim = op('y', premise, equalpoints(v('target'), v('point')))
    parameters = AT + [('timeunit', 'a'), ('clock', CLOCK), ('target', POINT)]
    for name, sort in reversed(parameters):
        claim = quant('f', name, sort, claim)
    doc = parse(format_graph(doc, 'compact') + 's[' + claim + '].')
    selected = extract_document(doc)
    # This new statement is a derived theorem, not attributed to the source author.
    basis = json.loads((ROOT / 'data/einstein-density-time-basis-v1.json').read_text(encoding='utf-8'))
    basis = extract_basis(doc, basis, selected, version='coordinate-witness-coherence-basis-v1', document_path=THEOREM)
    basis['extraction_source'].pop('statement_indices')
    basis['extraction_source']['statement_origin'] = 'New derived theorem over source declarations; no source-author statement was selected.'
    basis['extraction_source']['metadata_policy'] = 'Meaning entries and caveats come from the source basis; only declarations are projected from the source document.'
    basis['derived_claim'] = dict(source_document=FULL, attributed_to_source_author=False,
        claim='Any valid same-event target shares all four coordinates with the material velocity witness under seoc and seox.',
        limits='Conditional coherence, not existence or physical truth; does not identify events or point function objects.')
    review = deepcopy(json.loads((ROOT / 'data/density-formula-review-v4.json').read_text(encoding='utf-8')))
    review.update(version='density-formula-review-v5', supersedes='data/density-formula-review-v4.json')
    review['checks'].insert(-1, dict(id='coordinate_witness_coherence', status='proved_conditionally_from_existing_premises',
        evidence='The actual seoc/seob/senz/seox conjuncts imply coordinate agreement for any valid same-event target. The density and source-case points have the required shared bindings.',
        limit='No premise existence, empirical truth, cross-frame equality, event identity, or complete source equivalence is certified.'))
    review['evidence_reports'].append('reports/coordinate-witnesses-v1.json')
    dump = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {THEOREM: format_graph(selected.document, 'compact') + '\n', BASIS: dump(basis), REVIEW: dump(review)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def flatten(node):
    return flatten(node['arguments'][0]) + flatten(node['arguments'][1]) if node.get('kind') == 'and' else [node]


class Logic:
    """Closed whitelist; unknown syntax or meanings are rejected."""
    def __init__(self, declarations, sorts, meanings, expandable):
        self.declarations = declarations
        self.sorts = sorts
        self.meanings = meanings
        self.expandable = set(expandable)
        self.serial = 0

    def sort(self, value):
        key = json.dumps(value, sort_keys=True)
        require(key in self.sorts, 'Unsupported quantifier sort')
        return self.sorts[key]

    def named(self, symbol, args):
        if symbol in self.meanings:
            return self.meanings[symbol](*args)
        require(symbol in self.expandable, 'Unsupported proof meaning: ' + symbol)
        declaration = self.declarations[symbol]
        require(declaration['kind'] == 'definition', 'Cannot unfold primitive')
        env = dict(zip((p['name'] for p in declaration['parameters']), args, strict=True))
        return self.expr(declaration['body'], env)

    def expr(self, node, env):
        kind = node['kind']
        if kind == 'variable':
            return env[node['name']]
        if kind == 'function_ref':
            return lambda *args: self.named(node['symbol'], args)
        if kind == 'call':
            return self.named(node['symbol'], [self.expr(a, env) for a in node['arguments']])
        if kind == 'apply':
            function = self.expr(node['function'], env)
            args = [self.expr(a, env) for a in node['arguments']]
            if callable(function):
                return function(*args)
            require(z3.is_array(function) and len(args) == 1, 'Unsupported function application')
            return z3.Select(function, args[0])
        if kind in ('forall', 'exists'):
            self.serial += 1
            variable = z3.Const('bound_' + str(self.serial), self.sort(node['sort']))
            body = self.expr(node['body'], env | {node['variable']: variable})
            return (z3.ForAll if kind == 'forall' else z3.Exists)([variable], body)
        if kind == 'not':
            return z3.Not(self.expr(node['arguments'][0], env))
        require(kind in ('and', 'or', 'implies', 'iff', 'equal'), 'Unsupported proof syntax: ' + kind)
        a, b = [self.expr(x, env) for x in node['arguments']]
        return {'and': z3.And, 'or': z3.Or, 'implies': z3.Implies,
            'iff': lambda x, y: x == y, 'equal': lambda x, y: x == y}[kind](a, b)


def solve(formula, *, timeout_ms=10000):
    solver = z3.Solver()
    solver.set(timeout=timeout_ms, random_seed=0)
    solver.add(formula)
    status = solver.check()
    require(status != z3.unknown, 'Solver unknown: ' + solver.reason_unknown())
    return solver, str(status)


def equality_lemma(doc):
    ds = {d['name']: d for d in doc['declarations']}
    # No ordering/arithmetic on the index domain is needed for mutual inclusion.
    index = z3.DeclareSort('CutMembershipIndex')
    cut = z3.ArraySort(index, z3.BoolSort())
    a, b = z3.Consts('left_cut right_cut', cut)
    logic = Logic(ds, {json.dumps('number'): index}, {}, {'sca', 'sag', 'bc'})
    relation = logic.named('sca', [a, b])
    _, status = solve(z3.Not(relation == (a == b)))
    require(status == 'unsat', 'Source cut equality is not extensional equality')
    return dict(status=status, meanings_expanded=['sca', 'sag', 'bc'],
        statement='mutual cut inclusion iff extensional function equality',
        rational_order_or_cut_validity_assumed=False)


def projected_conditions(doc):
    ds = {d['name']: d for d in doc['declarations']}
    # Source AST selectors are checked independently of the theorem body below.
    point_sort = ds['seoc']['parameters'][6]['sort']
    cut_sort = ds['senz']['parameters'][1]['sort']
    individual, scene, cut = [z3.DeclareSort(n) for n in ('Entity', 'Scene', 'CutValue')]
    point = z3.ArraySort(individual, cut)
    coordinate = lambda p, axis: z3.Select(p, axis)
    valid = z3.Function('valid_cut', cut, z3.BoolSort())
    observed = z3.Function('observed', individual, individual, individual, point, scene, z3.BoolSort())
    domain = z3.Function('trajectory_domain', cut, z3.BoolSort())
    curve = z3.Function('trajectory', cut, point)
    clock = z3.Function('clock', individual, individual, individual, scene, cut)
    axes = {name: z3.Const(name, individual) for name in ROLES}
    meanings = {'ba': valid, 'sca': lambda a, b: a == b, 'zpb': observed,
        **{name: (lambda value=value: value) for name, value in axes.items()}}
    logic = Logic(ds, {json.dumps(sort, sort_keys=True): target for sort, target in
        [('individual', individual), ('situation', scene), (point_sort, point), (cut_sort, cut)]}, meanings, {'seot'})
    # POINT is an extensional array over individuals, matching its function
    # type. The conclusion compares only the four physical coordinate indices.
    original_expr = logic.expr
    def expr(node, env):
        if node['kind'] == 'apply':
            function = expr(node['function'], env)
            if isinstance(function, z3.ExprRef) and function.sort() == point:
                arguments = [expr(a, env) for a in node['arguments']]
                require(len(arguments) == 1, 'Point application arity')
                return coordinate(function, arguments[0])
        return original_expr(node, env)
    logic.expr = expr
    matter, frame, event, timeunit = z3.Consts('matter frame event timeunit', individual)
    context = z3.Const('context', scene)
    velocity_point, target = z3.Consts('velocity_point target_point', point)
    values = dict(matter=matter, frame=frame, event=event, timeunit=timeunit, context=context,
        domain=domain, curve=curve, clock=clock, point=velocity_point,
        ux=z3.Const('ux', cut), uy=z3.Const('uy', cut), uz=z3.Const('uz', cut))
    environment = lambda symbol, fields, source: dict(zip(
        (p['name'] for p in ds[symbol]['parameters']), (source[n] for n, _ in fields), strict=True))
    velocity_env = environment('seoc', AT, values)
    parts = flatten(ds['seoc']['body'])
    require(parts[0].get('symbol') == 'seob' and parts[5].get('symbol') == 'senz' and parts[6].get('symbol') == 'zpb',
        'Velocity projection no longer matches source structure')
    # Check the actual seob arguments before projecting its reverse conjunct.
    require(parts[0]['arguments'] == [dict(kind='variable', name=ds['seoc']['parameters'][i]['name']) for i in range(5)],
        'Velocity history refers to different inputs')
    reverse = flatten(ds['seob']['body'])[-1]
    require(reverse['kind'] == 'forall' and reverse['body']['kind'] == 'forall', 'Missing universal reverse history')
    history_env = environment('seob', TRACK, values)
    history_env[reverse['variable']] = event
    reverse_point = reverse['body']
    # These two ground instances are consequences of the universal clause.
    history = [expr(reverse_point['body'], history_env | {reverse_point['variable']: p}) for p in (velocity_point, target)]
    interior_args = [expr(a, velocity_env) for a in parts[5]['arguments']]
    interior_env = dict(zip((p['name'] for p in ds['senz']['parameters']), interior_args, strict=True))
    interior = flatten(ds['senz']['body'])
    require(interior[0].get('symbol') == 'ba' and interior[1]['kind'] == 'apply', 'Missing time-domain membership')
    time_env = environment('seox', TIME, values)
    time = ds['seox']['body']
    universal = time['arguments'][1]
    require(time['kind'] == 'and' and universal['kind'] == 'forall', 'Missing universal clock agreement')
    times = [expr(universal['body'], time_env | {universal['variable']: p}) for p in (velocity_point, target)]
    target_env = velocity_env | {ds['seoc']['parameters'][6]['name']: target}
    conditions = {
        'valid_velocity_coordinates': z3.And(*(expr(p, velocity_env) for p in parts[1:5])),
        'observed_velocity_point': expr(parts[6], velocity_env),
        'velocity_time_in_domain': expr(interior[1], interior_env),
        'valid_target_coordinates': z3.And(*(expr(p, target_env) for p in parts[1:5])),
        'observed_target_point': expr(parts[6], target_env),
        'same_event_clock_instances': z3.And(*times),
        'reverse_history_instances': z3.And(*history),
    }
    conclusion = z3.And(*(coordinate(target, axes[a]) == coordinate(velocity_point, axes[a]) for a in ROLES))
    return conditions, conclusion, dict(velocity=velocity_point, target=target, coordinate=coordinate, axes=axes,
        domain=domain, clock=clock(frame, event, timeunit, context)), dict(
        seoc_conjunct_indices=[1, 2, 3, 4, 5, 6], senz_conjunct_indices=[1],
        seob_conjunct_index=2, seob_instances=['velocity point', 'arbitrary target point'],
        seox_instances=['velocity point', 'arbitrary target point'],
        omitted='Existence, forward history, neighborhood, derivatives and other conjuncts are dropped, never strengthened.')


def coherence_proof(doc):
    equality = equality_lemma(doc)
    assumptions, conclusion, terms, projection = projected_conditions(doc)
    _, status = solve(z3.And(*assumptions.values(), z3.Not(conclusion)))
    require(status == 'unsat', 'Coordinate agreement does not follow from actual projected premises')
    counterexamples = {}
    for missing in assumptions:
        solver, outcome = solve(z3.And(*(value for name, value in assumptions.items() if name != missing), z3.Not(conclusion)))
        require(outcome == 'sat', 'Expected a countermodel without ' + missing)
        model = solver.model()
        coordinates = {label: [str(model.eval(terms['coordinate'](terms[label], terms['axes'][a]), model_completion=True))
            for a in ROLES] for label in ('velocity', 'target')}
        counterexamples[missing] = dict(status=outcome, coordinates=coordinates)
    # Physical coordinates may coincide while the representations differ on
    # unused arguments. Do not turn coordinate agreement into object identity.
    _, distinct_status = solve(z3.And(*assumptions.values(), conclusion, terms['velocity'] != terms['target']))
    require(distinct_status == 'sat', 'Representation identity was accidentally required')
    return dict(status=status, cut_equality=equality, projection=projection,
        conclusion='all four coordinates of any valid same-event target agree with the velocity witness',
        counterexamples=counterexamples, distinct_representations_with_equal_coordinates=distinct_status,
        proof_scope='logical consequence under extensional function semantics, not existence of physical histories or source equivalence')


def source_bindings(doc, parent):
    time_structure(doc, parent)
    velocity_structure(doc)
    density_structure(doc)
    ds = {d['name']: d for d in doc['declarations']}
    # The local density witness reaches seok with the same center and event.
    local = ds['seol']
    first = flatten(local['body'])[0]
    require(first == dict(kind='call', symbol='seok', arguments=[dict(kind='variable', name=p['name']) for p in local['parameters'][:-1]]),
        'Density normalization changed the center binding')
    density = ds['seok']
    names = {n: p['name'] for (n, _), p in zip(BOUND, density['parameters'], strict=True)}
    variable = lambda n: dict(kind='variable', name=names[n])
    parts = flatten(density['body'])
    require(parts[:4] == [dict(kind='call', symbol='ba', arguments=[dict(kind='apply', function=variable('point'),
        arguments=[dict(kind='call', symbol=a, arguments=[])])]) for a in ROLES], 'Density center validity changed')
    require(parts[5] == dict(kind='call', symbol='zpb', arguments=[variable(n) for n in ('matter','frame','event','point','context')]),
        'Density center belongs to different referents')
    # The explicit source-case points use these same named referents in each frame.
    from scripts.compose_density_referents import BINDINGS
    source = ds['senu']
    refs = {n: dict(kind='variable', name=p['name']) for (n, _), p in zip(BINDINGS, source['parameters'], strict=True)}
    conjuncts = flatten(source['body'])
    for prefix, point in (('old', 'oldpoint'), ('new', 'point')):
        expected = dict(kind='call', symbol='zpb', arguments=[refs[n] for n in ('matter',prefix+'frame','event',point,'context')])
        require(expected in conjuncts, 'Source point uses different event or frame')
        require(all(dict(kind='call', symbol='ba', arguments=[dict(kind='apply', function=refs[point], arguments=[
            dict(kind='call', symbol=a, arguments=[])])]) in conjuncts for a in ROLES), 'Source point validity lost')
    return dict(density_center_same_tuple=True, source_points_same_tuple_in_each_frame=True,
        density_velocity_and_source_coordinates_cohere=True, cross_frame_coordinate_equality_claimed=False,
        event_or_representation_identity_inferred=False)


def build_report():
    doc = normalize_document(parse((ROOT / FULL).read_text(encoding='utf-8')))
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    outputs = theorem_artifacts()
    for name, body in outputs.items():
        require((ROOT / name).read_bytes() == body.encode('utf-8'), 'Stored theorem artifact differs: ' + name)
    theorem = parse(outputs[THEOREM])
    for notation in ('full', 'compact'):
        form = format_graph(theorem, notation)
        require(parse(form) == theorem and parse(decode(encode(form, 'v2'))) == theorem, 'Theorem roundtrip differs')
    result = dict(status='conditional_coordinate_witness_coherence_proved', source_document=FULL,
        source_statement_index=INDEX, source_bindings=source_bindings(doc, parent), proof=coherence_proof(doc),
        semantic_completion=False, new_definitions=0, new_primitives=0, new_author_statements=0,
        derived_statements=1, theorem_document=THEOREM, roundtrips=True,
        solver_version=z3.get_version_string(),
        limits=['No assertion that the physical premises hold.',
            'No equality of coordinates in different frames.',
            'No event identity or point-function identity inferred.',
            'No complete source-unit meaning certification.'])
    paths = [FULL, PARENT, *outputs, 'data/einstein-density-time-basis-v1.json',
        'data/density-formula-review-v4.json', 'scripts/check_coordinate_witnesses.py', 'tests/test_coordinate_witnesses.py',
        'scripts/check_density_time.py', 'scripts/check_material_velocity.py', 'scripts/check_local_density.py',
        'scripts/compose_density_referents.py', 'reports/density-time-v1.json']
    result['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args(argv)
    outputs = theorem_artifacts()
    for name, body in outputs.items():
        path = ROOT / name
        require(not path.exists() or path.read_bytes() == body.encode('utf-8'), 'Output differs: ' + name)
        require(not args.verify_only or path.exists(), 'Missing artifact: ' + name)
    if not args.verify_only:
        for name, body in outputs.items():
            path = ROOT / name
            if not path.exists():
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    result = build_report()
    if args.verify_only:
        require(json.loads(REPORT.read_text(encoding='utf-8')) == result, 'Stored witness proof differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Coordinate witness coherence proved from actual premise projections; source completion remains open')


if __name__ == '__main__':
    main()
