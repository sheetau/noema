from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.shared_plurality import *
from scripts.check_shared_plurality import (EXAMPLE,EXAMPLE_PEOPLE,EXPECTED,PEOPLE,ref,model,values,doc,subsets,
    action_args,action_call,object_call,unknown,membership_checks,action_checks,object_checks,coverage_checks,
    reciprocal_checks,assignment_checks,binding_diagnostics,example,example_model)


def test_two_earlier_group_definitions_are_preserved_exactly():
    shared={d['name']:d for d in composed()['declarations']}
    for d in parse((ROOT/SOURCE).read_text(encoding='utf-8'))['declarations']:
        if d['name'] in NAMES:
            assert renamed(shared[NAMES[d['name']]],{v:k for k,v in NAMES.items()})==d
    assert len(shared)==24 and all(d['kind']=='definition' for d in shared.values())


def test_all_public_native_contracts_and_roundtrip_without_new_primitives():
    d=composed();b=basis()
    assert not b['primitives']
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['definitions'])==set(b['public_contracts'])=={x['name'] for x in d['declarations']}
    for declaration in d['declarations']:
        contract=b['public_contracts'][declaration['name']]
        assert [r['sort'] for r in contract['arguments']]==[p['sort'] for p in declaration['parameters']]
        assert contract['result']==declaration['result']
        assert all(r['interpretation'] for r in contract['arguments'])


def test_finite_event_target_coverage_and_reciprocal_models():
    assert action_checks()['models']==64
    assert object_checks()['models']==256
    assert coverage_checks()['models']==256
    assert reciprocal_checks()['models']==64
    assert membership_checks()['sequences']==31


def test_two_topics_form_complete_native_statements():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model(),EXAMPLE_PEOPLE)==EXPECTED


def test_empty_group_distinguishes_mathematical_inclusion_from_plural_assertion():
    m=model(actors=lambda x:False,targets=lambda x:True,occurs=lambda *x:True,participates=lambda *x:True,
        affects=lambda *x:True,assignment=lambda x:x,related=lambda *x:True,paired=lambda *x:True)
    bodies=[call('groupincludes',ref('targets'),ref('actors')),call('groupexists',ref('actors')),
        call('groupall',ref('actors'),ref('targets')),call('groupplural',ref('actors')),
        call('groupinjection',ref('actors'),ref('assignment')),action_call('collectiveaction'),action_call('distributedaction')]
    bodies += [object_call(n) for n in ('collectiveobject','eachobject','sameobject','assignedobjects','distinctobjects','exclusiveobjects')]
    bodies += [call(n,ref('actors'),ref('related'),call('now')) for n in ('reciprocalall','reciprocalneighbors','reciprocalpairs')]
    assert values(doc(bodies),m)==[True,False,False,False,True]+[False]*11


def test_missing_target_group_is_not_a_successful_assignment():
    m=model(actors=lambda x:True,targets=lambda x:False,occurs=lambda *x:True,
        participates=lambda *x:True,affects=lambda *x:True,assignment=lambda x:x)
    bodies=[object_call(n) for n in ('collectiveobject','eachobject','sameobject','assignedobjects','distinctobjects','exclusiveobjects')]
    assert values(doc(bodies),m)==[False]*6


def test_two_independent_events_do_not_supply_one_collective_event():
    m=model(actors=lambda x:True,occurs=lambda *x:True,participates=lambda a,e,w:a==e)
    assert values(doc([action_call('collectiveaction'),action_call('distributedaction')]),m)==[False,True]


@pytest.mark.parametrize('assignment',[('a','a'),('a','b'),('b','a'),('b','b')])
def test_event_assignment_requires_each_occurrence_and_same_person_but_not_exclusive_participation(assignment):
    assert assignment_checks(assignment)['models']==64


def test_same_target_can_be_reached_through_separate_events():
    m=model(actors=lambda x:True,targets=lambda x:x=='a',occurs=lambda *x:True,
        participates=lambda a,e,w:a==e,affects=lambda e,t,w:t=='a')
    assert values(doc([object_call(n) for n in ('collectiveobject','sameobject','eachobject')]),m)==[False,True,True]


def test_noninjective_target_assignment_can_be_exclusive_without_being_distinct():
    m=model(actors=lambda x:True,targets=lambda x:True,occurs=lambda *x:True,participates=lambda *x:True,
        affects=lambda e,t,w:t=='a',assignment=lambda x:'a')
    assert values(doc([object_call(n) for n in ('assignedobjects','distinctobjects','exclusiveobjects')]),m)==[True,False,True]


def test_other_possible_objects_do_not_invalidate_a_distinct_assignment_but_do_break_exclusivity():
    m=model(actors=lambda x:True,targets=lambda x:True,occurs=lambda *x:True,participates=lambda *x:True,
        affects=lambda *x:True,assignment=lambda x:x)
    assert values(doc([object_call(n) for n in ('assignedobjects','distinctobjects','exclusiveobjects')]),m)==[True,True,False]


def test_failed_assignment_is_not_absence_of_another_valid_assignment():
    m=model(actors=lambda x:True,targets=lambda x:True,occurs=lambda *x:True,
        participates=lambda a,e,w:a==e,affects=lambda e,t,w:e!=t,assignment=lambda x:x)
    d=doc([object_call('eachobject'),object_call('distinctobjects')])
    assert values(d,m)==[True,False]
    m['assignment']=lambda x:'b' if x=='a' else 'a'
    assert values(d,m)==[True,True]


def test_participants_are_not_assumed_exhaustive_from_collective_action():
    m=model(actors=lambda x:x=='a',occurs=lambda *x:True,participates=lambda *x:True)
    d=doc([action_call('collectiveaction'),call('exactparticipants',ref('actors'),call('bob'),call('now'),ref('participates'))])
    assert values(d,m)==[True,False]


def test_negated_group_all_is_not_all_members_negated():
    neg=lam([('x',I)],op('not',call('targets',v('x'))))
    m=model(actors=lambda x:True,targets=lambda x:x=='a')
    assert values(doc([op('not',call('groupall',ref('actors'),ref('targets'))),call('groupall',ref('actors'),neg)]),m)==[True,False]


def test_membership_keeps_identity_but_count_rejects_duplicates_and_invalid_numbers():
    two=seq(call('alice'),call('bob'));dup=seq(call('alice'),call('alice'))
    invalid=[num(-1),dict(kind='number',numerator=3,denominator=2),num(1),num(3)]
    bodies=[call('membercount',two,n) for n in invalid]+[call('membercount',dup,num(2)),call('membercount',seq(),num(0))]
    assert values(doc(bodies),model())==[False]*5+[True]


def test_unknown_individual_values_are_rejected_before_membership_evaluation():
    d=doc([call('distinctmembers',seq(call('alice'),call('bob'))),call('membercount',seq(call('alice'),call('bob')),num(2))])
    with pytest.raises(ValueError,match='wrong result sort'):
        values(d,model(alice=lambda:'outside1',bob=lambda:'outside2'))


def test_group_count_and_membership_survive_reordering_but_not_alias_duplication():
    forward=seq(call('alice'),call('bob'));reverse=seq(call('bob'),call('alice'))
    d=doc([call('membercount',forward,num(2)),call('membercount',reverse,num(2))])
    assert values(d,model())==[True,True]
    assert values(d,model(bob=lambda:'a'))==[False,False]


def test_reciprocals_reject_self_only_and_singletons():
    d=doc([call(n,ref('actors'),ref('related'),call('now')) for n in ('reciprocalall','reciprocalneighbors','reciprocalpairs')])
    assert values(d,model(actors=lambda x:True,related=lambda a,b,w:a==b))==[False]*3
    assert values(d,model(actors=lambda x:x=='a',related=lambda *x:True))==[False]*3


@pytest.mark.parametrize('relation',['occurs','participates','affects'])
def test_action_components_cannot_be_combined_from_different_worlds(relation):
    m=model(actors=lambda x:True,targets=lambda x:True,occurs=lambda *xs:xs[-1]=='now',
        participates=lambda *xs:xs[-1]=='now',affects=lambda *xs:xs[-1]=='now')
    m[relation]=lambda *xs:xs[-1]=='elsewhere'
    assert values(doc([object_call('collectiveobject'),object_call('eachobject')]),m)==[False,False]


def test_all_native_action_tuple_slots_are_checked_independently():
    rows=binding_diagnostics()
    assert len(rows)==11 and sum(r['value'] for r in rows)==3


def test_unknown_relation_is_not_false_even_inside_negative_sentence():
    m=model(actors=lambda x:True,targets=lambda x:True,occurs=lambda *xs:True,participates=lambda *xs:True)
    with pytest.raises(ValueError,match='Unknown'):
        values(doc([op('not',object_call('collectiveobject'))]),m)


def test_event_type_and_target_are_preserved_in_the_two_topic_example():
    m=example_model();m['lifted']=m['checked']
    assert values(doc([object_call('collectiveobject','pianos','lifted')]),m,EXAMPLE_PEOPLE)==[False]
    m=example_model();m['checked']=lambda e,t,w:(e,t,w)==('eventa','piano','now')
    assert values(doc([object_call('eachobject','machines','checked')]),m,EXAMPLE_PEOPLE)==[False]
