"""Typed lookup preserves identity, rejects mismatches, and defers execution."""
from copy import deepcopy
from fractions import Fraction as Q
import json
import pytest
from noema.constructed_discourse import function_sort,normalize_document
from noema.constructed_semantics import DescriptionValue,FunctionValue,evaluate_document
from scripts import tenth_motion_visible_profile as profile

KINDS=tuple(profile.EXTRA)
CUT=function_sort(['number'],'truth')
canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'))
def forbidden(*args):raise AssertionError('Quoted role or candidate executed during lookup')
def role_for(kind,name='candidateconstraint',rank=0):
    return DescriptionValue(canonical(dict(kind='function_ref',symbol=name)),
        canonical(function_sort([profile.EXTRA[kind]['result'],'situation'],'truth')),rank)
def candidate_for(kind,implementation=forbidden):
    t=profile.EXTRA[kind]['result']
    return FunctionValue(tuple(t['parameters']),t['result'],implementation)


@pytest.mark.parametrize('kind',KINDS)
def test_lookup_keeps_candidate_identity_and_distinct_closed_roles(kind):
    a,b=candidate_for(kind),candidate_for(kind)
    first,second=role_for(kind),role_for(kind,'otherconstraint')
    lookup=profile.TypedFunctionReferences(kind,{
        ('doc','node',first.syntax,'context'):a,('doc','node',second.syntax,'context'):b})
    assert lookup.described('doc','node',first,'context') is a
    assert lookup.handlers()[kind]('doc','node',second,'context') is b


@pytest.mark.parametrize('kind',KINDS)
@pytest.mark.parametrize('slot',range(4))
def test_unknown_document_node_role_or_context_is_rejected(kind,slot):
    role=role_for(kind);key=('doc','node',role.syntax,'context')
    lookup=profile.TypedFunctionReferences(kind,{key:candidate_for(kind)})
    arguments=['doc','node',role,'context']
    arguments[slot]=role_for(kind,'unknownconstraint') if slot==2 else 'unknown'
    with pytest.raises(ValueError,match='Unknown typed function reference'):
        lookup.described(*arguments)


@pytest.mark.parametrize('kind',KINDS)
def test_wrong_candidate_shapes_and_nonclosed_roles_are_rejected(kind):
    other=next(n for n in KINDS if n!=kind)
    for candidate in (False,candidate_for(other),FunctionValue(('individual',),'truth',forbidden),
            FunctionValue(tuple(profile.EXTRA[kind]['result']['parameters']),profile.EXTRA[kind]['result']['result'],None)):
        with pytest.raises(ValueError,match='declared function type'):
            profile.TypedFunctionReferences(kind,{('doc','node','role','context'):candidate})
    lookup=profile.TypedFunctionReferences(kind,{})
    for role in (False,role_for(other),role_for(kind,rank=1),DescriptionValue('{}','"individual"')):
        with pytest.raises(ValueError,match='closed typed role description'):
            lookup.described('doc','node',role,'context')
    with pytest.raises(ValueError,match='Unknown typed reference kind'):
        profile.TypedFunctionReferences('unknown',{})


@pytest.mark.parametrize('kind',KINDS)
def test_native_quoted_role_retrieves_callable_with_the_declared_result(kind):
    def call(name,*arguments):return dict(kind='call',symbol=name,arguments=list(arguments))
    def apply(fn,*arguments):return dict(kind='apply',function=fn,arguments=list(arguments))
    t=profile.EXTRA[kind]['result'];calls=[]
    cut=FunctionValue(('number',),'truth',lambda q:q<1)
    def candidate(value):
        calls.append(value)
        if t['result']=='truth':return value.implementation(Q(0))
        return FunctionValue(('individual',),CUT,lambda point:value)
    value=candidate_for(kind,candidate);role=role_for(kind)
    lookup=profile.TypedFunctionReferences(kind,{('doc','node',role.syntax,'context'):value})
    doc=deepcopy(profile.library())
    doc['declarations'] += [dict(kind='primitive',name=name,parameters=[],result=sort)
        for name,sort in (('document','individual'),('node','individual'),('context','situation'),('inputcut',CUT),('point','individual'))]
    doc['declarations'] += [dict(kind='primitive',name='roleprobe',parameters=[t,'situation'],result='truth'),
        dict(kind='definition',name='candidateconstraint',parameters=[dict(name='va',sort=t),dict(name='vb',sort='situation')],
            result='truth',body=call('roleprobe',dict(kind='variable',name='va'),dict(kind='variable',name='vb')))]
    fn=call(kind,call('document'),call('node'),dict(kind='quote',body=dict(kind='function_ref',symbol='candidateconstraint')),call('context'))
    body=apply(fn,call('inputcut'))
    if t['result']!='truth':body=apply(apply(body,call('point')),dict(kind='number',numerator=0,denominator=1))
    doc['statements']=[dict(kind='ask',body=body)]
    doc=normalize_document(doc)
    handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    handlers.update(lookup.handlers())
    handlers.update(document=lambda:'doc',node=lambda:'node',context=lambda:'context',inputcut=lambda:cut,point=lambda:'point')
    result=evaluate_document(doc,individuals=('doc','node','point'),situations=('context',),primitives=handlers)
    # Native evaluation wraps function arguments with checked call boundaries.
    # Direct lookup identity is tested above; here distinguish the actual input.
    assert result[0]['value'] is True and len(calls)==1
    assert calls[0].parameters==('number',) and calls[0].result=='truth'
    assert calls[0].implementation(Q(0)) and not calls[0].implementation(Q(2))
    handlers['inputcut']=lambda:FunctionValue(('number',),'truth',lambda q:q<-1)
    result=evaluate_document(doc,individuals=('doc','node','point'),situations=('context',),primitives=handlers)
    assert result[0]['value'] is False and len(calls)==2
