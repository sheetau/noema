"""Edition 0.8: typed, open definitions and explicitly scoped quantification.

Primitive declarations name assumptions of an interpretation; they do not supply
an explanation of a concept. Definitions cannot be recursive or forward-refer.
"""
import re
from fractions import Fraction

from .semantics import keys, require

SORTS = {'a': 'individual', 'b': 'number', 'c': 'truth'}
LOGIC = {'u': 'not', 'w': 'and', 'x': 'or', 'y': 'implies', 'z': 'iff', 'e': 'equal'}
QUANTIFIERS = {'f': 'forall', 'g': 'exists'}
MAX_DEPTH = 128


def name(value):
    require(isinstance(value, str) and re.fullmatch('[a-z2-7]+', value), 'Invalid symbol or variable')
    return value


def sort(value):
    require(isinstance(value, str) and value in SORTS.values(), 'Unknown sort')
    return value


def normalize_document(document):
    from .grammar import number_word
    keys(document, ('schema_version', 'lexicon_version', 'declarations', 'statements'))
    require(document['schema_version'] == document['lexicon_version'] == '0.8', 'Expected edition 0.8')
    require(isinstance(document['declarations'], list) and isinstance(document['statements'], list), 'Expected arrays')
    require(document['declarations'] or document['statements'], 'Empty document')
    signatures, declarations, statements = {}, [], []
    serial = 0

    def binder(original, type_, env):
        nonlocal serial
        name(original)
        canonical = 'v' + number_word(serial)
        serial += 1
        return canonical, {**env, original: (canonical, sort(type_))}

    def visit(expr, env, depth=0):
        require(depth <= MAX_DEPTH, 'Expression nesting exceeds 128 levels')
        require(isinstance(expr, dict), 'Expected an expression')
        kind = expr.get('kind')
        if kind == 'variable':
            keys(expr, ('kind', 'name'))
            ident = name(expr['name'])
            require(ident in env, 'Free variable')
            return {'kind': kind, 'name': env[ident][0]}, env[ident][1]
        if kind == 'number':
            keys(expr, ('kind', 'numerator', 'denominator'))
            a, b = expr['numerator'], expr['denominator']
            require(type(a) is int and type(b) is int and b > 0, 'Invalid rational number')
            n = Fraction(a, b)
            return {'kind': kind, 'numerator': n.numerator, 'denominator': n.denominator}, 'number'
        if kind == 'call':
            keys(expr, ('kind', 'symbol', 'arguments'))
            symbol = name(expr['symbol'])
            require(symbol in signatures, 'Unknown, recursive or forward symbol')
            params, result = signatures[symbol]
            args = expr['arguments']
            require(isinstance(args, list) and len(args) == len(params), 'Argument count mismatch')
            values = [visit(a, env, depth + 1) for a in args]
            require([t for _, t in values] == params, 'Argument sort mismatch')
            return {'kind': kind, 'symbol': symbol, 'arguments': [v for v, _ in values]}, result
        if kind in LOGIC.values():
            keys(expr, ('kind', 'arguments'))
            args = expr['arguments']
            require(isinstance(args, list) and len(args) == (1 if kind == 'not' else 2), 'Logical arity mismatch')
            values = [visit(a, env, depth + 1) for a in args]
            if kind == 'equal':
                require(values[0][1] == values[1][1], 'Equality sort mismatch')
            else:
                require(all(t == 'truth' for _, t in values), 'Logical operand must have truth sort')
            return {'kind': kind, 'arguments': [v for v, _ in values]}, 'truth'
        require(kind in QUANTIFIERS.values(), 'Unknown expression kind')
        keys(expr, ('kind', 'variable', 'sort', 'body'))
        canonical, inner = binder(expr['variable'], expr['sort'], env)
        body, type_ = visit(expr['body'], inner, depth + 1)
        require(type_ == 'truth', 'Quantifier body must have truth sort')
        return {'kind': kind, 'variable': canonical, 'sort': expr['sort'], 'body': body}, 'truth'

    for declaration in document['declarations']:
        require(isinstance(declaration, dict), 'Expected a declaration')
        kind = declaration.get('kind')
        require(kind in ('primitive', 'definition'), 'Unknown declaration kind')
        keys(declaration, ('kind', 'name', 'parameters', 'result') if kind == 'primitive'
             else ('kind', 'name', 'parameters', 'result', 'body'))
        symbol, result = name(declaration['name']), sort(declaration['result'])
        require(symbol not in signatures, 'Duplicate symbol')
        require(isinstance(declaration['parameters'], list), 'Expected parameters')
        if kind == 'primitive':
            params = [sort(t) for t in declaration['parameters']]
            item = {'kind': kind, 'name': symbol, 'parameters': params, 'result': result}
        else:
            env, parameters, originals = {}, [], set()
            serial = 0
            for param in declaration['parameters']:
                keys(param, ('name', 'sort'))
                original = name(param['name'])
                require(original not in originals, 'Duplicate parameter')
                originals.add(original)
                canonical, env = binder(original, param['sort'], env)
                parameters.append({'name': canonical, 'sort': param['sort']})
            body, actual = visit(declaration['body'], env)
            require(actual == result, 'Definition result sort mismatch')
            params = [p['sort'] for p in parameters]
            item = {'kind': kind, 'name': symbol, 'parameters': parameters, 'result': result, 'body': body}
        declarations.append(item)
        signatures[symbol] = (params, result)
    for statement in document['statements']:
        keys(statement, ('kind', 'body'))
        require(statement['kind'] in ('assert', 'ask'), 'Unknown statement kind')
        serial = 0
        body, actual = visit(statement['body'], {})
        require(actual == 'truth', 'Statement requires truth sort')
        statements.append({'kind': statement['kind'], 'body': body})
    return {'schema_version': '0.8', 'lexicon_version': '0.8', 'declarations': declarations, 'statements': statements}


def tokenize(text):
    require(isinstance(text, str), 'Expected Noema text')
    tokens, offset = [], 0
    while offset < len(text):
        if text[offset:].isspace():
            break
        match = re.match(r'\s*([a-z2-7]+|[\[\].:])', text[offset:])
        require(match is not None, f'Invalid edition 0.8 token at {offset}')
        tokens.append(match[1])
        offset += match.end()
    return tokens


def parse_document(text):
    from .grammar import read_number
    stream = tokenize(text)
    position = 0

    def peek():
        return stream[position] if position < len(stream) else None

    def take(expected=None):
        nonlocal position
        require(position < len(stream), 'Unexpected end of edition 0.8')
        value = stream[position]
        position += 1
        require(expected is None or value == expected, f'Expected {expected}, got {value}')
        return value

    def type_word():
        value = take()
        require(value in SORTS, 'Unknown sort word')
        return SORTS[value]

    def bracket(depth):
        take('[')
        result = expression(depth + 1)
        take(']')
        return result

    def expression(depth=0):
        require(depth <= MAX_DEPTH, 'Expression nesting exceeds 128 levels')
        word = take()
        if word == 'v':
            return {'kind': 'variable', 'name': name(take())}
        if word == 'n':
            sign = take()
            require(sign in ('p', 'u'), 'Number sign must be p or u')
            a, b = read_number(take()), read_number(take())
            return {'kind': 'number', 'numerator': a if sign == 'p' else -a, 'denominator': b}
        if word == 'k':
            symbol = name(take())
            take('[')
            args = []
            while peek() != ']':
                args.append(expression(depth + 1))
            take(']')
            return {'kind': 'call', 'symbol': symbol, 'arguments': args}
        if word in LOGIC:
            return {'kind': LOGIC[word], 'arguments': [bracket(depth) for _ in range(1 if word == 'u' else 2)]}
        require(word in QUANTIFIERS, 'Unknown expression word')
        variable, type_ = name(take()), type_word()
        return {'kind': QUANTIFIERS[word], 'variable': variable, 'sort': type_, 'body': bracket(depth)}

    if peek() == 'h':
        take('h')
        take(':')
    else:
        take('noema')
        take('h')
        take('h')
    declarations, statements = [], []
    while peek() is not None:
        marker = take()
        if marker in ('r', 'd'):
            require(not statements, 'Declarations must precede statements')
            symbol = name(take())
            take('[')
            params = []
            while peek() != ']':
                params.append(type_word() if marker == 'r' else {'name': name(take()), 'sort': type_word()})
            take(']')
            result = type_word()
            item = {'kind': 'primitive' if marker == 'r' else 'definition', 'name': symbol,
                    'parameters': params, 'result': result}
            if marker == 'd':
                item['body'] = bracket(0)
            declarations.append(item)
        else:
            require(marker in ('s', 'q'), 'Unknown document word')
            statements.append({'kind': 'assert' if marker == 's' else 'ask', 'body': bracket(0)})
        take('.')
    return normalize_document({'schema_version': '0.8', 'lexicon_version': '0.8',
                               'declarations': declarations, 'statements': statements})


def format_document(document, compact=False):
    from .grammar import number_word
    doc = normalize_document(document)
    types = {v: k for k, v in SORTS.items()}
    logic, quantifiers = {v: k for k, v in LOGIC.items()}, {v: k for k, v in QUANTIFIERS.items()}

    def expression(expr):
        kind = expr['kind']
        if kind == 'variable':
            return 'v ' + expr['name']
        if kind == 'number':
            return 'n ' + ('u' if expr['numerator'] < 0 else 'p') + ' ' + number_word(abs(expr['numerator'])) + ' ' + number_word(expr['denominator'])
        if kind == 'call':
            return 'k ' + expr['symbol'] + '[' + ' '.join(expression(a) for a in expr['arguments']) + ']'
        if kind in logic:
            return logic[kind] + ''.join('[' + expression(a) + ']' for a in expr['arguments'])
        return quantifiers[kind] + ' ' + expr['variable'] + ' ' + types[expr['sort']] + '[' + expression(expr['body']) + ']'

    lines = ['h:' if compact else 'noema h h']
    for item in doc['declarations']:
        if item['kind'] == 'primitive':
            line = 'r ' + item['name'] + '[' + ' '.join(types[t] for t in item['parameters']) + '] ' + types[item['result']]
        else:
            line = 'd ' + item['name'] + '[' + ' '.join(p['name'] + ' ' + types[p['sort']] for p in item['parameters'])
            line += '] ' + types[item['result']] + '[' + expression(item['body']) + ']'
        lines.append(line + '.')
    lines.extend(('s' if s['kind'] == 'assert' else 'q') + '[' + expression(s['body']) + '].' for s in doc['statements'])
    return '\n'.join(lines)


def definition_audit(document):
    """Report unexpanded assumptions; a primitive is never an explained definition."""
    doc = normalize_document(document)
    dependencies = {}

    def symbols(expr):
        result = {expr['symbol']} if expr['kind'] == 'call' else set()
        for child in expr.get('arguments', []):
            result.update(symbols(child))
        if 'body' in expr:
            result.update(symbols(expr['body']))
        return result

    for d in doc['declarations']:
        dependencies[d['name']] = {d['name']} if d['kind'] == 'primitive' else set().union(
            *(dependencies[s] for s in symbols(d['body'])))
    return {'primitive_symbols': [d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'],
            'definition_primitive_dependencies': {d['name']: sorted(dependencies[d['name']])
                                                  for d in doc['declarations'] if d['kind'] == 'definition'},
            'statement_primitive_dependencies': [sorted(set().union(*(dependencies[s] for s in symbols(item['body']))))
                                                 for item in doc['statements']]}
