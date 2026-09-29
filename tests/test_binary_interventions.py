import json

from noema.finite_semantics import FunctionValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.check_binary_interventions import ROOT, LIBRARY, STATE, exhaustive_checks, named_checks, ordered_checks


def test_every_two_variable_boolean_model_and_single_intervention():
    result = exhaustive_checks()
    assert result['binary_models'] == 256
    assert result['intervention_cases'] == 1024
    assert result['all_solution_sets_and_six_properties_match']


def test_no_solution_and_multiple_solutions_are_not_guarantees():
    cases = named_checks()['cases']
    assert cases['positive']['positive']
    assert cases['negative']['negative']
    assert cases['unchanged_true']['unchanged']
    assert cases['multiple_solutions']['possible']
    assert not cases['multiple_solutions']['guaranteed']
    assert not cases['multiple_solutions']['unique']
    assert not any(cases['no_solution'].values())
    for background in ('true', 'false'):
        assert cases['direct_background_' + background]['positive']
        assert cases['common_cause_background_' + background]['unchanged']
        assert not cases['common_cause_background_' + background]['positive']


def test_ordered_progress_is_not_limited_to_goal_attainment():
    cases = ordered_checks()
    assert cases['progress_one_to_two']['actual'] == [True, False, True]
    assert cases['possible_improvement_not_guaranteed']['actual'] == [False, False, True]


def test_intervention_replaces_equations_instead_of_adding_observations():
    doc = parse(LIBRARY.read_text(encoding='utf-8') + '''
r ta[] h[a h[a] c] c.r tb[] h[a] c.r tc[] h[a] c.
q[k sb[k ta[] k tb[] k tc[]]].
q[k sd[k ta[] k tb[] k tc[] i[state h[a] c][f x a[c[v state][v x]]]]].
''')
    # Every original equation x = not x is inconsistent. Intervening on all
    # variables replaces these equations and produces the all-true state.
    def check(mask):
        return evaluate_document(doc, individuals=('x', 'y'), situations=('context',), primitives={
            'ta': lambda: FunctionValue(('individual', STATE), 'truth', lambda x, s: not s(x)),
            'tb': lambda: FunctionValue(('individual',), 'truth', mask),
            'tc': lambda: FunctionValue(('individual',), 'truth', lambda x: True)})
    assert [r['value'] for r in check(lambda x: False)] == [False, False]
    assert [r['value'] for r in check(lambda x: True)] == [True, True]
    assert [r['value'] for r in check(lambda x: x == 'x')] == [False, False]


def test_causal_library_uses_definitions_without_new_primitives_or_grammar():
    text = LIBRARY.read_text(encoding='utf-8')
    doc = parse(text)
    basis = json.loads((ROOT / 'data/binary-interventions-basis-v1.json').read_text(encoding='utf-8'))
    audit = audit_basis(doc, basis)
    assert audit['primitive_count'] == 0
    assert audit['definition_count'] == 14
    assert all(not p for p in audit['definition_dependencies']['definition_primitive_dependencies'].values())
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')
