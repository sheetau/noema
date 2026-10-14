from copy import deepcopy
from itertools import product
import json

import pytest

from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.check_public_permission_risk import values, setup, model_for, attribution, DOMAIN, SCENES
from scripts.compose_public_permission_risk import ROOT, PARENT, SOURCE, CORE, BASIS, build, basis


@pytest.mark.parametrize('safe,bad,gs,gb',list(product((False,True),repeat=4)))
def test_same_policy_must_hold_in_every_nonempty_prospective_outcome(safe,bad,gs,gb):
    selected=tuple(p for p,b in (('safe',safe),('bad',bad)) if b)
    coherent=bool(selected) and (not safe or gs) and (not bad or gb)
    assert values(selected=selected,grants=(gs,gb))==[True]*3+[coherent,coherent and not bad,coherent and bad,coherent and not bad,False,False]


@pytest.mark.parametrize('variant',('wrong_policy','wrong_ruler','wrong_role','wrong_target','conflict','second_person_unpermitted'))
def test_unrelated_policy_permission_and_population_changes_do_not_substitute(variant):
    assert values(variant=variant)==[True]*3+[False]*6


@pytest.mark.parametrize('performed,actual_grant',list(product((False,True),repeat=2)))
def test_prospective_safety_is_separate_from_actual_grant_and_actual_speech(performed,actual_grant):
    assert values(performed=performed,actual_grant=actual_grant)==[True]*5+[False,True,performed,actual_grant]


def test_using_ones_faculty_in_another_activity_does_not_qualify_this_public_act():
    assert values(performed=True,variant='other_use_activity')==[True]*5+[False,True,False,False]


def test_harm_outside_the_selected_outcomes_is_not_counted():
    assert values(selected=('safe','bad'),harm=False)==[True]*5+[False,True,False,False]


@pytest.mark.parametrize('variant,message',[('unknown_prospects','Policy prospects are unknown'),('unknown_harm','Adverse outcome is unknown')])
def test_unknown_risk_information_is_not_filled_with_no_harm(variant,message):
    with pytest.raises(ValueError,match=message): values(variant=variant)


def test_policy_evaluation_does_not_execute_the_permitted_action():
    data=setup(); doc=deepcopy(data['document']); doc['statements']=doc['statements'][:7]
    staged={**data,'document':doc}; model=model_for(staged)
    def forbidden(*args): raise AssertionError('Action execution was required by permission')
    for name in ('ab','ac','dg','f3','f2','jdaudience','jdvoices'): model[name]=forbidden
    result=evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,max_steps=8_000_000)
    assert [r['value'] for r in result]==[True]*5+[False,True]


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_fragment_attribution_does_not_assert_or_execute_its_risk_content(path):
    assert len(attribution(parse((ROOT/path).read_text(encoding='utf-8'))))==2


def test_manuscript_preservation_and_exact_reproduction():
    texts=build(); assert all((ROOT/p).read_text(encoding='utf-8')==t for p,t in texts.items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    parent,source=[parse((ROOT/p).read_text(encoding='utf-8')) for p in (PARENT,SOURCE)]
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert source['statements'][:-1]==parent['statements']
    assert len(source['statements'])==17
