"""Editions 0.8-0.12: typed definitions, content, messages and questions.

Primitive declarations name assumptions of an interpretation; they do not supply
an explanation of a concept. Definitions cannot be recursive or forward-refer.
"""
import re
from fractions import Fraction

from .semantics import keys, require

SORTS = {'a': 'individual', 'b': 'number', 'c': 'truth'}
CONTENT_SORTS = {**SORTS, 'd': 'situation', 'e': 'content'}
MESSAGE_SORTS = {**CONTENT_SORTS, 'f': 'message'}
EDITIONS = {'h': '0.8', 'i': '0.9', 'j': '0.10', 'k': '0.11', 'l': '0.12'}
FORCES = {'s': 'assert', 'q': 'ask', 'm': 'direct'}
LOGIC = {'u': 'not', 'w': 'and', 'x': 'or', 'y': 'implies', 'z': 'iff', 'e': 'equal'}
QUANTIFIERS = {'f': 'forall', 'g': 'exists'}
MAX_DEPTH = 128


def name(value):
    require(isinstance(value, str) and re.fullmatch('[a-z2-7]+', value), 'Invalid symbol or variable')
    return value


def sorts(version):
    return MESSAGE_SORTS if version in ('0.10', '0.11', '0.12') else CONTENT_SORTS if version == '0.9' else SORTS


def sort(value, version='0.8', depth=0):
    require(depth <= MAX_DEPTH, 'Sort nesting exceeds 128 levels')
    if isinstance(value, dict):
        if value.get('kind') == 'question':
            require(version == '0.12', 'Question sorts require edition 0.12')
            keys(value, ('kind', 'parameters'))
            require(isinstance(value['parameters'], list), 'Invalid question sort')
            return question_sort([sort(t, version, depth + 1) for t in value['parameters']])
        require(version in ('0.11', '0.12'), 'Function sorts require edition 0.11 or later')
        keys(value, ('kind', 'parameters', 'result'))
        require(value['kind'] == 'function' and isinstance(value['parameters'], list), 'Invalid function sort')
        return function_sort([sort(t, version, depth + 1) for t in value['parameters']], sort(value['result'], version, depth + 1))
    choices = sorts(version)
    require(isinstance(value, str) and value in choices.values(), 'Unknown sort')
    return value


def function_sort(parameters, result):
    return {'kind': 'function', 'parameters': parameters, 'result': result}


def question_sort(parameters):
    return {'kind': 'question', 'parameters': parameters}


def normalize_document(document):
    from .grammar import number_word
    keys(document, ('schema_version', 'lexicon_version', 'declarations', 'statements'))
    version = document['schema_version']
    require(version in EDITIONS.values() and version == document['lexicon_version'], 'Expected edition 0.8 through 0.12')
    require(isinstance(document['declarations'], list) and isinstance(document['statements'], list), 'Expected arrays')
    require(document['declarations'] or document['statements'], 'Empty document')
    signatures, declarations, statements = {}, [], []
    serial = 0

    def binder(original, type_, env):
        nonlocal serial
        name(original)
        canonical = 'v' + number_word(serial)
        serial += 1
        return canonical, {**env, original: (canonical, sort(type_, version))}

    def visit(expr, env, depth=0):
        require(depth <= MAX_DEPTH, 'Expression nesting exceeds 128 levels')
        require(isinstance(expr, dict), 'Expected an expression')
        kind = expr.get('kind')
        if kind == 'question':
            require(version == '0.12', 'Answer questions require edition 0.12')
            keys(expr, ('kind', 'function'))
            function, actual = visit(expr['function'], env, depth + 1)
            require(isinstance(actual, dict) and actual['kind'] == 'function' and actual['result'] == 'truth',
                    'Question requires a truth-valued function')
            result = sort(question_sort(actual['parameters']), version)
            return {'kind': kind, 'function': function}, result
        if kind == 'answer_matches':
            require(version == '0.12', 'Answer matching requires edition 0.12')
            keys(expr, ('kind', 'question', 'arguments'))
            question, actual = visit(expr['question'], env, depth + 1)
            require(isinstance(actual, dict) and actual['kind'] == 'question', 'Expected question sort')
            require(isinstance(expr['arguments'], list) and len(expr['arguments']) == len(actual['parameters']),
                    'Answer count mismatch')
            values = [visit(a, env, depth + 1) for a in expr['arguments']]
            require([t for _, t in values] == actual['parameters'], 'Answer sort mismatch')
            return {'kind': kind, 'question': question, 'arguments': [v for v, _ in values]}, 'truth'
        if kind == 'function_ref':
            require(version in ('0.11', '0.12'), 'Function references require edition 0.11')
            keys(expr, ('kind', 'symbol'))
            symbol = name(expr['symbol'])
            require(symbol in signatures, 'Unknown, recursive or forward symbol')
            params, result = signatures[symbol]
            return {'kind': kind, 'symbol': symbol}, sort(function_sort(params, result), version)
        if kind == 'lambda':
            require(version in ('0.11', '0.12'), 'Function abstraction requires edition 0.11')
            keys(expr, ('kind', 'parameters', 'body'))
            require(isinstance(expr['parameters'], list), 'Expected parameters')
            parameters, originals, inner = [], set(), dict(env)
            for param in expr['parameters']:
                keys(param, ('name', 'sort'))
                original, type_ = name(param['name']), sort(param['sort'], version)
                require(original not in originals, 'Duplicate parameter')
                originals.add(original)
                canonical, inner = binder(original, type_, inner)
                parameters.append({'name': canonical, 'sort': type_})
            body, actual = visit(expr['body'], inner, depth + 1)
            result = function_sort([p['sort'] for p in parameters], actual)
            sort(result, version)
            return {'kind': kind, 'parameters': parameters, 'body': body}, result
        if kind == 'apply':
            require(version in ('0.11', '0.12'), 'Function application requires edition 0.11')
            keys(expr, ('kind', 'function', 'arguments'))
            function, type_ = visit(expr['function'], env, depth + 1)
            require(isinstance(type_, dict) and type_['kind'] == 'function', 'Application requires function sort')
            require(isinstance(expr['arguments'], list) and len(expr['arguments']) == len(type_['parameters']), 'Argument count mismatch')
            values = [visit(a, env, depth + 1) for a in expr['arguments']]
            require([t for _, t in values] == type_['parameters'], 'Argument sort mismatch')
            return {'kind': kind, 'function': function, 'arguments': [v for v, _ in values]}, type_['result']
        if kind == 'message':
            require(version in ('0.10', '0.11', '0.12'), 'Messages require edition 0.10 or later')
            keys(expr, ('kind', 'force', 'content'))
            require(expr['force'] in FORCES.values(), 'Unknown message force')
            content, actual = visit(expr['content'], env, depth + 1)
            require(actual == 'content', 'Message requires content sort')
            return {'kind': kind, 'force': expr['force'], 'content': content}, 'message'
        if kind == 'message_content':
            require(version in ('0.10', '0.11', '0.12'), 'Messages require edition 0.10 or later')
            keys(expr, ('kind', 'message'))
            message, actual = visit(expr['message'], env, depth + 1)
            require(actual == 'message', 'Message content requires message sort')
            return {'kind': kind, 'message': message}, 'content'
        if kind == 'content':
            require(version in ('0.9', '0.10', '0.11', '0.12'), 'Content requires edition 0.9 or later')
            keys(expr, ('kind', 'variable', 'body'))
            canonical, inner = binder(expr['variable'], 'situation', env)
            body, actual = visit(expr['body'], inner, depth + 1)
            require(actual == 'truth', 'Content body must have truth sort')
            return {'kind': kind, 'variable': canonical, 'body': body}, 'content'
        if kind == 'evaluate':
            require(version in ('0.9', '0.10', '0.11', '0.12'), 'Content evaluation requires edition 0.9 or later')
            keys(expr, ('kind', 'content', 'situation'))
            content, content_type = visit(expr['content'], env, depth + 1)
            situation, situation_type = visit(expr['situation'], env, depth + 1)
            require(content_type == 'content' and situation_type == 'situation', 'Evaluation requires content and situation')
            return {'kind': kind, 'content': content, 'situation': situation}, 'truth'
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
        return {'kind': kind, 'variable': canonical, 'sort': inner[expr['variable']][1], 'body': body}, 'truth'

    for declaration in document['declarations']:
        require(isinstance(declaration, dict), 'Expected a declaration')
        kind = declaration.get('kind')
        require(kind in ('primitive', 'definition'), 'Unknown declaration kind')
        keys(declaration, ('kind', 'name', 'parameters', 'result') if kind == 'primitive'
             else ('kind', 'name', 'parameters', 'result', 'body'))
        symbol, result = name(declaration['name']), sort(declaration['result'], version)
        require(symbol not in signatures, 'Duplicate symbol')
        require(isinstance(declaration['parameters'], list), 'Expected parameters')
        if kind == 'primitive':
            params = [sort(t, version) for t in declaration['parameters']]
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
                parameters.append({'name': canonical, 'sort': env[original][1]})
            body, actual = visit(declaration['body'], env)
            require(actual == result, 'Definition result sort mismatch')
            params = [p['sort'] for p in parameters]
            item = {'kind': kind, 'name': symbol, 'parameters': parameters, 'result': result, 'body': body}
        declarations.append(item)
        signatures[symbol] = (params, result)
    def statement_node(statement, depth=0):
        nonlocal serial
        require(depth <= MAX_DEPTH, 'Statement nesting exceeds 128 levels')
        require(isinstance(statement, dict), 'Expected a statement')
        if statement.get('kind') == 'suppose':
            require(version in ('0.10', '0.11', '0.12'), 'Assumption scopes require edition 0.10 or later')
            keys(statement, ('kind', 'condition', 'statements'))
            serial = 0
            condition, actual = visit(statement['condition'], {})
            require(actual == 'truth', 'Assumption condition requires truth sort')
            children = statement['statements']
            require(isinstance(children, list) and children, 'Assumption scope requires statements')
            return {'kind': 'suppose', 'condition': condition,
                    'statements': [statement_node(child, depth + 1) for child in children]}
        keys(statement, ('kind', 'body'))
        kind = statement['kind']
        require(kind in ('assert', 'ask', 'perform'), 'Unknown statement kind')
        require(kind != 'perform' or version in ('0.10', '0.11', '0.12'), 'Message performance requires edition 0.10 or later')
        serial = 0
        body, actual = visit(statement['body'], {})
        answer_question = (kind == 'ask' and version == '0.12'
                           and isinstance(actual, dict) and actual['kind'] == 'question')
        require(answer_question or actual == ('message' if kind == 'perform' else 'truth'), 'Statement body has wrong sort')
        return {'kind': kind, 'body': body}

    statements = [statement_node(statement) for statement in document['statements']]
    return {'schema_version': version, 'lexicon_version': version, 'declarations': declarations, 'statements': statements}


def tokenize(text):
    require(isinstance(text, str), 'Expected Noema text')
    tokens, offset = [], 0
    while offset < len(text):
        if text[offset:].isspace():
            break
        match = re.match(r'\s*([a-z2-7]+|[\[\].:])', text[offset:])
        require(match is not None, f'Invalid definition-language token at {offset}')
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
        require(position < len(stream), 'Unexpected end of definition-language input')
        value = stream[position]
        position += 1
        require(expected is None or value == expected, f'Expected {expected}, got {value}')
        return value

    def type_word(depth=0):
        require(depth <= MAX_DEPTH, 'Sort nesting exceeds 128 levels')
        value = take()
        if value == 'g':
            require(version == '0.12', 'Question sorts require edition 0.12')
            take('[')
            params = []
            while peek() != ']':
                params.append(type_word(depth + 1))
            take(']')
            return question_sort(params)
        if value == 'h':
            require(version in ('0.11', '0.12'), 'Function sorts require edition 0.11')
            take('[')
            params = []
            while peek() != ']':
                params.append(type_word(depth + 1))
            take(']')
            return function_sort(params, type_word(depth + 1))
        choices = sorts(version)
        require(value in choices, 'Unknown sort word')
        return choices[value]

    def bracket(depth):
        take('[')
        result = expression(depth + 1)
        take(']')
        return result

    def expression(depth=0):
        require(depth <= MAX_DEPTH, 'Expression nesting exceeds 128 levels')
        word = take()
        if word == 'h':
            require(version == '0.12', 'Answer matching requires edition 0.12')
            question = bracket(depth)
            take('[')
            args = []
            while peek() != ']':
                args.append(expression(depth + 1))
            take(']')
            return {'kind': 'answer_matches', 'question': question, 'arguments': args}
        if word == 'p':
            require(version in ('0.11', '0.12'), 'Function references require edition 0.11')
            return {'kind': 'function_ref', 'symbol': name(take())}
        if word == 'i':
            require(version in ('0.11', '0.12'), 'Function abstraction requires edition 0.11')
            take('[')
            params = []
            while peek() != ']':
                params.append({'name': name(take()), 'sort': type_word()})
            take(']')
            return {'kind': 'lambda', 'parameters': params, 'body': bracket(depth)}
        if word == 'c':
            require(version in ('0.11', '0.12'), 'Function application requires edition 0.11')
            function = bracket(depth)
            take('[')
            args = []
            while peek() != ']':
                args.append(expression(depth + 1))
            take(']')
            return {'kind': 'apply', 'function': function, 'arguments': args}
        if word == 'j':
            require(version in ('0.10', '0.11', '0.12'), 'Messages require edition 0.10 or later')
            force = take()
            if force == 'v':
                require(version == '0.12', 'Answer questions require edition 0.12')
                return {'kind': 'question', 'function': bracket(depth)}
            require(force in FORCES, 'Unknown message force')
            return {'kind': 'message', 'force': FORCES[force], 'content': bracket(depth)}
        if word == 'o':
            require(version in ('0.10', '0.11', '0.12'), 'Messages require edition 0.10 or later')
            return {'kind': 'message_content', 'message': bracket(depth)}
        if word == 'b':
            require(version in ('0.9', '0.10', '0.11', '0.12'), 'Content requires edition 0.9 or later')
            return {'kind': 'content', 'variable': name(take()), 'body': bracket(depth)}
        if word == 't':
            require(version in ('0.9', '0.10', '0.11', '0.12'), 'Content evaluation requires edition 0.9 or later')
            return {'kind': 'evaluate', 'content': bracket(depth), 'situation': bracket(depth)}
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

    def statement_node(depth=0):
        require(depth <= MAX_DEPTH, 'Statement nesting exceeds 128 levels')
        marker = take()
        if marker == 'a':
            require(version in ('0.10', '0.11', '0.12'), 'Assumption scopes require edition 0.10 or later')
            condition = bracket(0)
            take('[')
            children = []
            while peek() != ']':
                children.append(statement_node(depth + 1))
            take(']')
            item = {'kind': 'suppose', 'condition': condition, 'statements': children}
        else:
            require(marker in ('s', 'q', 'l'), 'Unknown document word')
            item = {'kind': {'s': 'assert', 'q': 'ask', 'l': 'perform'}[marker], 'body': bracket(0)}
        take('.')
        return item

    if peek() in EDITIONS:
        edition = take()
        take(':')
    else:
        take('noema')
        edition = take()
        require(edition in EDITIONS, 'Unknown definition-language edition')
        take(edition)
    version = EDITIONS[edition]
    declarations, statements = [], []
    while peek() is not None:
        marker = peek()
        if marker in ('r', 'd'):
            take()
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
            take('.')
        else:
            statements.append(statement_node())
    return normalize_document({'schema_version': version, 'lexicon_version': version,
                               'declarations': declarations, 'statements': statements})


def format_document(document, compact=False):
    from .grammar import number_word
    doc = normalize_document(document)
    types = {v: k for k, v in MESSAGE_SORTS.items()}
    logic, quantifiers = {v: k for k, v in LOGIC.items()}, {v: k for k, v in QUANTIFIERS.items()}

    def type_word(type_):
        if isinstance(type_, dict):
            if type_['kind'] == 'question':
                return 'g[' + ' '.join(type_word(t) for t in type_['parameters']) + ']'
            return 'h[' + ' '.join(type_word(t) for t in type_['parameters']) + '] ' + type_word(type_['result'])
        return types[type_]

    def parameters(items):
        return ' '.join(p['name'] + ' ' + type_word(p['sort']) for p in items)

    def expression(expr):
        kind = expr['kind']
        if kind == 'question':
            return 'j v[' + expression(expr['function']) + ']'
        if kind == 'answer_matches':
            return 'h[' + expression(expr['question']) + '][' + ' '.join(expression(a) for a in expr['arguments']) + ']'
        if kind == 'function_ref':
            return 'p ' + expr['symbol']
        if kind == 'lambda':
            return 'i[' + parameters(expr['parameters']) + '][' + expression(expr['body']) + ']'
        if kind == 'apply':
            return 'c[' + expression(expr['function']) + '][' + ' '.join(expression(a) for a in expr['arguments']) + ']'
        if kind == 'message':
            return 'j ' + {v: k for k, v in FORCES.items()}[expr['force']] + '[' + expression(expr['content']) + ']'
        if kind == 'message_content':
            return 'o[' + expression(expr['message']) + ']'
        if kind == 'content':
            return 'b ' + expr['variable'] + '[' + expression(expr['body']) + ']'
        if kind == 'evaluate':
            return 't[' + expression(expr['content']) + '][' + expression(expr['situation']) + ']'
        if kind == 'variable':
            return 'v ' + expr['name']
        if kind == 'number':
            return 'n ' + ('u' if expr['numerator'] < 0 else 'p') + ' ' + number_word(abs(expr['numerator'])) + ' ' + number_word(expr['denominator'])
        if kind == 'call':
            return 'k ' + expr['symbol'] + '[' + ' '.join(expression(a) for a in expr['arguments']) + ']'
        if kind in logic:
            return logic[kind] + ''.join('[' + expression(a) + ']' for a in expr['arguments'])
        return quantifiers[kind] + ' ' + expr['variable'] + ' ' + type_word(expr['sort']) + '[' + expression(expr['body']) + ']'

    def statement_node(item):
        if item['kind'] == 'suppose':
            return 'a[' + expression(item['condition']) + '][' + ' '.join(statement_node(s) for s in item['statements']) + '].'
        return {'assert': 's', 'ask': 'q', 'perform': 'l'}[item['kind']] + '[' + expression(item['body']) + '].'

    edition = {v: k for k, v in EDITIONS.items()}[doc['schema_version']]
    lines = [edition + ':' if compact else 'noema ' + edition + ' ' + edition]
    for item in doc['declarations']:
        if item['kind'] == 'primitive':
            line = 'r ' + item['name'] + '[' + ' '.join(type_word(t) for t in item['parameters']) + '] ' + type_word(item['result'])
        else:
            line = 'd ' + item['name'] + '[' + parameters(item['parameters'])
            line += '] ' + type_word(item['result']) + '[' + expression(item['body']) + ']'
        lines.append(line + '.')
    lines.extend(statement_node(s) for s in doc['statements'])
    return '\n'.join(lines)


def definition_audit(document):
    """Report unexpanded assumptions; a primitive is never an explained definition."""
    doc = normalize_document(document)
    dependencies = {}

    def symbols(expr):
        result = {expr['symbol']} if expr['kind'] in ('call', 'function_ref') else set()
        for child in expr.get('arguments', []):
            result.update(symbols(child))
        for field in ('body', 'content', 'situation', 'message', 'condition', 'function', 'question'):
            if field in expr:
                result.update(symbols(expr[field]))
        for child in expr.get('statements', []):
            result.update(symbols(child))
        return result

    for d in doc['declarations']:
        dependencies[d['name']] = {d['name']} if d['kind'] == 'primitive' else set().union(
            *(dependencies[s] for s in symbols(d['body'])))
    return {'primitive_symbols': [d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'],
            'definition_primitive_dependencies': {d['name']: sorted(dependencies[d['name']])
                                                  for d in doc['declarations'] if d['kind'] == 'definition'},
            'statement_primitive_dependencies': [sorted(set().union(*(dependencies[s] for s in symbols(item))))
                                                 for item in doc['statements']]}
