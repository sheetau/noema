from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.shared_speech import *
from scripts.check_shared_speech import (doc,query,model,values,quote,unknown,base,uptake_checks,force_checks,
    realization_checks,binding_diagnostics,example,example_model,EXAMPLE,expected_slots,key)


def test_original_seven_definitions_and_meanings_are_preserved():
    shared={d['name']:d for d in composed()['declarations']}
    old=parse((ROOT/SOURCE).read_text(encoding='utf-8'));b=json.loads((ROOT/SOURCE_BASIS).read_text(encoding='utf-8'))
    for d in old['declarations']:
        assert shared[NAMES[d['name']]]==renamed(d,NAMES)
        assert basis()['definitions'][NAMES[d['name']]]==b['definitions'][d['name']]
    assert len(shared)==19 and all(d['kind']=='definition' for d in shared.values())


def test_native_contracts_have_exact_types_and_distinct_roles():
    d=composed();b=basis()
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['public_contracts'])==set(b['definitions'])=={x['name'] for x in d['declarations']}
    for x in d['declarations']:
        c=b['public_contracts'][x['name']]
        assert [p['sort'] for p in x['parameters']]==[a['sort'] for a in c['arguments']]
        assert len(set(a['role'] for a in c['arguments']))==len(x['parameters'])
        assert c['result']==x['result']


def test_uptake_force_and_realization_conditions():
    assert uptake_checks()['models']==128
    assert force_checks()['models']==288
    assert realization_checks()['models']==32


def test_every_interpretive_tuple_slot_is_bound_to_the_same_native_target():
    rows=binding_diagnostics()
    assert len(rows)==68 and not any(r['result'] for r in rows)


def test_integrated_question_request_advice_and_unrealized_promise():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model())==[True,False,False,False,False,True,True,False,True,True,False]


@pytest.mark.parametrize('name,promise',[('speechto',False),('speechrequest',False),('speechadvice',False),
    ('speechcommand',False),('speechpromise',True)])
def test_recorded_speech_does_not_evaluate_quoted_action_or_goal(name,promise):
    m=model(promise=promise,perform=unknown,achieve=unknown)
    assert values(doc([query(name,promise=promise)]),m)==[True]


@pytest.mark.parametrize('name,promise',[('requestrealized',False),('promiserealized',True)])
def test_realization_explicitly_requires_the_quoted_action(name,promise):
    with pytest.raises(ValueError,match='Unknown'):
        values(doc([query(name,promise=promise)]),model(promise=promise,perform=unknown))


def test_no_response_is_neither_acceptance_nor_decline():
    m=model(accepts=lambda *a:False,declines=lambda *a:False)
    assert values(doc([query(n) for n in ('speechunderstood','speechaccepted','speechdeclined')]),m)==[True,False,False]


def test_conflicting_responses_are_not_silently_repaired():
    assert values(doc([query(n) for n in ('speechaccepted','speechdeclined')]),model())==[True,True]


def test_acceptance_does_not_imply_realization_or_realization_acceptance():
    d=doc([query('speechaccepted'),query('requestrealized')])
    assert values(d,model(perform=lambda *a:False))==[True,False]
    assert values(d,model(accepts=lambda *a:False))==[False,True]


def test_question_form_alone_is_not_a_request():
    # A known surface question remains a question; the contextual target and
    # expressed solicitation must be supplied independently.
    assert values(doc([query('speechto'),query('speechrequest')]),model(solicits=lambda *a:False))==[True,False]
    assert values(doc([query('speechto'),query('speechrequest')]),model(targets=lambda *a:False))==[True,False]


def test_equitruth_description_and_force_changes_require_new_grounding():
    for name in ('otherquestion','directiveform','promiseform'):
        d=doc([query('speechrequest')]);d['statements'][0]['body']['arguments'][4]=quote(name)
        assert values(d,model())==[False]
    d=doc([query('speechrequest')]);d['statements'][0]['body']['arguments'][9]=quote('otheraction')
    assert values(d,model())==[False]


def test_advice_requires_same_reason_and_does_not_assert_its_truth():
    assert values(doc([query('speechadvice')]),model(achieve=unknown,perform=unknown))==[True]
    assert values(doc([query('speechadvice')]),model(reasonshown=lambda *a:False))==[False]
    assert values(doc([query('speechadvice')]),model(supports=lambda *a:False))==[False]


def test_promise_is_not_just_predicting_an_outcome():
    assert values(doc([query('speechto',promise=True),query('speechpromise',promise=True)]),
        model(promise=True,undertakes=lambda *a:False))==[True,False]


def test_command_requires_authority_claim_independent_of_request():
    d=doc([query('speechrequest'),query('speechcommand')])
    assert values(d,model(claims=lambda *a:False))==[True,False]
    assert values(d,model(solicits=lambda *a:False))==[False,True]


def test_realization_keeps_speaker_recipient_and_time_distinct():
    for promise,name in ((False,'requestrealized'),(True,'promiserealized')):
        d=doc([query(name,promise=promise)])
        wrong='b' if promise else 'a'
        assert values(d,model(promise=promise,perform=lambda a,w:a==wrong and w=='later'))==[False]
        assert values(d,model(promise=promise,before=lambda *a:False))==[False]
        assert values(d,model(promise=promise,perform=lambda a,w:w=='now'))==[False]


@pytest.mark.parametrize('name,relation,promise',[('speechreceived','receives',False),
    ('speechunderstood','understands',False),('speechaccepted','accepts',False),('speechdeclined','declines',False),
    ('speechrequest','targets',False),('speechrequest','solicits',False),('speechadvice','supports',False),
    ('speechadvice','reasonshown',False),('speechpromise','undertakes',True),('speechcommand','claims',False)])
def test_unknown_social_input_is_not_a_negative_response(name,relation,promise):
    m=model(promise=promise);m[relation]=unknown
    with pytest.raises(ValueError,match='Unknown'):values(doc([query(name,promise=promise)]),m)
