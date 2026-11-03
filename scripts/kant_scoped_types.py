"""Backward type references confined to completed parameter-list elements."""
from copy import deepcopy
from noema.constructed_discourse import sort
from scripts.kant_type_grammar import BASE_TYPES,TYPE_TOKENS,LIST_TOKENS

REFERENCE_TOKENS=frozenset(('bound0','bound1','bound_shift'))
MAX_NODES=4096
MAX_DEPTH=128


def _children(value):
    if isinstance(value,str):return ()
    kind=value['kind']
    if kind=='sequence':return (value['element'],)
    if kind=='description':return (value['result'],)
    return (*value['parameters'],*(() if kind=='question' else (value['result'],)))


class _Budget:
    def __init__(self):self.remaining=MAX_NODES
    def charge(self,depth):
        if depth>MAX_DEPTH:raise ValueError('Type nesting outside the drawing resource limit')
        self.remaining-=1
        if self.remaining<0:raise ValueError('Expanded type header exceeds node budget')
    def tree(self,value,depth=0):
        self.charge(depth)
        for child in _children(value):self.tree(child,depth+1)


def _reference(distance):
    return ['bound0'] if distance==0 else ['bound_shift']*(distance-1)+['bound1']


def _emit(value,scope,references):
    if isinstance(value,str):return ['type_'+value]
    kind=value['kind']
    if kind=='sequence':normal=['type_sequence',*_emit(value['element'],scope,references)]
    elif kind=='description':
        rank=value.get('rank',0)
        if rank>128:raise ValueError('Description rank outside the drawing resource limit')
        normal=['quote_raise']*rank+['type_description',*_emit(value['result'],scope,references)]
    else:
        parameters=value['parameters']
        normal=['type_'+kind,*_emit_list(parameters,scope,references)]
        if kind=='function':normal+=_emit(value['result'],(*scope,*parameters),references)
    if references:
        for distance,previous in enumerate(reversed(scope)):
            if value==previous:
                short=_reference(distance)
                return short if len(short)<len(normal) else normal
    return normal


def _emit_list(values,scope,references):
    result=[];local=list(scope)
    for value in values:
        result+=_emit(value,tuple(local),references);local.append(value)
    return [*result,'types_end']


def type_tokens(value,*,references=True):
    _Budget().tree(value)
    return _emit(sort(value,'0.16'),(),references)


def type_list_tokens(values,*,references=True):
    budget=_Budget()
    for value in values:budget.tree(value)
    return _emit_list([sort(v,'0.16') for v in values],(),references)


def _read(take,depth,first,scope,budget):
    token=take() if first is None else first
    if token in REFERENCE_TOKENS:
        distance=0
        while token=='bound_shift':
            distance+=1
            if distance>=len(scope):raise ValueError('Unbound visible type reference')
            token=take()
        if token not in ('bound0','bound1') or distance and token!='bound1':
            raise ValueError('Invalid visible type reference tail')
        distance+=token=='bound1'
        if distance>=len(scope):raise ValueError('Unbound visible type reference')
        value=scope[-1-distance]
        budget.tree(value,depth)  # Reject expansion before making a copy.
        return deepcopy(value)
    budget.charge(depth)
    rank=0
    while token=='quote_raise':
        rank+=1
        if rank>128:raise ValueError('Description rank outside the drawing resource limit')
        token=take()
    if rank and token!='type_description':raise ValueError('Type rank marker must precede a description type')
    if token.startswith('type_') and token[5:] in BASE_TYPES:return token[5:]
    if token=='type_sequence':return dict(kind='sequence',element=_read(take,depth+1,None,scope,budget))
    if token=='type_description':return dict(kind='description',result=_read(take,depth+1,None,scope,budget),**({'rank':rank} if rank else {}))
    if token in ('type_question','type_function'):
        parameters=_read_list(take,depth+1,scope,budget)
        result=dict(kind=token[5:],parameters=parameters)
        if token=='type_function':result['result']=_read(take,depth+1,None,(*scope,*parameters),budget)
        return result
    raise ValueError('Expected a public type constructor')


def _read_list(take,depth,scope,budget):
    result=[];prefixed=None
    while True:
        token=take()
        if token=='types_end':return result
        legacy=token=='types_more'
        if not legacy and token not in TYPE_TOKENS|REFERENCE_TOKENS|{'quote_raise'}:
            raise ValueError('Expected a type-list element or end')
        if prefixed is not None and legacy!=prefixed:raise ValueError('Mixed type-list encodings')
        prefixed=legacy
        result.append(_read(take,depth,None if legacy else token,(*scope,*result),budget))


def read_type(take,depth=0,*,first=None):return _read(take,depth,first,(),_Budget())


def read_type_list(take,depth=0):return _read_list(take,depth,(),_Budget())
