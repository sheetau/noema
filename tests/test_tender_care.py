from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
import pytest
from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.check_tender_care import values,source_values,attribution,review_report,document,fixture,model,DOMAIN,SCENES
from scripts.compose_tender_care import ROOT,PARENT,SOURCE,CORE,BASIS,READING,REVIEW,build,basis,reading,review,manuscript
from scripts.check_caused_choice import evaluate
from scripts.check_thinking_disposition import forbidden


@pytest.mark.parametrize('a,b',list(product(range(3),repeat=2)))
def test_maximum_allows_ties_but_not_a_stronger_comparator(a,b):
    assert values(degrees=(a,b)) == [True,True,a>=b]


@pytest.mark.parametrize('degrees',[(3,2),(2,3),(2,2),(0,0)])
def test_common_increasing_relabeling_does_not_change_the_ordinal_comparison(degrees):
    assert values(degrees=degrees) == values(degrees=tuple(2*x+5 for x in degrees))


@pytest.mark.parametrize('variant',('wrong_goal_object','goal_alias','wrong_aim_actor','other_binding','no_action','other_performer'))
def test_same_agent_act_goal_and_object_are_required(variant):
    assert values(variant=variant) == [False,False,False]


@pytest.mark.parametrize('variant',('uncared_comparator','unassessed_comparator','empty','omitted','duplicate','target_excluded'))
def test_comparison_cannot_omit_or_leave_unassessed_a_scoped_target(variant):
    assert values(variant=variant) == [True,True,False]


def test_purpose_is_not_success_and_affection_is_not_management():
    # The goal implementation is forbidden in both cases, so success is not evaluated.
    assert values(affection=False) == [True,False,False]
    assert values() == values(memoize=False) == [True,True,True]
    assert values(degrees=(-1,0)) == [True,False,False]
    assert values(degrees=(1,-1)) == [True,True,False]
    assert values(degrees=(Fraction(1,3),Fraction(1,2))) == [True,True,False]


def test_single_comparison_target_is_explicitly_permitted_not_invented_as_a_competition():
    doc=fixture();p=model();from noema.constructed_semantics import SequenceValue
    p.update(jxobjects=lambda:SequenceValue(('object',),'"individual"'),jxscope=lambda obj:obj=='object')
    p={d['name']:p.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    assert evaluate(doc,p,DOMAIN,SCENES) == [True,True,True]


@pytest.mark.parametrize('variant',('unknown_aim','unknown_comparator','unknown_degree'))
def test_unknown_assessment_is_not_false_or_a_maximum(variant):
    with pytest.raises(ValueError,match='Unknown'): values(variant=variant)


@pytest.mark.parametrize('variant,expected',[
    ('baseline',[True,True,True]),('wrong_growth_object',[False,True,False]),
    ('wrong_goal_object',[True,False,False]),('other_binding',[True,False,False]),
    ('no_action',[True,False,False]),('other_performer',[True,False,False])])
def test_unfolding_and_care_share_the_depicted_object_without_merging_their_acts(variant,expected):
    assert source_values(variant=variant) == expected


def test_comparison_is_not_bypassed_by_the_successful_unfolding_depiction():
    assert source_values(degrees=(1,2)) == [True,False,False]


@pytest.mark.parametrize('family',(False,True))
def test_attribution_and_mapping_refer_to_new_content_without_evaluating_it(family):
    assert attribution(family=family) == [True]
    assert attribution(family=family,variant='old_quote') == [False]
    assert attribution(family=family,variant='author') == [False]


def test_the_actual_manuscript_dependency_and_review_are_updated():
    old,new=document(PARENT),document(SOURCE)
    assert new['declarations'][:len(old['declarations'])] == old['declarations']
    assert new['statements'][:-1] == old['statements'][:-1]
    assert _references(new['statements'][-1]) == {'iawiatattribution'}
    assert len(new['statements']) == len(old['statements']) == 22
    inspected=review_report();rows={r['id']:r for r in inspected['obligations']}
    assert not rows['tender_care']['unconnected_candidate_roots']
    assert all(row['selected_statement_path']['statement_index']==21 for row in rows['tender_care']['structural_evidence'])
    assert rows['tender_care']['decision']=='open'
    assert rows['more_than_machine']['candidate_roots']==[]
    assert rows['dignified_treatment']['unconnected_candidate_roots']==['iaustanding','iautreatment','iavclaim','iavtreatment']
    assert inspected['templates'][0]['symbol']=='iawiatschema'
    assert len(inspected['templates'][0]['parameters'])==8
    assert not inspected['semantic_completion'] and not inspected['counts_as_translated_coverage']


def test_reproducible_definitions_meaning_conventions_and_review_packet():
    files=build()
    assert all((ROOT/path).read_text(encoding='utf-8')==text for path,text in files.items())
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading()
    assert json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))==review(files)
