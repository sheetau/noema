from copy import deepcopy
from fractions import Fraction as F
import pytest
from noema.constructed_semantics import evaluate_document
from noema.constructed_discourse import normalize_document
from scripts.general_probability import *


def number(n):
    x=F(n);return dict(kind='number',numerator=x.numerator,denominator=x.denominator)
def ref(n):return dict(kind='function_ref',symbol=n)
def seq(names):return dict(kind='sequence',element=I,items=[call(n) for n in names])


def evaluate(questions,weights=(F(1,4),F(3,4)),*,condition=('a',),event=('a',),likelihood=(1,F(1,3)),posterior=(F(1,2),F(1,2)),unknown=False):
    d=composed();d['declarations']+= [dict(kind='primitive',name=n,parameters=ps,result=t) for n,ps,t in
        [('first',[],I),('second',[],I),('weight',[I],N),('event',[I],T),('condition',[I],T),('likelihood',[I],N),('posterior',[I],N)]]
    d['statements']=[dict(kind='ask',body=q) for q in questions];d=normalize_document(d)
    def property_(x):
        if unknown:raise ValueError('Unknown event information')
        return x in event
    model=dict(rationalbelow=lambda a,b:a<b,rationaladd=lambda a,b:a+b,rationalmultiply=lambda a,b:a*b,truthindicator=lambda a:F(int(a)),
        first=lambda:'a',second=lambda:'b',weight=lambda x:F(weights[('a','b').index(x)]),event=property_,condition=lambda x:x in condition,
        likelihood=lambda x:F(likelihood[('a','b').index(x)]),posterior=lambda x:F(posterior[('a','b').index(x)]))
    return [r['value'] for r in evaluate_document(d,individuals=('a','b'),situations=('now','later'),primitives=model)]


def base():return [seq(('first','second')),ref('weight')]


def test_unequal_weights_and_condition_direction():
    questions=[call('probabilityvalue',*base(),ref('event'),number(F(1,4))),call('probabilityvalue',*base(),ref('event'),number(F(1,2))),
        call('conditionalprobability',*base(),ref('condition'),ref('event'),number(F(1,4))),
        call('conditionalprobability',*base(),ref('event'),ref('condition'),number(1))]
    assert evaluate(questions,condition=('a','b'))==[True,False,True,True]


@pytest.mark.parametrize('cases,weights',[(('first','first'),(F(1,2),F(1,2))),((),(0,0)),(('first','second'),(-1,2)),(('first','second'),(F(1,3),F(1,3)))])
def test_invalid_spaces_are_not_probabilities(cases,weights):
    assert evaluate([call('probabilityspace',seq(cases),ref('weight'))],weights=weights)==[False]


def test_zero_probability_condition_is_undefined_and_unknown_is_rejected():
    assert evaluate([call('conditionaldefined',*base(),ref('condition')),
        call('conditionalprobability',*base(),ref('condition'),ref('event'),number(0))],condition=())==[False,False]
    with pytest.raises(ValueError,match='Unknown event'):evaluate([call('probabilityvalue',*base(),ref('event'),number(0))],unknown=True)


def test_intervals_independence_and_evidence_update_have_separate_conditions():
    qs=[call('probabilityinterval',*base(),ref('event'),number(F(1,5)),number(F(1,3))),
        call('probabilityinterval',*base(),ref('event'),number(F(1,3)),number(F(1,5))),
        call('probabilityindependent',*base(),ref('event'),ref('condition')),
        call('probabilityupdated',*base(),ref('likelihood'),ref('posterior'))]
    assert evaluate(qs)==[True,False,False,True]
    assert evaluate(qs,posterior=(F(1,4),F(3,4)))[-1] is False
    assert evaluate(qs,likelihood=(0,0))[-1] is False
