"""Keep exact candidate values, closed quotations and every accounting role."""
from copy import deepcopy
from fractions import Fraction as Q
import json
import pytest
from noema.constructed_discourse import function_sort, normalize_document
from noema.constructed_semantics import DescriptionValue, FunctionValue, evaluate_document
from scripts import energy_reference_visible_profile as profile

canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'))
def call(name,*args):return dict(kind='call',symbol=name,arguments=list(args))
def forbidden(*args):raise AssertionError('Quoted role or unrelated contract was executed')
def role(name='candidateconstraint',rank=0):
    return DescriptionValue(canonical(dict(kind='function_ref',symbol=name)),
        canonical(function_sort(['number','situation'],'truth')),rank)


def test_exact_candidates_preserve_zero_sign_and_distinct_roles():
    descriptions=[role('constraint'+chr(97+i)) for i in range(3)]
    values=[Q(-3,2),0,Q(7,3)]
    lookup=profile.RationalReferences({('doc','node',r.syntax,'context'):v for r,v in zip(descriptions,values)})
    for r,v in zip(descriptions,values):
        assert lookup.described('doc','node',r,'context')==v
        assert isinstance(lookup.described('doc','node',r,'context'),Q)


@pytest.mark.parametrize('slot',range(4))
def test_unknown_reference_slot_is_rejected(slot):
    r=role();lookup=profile.RationalReferences({('doc','node',r.syntax,'context'):Q(2,3)})
    args=['doc','node',r,'context']
    args[slot]=role('unknownconstraint') if slot==2 else 'unknown'
    with pytest.raises(ValueError,match='Unknown rational reference'):lookup.described(*args)


def test_inexact_candidates_and_nonclosed_or_wrongly_typed_roles_are_rejected():
    for value in (True,False,1.5,'1/2',None):
        with pytest.raises(ValueError,match='exact rational candidate'):
            profile.RationalReferences({('doc','node',role().syntax,'context'):value})
    lookup=profile.RationalReferences({})
    for description in (False,role(rank=1),DescriptionValue(role().syntax,'"individual"')):
        with pytest.raises(ValueError,match='closed rational role description'):
            lookup.described('doc','node',description,'context')


def test_native_reference_keeps_fraction_without_executing_quoted_role():
    document=deepcopy(profile.library())
    document['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=t)
        for n,t in [('document','individual'),('node','individual'),('context','situation')]]
    document['declarations'] += [dict(kind='primitive',name='roleprobe',parameters=['number','situation'],result='truth'),
        dict(kind='definition',name='candidateconstraint',parameters=[dict(name='va',sort='number'),dict(name='vb',sort='situation')],
            result='truth',body=call('roleprobe',dict(kind='variable',name='va'),dict(kind='variable',name='vb')))]
    number=dict(kind='number',numerator=-3,denominator=2)
    reference=call('describedrationalreference',call('document'),call('node'),
        dict(kind='quote',body=dict(kind='function_ref',symbol='candidateconstraint')),call('context'))
    document['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[reference,number]))]
    document=normalize_document(document)
    for candidate,wanted in [(Q(-3,2),True),(Q(-2),False)]:
        lookup=profile.RationalReferences({('doc','node',role().syntax,'context'):candidate})
        handlers={d['name']:forbidden for d in document['declarations'] if d['kind']=='primitive'}
        handlers.update(lookup.handlers())
        handlers.update(document=lambda:'doc',node=lambda:'node',context=lambda:'context')
        result=evaluate_document(document,individuals=('doc','node'),situations=('context',),primitives=handlers)
        assert result[0]['value'] is wanted


def test_closed_energy_accounting_keeps_all_shared_arguments():
    document=deepcopy(profile.library())
    types=profile.CONTRACTS['closedenergyexchange']['result']['parameters']
    slots=['arg'+chr(97+i) for i in range(len(types))]
    document['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=t) for n,t in zip(slots,types)]
    document['statements']=[dict(kind='ask',body=dict(kind='apply',function=call('closedenergyexchange'),
        arguments=[call(n) for n in slots]))]
    document=normalize_document(document)
    expected=tuple('object'+str(i) for i in range(7))+('context',)
    observed=[]
    def relation(*args):
        observed.append(args)
        return args==expected
    for pivot in (None,*range(len(types))):
        values=[('othercontext' if i==7 else 'other') if i==pivot else value for i,value in enumerate(expected)]
        handlers={d['name']:forbidden for d in document['declarations'] if d['kind']=='primitive'}
        handlers.update({n:lambda value=value:value for n,value in zip(slots,values)})
        handlers['closedenergyexchange']=lambda:FunctionValue(tuple(types),'truth',relation)
        result=evaluate_document(document,individuals=(*expected[:7],'other'),situations=('context','othercontext'),primitives=handlers)
        assert result[0]['value'] is (pivot is None)
        assert observed[-1]==tuple(values)
    assert len(observed)==9
