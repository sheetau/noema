from copy import deepcopy
import pytest
import z3
from noema.grammar import parse
from scripts import check_affine_field_witness as check


def test_all_twelve_partials_expand_the_actual_limit_definitions():
    report = check.derivative_checks()
    assert len(report['partials']) == 12
    assert {'sexw', 's5t', 'sjs', 'sjr', 'sjq', 'sjp', 'sjo'} <= set(report['executed_symbols'])
    assert not report['derivative_oracle_used']
    assert report['arbitrary_zero_reciprocal_irrelevant']
    assert not report['cut_representation_proved']


def test_wrong_derivative_and_invalid_limit_witnesses_are_not_certified():
    rows = check.derivative_checks()['refused_certificates']
    assert rows == dict(wrong_derivative='sat', zero_delta='sat', same_point_as_accumulation_witness='sat')


def test_nonlinear_field_mutation_does_not_inherit_affine_derivatives():
    doc = parse((check.ROOT/check.DOCUMENT).read_text(encoding='utf-8'))
    factory = next(d for d in doc['declarations'] if d['name'] == 'sexw')
    def change(node):
        if isinstance(node, dict):
            if node.get('kind') == 'call' and node.get('symbol') == 'shv':
                x = node['arguments'][1]
                node['arguments'][1] = dict(kind='call', symbol='shv', arguments=[deepcopy(x), deepcopy(x)])
                return True
            return any(change(x) for x in node.values())
        return isinstance(node, list) and any(change(x) for x in node)
    assert change(factory['body'])
    # Left-to-right traversal reaches the x term of the nested sum first.
    formula, _ = check.partial_formula(0, 0, doc=doc)
    assert check.solve(formula) == 'sat'


def test_numerical_condition_and_same_field_point_are_retained():
    result = check.connection_checks()
    assert result['actual_sent_unfolded'] and result['sens_preserved_with_same_arguments']
    assert result['same_field_region_point'] and result['all_three_diagonal_partials_match']
    assert not result['additional_field_equations_required']


def test_connection_check_detects_a_different_point_reference():
    doc = parse((check.ROOT/check.DOCUMENT).read_text(encoding='utf-8'))
    parameters, body = check.strip_prefix(doc['statements'][1]['body'])
    body['arguments'][1]['arguments'][-1] = dict(kind='variable', name=parameters[-2][0])
    with pytest.raises(ValueError, match='Different field/point/region'):
        check.connection_checks(doc)


def test_witness_substitution_is_not_applied_in_negative_positions():
    model, *_ = check.fixture()
    formula = model.named('sjq', [lambda x: z3.BoolVal(True), z3.Real('point')], positive=False)
    assert not model.instantiated and check.has_quantifier(formula)
    with pytest.raises(ValueError, match='Unresolved quantified'):
        check.solve(formula)


def test_full_quantifier_obligations_are_not_silently_counted_as_checked():
    formula, model = check.partial_formula(witnesses=False)
    assert not model.instantiated
    with pytest.raises(ValueError, match='Unresolved quantified'):
        check.solve(formula)


def test_undeclared_scalar_meanings_are_refused():
    model, *_ = check.fixture()
    with pytest.raises(ValueError, match='Unsupported scalar boundary'):
        model.named('unprovided', [])


def test_symbolic_coordinate_tables_are_total_functions():
    _, _, _, _, env, _, _ = check.fixture()
    table, offsets, point = env.values()
    outsider = z3.IntVal(99)
    assert z3.is_true(z3.simplify(table(outsider, outsider) == 0))
    assert z3.is_true(z3.simplify(offsets(outsider) == 0))
    assert z3.is_true(z3.simplify(point(outsider) == 0))
    assert z3.is_arith(table(z3.Int('arbitrary_role'), z3.IntVal(0)))


def test_unknown_solver_result_cannot_become_a_proof(monkeypatch):
    class Unfinished:
        def set(self, **kwargs): pass
        def add(self, *args): pass
        def check(self): return z3.unknown
        def reason_unknown(self): return 'simulated timeout'
    monkeypatch.setattr(z3, 'Solver', lambda: Unfinished())
    with pytest.raises(ValueError, match='Scalar proof unknown: simulated timeout'):
        check.solve(z3.BoolVal(True))
