from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_apparent_liberty import inclusion,values,attribution,document,CONTRASTS,alignment
from scripts.compose_apparent_liberty import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('first,second',list(product(range(16),repeat=2)))
def test_option_inclusion_matches_sets_of_the_same_people_and_activities(first,second):
    a={i for i in range(4) if first&(1<<i)};b={i for i in range(4) if second&(1<<i)}
    assert inclusion(first,second)==[a<=b,a<b]


def test_empty_scope_and_replacement_of_options_are_not_strict_improvement():
    assert inclusion(0,15,empty=True)==[True,False]
    assert inclusion(1,14)==[False,False]  # More options, but an old one is lost.
    assert inclusion(1,4)==[False,False]  # Same activity for another person.
    assert inclusion(15,15)==[True,False]


@pytest.mark.parametrize('flags',list(product((False,True),repeat=5)))
def test_civic_conditions_appearance_and_actual_mental_opportunity_are_distinct(flags):
    ca,cv,ma,mv,selected=flags
    assert values(civil_actual=ca,civil_view=cv,mental_actual=ma,mental_view=mv,selected=selected)==[
        ca,ma,ca and cv and mv and selected,ca and ma,True,ma]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_scope_norm_identity_candidate_selection_and_complete_assessment_matter(variant):
    assert values(variant=variant)[2] is False


@pytest.mark.parametrize('variant',('unknown_norm','unknown_methods','unknown_views'))
def test_unknown_evidence_is_preserved_in_quotation_and_rejected_when_needed(variant):
    assert values(variant=variant,indices=(4,))==[True]
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(2,))


def test_apparent_advantage_can_be_false_in_the_actual_context():
    assert values()==[True,False,True,False,True,False]
    assert values(mental_actual=True)==[True]*6


def test_missing_assessment_does_not_create_an_achievement_method():
    assert values(mental_actual=True,variant='unassessed_new_method')==[True,False,False,False,True,False]


@pytest.mark.parametrize('path',(SOURCE,CORE))
def test_attribution_preserves_author_scope_and_rank_without_running_content(path):
    assert attribution(path)==[True]
    for variant in ('node','author','scope','anchor'):assert attribution(path,variant)==[False]


def test_attribution_cannot_lower_the_rank_of_its_nested_evaluation():
    doc=deepcopy(document(CORE));declaration=next(d for d in doc['declarations'] if d['name']=='iacattribution')
    code=declaration['body']['arguments'][2];assert code['rank']==3;code['rank']=2
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_history_and_explicit_candidate_reading_are_retained():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements']
    assert alignment()['semantic_completion'] is False
    assert alignment()['degree_reading']=='proper_inclusion_candidate'


def test_artifacts_reproduce_and_caching_does_not_change_the_result():
    assert values(memoize=False)==values()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
