from fractions import Fraction
from itertools import product

import pytest

from noema.discourse import definition_audit
from noema.finite_semantics import FunctionValue, QuestionValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.language import convert
from noema.render import render
from noema.script import encode, decode


def evaluate(text, primitives=None, individuals=('a', 'b'), **kwargs):
    return evaluate_document(parse(text), individuals=individuals, situations=('now', 'later'),
                             primitives=primitives or {}, **kwargs)


def test_all_binary_relations_preserve_answer_order_and_empty_answers():
    pairs = list(product(('a', 'b'), repeat=2))
    for flags in product((False, True), repeat=4):
        relation = dict(zip(pairs, flags))
        text = 'l:r aa[a a] c.q[j v[p aa]].'
        assert evaluate(text, {'aa': lambda a, b: relation[a, b]}) == [
            {'kind': 'ask', 'answers': [list(p) for p in pairs if relation[p]]}]


def test_context_is_captured_and_assumption_scopes_survive():
    text = ('l:r aa[a d] c.r now[] d.r later[] d.'
            'd ba[scene d] g[a][j v[i[x a][k aa[v x v scene]]]].'
            'q[k ba[k now[]]].a[e[k now[]][k later[]]][q[k ba[k later[]]].].')
    assert evaluate(text, {'aa': lambda x, s: (x, s) in (('a', 'now'), ('b', 'later')),
                           'now': lambda: 'now', 'later': lambda: 'later'}) == [
        {'kind': 'ask', 'answers': [['a']]},
        {'kind': 'suppose', 'condition_value': False, 'statements': [{'kind': 'ask', 'answers': [['b']]}]}]


def test_question_reference_does_not_ask_and_primitive_calls_remain_checked():
    text = 'l:r aa[g[a]] c.s[k aa[j v[i[x a][e[v x][v x]]]]].'
    observed = []
    def consume(q):
        observed.append(q.function('a'))
        return True
    assert evaluate(text, {'aa': consume}) == [{'kind': 'assert', 'value': True}]
    assert observed == [True]
    with pytest.raises(ValueError, match='argument sort'):
        evaluate(text, {'aa': lambda q: q.function(Fraction(1))})


def test_explicit_numeric_candidate_needs_no_infinite_search():
    text = ('l:d aa[] g[b][j v[i[x b][e[v x][n p b c]]]].'
            's[h[k aa[]][n p b c]].q[h[k aa[]][n p b b]].')
    assert evaluate(text) == [{'kind': 'assert', 'value': True}, {'kind': 'ask', 'value': False}]
    with pytest.raises(ValueError, match='rational number domain'):
        evaluate(text + 'q[k aa[]].')


def test_questions_are_extensional_and_quantification_includes_all_answer_sets():
    text = ('l:s[e[j v[i[x a][e[v x][v x]]]][j v[i[y a][u[u[e[v y][v y]]]]]]].'
            's[g question g[a][w[g x a[h[v question][v x]]][g y a[u[h[v question][v y]]]]]].'
            's[f question g[a][e[v question][j v[i[x a][h[v question][v x]]]]]].')
    assert [s['value'] for s in evaluate(text)] == [True, True, True]


def test_nested_question_types_have_well_founded_finite_domains():
    text = ('l:s[f question g[g[c]][e[v question][v question]]].'
            's[f maker h[g[c]] g[c][f question g[c][e[c[v maker][v question]][c[v maker][v question]]]]].')
    assert [s['value'] for s in evaluate(text, max_steps=1000000)] == [True, True]


def test_zero_answers_and_zero_parameters_are_distinct():
    text = ('l:q[j v[i[][e[n p a b][n p a b]]]].'
            'q[j v[i[][e[n p a b][n p b b]]]].')
    assert evaluate(text) == [{'kind': 'ask', 'answers': [[]]}, {'kind': 'ask', 'answers': []}]


def test_primitive_question_values_and_signature_validation():
    text = 'l:r aa[] g[a].q[k aa[]].'
    assert evaluate(text, {'aa': lambda: QuestionValue(FunctionValue(('individual',), 'truth', lambda a: a == 'b'))}) == [
        {'kind': 'ask', 'answers': [['b']]}]
    with pytest.raises(ValueError, match='result sort'):
        evaluate(text, {'aa': lambda: QuestionValue(FunctionValue(('number',), 'truth', lambda a: True))})
    with pytest.raises(ValueError, match='result sort'):
        evaluate(text, {'aa': lambda: QuestionValue(FunctionValue(('individual',), 'truth', lambda a: 1))})


@pytest.mark.parametrize('text', [
    'k:r aa[g[a]] c.',
    'k:q[j v[i[x a][e[v x][v x]]]].',
    'k:q[h[j v[i[x a][e[v x][v x]]]][n p b b]].',
    'l:q[j v[i[x a][v x]]].',
    'l:q[j v[n p b b]].',
    'l:s[j v[i[x a][e[v x][v x]]]].',
    'l:l[j v[i[x a][e[v x][v x]]]].',
    'l:q[c[j v[i[x a][e[v x][v x]]]][n p b b]].',
    'l:q[h[j v[i[x a][e[v x][v x]]]][]].',
    'l:q[h[j v[i[x a][e[v x][v x]]]][n p b b]].',
    'l:q[h[i[x b][e[v x][v x]]][n p b b]].',
    'l:q[e[j v[i[x a][e[v x][v x]]]][j v[i[x b][e[v x][v x]]]]].',
    'l:d aa[] g[a][j v[i[x a][e[v x][v outside]]]].',
])
def test_version_scope_and_type_errors(text):
    with pytest.raises(ValueError):
        parse(text)


def test_question_domain_resource_limit_is_not_a_false_answer():
    with pytest.raises(ValueError, match='4096'):
        evaluate('l:s[f question g[a][e[v question][v question]]].', individuals=tuple(range(13)))


def test_roundtrips_render_audit_and_edition_conversion():
    doc = parse('l:r aa[a] c.d ab[] g[a][j v[p aa]].q[k ab[]].s[f x a[h[k ab[]][v x]]].')
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        assert parse(text) == doc
        assert parse(decode(encode(text, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
    audit = definition_audit(doc)
    assert audit['definition_primitive_dependencies'] == {'ab': ['aa']}
    assert audit['statement_primitive_dependencies'] == [['aa'], ['aa']]
    with pytest.raises(ValueError, match='0.12'):
        convert(doc, '0.11')
    old = parse('k:q[e[n p a b][n p b b]].')
    assert convert(convert(old, '0.12'), '0.11') == old


def test_old_message_domain_stays_the_same_after_upgrade():
    text = 'k:r aa[f] c.s[f msg f[k aa[v msg]]].'
    seen = []
    upgraded = convert(parse(text), '0.12')
    assert evaluate_document(upgraded, individuals=('a',), situations=('now',),
                             primitives={'aa': lambda msg: seen.append(msg) is None}) == [{'kind': 'assert', 'value': True}]
    assert len(seen) == 6
    assert {m.force for m in seen} == {'assert', 'ask', 'direct'}
