from dataclasses import replace
from fractions import Fraction

import pytest

from noema.discourse import definition_audit
from noema.finite_semantics import FunctionValue, SequenceValue, evaluate_document
from noema.grammar import format_graph, parse
from noema.language import convert
from noema.render import render
from noema.script import decode, encode


def evaluate(text, primitives=None, **kwargs):
    return evaluate_document(parse(text), individuals=('alice', 'bob'), situations=('now',),
                             primitives=primitives or {}, **kwargs)


def test_empty_order_multiplicity_and_partial_index_are_explicit():
    text = ('n:d aa[] j[b][l[b][n p c b n p b b n p c b]].'
            's[e[d[l[b][]]][n p a b]].s[e[d[k aa[]]][n p d b]].'
            's[a[k aa[]][n p a b][n p c b]].s[a[k aa[]][n p c b][n p c b]].'
            's[u[a[k aa[]][n p b b][n p c b]]].'
            's[u[e[k aa[]][l[b][n p b b n p c b n p c b]]]].'
            's[u[e[k aa[]][l[b][n p c b n p b b]]]].')
    assert all(row['value'] for row in evaluate(text))


@pytest.mark.parametrize('index', ['n u b b', 'n p d b', 'n p b c', 'n p 7777777 b'])
def test_outside_or_fractional_positions_are_false(index):
    assert evaluate(f'n:s[u[a[l[b][n p b b]][{index}][n p b b]]].')[0]['value']
    assert evaluate(f'n:s[u[a[l[b][]][{index}][n p b b]]].')[0]['value']


def test_fold_is_left_to_right_and_empty_returns_the_initial_state():
    text = ('n:r subtract[b b] b.'
            's[e[q[l[b][n p c b n p d b]][n p k b][p subtract]][n p f b]].'
            's[e[q[l[b][]][n p h b][p subtract]][n p h b]].')
    assert all(row['value'] for row in evaluate(text, {'subtract': lambda x, y: x - y}))


def test_concatenation_and_sequence_state_can_reverse_and_duplicate():
    text = ('n:d reverse[input j[b]] j[b]['
            'q[v input][l[b][]][i[state j[b] item b][m[l[b][v item]][v state]]]].'
            'd twice[input j[b]] j[b][m[v input][v input]].'
            's[e[k reverse[l[b][n p b b n p c b n p d b]]][l[b][n p d b n p c b n p b b]]].'
            's[e[k twice[l[b][n p b b]]][l[b][n p b b n p b b]]].'
            's[e[m[l[b][]][l[b][]]][l[b][]]].')
    assert all(row['value'] for row in evaluate(text))


def test_nested_sequences_and_functions_use_semantic_equality():
    text = ('n:s[e[l[j[b]][l[b][] l[b][n p b b]]][l[j[b]][l[b][] l[b][n p b b]]]].'
            's[e[l[h[c] c][i[x c][v x]]][l[h[c] c][i[y c][u[u[v y]]]]]].'
            's[a[l[h[c] c][i[x c][v x]]][n p a b][i[y c][u[u[v y]]]]].'
            's[u[e[l[h[c] c][i[x c][v x]]][l[h[c] c][i[y c][u[v y]]]]]].')
    assert all(row['value'] for row in evaluate(text))


def test_quote_disquote_sequences_and_description_identity():
    text = ('n:s[e[s[r[l[b][n p c b]]]][l[b][n p c b]]].'
            's[u[e[r[l[b][n p b b n p c b]]][r[l[b][n p c b n p b b]]]]].'
            's[e[q[l[i[b]][r[n p b b] r[n p c b]]][n p a b]'
            '[i[state b item i[b]][s[v item]]]][n p c b]].')
    assert all(row['value'] for row in evaluate(text))


@pytest.mark.parametrize('body', [
    'l[b][s[r[n p b b]]]',
    'd[l[b][s[r[n p b b]]]]',
    'a[l[b][]][s[r[n p b b]]][n p b b]',
    'a[l[b][]][n p a b][s[r[n p b b]]]',
    'q[l[b][]][s[r[n p b b]]][i[x b y b][v x]]',
    'q[l[b][]][n p a b][i[x b y b][s[r[n p b b]]]]',
    'm[l[b][]][l[b][s[r[n p b b]]]]',
])
def test_quotation_cannot_hide_evaluation_in_sequence_children(body):
    with pytest.raises(ValueError, match='disquote-free'):
        parse(f'n:s[e[r[{body}]][r[{body}]]].')


@pytest.mark.parametrize('text', [
    'm:r aa[] j[b].',
    'm:s[e[l[b][]][l[b][]]].',
    'n:s[e[l[b][e[n p a b][n p a b]]][l[b][]]].',
    'n:s[e[d[n p b b]][n p b b]].',
    'n:s[a[l[b][]][e[n p a b][n p a b]][n p a b]].',
    'n:s[a[l[b][]][n p a b][l[b][]]].',
    'n:s[e[q[l[b][]][n p a b][i[x b][v x]]][n p a b]].',
    'n:s[e[q[l[b][]][n p a b][i[x b y b][e[v x][v y]]]][n p a b]].',
    'n:s[e[m[l[b][]][l[a][]]][l[b][]]].',
    'n:s[e[l[b][v outside]][l[b][]]].',
])
def test_invalid_editions_types_and_scope_are_rejected(text):
    with pytest.raises(ValueError):
        parse(text)


@pytest.mark.parametrize('text', [
    'n:s[f x j[c][e[v x][v x]]].',
    'n:q[j v[i[x j[c]][e[v x][v x]]]].',
    'n:s[e[i[x j[c]][e[v x][v x]]][i[y j[c]][e[v y][v y]]]].',
    'n:s[f x h[c] j[c][e[v x][v x]]].',
])
def test_all_finite_sequences_are_an_infinite_domain(text):
    with pytest.raises(ValueError, match='unbounded sequence domain'):
        evaluate(text)


def test_sequence_primitive_validation_includes_nested_items_and_functions():
    text = 'n:r aa[j[b]] j[b].s[e[k aa[l[b][n p b b]]][l[b][n p b b]]].'
    assert evaluate(text, {'aa': lambda value: value})[0]['value']
    for callback in (lambda x: replace(x, items=[Fraction(1)]),
                     lambda x: replace(x, items=(True,)),
                     lambda x: replace(x, element_type='"truth"')):
        with pytest.raises(ValueError, match='result sort'):
            evaluate(text, {'aa': callback})
    text = ('n:r aa[] j[h[c] c].'
            's[a[k aa[]][n p a b][i[x c][v x]]].')
    bad = SequenceValue((FunctionValue(('truth',), 'truth', lambda x: Fraction(1)),),
                        '{"kind":"function","parameters":["truth"],"result":"truth"}')
    with pytest.raises(ValueError, match='result sort'):
        evaluate(text, {'aa': lambda: bad})


def test_empty_fold_does_not_call_the_step_and_iteration_is_budgeted():
    calls = []
    text = 'n:r aa[b b] b.s[e[q[l[b][]][n p a b][p aa]][n p a b]].'
    assert evaluate(text, {'aa': lambda x, y: calls.append(y) or x})[0]['value']
    assert calls == []
    items = ' '.join(['n p b b'] * 100)
    text = f'n:s[e[q[l[b][{items}]][n p a b][i[x b y b][v y]]][n p b b]].'
    with pytest.raises(ValueError, match='budget'):
        evaluate(text, max_steps=150)


def test_concatenation_charges_copied_items_before_allocating():
    value = SequenceValue((Fraction(1),) * 100, '"number"')
    text = 'n:r aa[] j[b].s[e[d[m[k aa[]][k aa[]]]][n p gi b]].'
    with pytest.raises(ValueError, match='budget'):
        evaluate(text, {'aa': lambda: value}, max_steps=300)
    assert evaluate(text, {'aa': lambda: value}, max_steps=500)[0]['value']


def test_transitive_quote_audit_and_sequence_type_depth():
    text = ('n:d aa[] b[s[r[n p b b]]].'
            'd ab[] j[b][l[b][k aa[]]].s[e[r[k ab[]]][r[k ab[]]]].')
    with pytest.raises(ValueError, match='disquote-free'):
        parse(text)
    deep = 'j[' * 130 + 'b' + ']' * 130
    with pytest.raises(ValueError, match='Sort nesting'):
        parse(f'n:r aa[] {deep}.')


def test_roundtrip_glyphs_audit_and_lossless_edition_conversion():
    doc = parse('n:r aa[] b.r ab[b b] b.'
                'd ba[] b[q[m[l[b][k aa[]]][l[b][]]][k aa[]][p ab]].'
                's[a[l[b][k ba[]]][d[l[b][]]][k aa[]]].')
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        assert parse(text) == parse(decode(encode(text, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
    audit = definition_audit(doc)
    assert audit['definition_primitive_dependencies'] == {'ba': ['aa', 'ab']}
    assert audit['statement_primitive_dependencies'] == [['aa', 'ab']]
    with pytest.raises(ValueError, match='0.14'):
        convert(doc, '0.13')
    old = parse('m:s[e[r[n p a b]][r[n p a b]]].')
    assert convert(convert(old, '0.14'), '0.13') == old
