"""Reversible, rank-preserving expression envelopes using existing Noema syntax.

An expression M:T is represented by the quotation of (lambda x:T. x=x)(M).
The quotation's syntax is the code; evaluating the equality is not decoding it.
No primitive interpretation, beta reduction, or natural-language processing runs.
"""
from copy import deepcopy

from .constructed_discourse import normalize_document, sort
from .description_templates import _bounded
from .semantics import keys, require


def _checked(document, quotation, max_nodes):
    require(type(max_nodes) is int and max_nodes > 0, 'Invalid expression-code budget')
    _bounded(quotation, max_nodes)
    require(isinstance(quotation, dict), 'Expression code requires a quotation object')
    keys(quotation, ('kind', 'body', 'rank') if 'rank' in quotation else ('kind', 'body'))
    require(quotation['kind'] == 'quote', 'Expression code requires a literal quotation')
    doc = normalize_document(document)
    require(doc['schema_version'] == '0.16', 'Expression codes require explicit edition 0.16')
    trial = {**doc, 'statements': [{'kind': 'assert', 'body': {
        'kind': 'equal', 'arguments': [quotation, quotation]}}]}
    checked = normalize_document(trial)['statements'][0]['body']['arguments'][0]
    _bounded(checked, max_nodes)
    return checked


def encode_expression(document, quotation, result_type, *, max_nodes=100_000):
    """Return a D_r(truth) code for the supplied closed D_r(T) quotation.

    T is explicit and checked by ordinary application typing. The rank is not
    lowered, even when the expression could also be quoted at a lower rank.
    """
    original = _checked(document, quotation, max_nodes)
    _bounded(result_type, max_nodes)
    type_ = sort(result_type, '0.16')
    variable = {'kind': 'variable', 'name': 'term'}
    wrapper = {'kind': 'lambda', 'parameters': [{'name': 'term', 'sort': type_}],
               'body': {'kind': 'equal', 'arguments': [deepcopy(variable), deepcopy(variable)]}}
    code = {'kind': 'quote', 'body': {'kind': 'apply', 'function': wrapper,
            'arguments': [deepcopy(original['body'])]}, **({'rank': original['rank']} if original.get('rank') else {})}
    return _checked(document, code, max_nodes)


def _parts(checked):
    body = checked['body']
    if body['kind'] != 'apply' or len(body['arguments']) != 1: return None
    wrapper = body['function']
    if wrapper['kind'] != 'lambda' or len(wrapper['parameters']) != 1: return None
    parameter = wrapper['parameters'][0]
    identity = {'kind': 'equal', 'arguments': [{'kind': 'variable', 'name': parameter['name']}] * 2}
    if wrapper['body'] != identity: return None
    return parameter['sort'], body['arguments'][0]


def decode_expression(document, code, *, max_nodes=100_000):
    """Return (T, D_r(T)) after checking the canonical envelope and its types.

    Well-typed expressions that are not envelopes are rejected, not evaluated
    for truth. Returned syntax is data and is not issued to a runtime evaluator.
    """
    checked = _checked(document, code, max_nodes)
    parts = _parts(checked)
    require(parts is not None, 'Not a canonical expression code')
    type_, body = parts
    quotation = {'kind': 'quote', 'body': deepcopy(body), **({'rank': checked['rank']} if checked.get('rank') else {})}
    quotation = _checked(document, quotation, max_nodes)
    require(encode_expression(document, quotation, type_, max_nodes=max_nodes) == checked,
            'Expression code does not roundtrip')
    return deepcopy(type_), quotation


def is_template_code(document, code, *, max_nodes=100_000):
    """Recognize a canonical code whose original result sort is a function.

    Ill-typed, open, over-budget and malformed quotations raise ValueError.
    A valid ordinary quotation or a non-function expression code returns false.
    """
    checked = _checked(document, code, max_nodes)
    parts = _parts(checked)
    if parts is None: return False
    type_, _ = decode_expression(document, checked, max_nodes=max_nodes)
    return isinstance(type_, dict) and type_['kind'] == 'function'
