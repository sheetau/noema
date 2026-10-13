from copy import deepcopy

import pytest

from noema.description_templates import apply_description
from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.policy_descriptions import close_policy_description


def quote(body):
    return {'kind': 'quote', 'body': body}


def ref(name):
    return quote({'kind': 'function_ref', 'symbol': name})


def call(name):
    return quote({'kind': 'call', 'symbol': name, 'arguments': []})


def test_mixed_types_are_preserved_without_value_capture_or_execution():
    doc = parse('n:r aa[a b j[d] h[b] c] e.r ab[] a.r ac[] b.r ad[] j[d].r ae[b] c.')
    before = deepcopy(doc)
    args = [call('ab'), call('ac'), call('ad'), ref('ae')]
    instance = apply_description(doc, ref('aa'), args)
    target = close_policy_description(doc, ref('aa'), args)
    assert target['body']['kind'] == 'lambda'
    assert target['body']['parameters'][0]['sort'] == {'kind': 'sequence', 'element': 'individual'}
    assert target['body']['body'] == instance['body']
    assert doc == before
    doc['statements'] = [{'kind': 'assert', 'body': {'kind': 'equal', 'arguments': [target, target]}}]
    def fail(*args):
        raise AssertionError('Constructing or comparing a description evaluated it')
    assert evaluate_document(doc, individuals=('person',), situations=('now',),
        primitives={row['name']: fail for row in doc['declarations']})[0]['value']
    assert parse(format_graph(doc, 'compact')) == doc


@pytest.mark.parametrize('text,args', [
    ('n:r aa[] c.', []),
    ('n:r aa[] a.', []),
    ('n:r aa[] j[d].', []),
    ('n:r aa[a] e.r ab[] b.', [call('ab')]),
    ('n:r aa[a] e.r ab[] a.', []),
    ('n:r aa[a] e.', [quote({'kind': 'variable', 'name': 'free'})]),
    ('n:r ab[] e.d aa[] e[s[r[k ab[]]]].', []),
])
def test_wrong_results_arity_types_capture_and_transitive_evaluation_are_rejected(text, args):
    with pytest.raises(ValueError):
        close_policy_description(parse(text), ref('aa'), args)


def test_closed_target_uses_ordinary_noema_and_does_not_collide_with_user_names():
    doc = parse('n:r aa[a] e.r ab[] a.r zzpolicy[] c.')
    target = close_policy_description(doc, ref('aa'), [call('ab')])
    # The temporary checker must not collide with an existing user declaration.
    doc['statements'] = [{'kind': 'ask', 'body': {'kind': 'equal', 'arguments': [target, target]}}]
    assert parse(format_graph(doc)) == doc
    assert len(doc['declarations']) == 3
    with pytest.raises(ValueError, match='budget'):
        close_policy_description(doc, ref('aa'), [call('ab')], max_nodes=2)


def test_same_value_aliases_do_not_collapse_target_syntax():
    doc = parse('n:r aa[a] e.r ab[] a.d ac[] a[k ab[]].')
    first = close_policy_description(doc, ref('aa'), [call('ab')])
    second = close_policy_description(doc, ref('aa'), [call('ac')])
    assert first != second
    assert first == close_policy_description(doc, ref('aa'), [call('ab')])
