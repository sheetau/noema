from pathlib import Path
import pytest

from noema.discourse import definition_audit
from noema.finite_semantics import Content, evaluate_document
from noema.grammar import parse, format_graph
from noema.language import convert
from noema.render import render
from noema.script import encode, decode


def values(doc, **kwargs):
    return [r['value'] for r in evaluate_document(doc, **kwargs)]


def test_ability_nonperformance_inability_and_ability_to_refrain_differ():
    doc = parse(Path('examples/v09/ability.noema').read_text(encoding='utf-8'))
    def model(outcomes):
        return {'aa': lambda actor, plan, now: actor == 'agent' and plan == 'method' and now == 'now',
                'ab': lambda actor, plan, now, outcome: actor == 'agent' and plan == 'method' and now == 'now' and outcome in outcomes,
                'ac': lambda actor, situation: actor == 'agent' and situation == 'success',
                'ad': lambda: 'agent', 'ae': lambda: 'now'}
    kwargs = {'individuals': ['agent', 'method'], 'situations': ['now', 'success', 'failure']}
    assert values(doc, primitives=model({'success'}), **kwargs) == [True, False, False]
    assert values(doc, primitives=model({'failure'}), **kwargs) == [True, True, True]
    # A favorable outcome alone does not establish a strategy guaranteeing it.
    assert values(doc, primitives=model({'success', 'failure'}), **kwargs) == [True, True, False]
    # Empty outcome sets must not make every ability vacuously true.
    assert values(doc, primitives=model(set()), **kwargs) == [True, True, False]


def test_content_is_not_the_current_truth_value_and_equality_ranges_over_all_situations():
    doc = parse('i:r aa[d] c.r ab[d] c.r ac[] d.'
                's[e[t[b x[k aa[v x]]][k ac[]]][t[b y[k ab[v y]]][k ac[]]]].'
                's[u[e[b x[k aa[v x]]][b y[k ab[v y]]]]].')
    assert values(doc, individuals=['object'], situations=['now', 'elsewhere'],
                  primitives={'aa': lambda s: False, 'ab': lambda s: s == 'elsewhere', 'ac': lambda: 'now'}) == [True, True]


def test_nested_content_keeps_outer_bindings_and_alpha_renaming():
    a = 'i:r aa[a d] c.r ab[] a.r ac[] d.d ba[x a] e[b x[k aa[k ab[] v x]]].s[t[k ba[k ab[]]][k ac[]]].'
    b = 'i:r aa[a d] c.r ab[] a.r ac[] d.d ba[unused a] e[b scene[k aa[k ab[] v scene]]].s[t[k ba[k ab[]]][k ac[]]].'
    assert parse(a) == parse(b)
    nested = parse('i:r aa[a d] c.r ab[] a.r ac[] d.'
                   'd ba[x a] e[b scene[t[b inner[k aa[v x v inner]]][v scene]]].'
                   's[t[k ba[k ab[]]][k ac[]]].')
    assert values(nested, individuals=['agent'], situations=['now', 'next'],
                  primitives={'aa': lambda a, s: s == 'next', 'ab': lambda: 'agent', 'ac': lambda: 'next'}) == [True]
    assert definition_audit(nested)['statement_primitive_dependencies'] == [['aa', 'ab', 'ac']]


def test_truth_parameter_is_frozen_but_situation_indexed_body_varies():
    doc = parse('i:r aa[d] c.r ab[] d.r ac[] d.'
                'd ba[p c] e[b world[v p]].'
                's[u[t[k ba[k aa[k ab[]]]][k ac[]]]].'
                's[t[b world[k aa[v world]]][k ac[]]].')
    assert values(doc, individuals=['object'], situations=['now', 'next'],
                  primitives={'aa': lambda s: s == 'next', 'ab': lambda: 'now', 'ac': lambda: 'next'}) == [True, True]


def test_content_quantifier_covers_truth_functions_and_ask_is_preserved():
    doc = parse('i:q[f p e[f world d[x[t[v p][v world]][u[t[v p][v world]]]]]].')
    assert evaluate_document(doc, individuals=['object'], situations=['a', 'b'], primitives={}) == [{'kind': 'ask', 'value': True}]


@pytest.mark.parametrize('text', [
    'h:r aa[d] c.', 'h:r aa[] c.s[t[b x[k aa[]]][v x]].',
    'i:r aa[] a.s[t[b x[k aa[]]][v x]].',
    'i:r aa[] c.r ab[] d.s[t[k aa[]][k ab[]]].',
    'i:r aa[] e.r ab[] a.s[t[k aa[]][k ab[]]].',
    'i:r aa[d] c.s[t[b x[k aa[v x]]][v x]].',
    'i:r aa[] e.s[u[k aa[]]].',
    'i:r aa[] e.r ab[] c.s[e[k aa[]][k ab[]]].',
])
def test_content_type_and_scope_errors_rejected(text):
    with pytest.raises(ValueError):
        parse(text)


def test_roundtrip_render_and_only_lossless_downgrades():
    doc = parse(Path('examples/v09/ability.noema').read_text(encoding='utf-8'))
    for notation in ('compact', 'full'):
        text = format_graph(doc, notation)
        assert parse(text) == doc
        assert parse(decode(encode(text, 'v2'))) == doc
        assert 'Noema 0.9' in render(text, alphabet='v2')
    with pytest.raises(ValueError):
        convert(doc, '0.8')
    old = parse('h:s[e[n p b b][n p b b]].')
    assert convert(convert(old, '0.9'), '0.8') == old
    assert old['schema_version'] == '0.8'


def test_finite_interpretation_rejects_incomplete_models_wrong_sorts_and_infinite_quantification():
    doc = parse('i:r aa[] e.r ab[] d.s[t[k aa[]][k ab[]]].')
    for content in (False, Content(('wrong',), (True,)), Content(('now',), (1,))):
        with pytest.raises(ValueError, match='sort'):
            evaluate_document(doc, individuals=['object'], situations=['now'], primitives={'aa': lambda: content, 'ab': lambda: 'now'})
    with pytest.raises(ValueError, match='exactly'):
        evaluate_document(doc, individuals=['object'], situations=['now'], primitives={})
    with pytest.raises(ValueError, match='rational'):
        evaluate_document(parse('i:s[f x b[e[v x][v x]]].'), individuals=['object'], situations=['now'], primitives={})
    with pytest.raises(ValueError, match='budget'):
        evaluate_document(parse('i:s[f x a[e[v x][v x]]].'), individuals=['object'], situations=['now'], primitives={}, max_steps=1)
