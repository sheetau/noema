from dataclasses import replace
from fractions import Fraction

import pytest

from noema.discourse import definition_audit
from noema.finite_semantics import DescriptionValue, evaluate_document
from noema.grammar import parse, format_graph
from noema.language import convert
from noema.render import render
from noema.script import encode, decode


def evaluate(text, primitives=None, **kwargs):
    return evaluate_document(parse(text), individuals=('alice', 'bob'), situations=('now', 'later'),
                             primitives=primitives or {}, **kwargs)


def test_distinct_descriptions_can_have_equal_denotations():
    text = ('m:r add[b b] b.'
            'd aa[] i[b][r[k add[n p c b n p c b]]].'
            'd ab[] i[b][r[n p e b]].'
            's[u[e[k aa[]][k ab[]]]].s[e[s[k aa[]]][s[k ab[]]]].')
    assert [s['value'] for s in evaluate(text, {'add': lambda x, y: x + y})] == [True, True]


def test_alpha_normalization_is_local_idempotent_and_does_not_leak():
    text = ('m:d aa[outside a] i[h[a] a][r[i[first a][v first]]].'
            's[f before a[e[k aa[v before]][r[i[second a][v second]]]]].'
            's[f left a[f right a[e[r[i[x a][v x]]][r[i[y a][v y]]]]]].')
    doc = parse(text)
    assert parse(format_graph(doc)) == doc
    assert [s['value'] for s in evaluate(text)] == [True, True]


def test_description_identity_keeps_structure_and_declared_names():
    text = ('m:d aa[] b[n p b b].d ab[] b[n p b b].'
            's[u[e[r[k aa[]]][r[k ab[]]]]].'
            's[u[e[r[c[i[x b][v x]][n p b b]]][r[n p b b]]]].'
            's[e[r[n p c e]][r[n p b c]]].')
    assert all(s['value'] for s in evaluate(text))


def test_constructing_a_quote_does_not_evaluate_even_an_infinite_quantifier():
    text = 'm:s[e[r[f x b[e[v x][v x]]]][r[f y b[e[v y][v y]]]]].'
    assert evaluate(text)[0]['value']
    with pytest.raises(ValueError, match='rational number domain'):
        evaluate('m:s[s[r[f x b[e[v x][v x]]]]].')
    seen = []
    assert evaluate('m:r aa[] b.s[e[r[k aa[]]][r[k aa[]]]].',
                    {'aa': lambda: seen.append('called') or Fraction(1)})[0]['value']
    assert seen == []


def test_disquotation_obeys_original_types_and_explicit_content_situations():
    text = ('m:r aa[d] c.r now[] d.r later[] d.'
            'd ba[] i[e][r[b scene[k aa[v scene]]]].'
            's[t[s[k ba[]]][k now[]]].s[u[t[s[k ba[]]][k later[]]]].'
            's[e[c[s[r[i[x b][v x]]]][n p c b]][n p c b]].'
            's[e[s[s[r[r[n p b b]]]]][n p b b]].'
            'q[s[r[j v[i[x a][e[v x][v x]]]]]].')
    result = evaluate(text, {'aa': lambda s: s == 'now', 'now': lambda: 'now', 'later': lambda: 'later'})
    assert all(s['value'] for s in result[:-1])
    assert result[-1]['answers'] == [['alice'], ['bob']]


@pytest.mark.parametrize('text', [
    'l:r aa[] i[b].',
    'l:s[e[r[n p b b]][r[n p b b]]].',
    'l:s[s[n p b b]].',
    'm:s[s[n p b b]].',
    'm:s[r[e[n p b b][n p b b]]].',
    'm:s[e[r[n p b b]][r[e[n p b b][n p b b]]]].',
    'm:d aa[x b] i[b][r[v x]].',
    'm:d aa[] i[b][r[k aa[]]].',
    'm:d aa[] i[b][r[k ab[]]].r ab[] b.',
    'm:d aa[] i[b][r[s[r[n p b b]]]].',
    'm:d aa[] b[s[r[n p b b]]].d ab[] i[b][r[k aa[]]].',
    'm:d aa[] b[s[r[n p b b]]].d ab[] b[k aa[]].d ac[] i[h[] b][r[p ab]].',
    'm:d aa[] i[b][r["natural language"]].',
])
def test_rejects_bad_editions_types_capture_and_hidden_evaluation(text):
    with pytest.raises(ValueError):
        parse(text)


@pytest.mark.parametrize('text', [
    'm:s[f x i[c][e[v x][v x]]].',
    'm:q[j v[i[x i[c]][e[v x][v x]]]].',
    'm:s[e[i[x i[c]][e[v x][v x]]][i[y i[c]][e[v y][v y]]]].',
])
def test_description_domain_is_not_replaced_with_seen_quotes(text):
    with pytest.raises(ValueError, match='description domain'):
        evaluate(text)


def test_primitive_can_return_a_local_description_but_cannot_inject_code():
    text = 'm:r aa[i[b]] i[b].s[e[s[k aa[r[n p b b]]]][n p b b]].'
    assert evaluate(text, {'aa': lambda x: x})[0]['value']
    with pytest.raises(ValueError, match='result sort'):
        evaluate(text, {'aa': lambda x: replace(x)})
    with pytest.raises(ValueError, match='result sort'):
        evaluate(text, {'aa': lambda x: DescriptionValue('{}', '"number"')})
    saved = []
    evaluate(text, {'aa': lambda x: saved.append(x) or x})
    with pytest.raises(ValueError, match='result sort'):
        evaluate(text, {'aa': lambda x: saved[0]})


def test_disquoted_primitive_results_and_resource_limits_remain_checked():
    with pytest.raises(ValueError, match='result sort'):
        evaluate('m:r aa[] b.s[e[s[r[k aa[]]]][n p b b]].', {'aa': lambda: True})
    with pytest.raises(ValueError, match='budget'):
        evaluate('m:s[e[s[r[n p b b]]][n p b b]].', max_steps=2)


def test_roundtrip_audit_render_and_conservative_upgrade():
    doc = parse('m:r aa[b] b.d ba[] i[h[b] b][r[p aa]].s[e[c[s[k ba[]]][n p b b]][n p b b]].')
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        assert parse(text) == parse(decode(encode(text, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
    audit = definition_audit(doc)
    assert audit['definition_primitive_dependencies'] == {'ba': ['aa']}
    assert audit['statement_primitive_dependencies'] == [['aa']]
    with pytest.raises(ValueError, match='0.13'):
        convert(doc, '0.12')
    old = parse('l:q[j v[i[x a][e[v x][v x]]]].')
    assert convert(convert(old, '0.13'), '0.12') == old
