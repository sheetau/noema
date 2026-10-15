"""Explicit finite-diagnostic lowering; stored documents are never rewritten.

For pure, total interpretations this preserves Boolean truth. Unlike the default
eager interpreter it need not observe errors in unused branches. Literal quoted
bodies are opaque; definitions they reference can still use diagnostic lowering.
"""
from copy import deepcopy

from .constructed_discourse import function_sort, normalize_document
from .semantics import require


SYMBOLS = dict(and_='jiscand', or_='jiscor', implies='jiscimplies')
OPERATORS = dict(zip(('and', 'or', 'implies'), SYMBOLS.values(), strict=True))


def lower(document, primitives):
    """Return a fresh checked graph and primitive map for opt-in diagnostics.

    Thunks use ordinary typed Noema lambdas and the existing guarded evaluator;
    no Python evaluation of Noema syntax or new quotation issuer is introduced.
    """
    doc = normalize_document(deepcopy(document))
    reserved = set(OPERATORS.values())
    require(not reserved.intersection(d['name'] for d in doc['declarations'])
            and not reserved.intersection(primitives), 'Diagnostic symbol collision')
    used = set()

    def rewrite(node):
        if isinstance(node, list):
            return [rewrite(item) for item in node]
        if not isinstance(node, dict) or node.get('kind') == 'quote':
            return deepcopy(node)
        if node.get('kind') in OPERATORS:
            symbol = OPERATORS[node['kind']]
            used.add(symbol)
            left, right = node['arguments']
            return dict(kind='call', symbol=symbol, arguments=[rewrite(left),
                dict(kind='lambda', parameters=[], body=rewrite(right))])
        return {key: rewrite(value) for key, value in node.items()}

    doc = rewrite(doc)
    declarations = [dict(kind='primitive', name=name,
        parameters=['truth', function_sort([], 'truth')], result='truth')
        for name in OPERATORS.values() if name in used]
    doc['declarations'] = declarations + doc['declarations']
    callbacks = {'jiscand': lambda left, right: left and right(),
                 'jiscor': lambda left, right: left or right(),
                 'jiscimplies': lambda left, right: not left or right()}
    return normalize_document(doc), {**primitives, **{name: callbacks[name] for name in used}}
