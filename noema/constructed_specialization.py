"""Opt-in rank-zero specialization and literal folds for edition 0.16.

This derives an ordinary, quotable definition without changing editions or
the quotation safety rule. It executes no primitive interpretations.
"""
from copy import deepcopy
from dataclasses import dataclass

from .discourse import MAX_DEPTH, name
from .constructed_discourse import normalize_document
from .grammar import number_word
from .semantics import require


@dataclass
class SpecializedDefinition:
    document: dict
    symbol: str
    bound_positions: list
    expanded_definitions: list
    disquotations_removed: int
    literal_fold_steps: int


def specialize_definition(document, source, target, bindings, *, max_nodes=100_000):
    """Bind parameter positions to closed typed AST expressions.

    Reduction uses capture-avoiding beta substitution, literal finite folds,
    and rank-zero s[r[expression]]. Higher-rank disquotation is rejected.
    Literal quotations are preserved internally, not macro-expanded. Pure
    named calls are retained unless needed to reveal a quoted expression.
    Unresolved disquotation and unquotable residual references are rejected.
    Equivalence is for total, pure interpretations respecting Noema value
    equality; evaluation order, resource use and behavior of effectful,
    partial or Python-identity-inspecting callbacks are not preserved.
    """
    require(type(max_nodes) is int and max_nodes > 0, 'Invalid specialization budget')
    doc = normalize_document(document)
    require(doc['schema_version'] == '0.16', 'This specialization requires edition 0.16')
    declarations = {d['name']: d for d in doc['declarations']}
    require(isinstance(source, str) and source in declarations and declarations[source]['kind'] == 'definition',
            'Specialize an existing definition')
    name(target)
    require(target not in declarations, 'Specialization target already exists')
    original = declarations[source]
    def higher_sort(value):
        if isinstance(value, list):
            return any(higher_sort(item) for item in value)
        if not isinstance(value, dict):
            return False
        return value.get('kind') == 'description' and value.get('rank', 0) > 0 or any(higher_sort(item) for item in value.values())
    require(not higher_sort([original['parameters'], original['result']]),
            'Higher-rank parameter or result is outside this specialization')
    require(isinstance(bindings, dict) and all(type(i) is int and 0 <= i < len(original['parameters']) for i in bindings),
            'Invalid bound parameter position')
    reserved = {target}

    def reserve(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('name', 'variable', 'symbol') and isinstance(item, str):
                    reserved.add(item)
                reserve(item)
        elif isinstance(value, list):
            for item in value:
                reserve(item)
    reserve(doc)
    reserve(list(bindings.values()))
    serial = 0

    def fresh():
        nonlocal serial
        while True:
            result = 'vs' + number_word(serial)
            serial += 1
            if result not in reserved:
                reserved.add(result)
                return result

    checked = {}
    for position, expression in sorted(bindings.items()):
        temporary = {'kind': 'definition', 'name': fresh(), 'parameters': [],
            'result': original['parameters'][position]['sort'], 'body': deepcopy(expression)}
        trial = {**doc, 'declarations': doc['declarations'] + [temporary], 'statements': []}
        checked[position] = normalize_document(trial)['declarations'][-1]['body']

    effect = {}

    def disquotes(value):
        if isinstance(value, list):
            return any(disquotes(v) for v in value)
        if not isinstance(value, dict):
            return False
        if value.get('kind') == 'quote':
            return False
        if value.get('kind') == 'disquote':
            return True
        if value.get('kind') in ('call', 'function_ref') and effect[value['symbol']]:
            return True
        return any(disquotes(v) for v in value.values())
    for declaration in doc['declarations']:
        effect[declaration['name']] = declaration['kind'] == 'definition' and disquotes(declaration['body'])

    visited, removed, expanded, active_depth, folded = 0, 0, [], 0, 0

    def tick():
        nonlocal visited
        visited += 1
        require(visited <= max_nodes, 'Specialization expansion budget exceeded')

    def copied(value):
        tick()
        if isinstance(value, dict):
            return {key: copied(item) for key, item in value.items()}
        if isinstance(value, list):
            return [copied(item) for item in value]
        return value

    def inline(symbol, arguments):
        declaration = declarations[symbol]
        require(len(arguments) == len(declaration['parameters']), 'Specialization call arity differs')
        if symbol not in expanded:
            expanded.append(symbol)
        return rewrite(declaration['body'], dict(zip((p['name'] for p in declaration['parameters']), arguments)))

    def expose(value):
        # Unfold only the outer expression, to expose a lambda or a quotation.
        while value.get('kind') == 'call' and declarations[value['symbol']]['kind'] == 'definition':
            tick()
            value = inline(value['symbol'], value['arguments'])
        return value

    def rewrite(value, env):
        nonlocal active_depth
        active_depth += 1
        try:
            require(active_depth <= MAX_DEPTH, 'Specialization nesting budget exceeded')
            return rewritten(value, env)
        finally:
            active_depth -= 1

    def rewritten(value, env):
        nonlocal removed, folded
        tick()
        if isinstance(value, list):
            return [rewrite(item, env) for item in value]
        if not isinstance(value, dict):
            return value
        kind = value.get('kind')
        if kind == 'quote':
            # A quote has a separate, closed binding namespace and identity.
            return copied(value)
        if kind == 'variable':
            return copied(env.get(value['name'], value))
        if kind == 'fold':
            sequence = expose(rewrite(value['sequence'], env))
            if sequence.get('kind') == 'sequence':
                accumulator = rewrite(value['initial'], env)
                # Bind each literal item before traversing the step body. An
                # open step can contain s[target]; traversing it first would
                # incorrectly reject the closed instantiation of that step.
                step = value['step']
                for item in sequence['items']:
                    tick()
                    folded += 1
                    if step.get('kind') == 'lambda':
                        require(len(step['parameters']) == 2, 'Fold step arity differs')
                        inner = dict(env)
                        for param, argument in zip(step['parameters'], (accumulator, item)):
                            inner[param['name']] = argument
                        accumulator = rewrite(step['body'], inner)
                    else:
                        accumulator = rewrite({'kind': 'apply', 'function': step,
                            'arguments': [accumulator, item]}, env)
                return accumulator
        if kind in ('lambda', 'content', 'forall', 'exists'):
            result, inner = deepcopy(value), dict(env)
            if kind == 'lambda':
                for param in result['parameters']:
                    old, param['name'] = param['name'], fresh()
                    inner[old] = {'kind': 'variable', 'name': param['name']}
            else:
                result['variable'] = fresh()
                inner[value['variable']] = {'kind': 'variable', 'name': result['variable']}
            result['body'] = rewrite(value['body'], inner)
            return result
        if kind == 'call':
            arguments = rewrite(value['arguments'], env)
            if effect[value['symbol']]:
                return inline(value['symbol'], arguments)
            return {**value, 'arguments': arguments}
        if kind == 'disquote':
            description = expose(rewrite(value['description'], env))
            require(description.get('kind') == 'quote', 'Disquotation is not statically a closed quotation')
            require(description.get('rank', 0) == 0, 'Higher-rank disquotation is not specialized')
            removed += 1
            return rewrite(description['body'], {})
        if kind == 'apply':
            function = expose(rewrite(value['function'], env))
            arguments = rewrite(value['arguments'], env)
            if function['kind'] == 'function_ref':
                return rewrite({'kind': 'call', 'symbol': function['symbol'], 'arguments': arguments}, {})
            if function['kind'] == 'lambda':
                return rewrite(function['body'], dict(zip((p['name'] for p in function['parameters']), arguments)))
            return {**value, 'function': function, 'arguments': arguments}
        return {key: rewrite(item, env) for key, item in value.items()}

    environment = {original['parameters'][i]['name']: expr for i, expr in checked.items()}
    body = rewrite(original['body'], environment)
    specialized = {**deepcopy(original), 'name': target, 'body': body,
        'parameters': [deepcopy(p) for i, p in enumerate(original['parameters']) if i not in checked]}
    result = normalize_document({**doc, 'declarations': doc['declarations'] + [specialized]})
    quote = {'kind': 'quote', 'body': {'kind': 'function_ref', 'symbol': target}}
    # The unchanged language checker verifies transitive quotability too.
    normalize_document({**result, 'statements': result['statements'] + [
        {'kind': 'ask', 'body': {'kind': 'equal', 'arguments': [quote, deepcopy(quote)]}}]})
    return SpecializedDefinition(result, target, sorted(checked), expanded, removed, folded)
