import pytest

pytest.importorskip('z3')

from noema.grammar import parse
from noema.polynomial_proofs import verify_universal

HEADER = 'k:r aa[b b] c.r ab[b b] b.r ac[b] b.r ad[b b] b.'
MEANINGS = {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'}


def check(body, **kwargs):
    return verify_universal(parse(HEADER + body), MEANINGS, **kwargs)[0]


def test_universal_nonlinear_real_validity_is_sufficient_for_rationals():
    assert check('s[f x b[u[k aa[k ad[v x v x] n p a b]]]].')['status'] == 'valid'


def test_irrational_counterexample_does_not_disprove_rational_claim():
    # Every rational x has x*x != 2, but a real model of its negation exists.
    result = check('s[f x b[u[e[k ad[v x v x]][n p c b]]]].')
    assert result['status'] == 'unknown'
    assert result['counterexample'] is None
    assert 'not certified rational' in result['reason']


def test_rational_counterexample_is_checked_by_exact_substitution():
    result = check('s[f x b[u[e[k ad[v x v x]][n p e b]]]].')
    assert result['status'] == 'invalid'
    assert next(iter(result['counterexample'].values())) in ('2', '-2')
    assert check('s[e[n p a b][n p b b]].')['status'] == 'invalid'


@pytest.mark.parametrize('body', [
    's[g x b[e[k ad[v x v x]][n p c b]]].',
    's[f x b[g y b[e[k ad[v y v y]][v x]]]].',
    's[u[f x b[e[v x][v x]]]].',
    'd zz[] c[f x b[e[v x][v x]]].s[k zz[]].',
    's[f x a[e[v x][v x]]].',
    'q[e[n p a b][n p a b]].',
    's[e[i[x b][v x]][i[x b][v x]]].',
])
def test_unsupported_quantification_or_function_equality_is_not_reinterpreted(body):
    with pytest.raises(ValueError):
        check(body)


def test_definition_and_lambda_expansion_preserves_lexical_scope():
    result = check('d zz[x b] h[b] b[i[y b][k ad[v x v y]]].'
                   's[f x b[f y b[e[c[k zz[v x]][v y]][k ad[v y v x]]]]].')
    assert result['status'] == 'valid'
    with pytest.raises(ValueError, match='budget'):
        check('s[f x b[e[v x][v x]]].', max_expansion=1)
