from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.shared_answers import *
from scripts.check_shared_answers import (doc,args,model,values,queries,information_checks,projection_checks,
    example,example_model,EXAMPLE_RESULTS,EXAMPLE,unknown,question,ref)
from scripts.shared_reference import truth


def test_twenty_composed_definitions_have_no_new_primitives():
    d=composed();assert len(d['declarations'])==20
    assert all(x['kind']=='definition' for x in d['declarations'])
    assert parse(format_graph(d))==parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    b=basis();assert not b['primitives']
    assert set(b['definitions'])==set(b['public_contracts'])=={x['name'] for x in d['declarations']}
    for x in raw()['declarations']:
        c=b['public_contracts'][x['name']]
        assert [p['sort'] for p in x['parameters']]==[p['sort'] for p in c['arguments']]
        assert [p['name'] for p in x['parameters']]==[p['role'] for p in c['arguments']]
        assert c['result']==x['result']


def test_all_unary_and_ordered_pair_answer_sets_against_independent_oracle():
    assert information_checks()==dict(models=64,candidates=2,closed_flags=[False,True],checks_per_model=11)
    assert information_checks(True)==dict(models=4096,candidates=4,closed_flags=[False,True],checks_per_model=13)


def test_every_pair_projection_and_fixed_slot():
    assert projection_checks()==dict(models=16,point_checks=192,all_ordered_pairs=True)


def test_integrated_answers_and_false_exhaustive_reply():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model())==EXAMPLE_RESULTS
    from scripts.shared_speech import composed as speech
    shared={x['name']:x for x in speech()['declarations']}
    for x in example()['declarations']:
        if x['name'] in ('speechto','speechpresented'):assert x==shared[x['name']]


@pytest.mark.parametrize('pair',[False,True])
def test_true_but_empty_information_does_not_claim_a_partial_answer(pair):
    p='pair' if pair else 'single'
    m=model(**{p+'question':lambda *a:True,p+'positive':lambda *a:False,p+'negative':lambda *a:False})
    result=values(doc(queries(pair)),m)
    assert result[:9]==[True,True,False,False,False,False,False,False,False]
    assert all(result[9:])


@pytest.mark.parametrize('pair',[False,True])
def test_actual_coverage_without_closure_remains_open_information(pair):
    p='pair' if pair else 'single';pred=lambda *a:a[0]=='a'
    m=model(**{p+'question':pred,p+'positive':pred,p+'negative':lambda *a:False})
    assert values(doc(queries(pair)),m)[:9]==[True,True,True,True,False,True,True,False,False]


@pytest.mark.parametrize('pair',[False,True])
def test_negative_information_is_not_automatically_all_answers(pair):
    p='pair' if pair else 'single'
    m=model(**{p+'question':lambda *a:a[0]=='a',p+'positive':lambda *a:False,p+'negative':lambda *a:a[0]=='b'})
    assert values(doc(queries(pair)),m)[:9]==[True,True,True,False,False,False,True,False,False]


@pytest.mark.parametrize('pair',[False,True])
def test_conflicting_information_is_preserved_and_detected(pair):
    p='pair' if pair else 'single'
    m=model(**{p+'question':lambda *a:True,p+'positive':lambda *a:True,p+'negative':lambda *a:True})
    assert values(doc(queries(pair)),m)[:9]==[False,False,True,True,False,False,False,False,False]


@pytest.mark.parametrize('pair',[False,True])
def test_explicit_empty_complete_answer_requires_no_actual_answers(pair):
    p='pair' if pair else 'single'
    m=model(**{p+'question':lambda *a:False,p+'positive':lambda *a:False,p+'negative':lambda *a:False})
    assert values(doc(queries(pair)),m)[:9]==[True,True,False,True,False,True,False,False,True]


def test_marginal_answers_cannot_be_multiplied_into_correct_pairs():
    m=model(pairquestion=lambda x,y:x==y,pairpositive=lambda x,y:True,pairnegative=lambda x,y:False)
    assert values(doc(queries(True)),m)[:9]==[True,False,True,True,False,False,False,False,False]
    # Both marginal questions admit both individuals, but cross pairs fail.
    qpair=args(True)[0]
    assert values(doc([matches(call('answerfirstquestion',qpair),call('aki')),
        matches(call('answersecondquestion',qpair),call('nao')),matches(qpair,call('aki'),call('nao'))]),m)==[True,True,False]


@pytest.mark.parametrize('pair',[False,True])
@pytest.mark.parametrize('field',['question','positive','negative'])
def test_unknown_interpretation_is_not_negative_or_unsettled(pair,field):
    p='pair' if pair else 'single';prefix='pairanswer' if pair else 'answer'
    m=model(**{p+'question':lambda *a:True,p+'positive':lambda *a:False,p+'negative':lambda *a:False})
    m[p+field]=unknown
    with pytest.raises(ValueError,match='Unknown'):
        values(doc([call(prefix+'sound',*args(pair))]),m)


def test_information_status_does_not_need_the_question_truth():
    m=model(singlepositive=lambda x:x=='a',singlenegative=lambda x:False)
    a=args();assert values(doc([call('answerconsistent',*a[1:]),call('answerinformative',*a[1:]),
        call('answerunsettled',*a[1:],call('nao'))]),m)==[True,True,True]


def test_quoted_reply_does_not_evaluate_unknown_answer_truth():
    d=deepcopy(example());index=next(i for i,x in enumerate(d['declarations']) if x['name']=='replycontent')
    d['declarations'][index]['body']['body']=call('unknownanswer')
    d['declarations'].insert(index,dict(kind='primitive',name='unknownanswer',parameters=[],result=T))
    statements=d['statements'][-2:];m=example_model();m['unknownanswer']=unknown
    d['statements']=statements[:1];assert values(d,m)==[True]
    d['statements']=statements[1:]
    with pytest.raises(ValueError,match='Unknown'):values(d,m)


def test_wrong_answer_type_and_arity_are_rejected():
    with pytest.raises(ValueError):doc([call('answersound',*args(True))])
    with pytest.raises(ValueError):doc([matches(args(True)[0],call('aki'))])
    with pytest.raises(ValueError):doc([matches(args()[0],call('aki'),call('nao'))])
