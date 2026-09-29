from itertools import product
from pathlib import Path

import pytest

from noema.discourse import definition_audit
from noema.finite_semantics import Content, FunctionValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.language import convert
from noema.render import render
from noema.script import encode, decode


def evaluate(text, primitives=None, **kwargs):
    return evaluate_document(parse(text), individuals=['a', 'b'], situations=['now', 'later'],
                             primitives=primitives or {}, **kwargs)


def test_named_reference_and_lambda_agree_with_direct_application_in_all_small_relations():
    text = ('k:r aa[a a] c.d ba[x a] h[a] c[i[y a][k aa[v x v y]]].'
            's[f x a[f y a[z[c[c[p ba][v x]][v y]][k aa[v x v y]]]]].')
    pairs = list(product(('a', 'b'), repeat=2))
    for flags in product((False, True), repeat=4):
        relation = dict(zip(pairs, flags))
        assert evaluate(text, {'aa': lambda a, b: relation[a, b]}) == [{'kind': 'assert', 'value': True}]
    assert definition_audit(parse(text))['statement_primitive_dependencies'] == [['aa']]


def test_lambda_captures_outer_values_and_shadowing_survives_normalization():
    text = ('k:d aa[x a] h[a] c[i[y a][e[v x][v y]]].'
            's[f x a[c[k aa[v x]][v x]]].'
            's[u[f x a[f y a[c[k aa[v x]][v y]]]]].')
    assert [s['value'] for s in evaluate(text)] == [True, True]
    left = 'k:d aa[x a] h[a] c[i[x a][e[v x][v x]]].'
    right = 'k:d aa[unused a] h[a] c[i[inner a][e[v inner][v inner]]].'
    assert parse(left) == parse(right)


def test_functions_of_functions_and_rational_application_are_exact():
    text = ('k:r add[b b] b.d twice[fun h[b] b value b] b[c[v fun][c[v fun][v value]]].'
            's[e[k twice[i[x b][k add[v x n p b c]] n p a b]][n p b b]].')
    assert evaluate(text, {'add': lambda a, b: a + b}) == [{'kind': 'assert', 'value': True}]


def test_function_equality_is_extensional_and_is_not_python_object_identity():
    text = ('k:r aa[a] c.r ab[a] c.'
            's[e[p aa][i[x a][k aa[v x]]]].'
            's[e[p aa][p ab]].')
    assert [s['value'] for s in evaluate(text, {'aa': lambda a: a == 'a', 'ab': lambda a: True})] == [True, False]
    assert [s['value'] for s in evaluate(text, {'aa': lambda a: True, 'ab': lambda a: True})] == [True, True]


def test_quantifying_functions_includes_all_tables_instead_of_declared_symbols_only():
    text = ('k:s[g property h[a] c['
            'w[g x a[c[v property][v x]]][g y a[u[c[v property][v y]]]]]].')
    assert evaluate(text) == [{'kind': 'assert', 'value': True}]
    # Four Boolean endofunctions include negation, which has no fixed point.
    assert evaluate('k:q[f fun h[c] c[g x c[e[c[v fun][v x]][v x]]]].') == [{'kind': 'ask', 'value': False}]
    # Higher-order identity agrees with application on every Boolean endofunction.
    assert evaluate('k:s[f fun h[c] c[e[c[i[g h[c] c][v g]][v fun]][v fun]]].') == [{'kind': 'assert', 'value': True}]


def test_zero_arity_and_content_valued_functions():
    text = ('k:r aa[a d] c.r ab[] a.'
            'd ba[x a] e[b w[k aa[v x v w]]].'
            's[e[c[p ab][]][k ab[]]].'
            's[e[c[p ba][k ab[]]][b scene[k aa[k ab[] v scene]]]].')
    assert [s['value'] for s in evaluate(text, {'aa': lambda a, s: s == 'later', 'ab': lambda: 'a'})] == [True, True]


def test_primitive_can_receive_a_defined_property_without_new_unexplained_concept_name():
    text = ('k:r aa[a d] c.r ab[h[a] e] c.'
            'd ba[x a] e[b w[k aa[v x v w]]].s[k ab[p ba]].')
    observed = []
    def consume(property_):
        observed.append(property_('a'))
        return True
    assert evaluate(text, {'aa': lambda a, s: s == 'later', 'ab': consume}) == [{'kind': 'assert', 'value': True}]
    assert observed == [Content(('now', 'later'), (False, True))]
    audit = definition_audit(parse(text))
    assert audit['primitive_symbols'] == ['aa', 'ab']
    assert audit['statement_primitive_dependencies'] == [['aa', 'ab']]


@pytest.mark.parametrize('text', [
    'j:r aa[h[a] c] c.',
    'j:s[e[i[x a][v x]][i[y a][v y]]].',
    'k:s[e[p missing][p missing]].',
    'k:d aa[] h[] c[p aa].',
    'k:d aa[] h[] c[p ab].r ab[] c.',
    'k:s[c[n p b b][n p b b]].',
    'k:r aa[a] c.s[c[p aa][]].',
    'k:r aa[a] c.s[c[p aa][n p b b]].',
    'k:r aa[a] c.r ab[b] c.s[e[p aa][p ab]].',
    'k:d aa[] h[a] c[i[x a x a][e[v x][v x]]].',
    'k:d aa[] h[a] c[i[x a][e[v x][v y]]].',
    'k:d aa[] h[a] c[i[x b][e[v x][v x]]].',
    'k:r aa[h[a] c] c.s[k aa[i[x a][v x]]].',
])
def test_type_scope_and_version_errors_are_rejected(text):
    with pytest.raises(ValueError):
        parse(text)


def test_infinite_function_comparisons_and_huge_domains_are_explicitly_refused():
    for text in ('k:s[e[i[x b][v x]][i[y b][v y]]].',
                 'k:s[g f h[a] b[e[v f][v f]]].'):
        with pytest.raises(ValueError, match='rational'):
            evaluate(text)
    with pytest.raises(ValueError, match='4096'):
        evaluate('k:s[f fun h[c c c c] c[e[v fun][v fun]]].')
    with pytest.raises(ValueError, match='nesting'):
        parse('k:r aa[' + 'h[' * 130 + 'a' + '] c' * 130 + '] c.')


def test_wrong_primitive_function_signature_and_result_fail_on_use():
    text = 'k:r aa[] h[b] b.s[e[c[k aa[]][n p b b]][n p b b]].'
    for value in (lambda a: a, FunctionValue(('truth',), 'truth', lambda a: a),
                  FunctionValue(('number',), 'number', lambda a: True)):
        with pytest.raises(ValueError, match='sort'):
            evaluate(text, {'aa': lambda: value})
    value = FunctionValue(('number',), 'number', lambda a: a)
    assert evaluate(text, {'aa': lambda: value}) == [{'kind': 'assert', 'value': True}]


def test_function_given_to_primitive_still_checks_argument_domain():
    text = 'k:r aa[h[a] a] c.s[k aa[i[x a][v x]]].'
    with pytest.raises(ValueError, match='argument sort'):
        evaluate(text, {'aa': lambda function: function('outside') == 'outside'})


def test_function_sorts_roundtrip_and_only_lossless_downgrades():
    text = 'k:d aa[x a] h[a] c[i[y a][e[v x][v y]]].q[f x a[c[k aa[v x]][v x]]].'
    doc = parse(text)
    for notation in ('full', 'compact'):
        result = format_graph(doc, notation)
        assert parse(result) == doc
        assert parse(decode(encode(result, 'v2'))) == doc
        assert 'Noema 0.11' in render(result, alphabet='v2')
    for version in ('0.8', '0.9', '0.10'):
        with pytest.raises(ValueError):
            convert(doc, version)
    previous = parse(Path('examples/v010/conditional-directive.noema').read_text(encoding='utf-8'))
    assert convert(convert(previous, '0.11'), '0.10') == previous


def test_kant_motto_receives_the_defined_exit_property_and_changes_with_its_conditions():
    from scripts.check_written_v011 import check_linked_draft
    audit, cases = check_linked_draft()
    assert 'an' not in audit['definition_dependencies']['primitive_symbols']
    assert audit['primitive_count'] == 14 and audit['definition_count'] == 9
    assert cases['capable_after_true']['observed']['change_content'] == [False, True]
    assert cases['capable_after_false']['observed']['change_content'] == [False, False]
