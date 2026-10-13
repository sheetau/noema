from copy import deepcopy
from itertools import product

import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, number_word, parse
from noema.semantics import SemanticError
from noema.specialization import specialize_definition
from scripts.check_described_prescriptions import EXTRA, model_for, values, ARGS
from scripts.compose_described_prescriptions import generic_composed


def quote(symbol):
    return {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': symbol}}


def test_prescription_specialization_preserves_all_boolean_cases_and_originals():
    doc = parse(generic_composed()[0] + EXTRA)
    original = deepcopy(doc)
    for before, after in (('rbb', 'rbg'), ('rbc', 'rbh'), ('rbd', 'rbi')):
        result = specialize_definition(doc, before, after, {4: quote('zj'), 5: quote('zk')})
        assert doc == original
        assert result.bound_positions == [4, 5] and result.disquotations_removed > 0
        assert result.document['declarations'][:-1] == doc['declarations']
        shortened = 'k za[] k zb[] k zc[] k zd[] k zi[] k ze[] p zh'
        target = parse(format_graph(result.document, 'compact') + f'q[k {before}[{ARGS}]].q[k {after}[{shortened}]].')
        for flags in product((False, True), repeat=5):
            row = values(target, model_for(target, *flags))
            assert row[0] == row[1]


def test_specialization_does_not_change_quoted_alias_identity():
    doc = parse(generic_composed()[0] + EXTRA)
    first = specialize_definition(doc, 'rbb', 'rbg', {4: quote('zj'), 5: quote('zk')})
    second = specialize_definition(first.document, 'rbb', 'rbh', {4: quote('zj'), 5: quote('zl')})
    args = 'k za[] k zb[] k zc[] k zd[] k zi[] k ze[] p zh'
    candidate = parse(format_graph(second.document, 'compact') + f'q[k rbg[{args}]].q[k rbh[{args}]].')
    assert values(candidate, model_for(candidate)) == [True, False]


def test_beta_reduction_avoids_capture_by_inner_quantifier():
    doc = parse('n:d aa[x a value i[a]] c[f y a[e[v x][s[v value]]]].r ab[] a.')
    result = specialize_definition(doc, 'aa', 'ac', {1: {'kind': 'quote', 'body': {'kind': 'call', 'symbol': 'ab', 'arguments': []}}})
    text = format_graph(result.document, 'compact') + 'q[k ac[k ab[]]].q[f x a[k ac[v x]]].'
    rows = evaluate_document(parse(text), individuals=('one', 'two'), situations=('now',), primitives={'ab': lambda: 'one'})
    assert [r['value'] for r in rows] == [True, False]


def test_inline_definition_binder_cannot_capture_callers_argument():
    doc = parse('n:d aa[x a y i[a]] c[f z a[e[v x][s[v y]]]].'
        'd ab[x a y a z a description i[a]] c[k aa[v z v description]].r ac[] a.')
    result = specialize_definition(doc, 'ab', 'ad', {3: {'kind': 'quote', 'body': {'kind': 'call', 'symbol': 'ac', 'arguments': []}}})
    candidate = parse(format_graph(result.document, 'compact') +
        'q[f x a[f y a[k ad[v x v y k ac[]]]]].q[f z a[k ad[k ac[] k ac[] v z]]].')
    rows = evaluate_document(candidate, individuals=('one', 'two'), situations=('now',), primitives={'ac': lambda: 'one'})
    assert [r['value'] for r in rows] == [True, False]


def test_closed_quoted_lambda_and_description_returning_helper_reduce():
    doc = parse('n:r aa[] a.d ab[] i[h[a] a][r[i[x a][v x]]].'
        'd ac[x a] a[c[s[k ab[]]][v x]].')
    result = specialize_definition(doc, 'ac', 'ad', {})
    target = parse(format_graph(result.document, 'compact') + 'q[e[k ad[k aa[]]][k aa[]]].')
    rows = evaluate_document(target, individuals=('one',), situations=('now',), primitives={'aa': lambda: 'one'})
    assert rows[0]['value']
    assert result.expanded_definitions == ['ab']


@pytest.mark.parametrize('binding', [
    {0: {'kind': 'variable', 'name': 'outside'}},
    {0: {'kind': 'number', 'numerator': 1, 'denominator': 1}},
    {False: quote('aa')}, {-1: quote('aa')}, {2: quote('aa')},
])
def test_invalid_open_wrong_type_or_wrong_position_bindings_are_rejected(binding):
    doc = parse('n:r aa[] a.d ab[value i[a]] a[s[v value]].')
    with pytest.raises(SemanticError):
        specialize_definition(doc, 'ab', 'ac', binding)


def test_unknown_description_is_not_guessed_or_executed():
    doc = parse('n:r aa[] i[a].d ab[value i[a]] a[s[v value]].')
    with pytest.raises(SemanticError, match='not statically'):
        specialize_definition(doc, 'ab', 'ac', {})
    with pytest.raises(SemanticError, match='not statically'):
        specialize_definition(doc, 'ab', 'ac', {0: {'kind': 'call', 'symbol': 'aa', 'arguments': []}})


def test_limits_existing_names_primitives_and_unapplied_evaluators_are_rejected():
    doc = parse('n:r aa[] a.d ab[value i[a]] a[s[v value]].d ac[] h[i[a]] a[p ab].')
    for source, target, bindings, limit in (
        ('aa', 'ad', {}, 1000), ('ab', 'aa', {}, 1000), ('ab', 'ad', {}, 0),
        ('ab', 'ad', {0: {'kind': 'quote', 'body': {'kind': 'call', 'symbol': 'aa', 'arguments': []}}}, 1),
        ('ac', 'ad', {}, 1000),
    ):
        with pytest.raises(SemanticError):
            specialize_definition(doc, source, target, bindings, max_nodes=limit)


def test_deep_acyclic_definition_chain_is_refused_before_python_recursion_failure():
    text = 'n:r aa[] a.d ab[value i[a]] a[s[v value]].'
    previous = 'ab'
    for i in range(150):
        symbol = 'zz' + number_word(i)
        text += f'd {symbol}[value i[a]] a[k {previous}[v value]].'
        previous = symbol
    doc = parse(text)
    with pytest.raises(SemanticError, match='nesting budget'):
        specialize_definition(doc, previous, 'ac', {0: {
            'kind': 'quote', 'body': {'kind': 'call', 'symbol': 'aa', 'arguments': []}}})


@pytest.mark.parametrize('header', ['m', 'n'])
def test_result_is_deterministic_quotable_and_keeps_prior_statements(header):
    doc = parse(header + ':r aa[] a.d ab[value i[a]] a[s[v value]].q[e[k aa[]][k aa[]]].')
    bindings = {0: {'kind': 'quote', 'body': {'kind': 'call', 'symbol': 'aa', 'arguments': []}}}
    first = specialize_definition(doc, 'ab', 'ac', bindings)
    assert first == specialize_definition(doc, 'ab', 'ac', bindings)
    assert first.document['statements'] == doc['statements']
    parsed = parse(format_graph(first.document, 'compact') + 'q[e[r[p ac]][r[p ac]]].')
    assert parsed['declarations'] == first.document['declarations']
