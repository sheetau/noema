"""Recover an expression's result type from public signatures and visible binders.

This supplies the arity of an already read function. It neither evaluates a
function nor replaces the final native syntax/type validation.
"""
from noema.constructed_discourse import function_sort,description_sort


def expression_type(node,scope,words,depth=0):
    if depth>128:raise ValueError('Function type inference exceeds expression depth')
    kind=node['kind']
    if kind=='number':return 'number'
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
    if kind in ('apply','quoted_application'):
        actual=expression_type(node['function'],scope,words,depth+1)
        type_=application_type(kind,actual)
        if len(node['arguments'])!=len(type_['parameters']):raise ValueError('Function argument count mismatch')
        if kind=='quoted_application':
            descriptions=[require_description(expression_type(a,scope,words,depth+1)) for a in node['arguments']]
            rank=max([actual.get('rank',0)]+[t.get('rank',0) for t in descriptions])
            return description_sort(type_['result'],rank)
        return type_['result']
    if kind=='quote':
        return description_sort(expression_type(node['body'],(),words,depth+1),node.get('rank',0))
    if kind in ('quoted_lift','disquote'):
        actual=require_description(expression_type(node['description'],scope,words,depth+1))
        return description_sort(actual,actual.get('rank',0)) if kind=='quoted_lift' else actual['result']
    if kind=='content':return 'content'
    if kind in ('and','or','implies','equal','not','forall','exists','evaluate'):return 'truth'
    raise ValueError('Unsupported expression in visible function type inference')


def require_function(type_):
    if not isinstance(type_,dict) or type_.get('kind')!='function':
        raise ValueError('Visible application requires a function type')
    return type_


def require_description(type_):
    if not isinstance(type_,dict) or type_.get('kind')!='description':
        raise ValueError('Visible quotation operation requires a description type')
    return type_


def application_type(kind,type_):
    if kind=='quoted_application':type_=require_description(type_)['result']
    return require_function(type_)
