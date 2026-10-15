from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_cohort_response import values,source_values,expected,attribution,document,alignment,CONTRASTS,UNKNOWNS,SOURCE_CONTRASTS
from scripts.compose_cohort_response import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('profile',list(product(range(4),repeat=3)))
def test_all_two_person_one_topic_profiles_against_independent_bitset_oracle(profile):
    assert values(profile)==[True,expected(profile)]


@pytest.mark.parametrize('mask',range(16))
def test_same_topic_for_different_people_counts_as_distinct_response_pairs(mask):
    topics=(('topicone','topictwo'),('topicone','topictwo'))
    assert values((mask,mask,mask),topics=topics,indices=(2,3))==[True,True]


def test_heterogeneous_topics_are_counted_per_person_without_requiring_equal_catalogues():
    topics=(('topicone','topictwo'),('topicone',))
    assert values((1,3,7),topics=topics,indices=(0,1,2,3))==[True,True,True,True]
    assert values((1,6,7),topics=topics)==[True,False]  # More pairs can hide a loss.


def test_plateau_and_assessed_absence_differ_from_one_jump_or_missing_evaluation():
    assert values((0,1,1,3))==[True,True]
    assert values((0,0,0))==[True,False]
    assert values((0,0,3),bound=2)==[True,False]
    assert values(variant='unclassified_other')==[False,False]


@pytest.mark.parametrize('bound',(0,-1,'1/2'))
def test_nonpositive_and_too_small_bounds_do_not_admit_growth(bound):
    assert values(bound=bound,indices=(1,))==[False]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_invalid_cohorts_topics_histories_assessment_or_outsider_responses_fail(variant):
    assert values(variant=variant,indices=(1,))==[False]


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_scope_or_evidence_is_not_false_response(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(1,))


def test_reordering_exact_catalogues_does_not_change_the_result():
    topics=(('topicone','topictwo'),('topicone','topictwo'))
    assert values((0,1,3),topics=topics,variant='reordered')==values((0,1,3),topics=topics)


def test_one_change_in_each_of_two_people_can_form_two_collective_stages():
    assert source_values()==[True,True,False,False,False]
    # Each individual is reviewed, so the two False values are not missing data.
    assert source_values(indices=(5,6))==[True,True]


@pytest.mark.parametrize('variant',SOURCE_CONTRASTS)
def test_source_requires_same_community_person_topic_own_faculty_and_supported_independent_judgments(variant):
    assert source_values(variant=variant,indices=(1,))==[False]


@pytest.mark.parametrize('variant',('unknown_members','unknown_classification','unknown_probe'))
def test_unknown_source_cohort_or_probe_stays_unknown(variant):
    with pytest.raises(ValueError,match='Unknown'):source_values(variant=variant,indices=(1,))


def test_model_world_changes_do_not_exchange_the_population_or_personal_topic_catalogues():
    for bits,want in (((True,True,True),True),((False,False,False),False),((True,False,True),False)):
        calls=[]
        assert source_values(state_bits=bits,indices=(0,1),calls=calls)==[True,want]
        for kind in ('members','population','topics'):
            rows=[r for r in calls if r[0]==kind]
            assert rows and all(r[1:]==('community','end') for r in rows)
        probes=[r for r in calls if r[0]=='probe']
        assert probes and all(r[1]=='community' and r[2] in ('person','other') and r[3]=='topicone' for r in probes)


def test_both_attributions_are_kept_and_do_not_assert_their_quoted_contents():
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context','missing_individual','missing_cohort'):
            assert attribution(path,variant)==[False]


def test_cohort_function_quote_has_its_own_rank():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='ianattribution')
    code=d['body']['arguments'][2];assert code['rank']==1;code['rank']=0
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_generic_baseline_parent_preservation_and_reproducible_artifacts():
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert new['statements'][-1]['body']['arguments'][0]==old['statements'][-1]['body']
    assert not alignment()['collective_causal_integration'] and not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
