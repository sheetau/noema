from copy import deepcopy

import pytest

from noema.description_templates import apply_description, is_description_instance
from noema.finite_semantics import evaluate_document
from noema.grammar import parse


def quote(body):
    return {'kind': 'quote', 'body': body}


def ref(name):
    return {'kind': 'function_ref', 'symbol': name}


def call(name):
    return {'kind': 'call', 'symbol': name, 'arguments': []}


def test_exact_template_and_argument_identity_without_executing_any_primitive():
    doc = parse('n:r aa[a] c.r ab[] a.d ac[x a] c[k aa[v x]].r ad[] a.')
    before = deepcopy(doc)
    template, arg = quote(ref('aa')), quote(call('ab'))
    result = apply_description(doc, template, [arg])
    assert result['body'] == {'kind': 'apply', 'function': ref('aa'), 'arguments': [call('ab')]}
    assert is_description_instance(doc, template, [arg], result)
    assert not is_description_instance(doc, quote(ref('ac')), [arg], result)
    assert not is_description_instance(doc, template, [quote(call('ad'))], result)
    assert not is_description_instance(doc, template, [arg], quote({'kind': 'call', 'symbol': 'aa', 'arguments': [call('ab')]}))
    assert doc == before
    doc['statements'] = [{'kind': 'assert', 'body': {'kind': 'equal', 'arguments': [result, result]}}]
    def fail(*args):
        raise AssertionError('Quotation executed its contents')
    assert evaluate_document(doc, individuals=('one',), situations=('now',), primitives={'aa': fail, 'ab': fail, 'ad': fail})[0]['value']


def test_combined_binders_are_alpha_normalized_without_capture_or_beta_reduction():
    doc = parse('m:r aa[] a.')
    outer = quote({'kind': 'lambda', 'parameters': [{'name': 'x', 'sort': {'kind': 'function', 'parameters': ['individual'], 'result': 'individual'}}],
        'body': {'kind': 'apply', 'function': {'kind': 'variable', 'name': 'x'}, 'arguments': [call('aa')]}})
    inner = quote({'kind': 'lambda', 'parameters': [{'name': 'x', 'sort': 'individual'}], 'body': {'kind': 'variable', 'name': 'x'}})
    result = apply_description(doc, outer, [inner])
    assert result['body']['kind'] == 'apply'
    assert result['body']['function']['parameters'][0]['name'] != result['body']['arguments'][0]['parameters'][0]['name']
    assert is_description_instance(doc, outer, [inner], result)
    doc['statements'] = [{'kind': 'assert', 'body': {'kind': 'equal', 'arguments': [
        {'kind': 'disquote', 'description': result}, call('aa')]}}]
    assert evaluate_document(doc, individuals=('one',), situations=('now',), primitives={'aa': lambda: 'one'})[0]['value']


def test_zero_arguments_and_arbitrary_typed_arity():
    doc = parse('n:r aa[] c.r ab[a c] c.r ac[] a.')
    result = apply_description(doc, quote(ref('aa')), [])
    assert result['body']['arguments'] == []
    truth = quote({'kind': 'equal', 'arguments': [call('ac'), call('ac')]})
    result = apply_description(doc, quote(ref('ab')), [quote(call('ac')), truth])
    assert len(result['body']['arguments']) == 2


@pytest.mark.parametrize('template,args', [
    (quote(ref('aa')), []),
    (quote(ref('aa')), [quote(ref('aa'))]),
    (quote(call('ab')), [quote(call('ab'))]),
    (quote(ref('aa')), [quote({'kind': 'variable', 'name': 'x'})]),
    ({'kind': 'quote', 'body': ref('aa'), 'extra': True}, [quote(call('ab'))]),
])
def test_invalid_arity_types_free_variables_and_extra_metadata_are_rejected(template, args):
    with pytest.raises(ValueError):
        apply_description(parse('n:r aa[a] c.r ab[] a.'), template, args)


def test_transitive_disquotation_is_still_rejected():
    doc = parse('n:r aa[] c.d ab[] c[s[r[k aa[]]]].')
    with pytest.raises(ValueError, match='disquote-free'):
        apply_description(doc, quote(ref('ab')), [])


def test_limits_are_explicit_and_unknown_names_are_rejected():
    doc = parse('n:r aa[] a.')
    for limit in (False, 0, -1, 2):
        with pytest.raises(ValueError):
            apply_description(doc, quote(ref('aa')), [], max_nodes=limit)
    with pytest.raises(ValueError):
        apply_description(doc, quote(ref('unknown')), [])
    result = apply_description(doc, quote(ref('aa')), [])
    assert result == apply_description(doc, quote(ref('aa')), [])


def test_instance_result_type_is_checked_and_not_silently_classified_false():
    doc = parse('n:r aa[] a.r ab[] c.')
    with pytest.raises(ValueError):
        is_description_instance(doc, quote(ref('aa')), [], quote(call('ab')))
