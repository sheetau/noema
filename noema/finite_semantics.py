"""Explicit finite interpretations for language examples; no real-world inference.

Content values are functions over the supplied situations. Quantification over
rationals is deliberately refused because a finite sample is not that domain.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import product

from .discourse import FORCES, normalize_document
from .semantics import require


@dataclass(frozen=True)
class Content:
    situations: tuple
    values: tuple


@dataclass(frozen=True)
class Message:
    force: str
    content: Content


def evaluate_document(document, *, individuals, primitives, situations=(), max_steps=100000):
    doc = normalize_document(document)
    require(type(max_steps) is int and max_steps > 0, 'Invalid interpretation budget')
    individuals, situations = tuple(individuals), tuple(situations)
    require(individuals and len(set(individuals)) == len(individuals), 'Individual domain must be nonempty and unique')
    require(len(set(situations)) == len(situations), 'Situation domain must be unique')
    require(doc['schema_version'] == '0.8' or situations, 'Edition 0.9 or later needs a nonempty situation domain')
    declarations = {d['name']: d for d in doc['declarations']}
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    require(isinstance(primitives, dict) and set(primitives) == required
            and all(callable(f) for f in primitives.values()), 'Provide exactly the declared primitive interpretations')
    steps = 0

    def tick():
        nonlocal steps
        steps += 1
        require(steps <= max_steps, 'Finite interpretation step budget exceeded')

    def valid(value, sort):
        if sort == 'individual':
            return value in individuals
        if sort == 'situation':
            return value in situations
        if sort == 'truth':
            return type(value) is bool
        if sort == 'number':
            return isinstance(value, Fraction)
        if sort == 'message':
            return isinstance(value, Message) and value.force in FORCES.values() and valid(value.content, 'content')
        return (isinstance(value, Content) and value.situations == situations
                and isinstance(value.values, tuple) and len(value.values) == len(situations)
                and all(type(v) is bool for v in value.values))

    def domain(sort):
        require(sort != 'number', 'Cannot finitely quantify the rational number domain')
        if sort == 'individual':
            return individuals
        if sort == 'situation':
            return situations
        if sort == 'truth':
            return (False, True)
        if sort == 'message':
            return (Message(force, content) for force in FORCES.values() for content in domain('content'))
        require(len(situations) <= 8, 'Exhaustive content quantification is limited to eight situations')
        return (Content(situations, values) for values in product((False, True), repeat=len(situations)))

    def expr(node, env):
        tick()
        kind = node['kind']
        if kind == 'variable':
            return env[node['name']]
        if kind == 'number':
            return Fraction(node['numerator'], node['denominator'])
        if kind == 'message':
            return Message(node['force'], expr(node['content'], env))
        if kind == 'message_content':
            return expr(node['message'], env).content
        if kind == 'content':
            return Content(situations, tuple(expr(node['body'], {**env, node['variable']: s}) for s in situations))
        if kind == 'evaluate':
            content, situation = expr(node['content'], env), expr(node['situation'], env)
            return content.values[situations.index(situation)]
        if kind == 'call':
            declaration = declarations[node['symbol']]
            args = [expr(a, env) for a in node['arguments']]
            if declaration['kind'] == 'definition':
                # Lexical closure: parameters capture already evaluated values.
                value = expr(declaration['body'], {p['name']: a for p, a in zip(declaration['parameters'], args, strict=True)})
            else:
                value = primitives[node['symbol']](*args)
            require(valid(value, declaration['result']), 'Primitive or definition interpretation has wrong result sort')
            return value
        if kind in ('forall', 'exists'):
            values = (expr(node['body'], {**env, node['variable']: v}) for v in domain(node['sort']))
            return all(values) if kind == 'forall' else any(values)
        values = [expr(a, env) for a in node['arguments']]
        if kind == 'not':
            return not values[0]
        a, b = values
        return {'and': lambda: a and b, 'or': lambda: a or b, 'implies': lambda: not a or b,
                'iff': lambda: a == b, 'equal': lambda: a == b}[kind]()

    def statement(node):
        tick()
        if node['kind'] == 'suppose':
            # Preserve the scope, even when false in this interpretation. This
            # is not a proof engine and does not rewrite primitive facts.
            return {'kind': 'suppose', 'condition_value': expr(node['condition'], {}),
                    'statements': [statement(child) for child in node['statements']]}
        return {'kind': node['kind'], 'value': expr(node['body'], {})}

    return [statement(s) for s in doc['statements']]
