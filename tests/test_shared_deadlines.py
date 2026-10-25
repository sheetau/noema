from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.shared_deadlines import *
from scripts.check_shared_deadlines import (doc,values,model,unknown,query,arguments,ref,quote,temporal_checks,frame_checks,
    binding_diagnostics,example,example_model,EXAMPLE,EXAMPLE_RESULTS,status_queries,describe)


def test_new_definitions_and_reused_contracts_match_published_native():
    d=composed();b=basis();byname={x['name']:x for x in d['declarations']}
    assert len(byname)==22 and len(MEANINGS)==14 and not b['primitives']
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['definitions'])==set(b['public_contracts'])==set(byname)
    for source in SOURCES:
        old={x['name']:x for x in parse((ROOT/source['document']).read_text(encoding='utf-8'))['declarations']}
        ob=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        for name in source['names']:
            assert byname[name]==old[name]
            assert b['definitions'][name]==ob['definitions'][name] and b['public_contracts'][name]==ob['public_contracts'][name]
    for x in raw()['declarations']:
        c=b['public_contracts'][x['name']]
        assert [p['sort'] for p in x['parameters']]==[p['sort'] for p in c['arguments']] and x['result']==c['result']
        assert len(set(p['role'] for p in c['arguments']))==len(x['parameters'])


def test_all_finite_realization_release_and_assessment_combinations():
    assert temporal_checks()==dict(models=1024,people=2,time_points=4,checks_per_model=10,complete_flags=[False,True])


def test_invalid_frames_and_each_grounding_slot():
    assert len(frame_checks())==8
    rows=binding_diagnostics();assert len(rows)==54 and not any(r['result'] for r in rows)


def test_native_example_retains_breach_after_late_performance_and_release():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model())==EXAMPLE_RESULTS


@pytest.mark.parametrize('point,expected',[('start',[False,True,False]),('middle',[True,False,False]),
    ('deadline',[True,False,False]),('after',[False,True,True])])
def test_origin_is_excluded_deadline_is_included_and_late_is_distinct(point,expected):
    assert values(doc([query(n) for n in ('deadlinefulfilled','deadlinebreached','deadlinelate')]),model(performed={point}))==expected


@pytest.mark.parametrize('point,breached',[('start',False),('middle',False),('deadline',False),('after',True)])
def test_release_at_deadline_prevents_breach_but_later_release_does_not(point,breached):
    assert values(doc([query('deadlinereleased'),query('deadlinebreached'),query('deadlinelate')]),
        model(performed={'after'},released={point}))==[True,breached,True]


def test_absent_completeness_is_not_evidence_of_pending_or_breach():
    assert values(doc([query('deadlinepending',complete=truth(False)),query('deadlinebreached',complete=truth(False)),
        query('deadlinelate',complete=truth(False))]),model(performed={'after'}))==[False]*3
    assert values(doc([query('deadlinebreached'),query('deadlinelate')]),model(performed={'after'}))==[True,True]


@pytest.mark.parametrize('field',['recognized','applicable','supports'])
def test_promise_and_actual_performance_do_not_supply_missing_normative_ground(field):
    d=doc([call('speechpromise',*arguments(PROMISE)),query('promisedeadline'),query('deadlinefulfilled'),query('deadlineachieved')])
    assert values(d,model(performed={'middle'},**{field:lambda *a:False}))==[True,False,False,True]


@pytest.mark.parametrize('field',['authorized','releases'])
def test_release_needs_both_authority_and_an_actual_release_record(field):
    assert values(doc([query('deadlinereleased'),query('deadlinebreached')]),
        model(released={'middle'},**{field:lambda *a:False}))==[False,True]


def test_description_construction_does_not_execute_any_captured_interpretation():
    description=query('deadlinedescription')
    assert values(doc([eq(description,description)]),model(**{n:unknown for n in ('perform','history','order','issued','due','performance')}))==[True]


@pytest.mark.parametrize('field,original,parameters,result,reference',[
    ('action','actform',[I],C,True),('historydescription','history',[S],T,True),('orderdescription','order',[S,S],T,True),
    ('issueddescription','issued',[],S,False),('duedescription','due',[],S,False),('performancedescription','performance',[],I,False)])
def test_equivalent_but_distinct_descriptions_do_not_replace_grounded_terms(field,original,parameters,result,reference):
    replacement=quote(ref('alias') if reference else call('alias'))
    from scripts.check_shared_deadlines import base
    d=deepcopy(base());ps=[('arg'+chr(97+i),t) for i,t in enumerate(parameters)]
    d['declarations'].append(definition('alias',ps,result,call(original,*(v(n) for n,t in ps))))
    d['statements']=[dict(kind='ask',body=query('deadlinerequired',**{field:replacement}))]
    assert values(d,model(performed={'middle'}))==[False]


def test_normative_activity_and_actor_are_not_lost_in_the_adapter():
    desc=query('deadlinedescription')
    def evaluate(actor,activity):return dict(kind='evaluate',content=apply(dict(kind='disquote',description=desc),call(actor),call(activity)),situation=call('assessment'))
    assert values(doc([evaluate('person','performance'),evaluate('person','source'),evaluate('source','performance')]),
        model(performed={'middle'}))==[True,False,False]


def test_an_alternative_reason_can_support_existence_without_matching_fixed_witness():
    def another_reason(authority,reason,*rest):return authority=='a' and reason=='a' and rest[-1]=='middle'
    assert values(doc([query('deadlinefreedat'),query('deadlinereleased')]),model(releases=another_reason))==[False,True]


def test_unknown_action_stays_quoted_for_promise_requirement_and_release():
    assert values(doc([query('promisedeadline'),query('deadlinerequired'),query('deadlinereleased')]),
        model(released={'middle'},perform=unknown))==[True,True,True]
    with pytest.raises(ValueError,match='Unknown'):
        values(doc([query('deadlinepending')]),model(assessment='middle',perform=unknown))


@pytest.mark.parametrize('field',['history','order','issued','due','performance','recognized','applicable','supports','authorized','releases','perform'])
def test_unknown_inputs_are_never_substituted_with_nonperformance(field):
    with pytest.raises(ValueError,match='Unknown'):
        values(doc([query('deadlinebreached',complete=truth(False))]),model(**{field:unknown}))


def test_promise_origin_must_match_the_deadline_origin():
    d=doc([query('promisedeadline',context=call('due'))])
    m=model(**{n:lambda *a:True for n in ('occurs','presents','conveys','targets','undertakes')})
    assert values(d,m)==[False]
