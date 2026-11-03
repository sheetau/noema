"""Prefix type grammar shared by typed binders and future declarations.

These are public grammatical categories, not lexical primitives or type IDs.
Parameter lists have explicit cons/nil structure; no inferred arity is needed.
"""
from noema.constructed_discourse import sort

BASE_TYPES = ('individual', 'number', 'truth', 'situation', 'content', 'message')
TYPE_TOKENS = frozenset('type_'+name for name in (*BASE_TYPES, 'sequence', 'description', 'question', 'function'))
LIST_TOKENS = frozenset(('types_more', 'types_end'))


def type_tokens(value):
    value = sort(value, '0.16')
    if isinstance(value, str):
        return ['type_'+value]
    kind = value['kind']
    if kind == 'sequence':
        return ['type_sequence', *type_tokens(value['element'])]
    if kind == 'description':
        rank = value.get('rank', 0)
        if rank > 128:
            raise ValueError('Description rank outside the drawing resource limit')
        return ['quote_raise']*rank + ['type_description', *type_tokens(value['result'])]
    if kind == 'question':
        return ['type_question', *type_list_tokens(value['parameters'])]
    return ['type_function', *type_list_tokens(value['parameters']), *type_tokens(value['result'])]


def type_list_tokens(values):
    return [token for value in values for token in ('types_more', *type_tokens(value))] + ['types_end']


def read_type(take, depth=0):
    if depth > 128:
        raise ValueError('Type nesting outside the drawing resource limit')
    token = take()
    rank=0
    while token=='quote_raise':
        rank+=1
        if rank>128:
            raise ValueError('Description rank outside the drawing resource limit')
        token=take()
    if rank and token!='type_description':
        raise ValueError('Type rank marker must precede a description type')
    if token.startswith('type_') and token[5:] in BASE_TYPES:
        return token[5:]
    if token == 'type_sequence':
        return dict(kind='sequence', element=read_type(take, depth+1))
    if token == 'type_description':
        return dict(kind='description', result=read_type(take, depth+1), **({'rank':rank} if rank else {}))
    if token == 'type_question':
        return dict(kind='question', parameters=read_type_list(take, depth+1))
    if token == 'type_function':
        parameters = read_type_list(take, depth+1)
        return dict(kind='function', parameters=parameters, result=read_type(take, depth+1))
    raise ValueError('Expected a public type constructor')


def read_type_list(take, depth=0):
    result = []
    while True:
        token = take()
        if token == 'types_end':
            return result
        if token != 'types_more':
            raise ValueError('Expected type-list continuation or end')
        result.append(read_type(take, depth))
