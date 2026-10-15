from copy import deepcopy
from itertools import product

import pytest

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.diagnostic_short_circuit import lower


TRUE = 'e[n p a b][n p a b]'


def run(text, model, *, lowered=True, memoize=False, **options):
    doc = parse(text)
    if lowered:
        doc, model = lower(doc, model)
    return [row['value'] for row in evaluate_document(doc, individuals=('one', 'two'),
        situations=('now',), primitives=model, memoize_definitions=memoize,
        memoize_expressions=memoize, **options)]


@pytest.mark.parametrize('bits', list(product((False, True), repeat=3)))
@pytest.mark.parametrize('memoize', (False, True))
def test_total_nested_truth_tables_and_captured_quantifiers_agree(bits, memoize):
    text = ('p:r aa[a] c.r ab[] c.r ac[] c.'
            'd ba[x a] c[y[w[k aa[v x]][k ab[]]][x[k ac[]][k aa[v x]]]].'
            'q[f x a[k ba[v x]]].')
    # x is disjunction, y is implication, w is conjunction in compact notation.
    model = {'aa': lambda x: bits[0] if x == 'one' else not bits[0],
             'ab': lambda: bits[1], 'ac': lambda: bits[2]}
    assert run(text, model, memoize=memoize) == run(text, model, lowered=False, memoize=memoize)


@pytest.mark.parametrize('operator,left,expected', [('w', False, False), ('x', True, True), ('y', False, True)])
def test_only_determined_branches_can_skip_unknown_input(operator, left, expected):
    text = f'p:r aa[] c.r ab[] c.q[{operator}[k aa[]][k ab[]]].'
    def unknown():
        raise ValueError('Unknown required input')
    model = {'aa': lambda: left, 'ab': unknown}
    assert run(text, model) == [expected]
    with pytest.raises(ValueError, match='Unknown required input'):
        run(text, model, lowered=False)
    with pytest.raises(ValueError, match='Unknown required input'):
        run(text, {**model, 'aa': lambda: not left})


def test_quoted_boolean_syntax_is_preserved_and_literal_evaluation_remains_eager():
    body = 'w[k aa[]][k ab[]]'
    text = 'p:r aa[] c.r ab[] c.q[e[r[' + body + ']][r[' + body + ']]].'
    doc = parse(text)
    before = deepcopy(doc)
    def unknown():
        raise ValueError('Unknown quoted input')
    model = {'aa': lambda: False, 'ab': unknown}
    transformed, callbacks = lower(doc, model)
    assert doc == before == transformed
    assert callbacks == model
    assert run(text, model) == [True]
    with pytest.raises(ValueError, match='Unknown quoted input'):
        run('p:r aa[] c.r ab[] c.q[s[r[' + body + ']]].', model)


@pytest.mark.parametrize('rank', ('', ' b', ' c'))
def test_thunks_keep_runtime_quotation_ceiling(rank):
    text = ('p:r touch[] c.d target[] i' + rank + '[c][r' + rank + '[k touch[]]].'
            'd run[] h[] c[i[][w[' + TRUE + '][s[k target[]]]]].'
            'd template[] i b[h[h[] c] c][r b[i[fn h[] c][c[v fn][]]]].'
            'q[c[s[k template[]]][k run[]]].')
    if rank == '':
        assert run(text, {'touch': lambda: True}) == [True]
    else:
        with pytest.raises(ValueError, match='Runtime quotation ceiling'):
            run(text, {'touch': lambda: True})


def test_lowering_preserves_source_and_roundtrip_and_rejects_private_symbol_collisions():
    doc = parse('p:r aa[] c.q[w[k aa[]][k aa[]]].')
    before = deepcopy(doc)
    model = {'aa': lambda: True}
    transformed, callbacks = lower(doc, model)
    assert doc == before and set(model) == {'aa'}
    assert parse(format_graph(transformed, 'compact')) == transformed
    with pytest.raises(ValueError, match='symbol collision'):
        lower(transformed, callbacks)
    with pytest.raises(ValueError, match='symbol collision'):
        lower(doc, {**model, 'jiscand': lambda: True})


def test_required_unbounded_domains_and_budget_errors_are_not_replaced_by_truth():
    with pytest.raises(ValueError, match='Cannot finitely quantify'):
        run('p:q[w[' + TRUE + '][f x i[c][e[v x][v x]]]].', {})
    with pytest.raises(ValueError, match='step budget'):
        run('p:q[w[' + TRUE + '][' + TRUE + ']].', {}, max_steps=1)


def test_ill_typed_dead_branch_is_still_rejected_before_execution():
    with pytest.raises(ValueError):
        run('p:r aa[] a.q[x[' + TRUE + '][k aa[]]].', {'aa': lambda: 'one'})
