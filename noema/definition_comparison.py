"""Compare closed descriptions modulo transparent definitions, without evaluation.

This is sufficient evidence of definitional sameness, not a semantic decision
procedure or an operational optimizer for the partial finite interpreter.
Nested quotations remain opaque: their spelling can itself be the subject.
"""
from copy import deepcopy

from .constructed_discourse import normalize_document, MAX_DEPTH
from .grammar import number_word
from .semantics import require


class ExpansionLimitError(ValueError):
    pass


def _size(value, limit):
    pending = [(value, 0)]
    count = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if count > limit or depth > MAX_DEPTH * 4:
            raise ExpansionLimitError('Definition comparison size or nesting limit exceeded')
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
    return count


class DefinitionComparator:
    """A namespace-bound, bounded comparison of typed closed quotations.

Definitions and lambda applications are expanded by capture-free substitution.
No logical identities, primitive interpretations, dictionaries or text-specific
rewrites are supplied. A negative result means only 'not established'.

    The equations assume transparent definitions and pure, total interpretations,
    extensional in higher-order arguments (not inspecting Python closure identity).
They do not preserve eager evaluation errors, effects, step counts or timing.
The returned syntax must not replace executable source on that basis.
"""

    def __init__(self, document, *, max_nodes=100_000, max_document_nodes=1_000_000):
        require(type(max_nodes) is int and max_nodes > 0, 'Invalid expansion budget')
        require(type(max_document_nodes) is int and max_document_nodes > 0, 'Invalid document budget')
        _size(document, max_document_nodes)
        self.document = normalize_document(document)
        self.declarations = {d['name']: d for d in self.document['declarations']}
        self.max_nodes = max_nodes

    def _checked_pair(self, left, right):
        for node in (left, right):
            _size(node, self.max_nodes)
            require(isinstance(node, dict) and node.get('kind') == 'quote', 'Expected a closed quotation')
        carrier = {**self.document, 'statements': [{'kind': 'ask', 'body': {
            'kind': 'equal', 'arguments': [left, right]}}]}
        return normalize_document(carrier)['statements'][0]['body']['arguments']

    def _expand(self, quotation):
        used, serial, spent = set(), 0, 0

        def charge(amount=1):
            nonlocal spent
            spent += amount
            if spent > self.max_nodes:
                raise ExpansionLimitError('Definition expansion budget exceeded')

        def copied(value):
            charge(_size(value, self.max_nodes))
            return deepcopy(value)

        def fresh():
            nonlocal serial
            result = 'zv' + number_word(serial)
            serial += 1
            return result

        def instantiate(parameters, body, arguments, depth):
            return visit(body, {p['name']: arg for p, arg in zip(parameters, arguments, strict=True)}, depth + 1)

        def visit(node, env, depth):
            charge()
            if depth > MAX_DEPTH:
                raise ExpansionLimitError('Definition expansion nesting exceeded')
            kind = node['kind']
            if kind == 'quote':
                # A nested quotation is a value with observable syntax identity.
                return copied(node)
            if kind == 'variable':
                return copied(env.get(node['name'], node))
            if kind in ('call', 'function_ref'):
                declaration = self.declarations[node['symbol']]
                arguments = [visit(arg, env, depth + 1) for arg in node.get('arguments', [])]
                if declaration['kind'] == 'definition':
                    used.add(node['symbol'])
                    if kind == 'call':
                        return instantiate(declaration['parameters'], declaration['body'], arguments, depth)
                    return visit({'kind': 'lambda', 'parameters': declaration['parameters'],
                        'body': declaration['body']}, {}, depth + 1)
                return {'kind': kind, 'symbol': node['symbol'], **({'arguments': arguments} if kind == 'call' else {})}
            if kind == 'lambda':
                inner, parameters = dict(env), []
                for param in node['parameters']:
                    ident = fresh()
                    inner[param['name']] = {'kind': 'variable', 'name': ident}
                    parameters.append({'name': ident, 'sort': deepcopy(param['sort'])})
                return {'kind': kind, 'parameters': parameters, 'body': visit(node['body'], inner, depth + 1)}
            if kind in ('forall', 'exists', 'content'):
                ident = fresh()
                inner = {**env, node['variable']: {'kind': 'variable', 'name': ident}}
                return {**{key: deepcopy(value) for key, value in node.items() if key not in ('variable', 'body')},
                    'variable': ident, 'body': visit(node['body'], inner, depth + 1)}
            if kind == 'apply':
                function = visit(node['function'], env, depth + 1)
                arguments = [visit(arg, env, depth + 1) for arg in node['arguments']]
                if function['kind'] == 'lambda':
                    return instantiate(function['parameters'], function['body'], arguments, depth)
                if function['kind'] == 'function_ref':
                    return {'kind': 'call', 'symbol': function['symbol'], 'arguments': arguments}
                return {'kind': kind, 'function': function, 'arguments': arguments}
            # Only expression children are visited; type descriptors are data.
            result = {}
            for key, value in node.items():
                if key in ('arguments', 'items'):
                    result[key] = [visit(child, env, depth + 1) for child in value]
                elif key in ('body', 'content', 'situation', 'message', 'function', 'question', 'description',
                        'sequence', 'index', 'value', 'left', 'right', 'initial', 'step'):
                    result[key] = visit(value, env, depth + 1)
                else:
                    result[key] = deepcopy(value)
            return result

        expanded = {**quotation, 'body': visit(quotation['body'], {}, 0)}
        _size(expanded, self.max_nodes)
        return expanded, sorted(used), spent

    def compare(self, left, right):
        left, right = self._checked_pair(left, right)
        # Preserve the quotation level as well as the described type.
        require(left.get('rank', 0) == right.get('rank', 0), 'Quotation ranks differ')
        first, used_left, steps_left = self._expand(left)
        second, used_right, steps_right = self._expand(right)
        first, second = self._checked_pair(first, second)
        return dict(status='same_definition_expansion' if first == second else 'not_established',
            left=first, right=second, expanded_definitions=sorted(set(used_left) | set(used_right)),
            expansion_steps=[steps_left, steps_right], contents_evaluated=False,
            assumptions=['transparent_definitions', 'pure_total_interpretations', 'extensional_higher_order_arguments'],
            universal_semantic_equivalence_decided=False, operational_rewrite_authorized=False)
