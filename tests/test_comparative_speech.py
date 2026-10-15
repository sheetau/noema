from itertools import product
import json

import pytest

from noema.constructed import parse
from scripts.compose_comparative_speech import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis
from scripts.check_comparative_speech import values,attribution,setup


@pytest.mark.parametrize('performed,judgment,candidate,actual',list(product((False,True),repeat=4)))
def test_personal_comparative_speech_is_separate_from_actual_improvement(performed,judgment,candidate,actual):
    assert values(performed,judgment,candidate,actual)==[True,performed and judgment and candidate,actual]+[True]*5+[actual]


@pytest.mark.parametrize('gs,cs,gp,cp',list(product((False,True),repeat=4)))
def test_joint_policy_preserves_both_independently_selected_permissions(gs,cs,gp,cp):
    general=not gs or gp;comparative=not cs or cp;joint=general and comparative
    assert values(general_selected=gs,comparative_selected=cs,general_permission=gp,comparative_permission=cp)==[
        True,True,False,comparative,general,joint,joint,joint,False]


@pytest.mark.parametrize('variant',('other_person','other_matter','reversed_forms','other_criterion','other_subject','empty_candidates','same_form','wrong_message'))
def test_judgment_forms_topic_and_public_message_must_match(variant):
    assert values(variant=variant)==[True,False,False]+[True]*5+[False]


@pytest.mark.parametrize('variant,expected',[
    ('wrong_target',[True,True,False,False,True,False,False,False,False]),
    ('old_policy_prospects',[True,True,False,True,True,True,False,False,False]),
    ('old_safety_awareness',[True,True,False,True,True,True,True,False,False]),
    ('split_outcomes',[True,True,False,True,True,True,False,False,False]),
])
def test_joint_policy_target_and_common_realization_are_required(variant,expected):
    assert values(variant=variant)==expected


@pytest.mark.parametrize('aware,safe',list(product((False,True),repeat=2)))
def test_joint_risk_and_recognition_remain_separate(aware,safe):
    assert values(aware=aware,actual_safe=safe)==[True,True,False,True,True,True,safe,aware and safe,False]


@pytest.mark.parametrize('variant,message',[('unknown_judgment','Unknown personal judgment'),('unknown_comparison','Unknown comparison')])
def test_unknown_judgment_or_comparison_is_not_guessed(variant,message):
    with pytest.raises(ValueError,match=message):values(variant=variant)
    # Quoting and permitting that activity must not execute it or judge truth.
    assert values(variant=variant,indices=(0,3,4,5,6,7))==[True]*6


def test_constructed_action_and_its_message_have_same_uncached_result():
    assert values(indices=(0,1,2,8),memoize=False)==values(indices=(0,1,2,8))==[True,True,False,False]


def test_same_definition_under_another_name_does_not_transfer_personal_judgment():
    lookup={d['name']:d for d in setup()['document']['declarations']}
    left={key:value for key,value in lookup['jdcompare'].items() if key!='name'}
    right={key:value for key,value in lookup['jdcomparealias'].items() if key!='name'}
    assert left==right
    assert values(variant='other_criterion')==[True,False,False]+[True]*5+[False]


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_attribution_does_not_execute_any_quoted_content(path):
    assert len(attribution(parse((ROOT/path).read_text(encoding='utf-8'))))==2


def test_parent_and_artifacts_are_preserved_and_reproducible():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    parent,source=[parse((ROOT/path).read_text(encoding='utf-8')) for path in (PARENT,SOURCE)]
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert source['statements'][:-1]==parent['statements'][:-1]
    assert source['statements'][-1]!=parent['statements'][-1]
    assert len(source['statements'])==len(parent['statements'])==17
