"""Keep opaque typed candidates, all lookup slots and nonfactive goal relations."""
from copy import deepcopy
import json
import pytest
from noema.constructed_discourse import function_sort,normalize_document
from noema.constructed_semantics import DescriptionValue,FunctionValue,evaluate_document
from scripts import closing_function_reference_visible_profile as profile

canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'))
def call(name,*args):return dict(kind='call',symbol=name,arguments=list(args))
def forbidden(*args):raise AssertionError('Quoted role or candidate function was executed')
def role(kind,name='constraint',rank=0):
    return DescriptionValue(canonical(dict(kind='function_ref',symbol=name)),
        canonical(function_sort([profile.EXTRA[kind]['result'],'situation'],'truth')),rank)
def candidate(kind):
    sort=profile.EXTRA[kind]['result']
    return FunctionValue(tuple(sort['parameters']),sort['result'],forbidden)


def same_opaque(actual,expected):
    seen=set()
    while actual is not expected:
        if not isinstance(actual,FunctionValue):return False
        assert actual.parameters==expected.parameters and actual.result==expected.result
        assert id(actual) not in seen;seen.add(id(actual))
        fn=actual.implementation
        if isinstance(fn,FunctionValue):actual=fn;continue
        if fn is forbidden:return False
        assert fn.__module__=='noema.constructed_semantics'
        assert fn.__qualname__.endswith('.make_function.<locals>.guarded')
        cells=dict(zip(fn.__code__.co_freevars,(c.cell_contents for c in fn.__closure__)))
        actual=cells['raw']
    return True


@pytest.mark.parametrize('kind',tuple(profile.EXTRA))
def test_exact_function_identity_all_reference_slots_and_types(kind):
    r=role(kind);value=candidate(kind);other=candidate(kind);r2=role(kind,'differentconstraint')
    lookup=profile.TypedFunctionReferences(kind,{
        ('doc','node',r.syntax,'context'):value,('doc','node',r2.syntax,'context'):other})
    assert lookup.described('doc','node',r,'context') is value
    assert lookup.described('doc','node',r2,'context') is other
    for slot in range(4):
        args=['doc','node',r,'context'];args[slot]=role(kind,'unknown') if slot==2 else 'unknown'
        with pytest.raises(ValueError,match='Unknown typed function reference'):lookup.described(*args)
    for bad in (False,role(kind,rank=1),DescriptionValue(r.syntax,canonical(function_sort(['individual','situation'],'truth')))):
        with pytest.raises(ValueError,match='closed typed role'):lookup.described('doc','node',bad,'context')
    sort=profile.EXTRA[kind]['result']
    for bad in (False,FunctionValue(tuple(sort['parameters'])+('individual',),'truth',forbidden),
                FunctionValue(tuple(sort['parameters']),'individual',forbidden),
                FunctionValue(tuple(sort['parameters']),sort['result'],None)):
        with pytest.raises(ValueError,match='declared function type'):
            profile.TypedFunctionReferences(kind,{('doc','node',r.syntax,'context'):bad})


@pytest.mark.parametrize('kind',tuple(profile.EXTRA))
def test_native_lookup_does_not_execute_role_or_function(kind):
    doc=deepcopy(profile.library());sort=profile.EXTRA[kind]['result']
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in
        [('document','individual'),('node','individual'),('context','situation')]]
    doc['declarations'] += [dict(kind='primitive',name='roleprobe',parameters=[sort,'situation'],result='truth'),
        dict(kind='primitive',name='capture',parameters=[sort],result='truth'),
        dict(kind='definition',name='constraint',parameters=[dict(name='va',sort=sort),dict(name='vb',sort='situation')],
            result='truth',body=call('roleprobe',dict(kind='variable',name='va'),dict(kind='variable',name='vb')))]
    reference=call(kind,call('document'),call('node'),dict(kind='quote',body=dict(kind='function_ref',symbol='constraint')),call('context'))
    doc['statements']=[dict(kind='ask',body=call('capture',reference))]
    doc=normalize_document(doc);value=candidate(kind);different=candidate(kind)
    lookup=profile.TypedFunctionReferences(kind,{('doc','node',role(kind).syntax,'context'):value})
    def capture(actual):
        assert same_opaque(actual,value)
        assert not same_opaque(actual,different)
        return True
    handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    handlers.update(lookup.handlers());handlers.update(document=lambda:'doc',node=lambda:'node',context=lambda:'context',capture=capture)
    result=evaluate_document(doc,individuals=('doc','node'),situations=('context',),primitives=handlers)
    assert result[0]['value'] is True


def test_work_advancement_may_be_false_and_preserves_each_argument():
    doc=deepcopy(profile.library());sort=profile.CONTRACTS['workadvancement']['result']
    assert sort==function_sort(['individual','individual','situation'],'truth')
    slots=('person','work','context')
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in zip(slots,sort['parameters'],strict=True)]
    doc['statements']=[dict(kind='ask',body=dict(kind='apply',function=call('workadvancement'),arguments=[call(n) for n in slots]))]
    doc=normalize_document(doc);expected=('personA','workA','here');observed=[]
    for truth in (False,True):
        for pivot in (None,0,1,2):
            values=tuple(('elsewhere' if i==2 else 'other') if i==pivot else x for i,x in enumerate(expected))
            def relation(*args):observed.append(args);return truth and args==expected
            handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
            handlers.update({n:lambda x=x:x for n,x in zip(slots,values,strict=True)})
            handlers['workadvancement']=lambda:FunctionValue(tuple(sort['parameters']),'truth',relation)
            result=evaluate_document(doc,individuals=('personA','workA','other'),situations=('here','elsewhere'),primitives=handlers)
            assert result[0]['value'] is (truth and pivot is None)
            assert observed[-1]==values
    assert len(observed)==8


def test_unknown_reference_kind_is_rejected():
    with pytest.raises(ValueError,match='Unknown typed reference kind'):
        profile.TypedFunctionReferences('unknown',{})
