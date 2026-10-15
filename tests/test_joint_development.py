from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.check_joint_development import values,source_values,attribution,document,alignment,CONTRASTS,UNKNOWNS
from scripts.compose_joint_development import ROOT,PARENT,SOURCE,CORE,BASIS,build,basis


@pytest.mark.parametrize('mtable,ytable',list(product(range(16),range(16))))
def test_all_two_cause_mediator_and_result_tables_separate_joint_change_from_each_members_necessity(mtable,ytable):
    assert values(mtable,ytable)==[
        mtable in (8,10,12,14) and ytable in (8,10),
        mtable==8 and ytable in (8,10)]


@pytest.mark.parametrize('variant',CONTRASTS)
def test_cause_population_and_distinct_declared_variables_are_required(variant):
    assert values(variant=variant)==[False,False]


@pytest.mark.parametrize('variant',('swapped_premises','unreviewed_single','no_single_solution'))
def test_full_coalition_worlds_can_hide_a_single_removal_defect(variant):
    assert values(variant=variant)==[True,False]


@pytest.mark.parametrize('variant',UNKNOWNS)
def test_unknown_equation_or_single_member_evidence_is_not_false_causation(variant):
    with pytest.raises(ValueError,match='Unknown'):values(variant=variant,indices=(1,))


def test_single_contributor_is_explicitly_allowed_with_other_background_variable_fixed():
    assert values(variant='single_contributor')==[True,True]


@pytest.mark.parametrize('bits',list(product((False,True),repeat=2)))
def test_each_persons_actual_development_is_evaluated_independently_at_one_shared_world_point(bits):
    assert source_values(state_bits=bits+(False,False),indices=(7,8))==list(bits)


def test_actual_development_judgments_and_action_methods_support_the_joint_candidate():
    assert source_values()==[True,True]
    assert source_values(indices=(2,))==[True]


def test_either_person_sufficient_differs_from_both_people_required():
    assert source_values(mtable=14)==[True,False]


@pytest.mark.parametrize('variant',('swapped_people','unreviewed_single','no_single_solution'))
def test_source_detects_person_identity_or_assessment_defects_only_exposed_by_single_removal(variant):
    assert source_values(variant=variant)==[True,False]


def test_source_unknown_single_removal_stays_unknown():
    with pytest.raises(ValueError,match='Unknown'):source_values(variant='unknown_single',indices=(1,))


def test_direct_collective_cause_without_mediator_dependence_is_rejected():
    assert source_values(ytable=12)==[False,False]


def test_same_contributors_and_cohort_are_kept_while_each_person_is_removed():
    calls=[]
    assert source_values(indices=(1,),calls=calls)==[True]
    selected=[row for row in calls if row[0]=='contributors']
    assert selected and all(row[1:]==('community','end') for row in selected)
    probes=[row for row in calls if row[0]=='probe']
    assert probes and all(row[1]=='community' and row[2] in ('person','other') and row[3]=='topicone' for row in probes)
    assert any(row[4:]==(True,False,False,False) for row in probes)
    assert any(row[4:]==(False,True,False,False) for row in probes)
    assert any(row[4:]==(True,True,False,False) for row in probes)


def test_absent_changes_are_assessed_in_a_valid_single_removal_world():
    assert source_values(state_bits=(True,False,False,False),indices=(3,4,5,6))==[True,False,True,False]


def test_old_conditional_and_new_joint_candidate_are_attributed_without_execution():
    for path in (CORE,SOURCE):
        assert attribution(path)==[True]
        for variant in ('node','author','scope','context','missing_member','missing_joint'):
            assert attribution(path,variant)==[False]


def test_joint_template_quote_keeps_rank_two():
    doc=deepcopy(document(CORE));d=next(d for d in doc['declarations'] if d['name']=='iapattribution')
    code=d['body']['arguments'][2];assert code['rank']==2;code['rank']=1
    with pytest.raises(ValueError):parse(format_graph(doc,'compact'))


def test_uncached_generic_baseline_parent_preservation_and_reproducible_artifacts():
    assert values(memoize=False)==values()
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])]==old['declarations']
    assert new['statements'][:-1]==old['statements'][:-1]
    assert new['statements'][-1]['body']['arguments'][0]==old['statements'][-1]['body']
    assert alignment()['collective_conditional_unfilled'] and not alignment()['adds_new_text_coverage']
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
