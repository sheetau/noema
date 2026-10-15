from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_cohort_mediation import values,source_values,expected,attribution,document,alignment,CONTRASTS,UNKNOWNS
from scripts.compose_cohort_mediation import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('profile',list(product(range(4),repeat=3)))
def test_cohort_action_methods_match_independent_two_person_profile_oracle(profile):
    assert values(profile)==[True,expected(profile)]


@pytest.mark.parametrize('variant',('no_skip','other_performer'))
def test_one_sided_ability_or_someone_elses_execution_is_not_personal_choice(variant):
    assert values(variant=variant)==[True,False]


def test_source_evaluates_collective_judgments_and_action_choices_without_individual_two_stage_growth():
    assert source_values()==[True,True,True,True,True,False,False]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_wrong_cohort_missing_evidence_or_changed_counterfactual_history_rejects_mediation(variant):
    assert source_values(variant=variant,indices=(0,))==[False]


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_required_worlds_methods_and_judgments_remain_unknown(variant):
    with pytest.raises(ValueError,match='Unknown'):source_values(variant=variant,indices=(0,))


def test_mediator_is_required_even_when_it_naturally_tracks_the_cause():
    assert source_values(ytable=12,indices=(0,))==[False]
    assert source_values(ytable=8,indices=(0,))==[True]


def test_each_world_preserves_same_cohort_personal_topics_and_activities():
    calls=[]
    assert source_values(indices=(0,),calls=calls)==[True]
    populations=[r for r in calls if r[0]=='population']
    assert populations and all(r[1:]==('community','end') for r in populations)
    for kind in ('topics','activities'):
        rows=[r for r in calls if r[0]==kind]
        assert rows and all(r[1]=='community' and r[2] in ('person','other') and r[3]=='end' for r in rows)
    probes=[r for r in calls if r[0]=='probe']
    assert any(r[4:]==(False,False,False) for r in probes)
    assert any(r[4:]==(True,False,False) for r in probes)
    assert any(r[4:]==(True,True,True) for r in probes)


def test_valid_but_different_joint_history_is_not_a_substitute_for_the_causes_history():
    # An extra point after the interval is individually valid in the cohort model;
    # full history matching still rejects using it as the same causal world.
    assert source_values(variant='different_joint_history',state_bits=(True,False,False),indices=(1,3,9))==[True,True,False]
    assert source_values(variant='different_joint_history',indices=(0,))==[False]


def test_reviewed_absence_is_distinct_from_missing_joint_assessments():
    assert source_values(state_bits=(True,False,False),indices=(1,2,3,4))==[True,False,True,False]
    assert source_values(variant='unassessed_joint',state_bits=(True,False,False),indices=(1,))==[False]
    assert source_values(variant='unreviewed_joint',state_bits=(True,False,False),indices=(3,))==[False]


def test_both_readings_pass_the_same_actor_community_and_interval_to_the_remainder():
    calls=[]
    assert source_values(indices=(5,6),calls=calls)==[True,True]
    rest=[r for r in calls if r[0]=='remaining']
    assert rest and all(r[2:]==('person','community','end','after') for r in rest)
    assert any(code_is(r[1],'iahinner',1) for r in rest)
    assert any(code_is(r[1],'iahvocation',1) for r in rest)
    assert source_values(remaining=False,indices=(5,))==[False]


def test_false_antecedent_does_not_assert_collective_growth_or_evaluate_unknown_methods():
    assert source_values(urge=False,assigned=False,variant='unknown_available',indices=(5,6))==[True,True]


def test_attribution_preserves_context_without_asserting_the_quoted_causal_candidate():
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_integrated_higher_order_template_keeps_rank_two():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iaoattribution')
    code=d['body']['arguments'][2];assert code['rank']==2;code['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_generic_baseline_parent_preservation_and_artifact_reproducibility():
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert alignment()['collective_effect_causal_integration'] and alignment()['collective_cause_unresolved']
    assert not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
