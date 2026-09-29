import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse


DOCUMENT = '''n:r aa[a d] c.r ab[] a.r ac[] d.
d ba[person a] e[b scene[k aa[v person v scene]]].
q[t[k ba[k ab[]]][k ac[]]].q[t[k ba[k ab[]]][k ac[]]].'''


def run_content(value, memoize):
    calls = []
    def fact(person, scene):
        calls.append((person, scene))  # Count work; does not affect the returned interpretation.
        return value
    rows = evaluate_document(parse(DOCUMENT), individuals=('person',), situations=('first', 'second'),
        primitives={'aa': fact, 'ab': lambda: 'person', 'ac': lambda: 'first'}, memoize_definitions=memoize)
    return rows, calls


def test_memoized_content_keeps_values_and_reuses_the_whole_situation_profile():
    ordinary, ordinary_calls = run_content(True, False)
    cached, cached_calls = run_content(True, True)
    assert ordinary == cached == [{'kind': 'ask', 'value': True}] * 2
    assert len(ordinary_calls) == 4 and cached_calls == [('person', 'first'), ('person', 'second')]


def test_definition_cache_never_crosses_interpretations():
    assert all(row['value'] for row in run_content(True, True)[0])
    assert all(not row['value'] for row in run_content(False, True)[0])


def test_higher_order_definition_arguments_keep_ordinary_evaluation():
    doc = parse('n:r aa[a] c.r ab[] a.d ba[fn h[a] c] c[c[v fn][k ab[]]].q[k ba[p aa]].q[k ba[p aa]].')
    calls = []
    def fact(person):
        calls.append(person)
        return True
    result = evaluate_document(doc, individuals=('person',), situations=('text',),
        primitives={'aa': fact, 'ab': lambda: 'person'}, memoize_definitions=True)
    assert result == [{'kind': 'ask', 'value': True}] * 2 and calls == ['person', 'person']


def test_memoization_keeps_type_validation_budget_and_strict_option_checks():
    doc = parse(DOCUMENT)
    model = {'aa': lambda *args: 'not a truth value', 'ab': lambda: 'person', 'ac': lambda: 'first'}
    with pytest.raises(ValueError, match='wrong result sort'):
        evaluate_document(doc, individuals=('person',), situations=('first',), primitives=model, memoize_definitions=True)
    with pytest.raises(ValueError, match='step budget'):
        evaluate_document(doc, individuals=('person',), situations=('first',), primitives=model, memoize_definitions=True, max_steps=1)
    with pytest.raises(ValueError, match='memoization option'):
        evaluate_document(doc, individuals=('person',), situations=('first',), primitives=model, memoize_definitions=1)
