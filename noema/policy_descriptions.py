"""Close typed content descriptions for the existing empty-binding norm interface."""
from .description_templates import apply_description
from .discourse import description_sort, function_sort, normalize_document, sequence_sort


def close_policy_description(document, template, arguments, *, max_nodes=100_000):
    """Build an ordinary quotation without evaluating any argument or template.

    Arguments are closed, typed Noema quotations. This is authoring assistance,
    not run-time capture or conversion of interpreted objects to individual IDs.
    The returned target is used with an empty individual binding sequence; all
    typed argument expressions are already preserved inside its quoted body.
    """
    instance = apply_description(document, template, arguments, max_nodes=max_nodes)
    target = {'kind': 'quote', 'body': {'kind': 'lambda',
        'parameters': [{'name': 'bindings', 'sort': sequence_sort('individual')}],
        'body': instance['body']}}
    # A checked temporary definition enforces a CONTENT result, rather than
    # silently accepting truth, message, function, or description targets.
    doc = normalize_document(document)
    names = {row['name'] for row in doc['declarations']}
    name = 'zzpolicy'
    while name in names:
        name += 'z'
    probe = {'kind': 'definition', 'name': name, 'parameters': [],
        'result': description_sort(function_sort([sequence_sort('individual')], 'content')),
        'body': target}
    checked = normalize_document({**doc, 'declarations': [*doc['declarations'], probe]})
    return checked['declarations'][-1]['body']
