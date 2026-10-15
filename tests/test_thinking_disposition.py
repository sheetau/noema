from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_thinking_disposition import values,thinking,attribution,document,alignment,CONTRASTS,UNKNOWNS
from scripts.compose_thinking_disposition import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('hits,classified',list(product(range(8),repeat=2)))
def test_graded_orientation_allows_exceptions_but_requires_complete_assessment(hits,classified):
    expected=classified==7 and sum(w for i,w in enumerate((2,1,1)) if hits&(1<<i))>=2
    assert values(hits=hits,classified=classified,indices=(0,))==[expected]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_no_selective_omission_duplicates_or_substitution_of_the_described_target(variant):
    assert values(variant=variant,indices=(0,))==[False]


@pytest.mark.parametrize('threshold',(-1,0,Fraction(5,4)))
def test_invalid_threshold_is_not_a_disposition(threshold):
    assert values(threshold=threshold,indices=(0,))==[False]


@pytest.mark.parametrize('weights',((2,0,1),(2,-1,1)))
def test_weight_cannot_discard_an_unfavorable_occasion(weights):
    assert values(weights=weights,indices=(0,))==[False]


def test_equal_boundary_weight_scaling_order_and_stronger_criterion():
    assert values(hits=1,indices=(0,))==[True]
    assert values(hits=1,threshold=Fraction(3,4),indices=(0,))==[False]
    assert values(hits=1,weights=(6,3,3),indices=(0,))==[True]
    assert values(hits=1,weights=(1,Fraction(1,2),Fraction(1,2)),indices=(0,))==[True]
    assert values(hits=1,variant='reordered',indices=(0,))==[True]


@pytest.mark.parametrize('urge,assigned',list(product((False,True),repeat=2)))
def test_inner_calling_and_assigned_task_are_separate_readings(urge,assigned):
    assert values(urge=urge,assigned=assigned)==[True,urge,assigned]


@pytest.mark.parametrize('variant',('same_features','missing_latent','other_growth_person'))
def test_development_keeps_both_distinct_traits_in_the_same_person(variant):
    assert values(variant=variant)==[True,False,False]


def test_another_norm_source_or_unassessed_impulse_does_not_erase_known_inclination():
    assert values(variant='other_assignment_source')==[True,True,False]
    assert values(variant='unassessed_urge')==[True,False,True]


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_inputs_are_not_filled(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(0,))


@pytest.mark.parametrize('variant',('baseline','nonhuman','other_owner','no_judgment','unsupported','guided'))
def test_actual_thinking_is_checked_separately_from_orientation(variant):
    assert thinking(variant)==[variant=='baseline']


def test_candidates_and_annotation_preserve_quote_roles_without_executing_either_content():
    assert values(indices=(4,5,6))==[True,True,False]
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_quote_rank_cannot_be_reduced():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iahattribution')
    code=d['body']['arguments'][2];assert code['rank']==2;code['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_reproduction_history_and_uncached_baseline():
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['reading_unresolved'] and not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
