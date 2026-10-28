"""Exercise the retained general function contracts through Native application."""
from copy import deepcopy
from fractions import Fraction as Q
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_semantics import FunctionValue,evaluate_document
from scripts import tenth_mass_visible_profile as profile

FUNCTIONS=tuple(n for n,d in profile.CONTRACTS.items() if not d['parameters'] and isinstance(d['result'],dict))
CUT=dict(kind='function',parameters=['number'],result='truth')
def call(name,*args):return dict(kind='call',symbol=name,arguments=list(args))
def apply(fn,*args):return dict(kind='apply',function=fn,arguments=list(args))
def forbidden(*args):raise AssertionError('Unrelated contract was executed')


def test_general_contracts_do_not_publish_source_references_or_arithmetic_aliases():
    assert len(profile.CONTRACTS)==35 and len(FUNCTIONS)==15 and not profile.EXTRA
    assert not set(profile.SOURCE_RELATIONS).intersection({'zza','zzd','zrcsubject','zrcrole','eiszk','eisyp','eisyq'})
    assert profile.MATH_ALIASES=={'zza':'rationalbelow','zzd':'rationalmultiply'}
    assert parse(format_graph(profile.library()))==profile.library()


@pytest.mark.parametrize('name',FUNCTIONS)
def test_general_function_values_keep_every_argument_and_result_type(name):
    declaration=profile.CONTRACTS[name];type_=declaration['result']
    assert type_['kind']=='function'
    arguments=type_['parameters'];result_type=type_['result']
    assert all(t in ('individual','situation') or t==CUT for t in arguments)
    assert result_type in ('individual','truth') or result_type==CUT
    observed=[]
    def value(sort,index,changed=False):
        if sort=='individual':return 'object'+str(index)+('other' if changed else '')
        if sort=='situation':return 'context'+str(index)+('other' if changed else '')
        assert sort==CUT
        threshold=Q(index+1)+(10 if changed else 0)
        return FunctionValue(('number',),'truth',lambda q:q<threshold)
    def key(sort,x,index):
        if sort in ('individual','situation'):return x
        assert isinstance(x,FunctionValue) and x.parameters==('number',) and x.result=='truth'
        return tuple(x(Q(index+1)+offset) for offset in (-Q(1,2),Q(1,2),Q(21,2)))
    expected=tuple(key(t,value(t,i),i) for i,t in enumerate(arguments))
    def function(*xs):
        actual=tuple(key(t,x,i) for i,(t,x) in enumerate(zip(arguments,xs,strict=True)))
        observed.append(actual);matches=actual==expected
        if result_type=='truth':return matches
        if result_type=='individual':return 'answer' if matches else 'otheranswer'
        return FunctionValue(('number',),'truth',lambda q:q<(Q(1) if matches else Q(-1)))
    fn=FunctionValue(tuple(arguments),result_type,function)
    document=deepcopy(profile.library());slots=['arg'+chr(97+i) for i in range(len(arguments))]
    document['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=t) for n,t in zip(slots,arguments)]
    expression=apply(call(name),*(call(n) for n in slots))
    if result_type=='individual':
        document['declarations'].append(dict(kind='primitive',name='expectedanswer',parameters=[],result='individual'))
        expression=dict(kind='equal',arguments=[expression,call('expectedanswer')])
    elif result_type==CUT:expression=apply(expression,dict(kind='number',numerator=0,denominator=1))
    document['statements']=[dict(kind='ask',body=expression)]
    document=parse(format_graph(document))
    individuals=['answer','otheranswer']+[value('individual',i,changed) for i in range(len(arguments)) for changed in (False,True)]
    situations=[value('situation',i,changed) for i in range(len(arguments)) for changed in (False,True)]
    for changed in (None,*range(len(arguments))):
        handlers={d['name']:forbidden for d in document['declarations'] if d['kind']=='primitive'}
        handlers[name]=lambda:fn
        if result_type=='individual':handlers['expectedanswer']=lambda:'answer'
        for i,(n,t) in enumerate(zip(slots,arguments)):
            x=value(t,i,changed==i);handlers[n]=lambda x=x:x
        result=evaluate_document(document,individuals=individuals,situations=situations,primitives=handlers)
        assert result[0]['value']==(changed is None),(name,changed)
    assert len(observed)==len(arguments)+1
