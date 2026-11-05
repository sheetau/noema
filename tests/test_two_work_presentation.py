import pytest
from scripts.two_work_presentation import expand_head


def call(name,args=()):return dict(kind='call',symbol=name,arguments=list(args))
def definition(name,body,parameters=()):return dict(kind='definition',name=name,parameters=list(parameters),body=body)


def test_explicit_heads_expand_but_quotation_and_argument_scopes_do_not():
    quoted=dict(kind='quote',body=call('b'))
    final=dict(kind='equal',arguments=[quoted,quoted])
    ds={'a':definition('a',call('b')),'b':definition('b',final)}
    s=dict(kind='assert',body=call('a'))
    actual,steps=expand_head(s,ds)
    assert steps==['a','b'] and actual['body']==final
    parameterized=dict(kind='assert',body=call('a',[call('b')]))
    assert expand_head(parameterized,ds)==(parameterized,[])
    assert s['body']==call('a')
    ds['b']=definition('b',call('a'))
    with pytest.raises(ValueError):expand_head(s,ds)
