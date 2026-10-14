from itertools import product

import pytest

from noema.finite_semantics import evaluate_document as reference, FunctionValue
from noema.higher_order_semantics import evaluate_document as cached
from noema.grammar import parse


def run(engine, text, primitives, **kwargs):
    return engine(parse(text), individuals=('first', 'second'), situations=('before', 'after'),
        primitives=primitives, **kwargs)


@pytest.mark.parametrize('bits', list(product((False, True), repeat=4)))
def test_captured_functions_content_questions_and_function_equality(bits):
    text = '''n:r aa[a a] c.r ab[a d] c.r ac[] a.r ad[] d.
d ba[x a] h[a] c[i[y a][k aa[v x v y]]].
d bb[x a] h[a] h[a] c[i[y a][i[z a][w[k aa[v x v z]][k aa[v y v z]]]]].
q[f x a[f y a[z[c[k ba[v x]][v y]][k aa[v x v y]]]]].
q[f x a[f y a[f z a[z[c[c[k bb[v x]][v y]][v z]][w[k aa[v x v z]][k aa[v y v z]]]]]]].
q[e[k ba[k ac[]]][i[y a][k aa[k ac[] v y]]]].
q[j v[i[x a y a][k aa[v x v y]]]].
q[t[b point[k ab[k ac[] v point]]][k ad[]]].
q[f fn h[a] c[e[c[v fn][k ac[]]][c[v fn][k ac[]]]]].'''
    model = {'aa': lambda a, b: bits[(a == 'second') * 2 + (b == 'second')],
        'ab': lambda a, s: bits[(a == 'second') * 2 + (s == 'after')],
        'ac': lambda: 'first', 'ad': lambda: 'after'}
    assert run(cached, text, model) == run(reference, text, model)


def test_function_returning_primitives_and_folds_keep_order_and_multiplicity():
    text = '''n:r aa[a] h[a] c.r ab[] a.r ac[b b] b.
d ba[items j[b]] b[q[v items][n p a b][i[state b item b][k ac[v state v item]]]].
q[f x a[f y a[z[c[k aa[v x]][v y]][e[v x][v y]]]]].
q[e[k ba[l[b][n p b b n p c b n p b b]]][n p j b]].
q[e[k ba[l[b][n p c b n p b b n p b b]]][n p l b]].
q[j v[i[item a][c[k aa[k ab[]]][v item]]]].'''
    model = {'aa': lambda a: FunctionValue(('individual',), 'truth', lambda b: a == b),
        'ab': lambda: 'first', 'ac': lambda state, item: state * 2 + item}
    expected = run(reference, text, model)
    assert expected[:3] == [{'kind': 'ask', 'value': True}] * 3
    assert run(cached, text, model) == expected


def test_reuse_reduces_work_without_caching_across_models():
    text = '''n:r aa[a a] c.d ba[x a] h[a] c[i[y a][k aa[v x v y]]].
q[f x a[f y a[f z a[c[k ba[v x]][v y]]]]].'''
    def measured(engine, value):
        calls = []
        def fact(a, b): calls.append((a, b)); return value
        result = run(engine, text, {'aa': fact})
        return result, calls
    ordinary, full_calls = measured(reference, True)
    result, calls = measured(cached, True)
    assert result == ordinary and len(calls) == 4 < len(full_calls)
    assert measured(cached, False)[0] == [{'kind': 'ask', 'value': False}]


def test_descriptions_keep_syntax_identity_and_quote_does_not_execute():
    text = '''n:r aa[] c.d ba[] c[k aa[]].
q[e[r[k aa[]]][r[k aa[]]]].q[e[r[k aa[]]][r[k ba[]]]].'''
    def forbidden(): raise ValueError('Unknown quoted meaning')
    for engine in (reference, cached):
        assert run(engine, text, {'aa': forbidden}) == [
            {'kind': 'ask', 'value': True}, {'kind': 'ask', 'value': False}]
        with pytest.raises(ValueError, match='Unknown quoted meaning'):
            run(engine, 'n:r aa[] c.q[s[r[k aa[]]]].', {'aa': forbidden})


def test_foreign_descriptions_are_still_rejected():
    for engine in (reference, cached):
        saved = []
        def retain(desc): saved.append(desc); return True
        run(engine, 'n:r aa[i[c]] c.q[k aa[r[e[n p a b][n p a b]]]].', {'aa': retain})
        with pytest.raises(ValueError, match='wrong result sort'):
            run(engine, 'n:r aa[] i[c].q[s[k aa[]]].', {'aa': lambda: saved[0]})


def test_boolean_branches_remain_eager():
    text = 'n:r aa[] c.q[y[e[n p a b][n p b b]][k aa[]]].'
    def forbidden(): raise ValueError('Required branch')
    for engine in (reference, cached):
        with pytest.raises(ValueError, match='Required branch'):
            run(engine, text, {'aa': forbidden})


def test_unselected_content_points_are_still_evaluated():
    text = 'n:r aa[d] c.r ab[] d.q[t[b point[k aa[v point]]][k ab[]]].'
    def fact(point):
        if point == 'after': raise ValueError('Unknown future')
        return True
    for engine in (reference, cached):
        with pytest.raises(ValueError, match='Unknown future'):
            run(engine, text, {'aa': fact, 'ab': lambda: 'before'})


@pytest.mark.parametrize('sort', ['b', 'j[a]', 'i[c]'])
def test_unbounded_domains_remain_refused(sort):
    text = 'n:q[f x ' + sort + '[e[v x][v x]]].'
    for engine in (reference, cached):
        with pytest.raises(ValueError, match='Cannot finitely quantify'):
            run(engine, text, {})


def test_invalid_results_budgets_and_statistics():
    with pytest.raises(ValueError, match='wrong result sort'):
        run(cached, 'n:r aa[] c.q[k aa[]].', {'aa': lambda: 1})
    stats = {}
    with pytest.raises(ValueError, match='step budget'):
        run(cached, 'n:q[e[n p a b][n p a b]].', {}, max_steps=1, statistics=stats)
    assert stats['steps'] == 2
    with pytest.raises(ValueError, match='Statistics'):
        run(cached, 'n:q[e[n p a b][n p a b]].', {}, statistics=[])
