from pathlib import Path

import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.script import encode, decode

LIBRARY = Path('examples/v011/real-cuts.noema')
INTERPRETATIONS = {'aa': 'less', 'ab': 'add', 'ac': 'negate', 'ad': 'multiply'}


def library(tail=''):
    return parse(LIBRARY.read_text(encoding='utf-8') + tail)


def proof(tail):
    pytest.importorskip('z3')
    from noema.rational_proofs import verify
    return verify(library(tail), INTERPRETATIONS)


@pytest.mark.parametrize('tail', [
    's[f r b[k ba[k bb[v r]]]].',
    's[f r b[f q b[z[c[k be[k bb[v r]]][v q]][k aa[v q k ac[v r]]]]]].',
    's[f a b[f b b[f q b[z[c[k bd[k bb[v a] k bb[v b]]][v q]][k aa[v q k ab[v a v b]]]]]]].',
    's[f a b[f b b[f q b[z[c[k bf[k bb[v a] k bb[v b]]][v q]][k aa[v q k ab[v a k ac[v b]]]]]]]].',
    's[f a b[f b b[z[k bg[k bb[v a] k bb[v b]]][k aa[v a v b]]]]].',
    's[f a b[f b b[f c b[z[k bi[k bb[v a] k bb[v b] k bb[v c]]][e[k ab[v b k ac[v a]]][k ab[v c k ac[v b]]]]]]]].',
])
def test_rational_embeddings_and_operations_match_for_all_rational_inputs(tail):
    assert proof(tail)[0]['status'] == 'valid'


@pytest.mark.parametrize('tail', [
    's[k ba[i[q b][e[v q][v q]]]].',
    's[k ba[i[q b][u[e[v q][v q]]]]].',
    's[k ba[i[q b][u[k aa[n p a b v q]]]]].',
    's[f a b[f b b[f q b[z[c[k bf[k bb[v a] k bb[v b]]][v q]][k aa[v q k ab[v b k ac[v a]]]]]]]].',
])
def test_empty_full_closed_boundary_and_reversed_subtraction_are_rejected(tail):
    assert proof(tail)[0]['status'] == 'invalid'


def test_sqrt_two_description_uses_exact_rational_membership_without_float():
    # Check specific members, not the assertion that this function is a cut.
    tail = ('s[c[k bh[]][n u c b]].s[c[k bh[]][n p a b]].s[c[k bh[]][n p b b]].'
            's[c[k bh[]][n p h f]].s[u[c[k bh[]][n p j g]]].s[u[c[k bh[]][n p c b]]].')
    results = evaluate_document(library(tail), individuals=['object'], situations=['now'], primitives={
        'aa': lambda a, b: a < b, 'ab': lambda a, b: a + b, 'ac': lambda a: -a, 'ad': lambda a, b: a * b})
    assert all(item == {'kind': 'assert', 'value': True} for item in results)


def test_general_finite_evaluator_still_refuses_rational_quantification():
    with pytest.raises(ValueError, match='rational'):
        evaluate_document(library('s[k ba[k bb[n p b b]]].'), individuals=['object'], situations=['now'], primitives={
            'aa': lambda a, b: a < b, 'ab': lambda a, b: a + b, 'ac': lambda a: -a, 'ad': lambda a, b: a * b})


def test_linear_verifier_cannot_silently_change_nonlinear_rational_meaning_to_real():
    with pytest.raises(ValueError, match='Nonlinear'):
        proof('s[g q b[e[k ad[v q v q]][n p c b]]].')
    with pytest.raises(ValueError, match='Nonlinear'):
        proof('s[k ba[k bh[]]].')
    with pytest.raises(ValueError, match='quantification'):
        proof('s[f cut h[b] c[e[v cut][v cut]]].')


def test_numeric_verifier_mapping_and_statement_scope_are_explicit():
    pytest.importorskip('z3')
    from noema.rational_proofs import verify
    with pytest.raises(ValueError, match='signature'):
        verify(library(), {**INTERPRETATIONS, 'aa': 'add'})
    with pytest.raises(ValueError, match='explicitly'):
        verify(library(), {})
    with pytest.raises(ValueError, match='assertions'):
        proof('q[e[n p b b][n p b b]].')
    with pytest.raises(ValueError, match='budget'):
        verify(library('s[k ba[k bb[n p b b]]].'), INTERPRETATIONS, max_expansion=1)


def test_real_library_roundtrips_without_solver_or_models():
    doc = library()
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        assert parse(text) == doc
        assert parse(decode(encode(text, 'v2'))) == doc
