from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_faculty_opportunities import (growth,opportunities,values,attribution,document,alignment,CONTRASTS,UNKNOWNS)
from scripts.compose_faculty_opportunities import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('before,after',list(product(range(4),repeat=2)))
def test_growth_is_strict_inclusion_of_the_same_persons_activity_capacities(before,after):
    first={i for i in range(2) if before&(1<<i)};last={i for i in range(2) if after&(1<<i)}
    assert growth(before,after)==[first<last]


@pytest.mark.parametrize('a,b,t',list(product((False,True),repeat=3)))
def test_growth_needs_assessed_endpoints_and_forward_time(a,b,t):
    assert growth(assessed_before=a,assessed_after=b,ordered=t)==[a and b and t]


@pytest.mark.parametrize('first,second,joint',list(product((False,True),repeat=3)))
def test_each_faculty_can_use_its_own_method_without_one_joint_method(first,second,joint):
    assert opportunities(first=first,second=second,joint=joint)==[joint or first and second,joint]


def test_empty_scope_equal_capacity_and_replacement_are_not_growth():
    assert growth(variant='empty')==[False]
    assert growth(variant='wrong_person')==[False]
    assert growth(1,1)==[False]
    assert growth(1,2)==[False]
    assert opportunities(empty=True)==[False,False]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_source_keeps_all_people_faculties_goals_and_assessments(variant):
    assert values(variant=variant,indices=(2,3))==[False,False]


@pytest.mark.parametrize('joint',(False,True))
def test_actual_full_contrast_uses_separate_opportunity_definition(joint):
    assert values(joint=joint)==[True,joint,True,True,True,True]


def test_one_bad_off_solution_cannot_be_hidden_by_a_good_off_solution():
    assert values(table=2,indices=(0,2,3,4))==[True,True,False,False]


def test_proven_success_survives_another_unassessed_result_method():
    assert values(variant='first_person_unassessed_result_method',indices=(0,2,3,4))==[True]*4


def test_one_persons_confirmed_growth_cannot_fill_another_persons_unassessed_activity():
    assert values(variant='extra_unassessed_result_method',indices=(0,2,3,4))==[True,False,False,False]


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_scope_time_or_methods_can_be_quoted_but_not_filled(variant):
    assert values(variant=variant,indices=(5,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(0,))


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_source_attribution_preserves_identity_without_asserting_actual_growth(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','anchor'):assert attribution(path,variant)==[False]


def test_rank_of_nested_content_cannot_be_lowered():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iaeattribution')
    code=d['body']['arguments'][2];assert code['rank']==3;code['rank']=2
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_history_and_partial_reading_are_preserved():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['per_faculty_not_joint'] and not alignment()['semantic_completion']


def test_artifacts_and_generic_uncached_evaluation_reproduce():
    assert growth(memoize=False)==growth()
    assert opportunities(memoize=False)==opportunities()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
