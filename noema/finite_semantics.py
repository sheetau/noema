"""Explicit finite interpretations for language examples; no real-world inference.

Content values are functions over the supplied situations. Quantification over
rationals is deliberately refused because a finite sample is not that domain.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import json

from .discourse import FORCES, function_sort, question_sort, description_sort, sequence_sort, normalize_document
from .semantics import require


@dataclass(frozen=True)
class Content:
    situations: tuple
    values: tuple


@dataclass(frozen=True)
class Message:
    force: str
    content: Content


@dataclass(frozen=True, eq=False)
class FunctionValue:
    parameters: tuple
    result: object
    implementation: object

    def __call__(self, *args):
        return self.implementation(*args)


MAX_FUNCTION_DOMAIN = 4096


@dataclass(frozen=True, eq=False)
class QuestionValue:
    function: FunctionValue


@dataclass(frozen=True, eq=False)
class DescriptionValue:
    """Interned, checked syntax. Only its issuing interpretation may evaluate it.

    No Python evaluator or mutable AST is exposed to primitive callbacks.
    The canonical JSON is diagnostic data, not an executable input channel.
    """
    syntax: str
    result_type: str


@dataclass(frozen=True, eq=False)
class SequenceValue:
    """An ordered finite tuple, with an immutable canonical JSON element sort."""
    items: tuple
    element_type: str


def evaluate_document(document, *, individuals, primitives, situations=(), max_steps=100000, memoize_definitions=False):
    """Evaluate a finite interpretation.

    Opt-in memoization requires deterministic, side-effect-free primitive
    interpretations for this call. Only scalar-argument/scalar-result
    definitions are cached; higher-order values retain ordinary evaluation.
    The cache belongs to this evaluation and never spans models or documents.
    """
    doc = normalize_document(document)
    require(type(max_steps) is int and max_steps > 0, 'Invalid interpretation budget')
    require(type(memoize_definitions) is bool, 'Invalid definition memoization option')
    individuals, situations = tuple(individuals), tuple(situations)
    require(individuals and len(set(individuals)) == len(individuals), 'Individual domain must be nonempty and unique')
    require(len(set(situations)) == len(situations), 'Situation domain must be unique')
    require(doc['schema_version'] == '0.8' or situations, 'Edition 0.9 or later needs a nonempty situation domain')
    declarations = {d['name']: d for d in doc['declarations']}
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    require(isinstance(primitives, dict) and set(primitives) == required
            and all(callable(f) for f in primitives.values()), 'Provide exactly the declared primitive interpretations')
    steps = 0
    node_sorts = {}
    descriptions = {}
    definition_cache = {}
    memoizable = {name for name, d in declarations.items()
        if memoize_definitions and d['kind'] == 'definition' and isinstance(d['result'], str)
        and all(isinstance(p['sort'], str) for p in d['parameters'])}

    def canonical(value):
        return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

    def infer(node, env):
        """Record sorts of already validated nodes without evaluating their bodies."""
        kind = node['kind']
        if kind == 'sequence':
            for item in node['items']:
                infer(item, env)
            result = sequence_sort(node['element'])
        elif kind in ('length', 'position', 'fold', 'concat'):
            fields = {'length': ('sequence',), 'position': ('sequence', 'index', 'value'),
                      'fold': ('sequence', 'initial', 'step'), 'concat': ('left', 'right')}[kind]
            types = {field: infer(node[field], env) for field in fields}
            result = ('number' if kind == 'length' else 'truth' if kind == 'position'
                      else types['initial'] if kind == 'fold' else types['left'])
        elif kind == 'quote':
            result = description_sort(infer(node['body'], {}))
        elif kind == 'disquote':
            result = infer(node['description'], env)['result']
        elif kind == 'variable':
            result = env[node['name']]
        elif kind == 'number':
            result = 'number'
        elif kind == 'function_ref':
            d = declarations[node['symbol']]
            params = d['parameters'] if d['kind'] == 'primitive' else [p['sort'] for p in d['parameters']]
            result = function_sort(params, d['result'])
        elif kind == 'lambda':
            body = infer(node['body'], {**env, **{p['name']: p['sort'] for p in node['parameters']}})
            result = function_sort([p['sort'] for p in node['parameters']], body)
        elif kind in ('content', 'forall', 'exists'):
            infer(node['body'], {**env, node['variable']: 'situation' if kind == 'content' else node['sort']})
            result = 'content' if kind == 'content' else 'truth'
        else:
            for child in node.get('arguments', []):
                infer(child, env)
            for field in ('content', 'situation', 'message', 'function', 'question'):
                if field in node:
                    infer(node[field], env)
            if kind == 'call':
                result = declarations[node['symbol']]['result']
            elif kind == 'apply':
                result = node_sorts[id(node['function'])]['result']
            elif kind == 'question':
                result = question_sort(node_sorts[id(node['function'])]['parameters'])
            else:
                result = {'message': 'message', 'message_content': 'content'}.get(kind, 'truth')
        node_sorts[id(node)] = result
        return result

    def infer_statement(node):
        if node['kind'] == 'suppose':
            infer(node['condition'], {})
            for child in node['statements']:
                infer_statement(child)
        else:
            infer(node['body'], {})

    for declaration in doc['declarations']:
        if declaration['kind'] == 'definition':
            infer(declaration['body'], {p['name']: p['sort'] for p in declaration['parameters']})
    for item in doc['statements']:
        infer_statement(item)

    def tick(amount=1):
        nonlocal steps
        steps += amount
        require(steps <= max_steps, 'Finite interpretation step budget exceeded')

    def valid(value, sort):
        if isinstance(sort, dict):
            if sort['kind'] == 'sequence':
                if not (isinstance(value, SequenceValue) and type(value.items) is tuple
                        and value.element_type == canonical(sort['element'])):
                    return False
                for item in value.items:
                    tick()
                    if not valid(item, sort['element']):
                        return False
                return True
            if sort['kind'] == 'description':
                record = descriptions.get(value.syntax) if isinstance(value, DescriptionValue) else None
                return (record is not None and record[0] is value
                        and value.result_type == canonical(sort['result']))
            if sort['kind'] == 'question':
                return isinstance(value, QuestionValue) and valid(value.function, function_sort(sort['parameters'], 'truth'))
            return (isinstance(value, FunctionValue) and list(value.parameters) == sort['parameters']
                    and value.result == sort['result'] and callable(value.implementation))
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
        if isinstance(sort, dict):
            require(sort['kind'] != 'description', 'Cannot finitely quantify the description domain')
            require(sort['kind'] != 'sequence', 'Cannot finitely quantify the unbounded sequence domain')
            if sort['kind'] == 'question':
                return tuple(QuestionValue(f) for f in domain(function_sort(sort['parameters'], 'truth')))
            inputs = argument_domain(sort['parameters'])
            outputs = tuple(domain(sort['result']))
            count = 1
            for _ in inputs:
                count *= len(outputs)
                require(count <= MAX_FUNCTION_DOMAIN, 'Finite function domain exceeds 4096 tables')
            def make(table):
                def lookup(*args):
                    for given, value in zip(inputs, table, strict=True):
                        if all(equal(a, b) for a, b in zip(args, given, strict=True)):
                            return value
                    raise ValueError('Function argument outside domain')
                return make_function(sort['parameters'], sort['result'], lookup)
            return tuple(make(table) for table in product(outputs, repeat=len(inputs)))
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

    def argument_domain(parameters):
        domains, count = [], 1
        for type_ in parameters:
            values = tuple(domain(type_))
            count *= len(values)
            require(count <= MAX_FUNCTION_DOMAIN, 'Finite function argument domain exceeds 4096 tuples')
            domains.append(values)
        return tuple(product(*domains))

    def invoke(function, args):
        tick()
        require(len(args) == len(function.parameters) and all(valid(a, t) for a, t in zip(args, function.parameters)),
                'Function interpretation has wrong argument sort')
        value = function(*args)
        require(valid(value, function.result), 'Function interpretation has wrong result sort')
        return value

    def make_function(parameters, result, implementation):
        raw = FunctionValue(tuple(parameters), result, implementation)
        return FunctionValue(raw.parameters, result, lambda *args: invoke(raw, args))

    def equal(a, b):
        if isinstance(a, SequenceValue):
            require(isinstance(b, SequenceValue) and a.element_type == b.element_type, 'Sequence equality sort mismatch')
            if len(a.items) != len(b.items):
                return False
            for left, right in zip(a.items, b.items, strict=True):
                tick()
                if not equal(left, right):
                    return False
            return True
        if isinstance(a, QuestionValue):
            require(isinstance(b, QuestionValue), 'Question equality sort mismatch')
            return equal(a.function, b.function)
        if isinstance(a, FunctionValue):
            require(isinstance(b, FunctionValue) and a.parameters == b.parameters and a.result == b.result,
                    'Function equality sort mismatch')
            return all(equal(invoke(a, args), invoke(b, args)) for args in argument_domain(a.parameters))
        return a == b

    def named(symbol, args):
        declaration = declarations[symbol]
        key = (symbol, tuple(args)) if symbol in memoizable else None
        if key is not None and key in definition_cache:
            return definition_cache[key]
        if declaration['kind'] == 'definition':
            value = expr(declaration['body'], {p['name']: a for p, a in zip(declaration['parameters'], args, strict=True)})
        else:
            value = primitives[symbol](*args)
        require(valid(value, declaration['result']), 'Primitive or definition interpretation has wrong result sort')
        if key is not None:
            definition_cache[key] = value
        if isinstance(value, FunctionValue):
            return make_function(value.parameters, value.result, value.implementation)
        if isinstance(value, QuestionValue):
            f = value.function
            return QuestionValue(make_function(f.parameters, f.result, f.implementation))
        return value

    def expr(node, env):
        tick()
        kind = node['kind']
        if kind == 'sequence':
            return SequenceValue(tuple(expr(item, env) for item in node['items']), canonical(node['element']))
        if kind == 'length':
            return Fraction(len(expr(node['sequence'], env).items))
        if kind == 'position':
            sequence = expr(node['sequence'], env)
            index, value = expr(node['index'], env), expr(node['value'], env)
            return (index.denominator == 1 and 0 <= index < len(sequence.items)
                    and equal(sequence.items[index.numerator], value))
        if kind == 'concat':
            left, right = expr(node['left'], env), expr(node['right'], env)
            # Charge before allocation, including when nested concatenations
            # occur inside one function body before result validation.
            tick(len(left.items) + len(right.items))
            return SequenceValue(left.items + right.items, left.element_type)
        if kind == 'fold':
            sequence, state, step = (expr(node[field], env) for field in ('sequence', 'initial', 'step'))
            for item in sequence.items:
                state = invoke(step, [state, item])
            return state
        if kind == 'quote':
            syntax = canonical(node['body'])
            if syntax not in descriptions:
                descriptions[syntax] = (DescriptionValue(syntax, canonical(node_sorts[id(node['body'])])), node['body'])
            return descriptions[syntax][0]
        if kind == 'disquote':
            value = expr(node['description'], env)
            require(valid(value, node_sorts[id(node['description'])]), 'Description belongs to another interpretation or is unchecked')
            # Quotation itself did not run the body. Evaluation is explicit,
            # closed, budgeted, and limited to the validated local AST.
            return expr(descriptions[value.syntax][1], {})
        if kind == 'question':
            return QuestionValue(expr(node['function'], env))
        if kind == 'answer_matches':
            return invoke(expr(node['question'], env).function, [expr(a, env) for a in node['arguments']])
        if kind == 'variable':
            return env[node['name']]
        if kind == 'number':
            return Fraction(node['numerator'], node['denominator'])
        if kind == 'function_ref':
            declaration = declarations[node['symbol']]
            parameters = (declaration['parameters'] if declaration['kind'] == 'primitive'
                          else [p['sort'] for p in declaration['parameters']])
            return make_function(parameters, declaration['result'], lambda *args: named(node['symbol'], args))
        if kind == 'lambda':
            # Capture values from the lexical environment, including outer lambdas.
            captured = dict(env)
            parameters = node['parameters']
            return make_function([p['sort'] for p in parameters], node_sorts[id(node['body'])],
                                 lambda *args: expr(node['body'], {**captured, **{p['name']: a for p, a in zip(parameters, args, strict=True)}}))
        if kind == 'apply':
            return invoke(expr(node['function'], env), [expr(a, env) for a in node['arguments']])
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
            args = [expr(a, env) for a in node['arguments']]
            return named(node['symbol'], args)
        if kind in ('forall', 'exists'):
            values = (expr(node['body'], {**env, node['variable']: v}) for v in domain(node['sort']))
            return all(values) if kind == 'forall' else any(values)
        values = [expr(a, env) for a in node['arguments']]
        if kind == 'not':
            return not values[0]
        a, b = values
        return {'and': lambda: a and b, 'or': lambda: a or b, 'implies': lambda: not a or b,
                'iff': lambda: a == b, 'equal': lambda: equal(a, b)}[kind]()

    def statement(node):
        tick()
        if node['kind'] == 'suppose':
            # Preserve the scope, even when false in this interpretation. This
            # is not a proof engine and does not rewrite primitive facts.
            return {'kind': 'suppose', 'condition_value': expr(node['condition'], {}),
                    'statements': [statement(child) for child in node['statements']]}
        value = expr(node['body'], {})
        if node['kind'] == 'ask' and isinstance(value, QuestionValue):
            return {'kind': 'ask', 'answers': [list(args) for args in argument_domain(value.function.parameters)
                                              if invoke(value.function, args)]}
        return {'kind': node['kind'], 'value': value}

    return [statement(s) for s in doc['statements']]
