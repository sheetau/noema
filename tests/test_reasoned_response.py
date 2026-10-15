from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_reasoned_response import values,source_values,attribution,document,alignment,CONTRASTS,UNKNOWNS,SOURCE_CONTRASTS
from scripts.compose_reasoned_response import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('counts',list(product(range(4),repeat=3)))
def test_three_point_nested_response_profiles_have_two_bounded_strict_increases(counts):
    expected=counts[1]==counts[0]+1 and counts[2]==counts[1]+1
    assert values(tuple((1<<c)-1 for c in counts))==[True,expected]


def test_reviewed_absence_single_response_and_plateau_are_distinct():
    assert values((0,0,0))==[True,False]
    assert values((0,1,1))==[True,False]
    assert values((0,0,3),bound=2)==[True,False]
    assert values((0,1,1,3))==[True,True]
    assert values((1,6,7))==[True,False]  # Count growth hides loss of a former topic.


@pytest.mark.parametrize('bound',(0,-1,'1/2'))
def test_nonpositive_or_too_small_bounds_cannot_accept_growth(bound):
    assert values(bound=bound,indices=(1,))==[False]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_scope_assessment_subject_and_temporal_defects_do_not_count_as_growth(variant):
    assert values(variant=variant,indices=(1,))==[False]


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_required_inputs_are_not_fabricated_as_absent_response(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(1,))


def test_evaluation_and_topic_order_do_not_imply_a_change():
    assert values(variant='unclassified')==[False,False]
    assert values(variant='other_person')==[True,False]
    assert values(variant='reordered')==[True,True]


def test_actual_anchor_can_lack_judgments_while_hypothetical_responses_expand():
    assert source_values()==[True,True,False]
    assert source_values(state_bits=(True,False,True))==[True,False,False]


@pytest.mark.parametrize('variant',SOURCE_CONTRASTS)
def test_response_uses_same_topic_person_own_faculty_supported_reason_and_no_guidance(variant):
    assert source_values(variant=variant,indices=(1,))==[False]


def test_natural_and_forced_worlds_keep_the_same_actual_topic_catalogue_and_bound():
    calls=[]
    assert source_values(indices=(2,),calls=calls)==[True]
    for kind in ('topics','bound'):
        rows=[r for r in calls if r[0]==kind]
        assert rows and all(r[1:]==('person','end') for r in rows)
    probes=[r for r in calls if r[0]=='probe']
    assert probes and all(r[1]=='person' and r[2] in ('topicone','topictwo') for r in probes)
    assert any(r[4:]==(True,False,False) for r in probes)
    assert any(r[4:]==(False,False,False) for r in probes)


@pytest.mark.parametrize('options',({'ytable':12},{'variant':'unreviewed_joint'},{'variant':'single_response'}))
def test_full_conditional_needs_the_profile_as_a_reviewed_causal_mediator(options):
    assert source_values(indices=(2,),**options)==[False]


def test_direct_and_mediated_joint_contribution_is_still_allowed():
    assert source_values(ytable=8,indices=(2,))==[True]


def test_unknown_joint_assessment_and_unknown_probe_remain_unknown():
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_joint',indices=(2,))
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_probe',indices=(1,))


def test_both_readings_and_remainder_keep_identity_across_the_completed_candidate():
    calls=[]
    assert source_values(indices=(2,3),calls=calls)==[True,True]
    rest=[r for r in calls if r[0]=='remaining']
    assert rest and all(r[2:]==('person','end','after') for r in rest)
    assert any(code_is(r[1],'iahinner',1) for r in rest)
    assert any(code_is(r[1],'iahvocation',1) for r in rest)
    assert source_values(remaining=False,indices=(2,))==[False]


def test_false_development_does_not_force_an_actual_result_or_unknown_probe():
    assert source_values(urge=False,assigned=False,variant='unknown_probe',indices=(2,3))==[True,True]


def test_attribution_preserves_context_without_asserting_its_quoted_content():
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context'):assert attribution(path,variant)==[False]


def test_template_quote_rank_cannot_be_lowered():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iamattribution')
    code=d['body']['arguments'][2];assert code['rank']==2;code['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_baseline_and_parent_and_reproducible_artifacts():
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert not alignment()['mediator_content_unfilled'] and alignment()['mediator_reading_unresolved']
    assert not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
