"""Check explicit witnesses without enumerating or bounding their domains.

Only a positive, leading existential block (possibly in one named definition)
is discharged. A true instance proves existence in the supplied interpretation;
a false instance only rejects those witnesses. Primitive interpretations must
be pure and total for that logical reading. Unknowns and resource errors escape.
"""
from copy import deepcopy

from .constructed_discourse import normalize_document
from .constructed_semantics import evaluate_document
from .semantics import require


def instantiate_witnesses(document, witnesses):
    """Return an ordinary checked document for one closed existential instance.

    Witnesses are closed Noema AST terms in binder order, not Python values.
    Lambda application preserves binding and quotation boundaries; there is no
    textual substitution or search. Nested/nonleading existentials are retained.
    """
    doc = normalize_document(document)
    require(len(doc['statements']) == 1 and doc['statements'][0]['kind'] in ('assert', 'ask'),
            'Expected one positive existence statement or query')
    node = doc['statements'][0]['body']
    outer = None
    if node['kind'] == 'call':
        declaration = next(d for d in doc['declarations'] if d['name'] == node['symbol'])
        require(declaration['kind'] == 'definition', 'Expected a defined existential claim')
        outer = (declaration['parameters'], node['arguments'])
        node = declaration['body']
    parameters = []
    while node['kind'] == 'exists':
        parameters.append(dict(name=node['variable'], sort=node['sort']))
        node = node['body']
    require(parameters and isinstance(witnesses, list) and len(witnesses) == len(parameters),
            'Supply exactly the leading existential witnesses in order')
    # Check witnesses independently, so even definition parameters cannot be
    # captured accidentally. These temporary declarations never enter the result.
    reserved = {d['name'] for d in doc['declarations']}
    temporary_name = 'zwitness'
    while temporary_name in reserved:
        temporary_name += 'a'
    checked = []
    for parameter, term in zip(parameters, witnesses, strict=True):
        declaration = dict(kind='definition', name=temporary_name, parameters=[],
                           result=parameter['sort'], body=deepcopy(term))
        trial = dict(doc, declarations=doc['declarations'] + [declaration], statements=[])
        checked.append(normalize_document(trial)['declarations'][-1]['body'])
    body = dict(kind='apply', function=dict(kind='lambda', parameters=parameters, body=node),
                arguments=checked)
    if outer is not None and outer[0]:
        body = dict(kind='apply', function=dict(kind='lambda', parameters=outer[0], body=body),
                    arguments=outer[1])
    return normalize_document(dict(doc, statements=[dict(kind='ask', body=body)]))


def verify_witnesses(document, witnesses, **interpretation):
    """Certify this instance in a model; never disprove unrestricted existence."""
    instance = instantiate_witnesses(document, witnesses)
    rows = evaluate_document(instance, **interpretation)
    value = rows[0]['value']
    require(type(value) is bool, 'Existential instance must have truth sort')
    return dict(status='valid' if value else 'uncertified', instance_value=value,
                interpretation_relative=True, theorem_disproved=False,
                unrestricted_domain_enumerated=False, witnesses_checked=len(witnesses))
