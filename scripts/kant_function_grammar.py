"""Recover an expression's result type from public signatures and visible binders.

This supplies the arity of an already read function. It neither evaluates a
function nor replaces the final native syntax/type validation.
"""
from noema.constructed_discourse import function_sort,description_sort


def expression_type(node,scope,words,depth=0):
    if depth>128:raise ValueError('Function type inference exceeds expression depth')
    kind=node['kind']
    if kind in ('call','function_ref'):
        if node['symbol'] not in words:raise ValueError('Unknown public function or value')
        entry=words[node['symbol']][1]
        return function_sort(entry['parameters'],entry['result']) if kind=='function_ref' else entry['result']
    if kind=='variable':
        for name,type_ in reversed(scope):
            if name==node['name']:return type_
        raise ValueError('Unbound variable in function expression')
    if kind=='lambda':
        inner=(*scope,*((p['name'],p['sort']) for p in node['parameters']))
        return function_sort([p['sort'] for p in node['parameters']],
            expression_type(node['body'],inner,words,depth+1))
    if kind=='apply':
        type_=expression_type(node['function'],scope,words,depth+1)
        require_function(type_)
        if len(node['arguments'])!=len(type_['parameters']):raise ValueError('Function argument count mismatch')
        return type_['result']
    if kind=='quote':
        return description_sort(expression_type(node['body'],(),words,depth+1),node.get('rank',0))
    if kind in ('and','or','implies','equal','not','forall','exists','evaluate'):return 'truth'
    raise ValueError('Unsupported expression in visible function type inference')


def require_function(type_):
    if not isinstance(type_,dict) or type_.get('kind')!='function':
        raise ValueError('Visible application requires a function type')
    return type_
