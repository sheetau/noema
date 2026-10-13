"""Construct/check typed quotation instances without executing their contents."""
from copy import deepcopy

from .discourse import MAX_DEPTH, normalize_document
from .semantics import keys, require


def _bounded(value, budget):
    stack = [(value, 0)]
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        require(count <= budget, 'Description construction budget exceeded')
        require(depth <= MAX_DEPTH * 4, 'Description construction nesting exceeded')
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)


def _quotation(value):
    keys(value, ('kind', 'body'))
    require(value['kind'] == 'quote', 'Expected a literal quotation')
    return value


def _checked(doc, quotation):
    # The existing normalizer supplies closedness, type, transitive quotation
    # safety and alpha normalization. No interpreter or callback is involved.
    trial = {**doc, 'statements': [{'kind': 'assert', 'body': {
        'kind': 'equal', 'arguments': [quotation, quotation]}}]}
    return normalize_document(trial)['statements'][0]['body']['arguments'][0]


def apply_description(document, template, arguments, *, max_nodes=100_000):
    """Return an ordinary quote of applying a quoted function to quoted args.

    Call and function-reference spellings are preserved. No beta reduction,
    alias expansion, primitive evaluation or new language syntax is used.
    The resulting quotation belongs to the supplied document's namespace.
    """
    require(type(max_nodes) is int and max_nodes > 0, 'Invalid description construction budget')
    require(isinstance(arguments, list), 'Description arguments must be a list')
    _bounded([template, arguments], max_nodes)
    _quotation(template)
    for argument in arguments:
        _quotation(argument)
    doc = normalize_document(document)
    require(doc['schema_version'] in ('0.13', '0.14'), 'Description templates require edition 0.13 or later')
    # Validate each input as a closed quotation in its own binding namespace
    # before combining them. This also rejects malformed metadata.
    template = _checked(doc, template)
    arguments = [_checked(doc, argument) for argument in arguments]
    result = {'kind': 'quote', 'body': {'kind': 'apply',
        'function': deepcopy(template['body']), 'arguments': [deepcopy(arg['body']) for arg in arguments]}}
    _bounded(result, max_nodes)
    return _checked(doc, result)


def is_description_instance(document, template, arguments, instance, *, max_nodes=100_000):
    """Compare a closed typed instance with the exact application description.

    Ill-typed inputs are rejected rather than classified as noninstances.
    Definitional/value equivalence does not turn other syntax into an instance.
    """
    require(type(max_nodes) is int and max_nodes > 0, 'Invalid description construction budget')
    _bounded(instance, max_nodes)
    _quotation(instance)
    expected = apply_description(document, template, arguments, max_nodes=max_nodes)
    doc = normalize_document(document)
    trial = {**doc, 'statements': [{'kind': 'assert', 'body': {
        'kind': 'equal', 'arguments': [instance, expected]}}]}
    # Comparing in the language also checks the two descriptions' result
    # types. A quotation of an unrelated sort is malformed input here.
    first, second = normalize_document(trial)['statements'][0]['body']['arguments']
    return first == second
