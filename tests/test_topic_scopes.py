from itertools import product
import json

import pytest

from noema.constructed import parse
from scripts.compose_topic_scopes import ROOT, PARENT, SOURCE, CORE, BASIS, build, basis
from scripts.check_topic_scopes import PEOPLE, values, attribution


@pytest.mark.parametrize('first,second,member1,member2,grant1,grant2',list(product((False,True),repeat=6)))
def test_every_selected_topic_and_permission_must_match(first,second,member1,member2,grant1,grant2):
    selected=tuple(p for p,b in zip(PEOPLE,(first,second),strict=True) if b)
    scoped=(not first or member1) and (not second or member2)
    permitted=(not first or grant1) and (not second or grant2)
    assert values(selected,(member1,member2),(grant1,grant2)) == [scoped,scoped and permitted,
        permitted,scoped and permitted,scoped and permitted]


@pytest.mark.parametrize('variant,expected',[
    ('wrong_authority',[False,False,True,False,False]),
    ('outcome_scope',[False,False,True,False,False]),
    ('wrong_subject',[False,False,True,False,False]),
    ('wrong_norm_target',[True,False,False,False,False]),
    ('old_policy_prospects',[True,True,True,False,False]),
    ('old_safety_awareness',[True,True,True,True,False]),
])
def test_subject_scope_policy_and_recognition_do_not_transfer_to_unrelated_targets(variant,expected):
    assert values(variant=variant)==expected


@pytest.mark.parametrize('aware,safe',list(product((False,True),repeat=2)))
def test_scoped_source_retains_distinction_between_awareness_and_actual_safety(aware,safe):
    assert values(aware=aware,actual_safe=safe)==[True,True,True,safe,aware and safe]


def test_outcome_population_cannot_drop_unpermitted_selected_speaker():
    assert values(grants=(True,False),variant='late_population')==[True,False,False,False,False]


def test_unknown_scope_does_not_become_empty_or_false():
    with pytest.raises(ValueError,match='Unknown topic scope'): values(variant='unknown_domains')


@pytest.mark.parametrize('members',[(True,True),(True,False)])
def test_rules_are_invariant_under_consistent_renaming_of_individuals(members):
    assert values(members=members,rename=True)==values(members=members)


def test_scoped_policy_has_same_uncached_result():
    assert values(members=(True,False),indices=(0,1,2),memoize=False)==values(members=(True,False),indices=(0,1,2))==[False,False,True]


@pytest.mark.parametrize('path',[SOURCE,CORE])
def test_author_attribution_does_not_execute_scoped_policy_or_attitude(path):
    assert len(attribution(parse((ROOT/path).read_text(encoding='utf-8'))))==2


def test_reproduction_preserves_parent_and_revises_only_the_last_statement():
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    parent,source=[parse((ROOT/path).read_text(encoding='utf-8')) for path in (PARENT,SOURCE)]
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert source['statements'][:-1]==parent['statements'][:-1]
    assert source['statements'][-1]!=parent['statements'][-1]
    assert len(source['statements'])==len(parent['statements'])==17
