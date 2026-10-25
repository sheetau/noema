from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.shared_conversation import *
from scripts.check_shared_conversation import (doc,values,model,unknown,state,claim,ref,quote,seq,
    accepted,withdrawn,corrected,linked,INITIAL,ADOPTED,CORRECTED,state_checks,grounded_checks,binding_diagnostics,
    example,example_model,EXAMPLE,EXAMPLE_RESULTS)


def test_published_sources_contracts_and_exact_reused_declarations():
    d=composed();b=basis();byname={x['name']:x for x in d['declarations']}
    assert len(byname)==20 and len(b['definitions'])==19 and len(MEANINGS)==14
    assert set(b['primitives'])=={'rationaladd'}
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['public_contracts'])==set(byname)
    for source in SOURCES:
        old={x['name']:x for x in parse((ROOT/source['document']).read_text(encoding='utf-8'))['declarations']}
        ob=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        for n in source['names']:
            assert byname[n]==old[n]
            assert b['public_contracts'][n]==ob['public_contracts'][n]
            for field in ('definitions','primitives'):
                if n in ob[field]:assert b[field][n]==ob[field][n]
    for x in raw()['declarations']:
        c=b['public_contracts'][x['name']]
        types=x['parameters'] if x['kind']=='primitive' else [p['sort'] for p in x['parameters']]
        assert types==[p['sort'] for p in c['arguments']] and x['result']==c['result']
        assert len(set(p['role'] for p in c['arguments']))==len(types)


def test_finite_state_pairs_and_independent_social_flags():
    assert state_checks()==dict(models=256,people=2,descriptions=2,checks_per_model=18)
    assert grounded_checks()==dict(models=128,explicit_social_flags=3,possible_after_states=16)


def test_all_social_tuple_slots_are_bound_independently():
    rows=binding_diagnostics();assert len(rows)==38 and not any(r['result'] for r in rows)


def test_retained_history_connects_partial_answers_and_preserves_other_person():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model(),('start','middle','end'))==EXAMPLE_RESULTS
    from scripts.shared_answers import composed as answers
    old={x['name']:x for x in answers()['declarations']}
    for x in example()['declarations']:
        if x['name'] in old:assert x==old[x['name']]


@pytest.mark.parametrize('owners,claims',[([],['firstform']),(['aki'],[]),(['aki','nao'],['firstform'])])
def test_misaligned_state_is_invalid_even_if_a_target_position_matches(owners,claims):
    bad=[seq(I,[call(x) for x in owners]),seq(D,[claim(x) for x in claims])]
    assert values(doc([call('commitmentvalid',*bad),call('commitmenthas',*bad,call('aki'),claim()),
        call('commitmentsame',*bad,*bad)]),model())==[False,False,False]


def test_empty_state_and_duplicate_records_have_explicit_set_semantics():
    empty=state([]);twice=state(ADOPTED+ADOPTED)
    assert values(doc([call('commitmentvalid',*empty),call('commitmenthas',*empty,call('nao'),claim()),
        call('commitmentsame',*twice,*state(ADOPTED)),withdrawn(before=ADOPTED+ADOPTED),
        withdrawn(before=ADOPTED+ADOPTED,after=ADOPTED)]),model())==[True,False,True,True,False]


def test_pair_reordering_preserves_state_but_swapping_owners_alone_does_not():
    original=state(ADOPTED);reverse=state(list(reversed(ADOPTED)));bad=[reverse[0],original[1]]
    assert values(doc([call('commitmentsame',*original,*reverse),call('commitmentsame',*original,*bad)]),model())==[True,False]


def test_repeated_acceptance_is_not_a_new_addition():
    a=state(ADOPTED)
    assert values(doc([accepted(before=ADOPTED),call('commitmentincluded',*a,*a,call('nao'),claim()),
        call('commitmentadded',*a,*a,call('nao'),claim())]),model())==[True,True,False]


@pytest.mark.parametrize('builder',[accepted,withdrawn,corrected])
def test_other_persons_adoption_cannot_disappear_during_a_change(builder):
    target=ADOPTED if builder is accepted else INITIAL if builder is withdrawn else CORRECTED
    changed=[p for p in target if p[0]!='aki']
    assert values(doc([builder(after=changed)]),model())==[False]


def test_withdrawal_requires_previous_adoption_and_does_not_add_a_denial():
    assert values(doc([withdrawn(before=INITIAL)]),model())==[False]
    d=doc([withdrawn(after=INITIAL+[('nao','negativeform')])]) if False else None
    # Define the negative content explicitly; recording it would be an extra
    # adoption, whereas withdrawal removes only the specified old record.
    from scripts.check_shared_conversation import base
    d=deepcopy(base())
    negative=dict(kind='message',force='assert',content=dict(kind='content',variable='world',body=op('not',call('payload',v('subject'),v('world')))))
    d['declarations'].append(definition('negativeform',[('subject',I)],U,negative))
    d['statements']=[dict(kind='ask',body=withdrawn(after=INITIAL+[('nao','negativeform')]))]
    assert values(d,model())==[False]
    assert values(doc([withdrawn()]),model())==[True]


def test_correction_to_an_already_present_description_keeps_that_record():
    before=ADOPTED+[('nao','secondform')]
    assert values(doc([corrected(before=before),corrected(before=INITIAL)]),model())==[True,False]
    same=corrected();same['arguments'][6]=same['arguments'][5]
    assert values(doc([same]),model())==[False]


@pytest.mark.parametrize('payload',[True,False])
def test_equitruth_content_does_not_collapse_distinct_recorded_descriptions(payload):
    assert values(doc([accepted(),withdrawn(),corrected()]),model(payload=lambda *a:payload))==[True,True,True]


def test_unknown_message_truth_is_not_evaluated_by_state_changes():
    assert values(doc([accepted(),withdrawn(),corrected(),linked()]),model())==[True]*4
    body=dict(kind='evaluate',content=dict(kind='message_content',message=dict(kind='disquote',description=claim())),situation=call('now'))
    with pytest.raises(ValueError,match='Unknown'):values(doc([body]),model())


def test_subject_description_must_denote_the_same_presented_subject():
    body=accepted();body['arguments'][-1]=quote(call('nao'))
    body['arguments'][3]['items'][1]=claim(subject='nao')
    # Both the stored description and grounding use the new description. The
    # mismatch is specifically between its denotation and the subject slot.
    assert values(doc([body]),model())==[False]
    body['arguments'][7]=call('nao')
    assert values(doc([body]),model(**{n:lambda *a:True for n in ('conveys','receives','understands','accepts')}))==[True]


def test_unknown_subject_denotation_is_rejected_even_when_content_stays_quoted():
    d=doc([accepted()]);d['declarations'].append(dict(kind='primitive',name='unidentified',parameters=[],result=I))
    d['statements'][0]['body']['arguments'][-1]=quote(call('unidentified'))
    with pytest.raises(ValueError,match='Unknown'):values(d,model(unidentified=unknown))


@pytest.mark.parametrize('change',['conversation','state','time'])
def test_history_link_rejects_wrong_conversation_state_or_direction(change):
    body=linked()
    if change=='conversation':body['arguments'][1]=call('nao')
    elif change=='state':body['arguments'][4:6]=state(INITIAL)
    else:body['arguments'][6:8]=[call('then'),call('now')]
    assert values(doc([body]),model())==[False]


@pytest.mark.parametrize('name',['accepts','withdraws','corrects','before','rationaladd'])
def test_unknown_grounding_or_arithmetic_is_not_a_negative_record(name):
    body=accepted() if name in ('accepts','rationaladd') else withdrawn() if name=='withdraws' else corrected() if name=='corrects' else linked()
    with pytest.raises(ValueError,match='Unknown'):values(doc([body]),model(**{name:unknown}))
